from maya import cmds

from openpype.hosts.maya.api import plugin
from openpype.lib import EnumDef
from openpype.pipeline.context_tools import get_current_project_name
from openpype.modules.ftrack.lib import get_ftrack_statuses


class CreateRig(plugin.MayaCreator):
    """Artist-friendly rig with controls to direct motion"""

    identifier = "io.openpype.creators.maya.rig"
    label = "Rig"
    family = "rig"
    icon = "wheelchair"

    def create(self, subset_name, instance_data, pre_create_data):

        instance = super(CreateRig, self).create(subset_name,
                                                 instance_data,
                                                 pre_create_data)

        instance_node = instance.get("instance_node")

        self.log.info("Creating Rig instance set up ...")
        controls = cmds.sets(name=subset_name + "_controls_SET", empty=True)
        pointcache = cmds.sets(name=subset_name + "_out_SET", empty=True)
        cmds.sets([controls, pointcache], forceElement=instance_node)

    def get_instance_attr_defs(self):
        project_name = get_current_project_name()
        statuses = get_ftrack_statuses(project_name)
        statuses = sorted([status['name'] for status in statuses])

        return [
            EnumDef("ftrackStatus",
                    label="Ftrack Status",
                    items=statuses,
                    default="In progress"),
        ]
