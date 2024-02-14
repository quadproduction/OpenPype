from openpype.hosts.maya.api import plugin
from openpype.lib import (
    BoolDef,
    TextDef,
    EnumDef
)
from openpype.pipeline.context_tools import get_current_project_name
from openpype.modules.ftrack.lib import get_ftrack_statuses


class CreateModel(plugin.MayaCreator):
    """Polygonal static geometry"""

    identifier = "io.openpype.creators.maya.model"
    label = "Model"
    family = "model"
    icon = "cube"
    default_variants = ["Main", "Proxy", "_MD", "_HD", "_LD"]

    write_color_sets = False
    write_face_sets = False

    def get_instance_attr_defs(self):
        project_name = get_current_project_name()
        statuses = get_ftrack_statuses(project_name)
        statuses = sorted([status['name'] for status in statuses])

        return [
            BoolDef("writeColorSets",
                    label="Write vertex colors",
                    tooltip="Write vertex colors with the geometry",
                    default=self.write_color_sets),
            BoolDef("writeFaceSets",
                    label="Write face sets",
                    tooltip="Write face sets with the geometry",
                    default=self.write_face_sets),
            BoolDef("includeParentHierarchy",
                    label="Include Parent Hierarchy",
                    tooltip="Whether to include parent hierarchy of nodes in "
                            "the publish instance",
                    default=False),
            EnumDef("ftrackStatus",
                    label="Ftrack Status",
                    items=statuses,
                    default="In progress"),
            TextDef("attr",
                    label="Custom Attributes",
                    default="",
                    placeholder="attr1, attr2"),
            TextDef("attrPrefix",
                    label="Custom Attributes Prefix",
                    placeholder="prefix1, prefix2")
        ]
