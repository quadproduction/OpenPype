from openpype.hosts.maya.api import (
    lib,
    plugin
)
from openpype.lib import (
    NumberDef,
    EnumDef
)
from openpype.pipeline.context_tools import get_current_project_name
from openpype.modules.ftrack.lib import get_ftrack_statuses


class CreateYetiCache(plugin.MayaCreator):
    """Output for procedural plugin nodes of Yeti """

    identifier = "io.openpype.creators.maya.yeticache"
    label = "Yeti Cache"
    family = "yeticache"
    icon = "pagelines"

    def get_instance_attr_defs(self):
        project_name = get_current_project_name()
        statuses = get_ftrack_statuses(project_name)
        statuses = sorted([status['name'] for status in statuses])

        defs = [
            NumberDef("preroll",
                      label="Preroll",
                      minimum=0,
                      default=0,
                      decimals=0)
        ]

        # Add animation data without step and handles
        defs.extend(lib.collect_animation_defs())
        remove = {"step", "handleStart", "handleEnd"}
        defs = [attr_def for attr_def in defs if attr_def.key not in remove]

        # Add samples after frame range
        defs.extend([
            NumberDef("samples",
                      label="Samples",
                      default=3,
                      decimals=0),
            EnumDef("ftrackStatus",
                    label="Ftrack Status",
                    items=statuses,
                    default="In progress"),
        ])

        return defs
