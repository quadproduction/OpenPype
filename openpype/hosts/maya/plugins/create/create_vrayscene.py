# -*- coding: utf-8 -*-
"""Create instance of vrayscene."""

from openpype.hosts.maya.api import (
    lib_rendersettings,
    plugin
)
from openpype.pipeline import CreatorError
from openpype.lib import (
    BoolDef,
    EnumDef
)
from openpype.pipeline.context_tools import get_current_project_name
from openpype.modules.ftrack.lib import get_ftrack_statuses


class CreateVRayScene(plugin.RenderlayerCreator):
    """Create Vray Scene."""

    identifier = "io.openpype.creators.maya.vrayscene"

    family = "vrayscene"
    label = "VRay Scene"
    icon = "cubes"

    render_settings = {}
    singleton_node_name = "vraysceneMain"

    @classmethod
    def apply_settings(cls, project_settings):
        cls.render_settings = project_settings["maya"]["RenderSettings"]

    def create(self, subset_name, instance_data, pre_create_data):
        # Only allow a single render instance to exist
        if self._get_singleton_node():
            raise CreatorError("A Render instance already exists - only "
                               "one can be configured.")

        super(CreateVRayScene, self).create(subset_name,
                                            instance_data,
                                            pre_create_data)

        # Apply default project render settings on create
        if self.render_settings.get("apply_render_settings"):
            lib_rendersettings.RenderSettings().set_default_renderer_settings()

    def get_instance_attr_defs(self):
        """Create instance settings."""
        project_name = get_current_project_name()
        statuses = get_ftrack_statuses(project_name)
        statuses = sorted([status['name'] for status in statuses])

        return [
            BoolDef("vraySceneMultipleFiles",
                    label="V-Ray Scene Multiple Files",
                    default=False),
            BoolDef("exportOnFarm",
                    label="Export on farm",
                    default=False),
            EnumDef("ftrackStatus",
                    label="Ftrack Status",
                    items=statuses,
                    default="In progress"),
        ]
