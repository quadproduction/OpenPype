from maya import cmds

from openpype.hosts.maya.api import (
    lib,
    plugin
)
from openpype.lib import EnumDef
from openpype.pipeline.context_tools import get_current_project_name
from openpype.modules.ftrack.lib import get_ftrack_statuses


class CreateYetiRig(plugin.MayaCreator):
    """Output for procedural plugin nodes ( Yeti / XGen / etc)"""

    identifier = "io.openpype.creators.maya.yetirig"
    label = "Yeti Rig"
    family = "yetiRig"
    icon = "usb"

    def create(self, subset_name, instance_data, pre_create_data):

        with lib.undo_chunk():
            instance = super(CreateYetiRig, self).create(subset_name,
                                                         instance_data,
                                                         pre_create_data)
            instance_node = instance.get("instance_node")

            self.log.info("Creating Rig instance set up ...")
            input_meshes = cmds.sets(name="input_SET", empty=True)
            cmds.sets(input_meshes, forceElement=instance_node)

    def get_instance_attr_defs(self):
        """Create instance settings."""
        project_name = get_current_project_name()
        statuses = get_ftrack_statuses(project_name)
        statuses = sorted([status['name'] for status in statuses])

        return [
            EnumDef("ftrackStatus",
                    label="Ftrack Status",
                    items=statuses,
                    default="In progress"),
        ]
