    # -*- coding: utf-8 -*-
"""Creator plugin for creating Bgeo Cache."""
from openpype.hosts.houdini.api import plugin
# from openpype.pipeline import CreatedInstance

import hou


class CreateBgeoCache(plugin.HoudiniCreator):
    """Geometry to Bgeo"""
    identifier = "io.openpype.creators.houdini.bgeocache"
    name = "bgeocache"
    label = "Bgeo Cache"
    family = "bgeocache"
    icon = "code-fork"

    def create(self, subset_name, instance_data, pre_create_data):
        import hou

        instance_data.pop("active", None)
        instance_data.update({"node_type": "geometry"})

        instance = super(CreateBgeoCache, self).create(
            subset_name,
            instance_data,
            pre_create_data)  # type: CreatedInstance

        instance_node = hou.node(instance.get("instance_node"))
        parms = {
            "sopoutput": "$HIP/pyblish/{}.$F4.bgeo.sc".format(subset_name),
            "initsim": True,
            "trange": 1
        }

        if self.selected_nodes:
            parms["soppath"] = self.selected_nodes[0].path()

        instance_node.setParms(parms)

    def get_network_categories(self):
        return [
            hou.ropNodeTypeCategory(),
            hou.sopNodeTypeCategory()
        ]
