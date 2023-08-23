# -*- coding: utf-8 -*-
"""Creator plugin for creating VDB Caches."""
from openpype.hosts.houdini.api import plugin
from openpype.pipeline import CreatedInstance
from openpype.lib import BoolDef

import hou


class CreateVDBCache(plugin.HoudiniCreator):
    """OpenVDB from Geometry ROP"""
    identifier = "io.openpype.creators.houdini.vdbcache"
    name = "vbdcache"
    label = "VDB Cache"
    family = "vdbcache"
    icon = "cloud"

    def create(self, subset_name, instance_data, pre_create_data):
        import hou

        instance_data.pop("active", None)
        instance_data.update({"node_type": "geometry"})
        instance_data["farm"] = pre_create_data.get("farm")

        instance = super(CreateVDBCache, self).create(
            subset_name,
            instance_data,
            pre_create_data)  # type: CreatedInstance

        instance_node = hou.node(instance.get("instance_node"))
        parms = {
            "sopoutput": "$HIP/pyblish/{}.$F4.vdb".format(subset_name),
            "initsim": True,
            "trange": 1
        }

        if self.selected_nodes:
            parms["soppath"] = self.selected_nodes[0].path()

        instance_node.setParms(parms)

        selectedNode = hou.selectedNodes()[0]
        parentNode = selectedNode.parent()
        filenode = parentNode.createNode("file")
        filenode.setName("FILE_{}".format(subset_name), unique_name=True)

        filenode.setInput(0,selectedNode,0)
        filenode.moveToGoodPosition()

        if len(selectedNode.outputs()) > 0:
            for outNode in selectedNode.outputs():
                outNode.setInput(0,filenode,0)
                
        filenode.setInput(0,selectedNode,0)
        filenode.moveToGoodPosition()

        newPath = parms["sopoutput"]
        hip = hou.text.expandString("$HIP")
        newPath = newPath.replace("$HIP", hip)
        filenode.parm("file").set(newPath)

    def get_network_categories(self):
        return [
            hou.ropNodeTypeCategory(),
            hou.sopNodeTypeCategory()
        ]

    def get_pre_create_attr_defs(self):
        attrs = super(CreateVDBCache, self).get_pre_create_attr_defs()
        return attrs + [
            BoolDef("farm",
                    label="Submitting to Farm",
                    default=False)
        ]