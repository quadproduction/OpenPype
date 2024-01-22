from openpype.hosts.maya.api import (
    lib,
    plugin
)
from openpype.lib import (
    BoolDef,
    TextDef,
    EnumDef
)
from openpype.pipeline.context_tools import get_current_project_name
from openpype.modules.ftrack.lib import get_ftrack_statuses


class CreateProxyAlembic(plugin.MayaCreator):
    """Proxy Alembic for animated data"""

    identifier = "io.openpype.creators.maya.proxyabc"
    label = "Proxy Alembic"
    family = "proxyAbc"
    icon = "gears"
    write_color_sets = False
    write_face_sets = False

    def get_instance_attr_defs(self):

        defs = lib.collect_animation_defs()
        project_name = get_current_project_name()
        statuses = get_ftrack_statuses(project_name)
        statuses = sorted([status['name'] for status in statuses])

        defs.extend([
            BoolDef("writeColorSets",
                    label="Write vertex colors",
                    tooltip="Write vertex colors with the geometry",
                    default=self.write_color_sets),
            BoolDef("writeFaceSets",
                    label="Write face sets",
                    tooltip="Write face sets with the geometry",
                    default=self.write_face_sets),
            BoolDef("worldSpace",
                    label="World-Space Export",
                    default=True),
            TextDef("nameSuffix",
                    label="Name Suffix for Bounding Box",
                    default="_BBox",
                    placeholder="_BBox"),
            TextDef("attr",
                    label="Custom Attributes",
                    default="",
                    placeholder="attr1, attr2"),
            TextDef("attrPrefix",
                    label="Custom Attributes Prefix",
                    placeholder="prefix1, prefix2"),
            EnumDef("ftrackStatus",
                    label="Ftrack Status",
                    items=statuses,
                    default="In progress"),
        ])

        return defs
