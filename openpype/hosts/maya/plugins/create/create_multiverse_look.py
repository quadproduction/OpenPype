from openpype.hosts.maya.api import plugin
from openpype.lib import (
    BoolDef,
    EnumDef
)
from openpype.pipeline.context_tools import get_current_project_name
from openpype.modules.ftrack.lib import get_ftrack_statuses


class CreateMultiverseLook(plugin.MayaCreator):
    """Create Multiverse Look"""

    identifier = "io.openpype.creators.maya.mvlook"
    label = "Multiverse Look"
    family = "mvLook"
    icon = "cubes"

    def get_instance_attr_defs(self):
        project_name = get_current_project_name()
        statuses = get_ftrack_statuses(project_name)
        statuses = sorted([status['name'] for status in statuses])

        return [
            EnumDef("fileFormat",
                    label="File Format",
                    tooltip="USD export file format",
                    items=["usda", "usd"],
                    default="usda"),
            BoolDef("publishMipMap",
                    label="Publish MipMap",
                    default=True),
            EnumDef("ftrackStatus",
                    label="Ftrack Status",
                    items=statuses,
                    default="In progress"),
        ]
