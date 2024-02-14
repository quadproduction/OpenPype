from openpype.hosts.maya.api import (
    plugin,
    lib
)
from openpype.lib import (
    BoolDef,
    EnumDef
)
from openpype.pipeline.context_tools import get_current_project_name
from openpype.modules.ftrack.lib import get_ftrack_statuses


class CreateVrayProxy(plugin.MayaCreator):
    """Alembic pointcache for animated data"""

    identifier = "io.openpype.creators.maya.vrayproxy"
    label = "VRay Proxy"
    family = "vrayproxy"
    icon = "gears"

    vrmesh = True
    alembic = True

    def get_instance_attr_defs(self):
        project_name = get_current_project_name()
        statuses = get_ftrack_statuses(project_name)
        statuses = sorted([status['name'] for status in statuses])

        defs = [
            BoolDef("animation",
                    label="Export Animation",
                    default=False)
        ]

        # Add time range attributes but remove some attributes
        # which this instance actually doesn't use
        defs.extend(lib.collect_animation_defs())
        remove = {"handleStart", "handleEnd", "step"}
        defs = [attr_def for attr_def in defs if attr_def.key not in remove]

        defs.extend([
            BoolDef("vertexColors",
                    label="Write vertex colors",
                    tooltip="Write vertex colors with the geometry",
                    default=False),
            BoolDef("vrmesh",
                    label="Export VRayMesh",
                    tooltip="Publish a .vrmesh (VRayMesh) file for "
                            "this VRayProxy",
                    default=self.vrmesh),
            BoolDef("alembic",
                    label="Export Alembic",
                    tooltip="Publish a .abc (Alembic) file for "
                            "this VRayProxy",
                    default=self.alembic),
            EnumDef("ftrackStatus",
                    label="Ftrack Status",
                    items=statuses,
                    default="In progress"),
        ])

        return defs
