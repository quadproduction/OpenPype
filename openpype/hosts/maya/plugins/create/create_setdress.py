from openpype.hosts.maya.api import plugin
from openpype.lib import (
    BoolDef,
    EnumDef
)
from openpype.pipeline.context_tools import get_current_project_name
from openpype.modules.ftrack.lib import get_ftrack_statuses


class CreateSetDress(plugin.MayaCreator):
    """A grouped package of loaded content"""

    identifier = "io.openpype.creators.maya.setdress"
    label = "Set Dress"
    family = "setdress"
    icon = "cubes"
    default_variants = ["Main", "Anim"]

    def get_instance_attr_defs(self):
        project_name = get_current_project_name()
        statuses = get_ftrack_statuses(project_name)
        statuses = sorted([status['name'] for status in statuses])

        return [
            BoolDef("exactSetMembersOnly",
                    label="Exact Set Members Only",
                    default=True),
            EnumDef("ftrackStatus",
                    label="Ftrack Status",
                    items=statuses,
                    default="In progress"),
        ]
