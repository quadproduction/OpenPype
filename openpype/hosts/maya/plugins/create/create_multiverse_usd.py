from openpype.hosts.maya.api import plugin, lib
from openpype.lib import (
    BoolDef,
    NumberDef,
    TextDef,
    EnumDef
)
from openpype.pipeline.context_tools import get_current_project_name
from openpype.modules.ftrack.lib import get_ftrack_statuses


class CreateMultiverseUsd(plugin.MayaCreator):
    """Create Multiverse USD Asset"""

    identifier = "io.openpype.creators.maya.mvusdasset"
    label = "Multiverse USD Asset"
    family = "usd"
    icon = "cubes"
    description = "Create Multiverse USD Asset"

    def get_publish_families(self):
        return ["usd", "mvUsd"]

    def get_instance_attr_defs(self):

        defs = lib.collect_animation_defs(fps=True)
        project_name = get_current_project_name()
        statuses = get_ftrack_statuses(project_name)
        statuses = sorted([status['name'] for status in statuses])

        defs.extend([
            EnumDef("fileFormat",
                    label="File format",
                    items=["usd", "usda", "usdz"],
                    default="usd"),
            BoolDef("stripNamespaces",
                    label="Strip Namespaces",
                    default=True),
            BoolDef("mergeTransformAndShape",
                    label="Merge Transform and Shape",
                    default=False),
            BoolDef("writeAncestors",
                    label="Write Ancestors",
                    default=True),
            BoolDef("flattenParentXforms",
                    label="Flatten Parent Xforms",
                    default=False),
            BoolDef("writeSparseOverrides",
                    label="Write Sparse Overrides",
                    default=False),
            BoolDef("useMetaPrimPath",
                    label="Use Meta Prim Path",
                    default=False),
            TextDef("customRootPath",
                    label="Custom Root Path",
                    default=''),
            TextDef("customAttributes",
                    label="Custom Attributes",
                    tooltip="Comma-separated list of attribute names",
                    default=''),
            TextDef("nodeTypesToIgnore",
                    label="Node Types to Ignore",
                    tooltip="Comma-separated list of node types to be ignored",
                    default=''),
            EnumDef("ftrackStatus",
                    label="Ftrack Status",
                    items=statuses,
                    default="In progress"),
            BoolDef("writeMeshes",
                    label="Write Meshes",
                    default=True),
            BoolDef("writeCurves",
                    label="Write Curves",
                    default=True),
            BoolDef("writeParticles",
                    label="Write Particles",
                    default=True),
            BoolDef("writeCameras",
                    label="Write Cameras",
                    default=False),
            BoolDef("writeLights",
                    label="Write Lights",
                    default=False),
            BoolDef("writeJoints",
                    label="Write Joints",
                    default=False),
            BoolDef("writeCollections",
                    label="Write Collections",
                    default=False),
            BoolDef("writePositions",
                    label="Write Positions",
                    default=True),
            BoolDef("writeNormals",
                    label="Write Normals",
                    default=True),
            BoolDef("writeUVs",
                    label="Write UVs",
                    default=True),
            BoolDef("writeColorSets",
                    label="Write Color Sets",
                    default=False),
            BoolDef("writeTangents",
                    label="Write Tangents",
                    default=False),
            BoolDef("writeRefPositions",
                    label="Write Ref Positions",
                    default=True),
            BoolDef("writeBlendShapes",
                    label="Write BlendShapes",
                    default=False),
            BoolDef("writeDisplayColor",
                    label="Write Display Color",
                    default=True),
            BoolDef("writeSkinWeights",
                    label="Write Skin Weights",
                    default=False),
            BoolDef("writeMaterialAssignment",
                    label="Write Material Assignment",
                    default=False),
            BoolDef("writeHardwareShader",
                    label="Write Hardware Shader",
                    default=False),
            BoolDef("writeShadingNetworks",
                    label="Write Shading Networks",
                    default=False),
            BoolDef("writeTransformMatrix",
                    label="Write Transform Matrix",
                    default=True),
            BoolDef("writeUsdAttributes",
                    label="Write USD Attributes",
                    default=True),
            BoolDef("writeInstancesAsReferences",
                    label="Write Instances as References",
                    default=False),
            BoolDef("timeVaryingTopology",
                    label="Time Varying Topology",
                    default=False),
            TextDef("customMaterialNamespace",
                    label="Custom Material Namespace",
                    default=''),
            NumberDef("numTimeSamples",
                      label="Num Time Samples",
                      default=1),
            NumberDef("timeSamplesSpan",
                      label="Time Samples Span",
                      default=0.0),
        ])

        return defs
