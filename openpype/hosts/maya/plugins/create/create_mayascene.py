from openpype.hosts.maya.api import plugin
from openpype.lib import EnumDef
from openpype.pipeline.context_tools import get_current_project_name
from openpype.modules.ftrack.lib import get_ftrack_statuses


class CreateMayaScene(plugin.MayaCreator):
    """Raw Maya Scene file export"""

    identifier = "io.openpype.creators.maya.mayascene"
    name = "mayaScene"
    label = "Maya Scene"
    family = "mayaScene"
    icon = "file-archive-o"

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
