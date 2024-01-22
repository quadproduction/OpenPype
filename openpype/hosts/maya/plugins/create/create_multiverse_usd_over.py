from openpype.hosts.maya.api import plugin, lib
from openpype.lib import (
    BoolDef,
    NumberDef,
    EnumDef
)
from openpype.pipeline.context_tools import get_current_project_name
from openpype.modules.ftrack.lib import get_ftrack_statuses


class CreateMultiverseUsdOver(plugin.MayaCreator):
    """Create Multiverse USD Override"""

    identifier = "io.openpype.creators.maya.mvusdoverride"
    label = "Multiverse USD Override"
    family = "mvUsdOverride"
    icon = "cubes"

    def get_instance_attr_defs(self):
        defs = lib.collect_animation_defs(fps=True)
        project_name = get_current_project_name()
        statuses = get_ftrack_statuses(project_name)
        statuses = sorted([status['name'] for status in statuses])

        defs.extend([
            EnumDef("fileFormat",
                    label="File format",
                    items=["usd", "usda"],
                    default="usd"),
            BoolDef("writeAll",
                    label="Write All",
                    default=False),
            BoolDef("writeTransforms",
                    label="Write Transforms",
                    default=True),
            BoolDef("writeVisibility",
                    label="Write Visibility",
                    default=True),
            BoolDef("writeAttributes",
                    label="Write Attributes",
                    default=True),
            BoolDef("writeMaterials",
                    label="Write Materials",
                    default=True),
            BoolDef("writeVariants",
                    label="Write Variants",
                    default=True),
            BoolDef("writeVariantsDefinition",
                    label="Write Variants Definition",
                    default=True),
            BoolDef("writeActiveState",
                    label="Write Active State",
                    default=True),
            BoolDef("writeNamespaces",
                    label="Write Namespaces",
                    default=False),
            NumberDef("numTimeSamples",
                      label="Num Time Samples",
                      default=1),
            NumberDef("timeSamplesSpan",
                      label="Time Samples Span",
                      default=0.0),
            EnumDef("ftrackStatus",
                    label="Ftrack Status",
                    items=statuses,
                    default="In progress"),
        ])

        return defs
