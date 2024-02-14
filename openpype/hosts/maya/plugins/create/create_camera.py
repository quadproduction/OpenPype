from openpype.hosts.maya.api import (
    lib,
    plugin
)
from openpype.lib import (
    BoolDef,
    EnumDef
)
from openpype.pipeline.context_tools import get_current_project_name
from openpype.modules.ftrack.lib import get_ftrack_statuses


class CreateCamera(plugin.MayaCreator):
    """Single baked camera"""

    identifier = "io.openpype.creators.maya.camera"
    label = "Camera"
    family = "camera"
    icon = "video-camera"

    def get_instance_attr_defs(self):

        defs = lib.collect_animation_defs()

        project_name = get_current_project_name()
        statuses = get_ftrack_statuses(project_name)
        statuses = sorted([status['name'] for status in statuses])

        defs.extend([
            EnumDef("ftrackStatus",
                    label="Ftrack Status",
                    items=statuses,
                    default="In progress"),
            BoolDef("bakeToWorldSpace",
                    label="Bake to World-Space",
                    tooltip="Bake to World-Space",
                    default=True),
        ])

        return defs


class CreateCameraRig(plugin.MayaCreator):
    """Complex hierarchy with camera."""

    identifier = "io.openpype.creators.maya.camerarig"
    label = "Camera Rig"
    family = "camerarig"
    icon = "video-camera"

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
