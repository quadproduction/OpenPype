import hou

import pyblish.api

from openpype.hosts.houdini.api import lib


class CollectInstances(pyblish.api.ContextPlugin):
    """Gather instances by all node in out graph and pre-defined attributes

    This collector takes into account assets that are associated with
    an specific node and marked with a unique identifier;

    Identifier:
        id (str): "pyblish.avalon.instance

    Specific node:
        The specific node is important because it dictates in which way the
        subset is being exported.

        alembic: will export Alembic file which supports cascading attributes
                 like 'cbId' and 'path'
        geometry: Can export a wide range of file types, default out

    """

    order = pyblish.api.CollectorOrder - 0.01
    label = "Collect Instances"
    hosts = ["houdini"]

    def process(self, context):

        nodes = hou.node("/out").children()
        nodes += hou.node("/obj").children()

        # Include instances in USD stage only when it exists so it
        # remains backwards compatible with version before houdini 18
        stage = hou.node("/stage")
        if stage:
            nodes += stage.recursiveGlob("*", filter=hou.nodeTypeFilter.Rop)

        for node in nodes:

            if not node.parm("id"):
                continue

            if node.evalParm("id") != "pyblish.avalon.instance":
                continue

            # instance was created by new creator code, skip it as
            # it is already collected.
            if node.parm("creator_identifier"):
                continue

            has_family = node.evalParm("family")
            assert has_family, "'%s' is missing 'family'" % node.name()

            self.log.info(
                "Processing legacy instance node {}".format(node.path())
            )

            data = lib.read(node)
            # Check bypass state and reverse
            if hasattr(node, "isBypassed"):
                data.update({"active": not node.isBypassed()})

            # temporarily translation of `active` to `publish` till issue has
            # been resolved.
            # https://github.com/pyblish/pyblish-base/issues/307
            if "active" in data:
                data["publish"] = data["active"]

            # Create nice name if the instance has a frame range.
            label = data.get("name", node.name())
            label += " (%s)" % data["asset"]  # include asset in name

            instance = context.create_instance(label)

            # Include `families` using `family` data
            instance.data["families"] = [instance.data["family"]]

            instance[:] = [node]
            instance.data["instance_node"] = node.path()
            instance.data.update(data)

        def sort_by_family(instance):
            """Sort by family"""
            return instance.data.get("families", instance.data.get("family"))

        # get connected node to add as dependencies of current node
        for instance in context:
            if not instance.data.get("instance_node"):
                continue

            ropnode = hou.node(instance.data["instance_node"])
            dependencies = ['']
            dependencies = self.get_parent(ropnode, dependencies)
            # remove duplicate name of dependencies list 
            dependencies = list(set(dependencies))
            instance.data["dependencies"] = dependencies

            dependencies_inst = []
            for context_instance in context:
                if context_instance.data["name"] in instance.data["dependencies"] :
                    dependencies_inst.append(context_instance)
            instance.data["dependencies"] = dependencies_inst

            # define order priority 
            instance.data["dependencyOrder"] = "order" + str(len(dependencies))
            instance.data["dependencyOrder"] = [instance.data["dependencyOrder"]] 
            self.log.debug("dependencies {}".format(instance.data["dependencies"]))

            # used to get subset to reload
            dependenciesName = []
            for depencyName in dependencies:
                dependenciesName.append("{}_{}".format(instance.data["asset"], depencyName))
            instance.data["dependenciesName"] = ",".join(dependenciesName)
            

        def sort_by_dependency(instance):
            """Sort by dependency"""
            return instance.data.get("dependencyOrder", instance.data.get("dependencyOrder"))
        
        if instance.data["dependencies"]:
            context[:] = sorted(context, key=sort_by_dependency)
        self.log.debug("Context {}".format(context))

        return context

    def get_parent(self, node, list):
        """Get the connected node as input of node

        Args:
            node : ropNode
            list : dependencie list

        Returns:
            list: a list of inputs of  designated node
        """   
        if node.inputConnections() :
            for parent in node.inputConnections():
                parent_node = parent.inputNode()
                list.append(parent_node.name())
                self.get_parent(parent_node, list)

        return list
    
    def get_frame_data(self, node):
        """Get the frame data: start frame, end frame and steps
        Args:
            node(hou.Node)

        Returns:
            dict

        """

        data = {}

        if node.parm("trange") is None:
            return data

        if node.evalParm("trange") == 0:
            return data

        data["frameStart"] = node.evalParm("f1")
        data["frameEnd"] = node.evalParm("f2")
        data["byFrameStep"] = node.evalParm("f3")

        return data
