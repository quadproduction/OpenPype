from openpype.hosts.maya.api import plugin
from openpype.lib import (
    BoolDef,
    EnumDef
)
from openpype.pipeline.context_tools import get_current_project_name
from openpype.modules.ftrack.lib import get_ftrack_statuses


class CreateLayout(plugin.MayaCreator):
    """A grouped package of loaded content"""

    identifier = "io.openpype.creators.maya.layout"
    label = "Layout"
    family = "layout"
    icon = "cubes"

    def get_instance_attr_defs(self):
        project_name = get_current_project_name()
        statuses = get_ftrack_statuses(project_name)
        statuses = sorted([status['name'] for status in statuses])

        return [
            EnumDef("ftrackStatus",
                    label="Ftrack Status",
                    items=statuses,
                    default="In progress"),
            BoolDef("groupLoadedAssets",
                    label="Group Loaded Assets",
                    tooltip="Enable this when you want to publish group of "
                            "loaded asset",
                    default=False)
        ]
