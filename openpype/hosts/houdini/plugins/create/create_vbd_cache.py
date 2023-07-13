# -*- coding: utf-8 -*-
"""Creator plugin for creating VDB Caches."""
from openpype.hosts.houdini.api import plugin
from openpype.pipeline import CreatedInstance
from openpype.client import get_project, get_assets
from openpype.pipeline import legacy_io
from openpype.lib import EnumDef, TextDef, BoolDef

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

    def get_network_categories(self):
        return [
            hou.ropNodeTypeCategory(),
            hou.sopNodeTypeCategory()
        ]
    
    def get_pre_create_attr_defs(self):
        attrs = super(CreateVDBCache, self).get_pre_create_attr_defs()

        project_name = legacy_io.active_project()
        asset_list = [""]
        for asset in get_assets(project_name, fields=["name"]):
            asset_list.append(asset["name"])
        
        fx_list = ["","Hair", "Cloth", "Other"]

        order_list = ['Asset Fx Variant', 'Asset Variant Fx', 'Fx Asset Variant', 
                      'Fx Variant Asset', 'Variant Asset Fx', 'Variant Fx Asset']

        return attrs + [
            BoolDef("useSpecificName",
                    label="Use Specific name",
                    default=False),
            EnumDef("nameOrder",
                    order_list,
                    default="Asset Fx Variant",
                    label="Name order"),
            EnumDef("specificAsset",
                    asset_list,
                    default="",
                    label="Specific Asset"),
            EnumDef("fxName",
                    fx_list,
                    default="",
                    label="Fx name"),
            BoolDef("useCustomFxName",
                    label="Use Custom Fx name",
                    default=False),
            TextDef("customFxName",
                    default="",
                    label="Custom Fx name")
        ]
