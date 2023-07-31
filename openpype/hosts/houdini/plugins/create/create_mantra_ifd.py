# -*- coding: utf-8 -*-
"""Creator plugin for creating pointcache alembics."""
from openpype.hosts.houdini.api import plugin
from openpype.pipeline import CreatedInstance
from openpype.lib import BoolDef


class CreateMantraIFD(plugin.HoudiniCreator):
    """Mantra .ifd Archive"""
    identifier = "io.openpype.creators.houdini.mantraifd"
    label = "Mantra IFD"
    family = "mantraifd"
    icon = "gears"

    def create(self, subset_name, instance_data, pre_create_data):
        import hou
        instance_data.pop("active", None)
        instance_data.update({"node_type": "ifd"})
        instance_data["farm"] = pre_create_data.get("farm")
        instance = super(CreateMantraIFD, self).create(
            subset_name,
            instance_data,
            pre_create_data)  # type: CreatedInstance

        instance_node = hou.node(instance.get("instance_node"))

        filepath = "{}{}".format(
            hou.text.expandString("$HIP/pyblish/"),
            "{}.$F4.ifd".format(subset_name))
        parms = {
            # Render frame range
            "trange": 1,
            # Arnold ROP settings
            "soho_diskfile": filepath,
            "soho_outputmode": 1
        }

        instance_node.setParms(parms)

        # Lock any parameters in this list
        to_lock = ["soho_outputmode", "family", "id"]
        self.lock_parameters(instance_node, to_lock)

    def get_pre_create_attr_defs(self):
        attrs = super(CreateMantraIFD, self).get_pre_create_attr_defs()
        return attrs + [
            BoolDef("farm",
                    label="Submitting to Farm",
                    default=False)
        ]