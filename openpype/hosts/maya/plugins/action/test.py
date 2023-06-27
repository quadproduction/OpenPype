
from maya import cmds

from openpype.pipeline import BuilderAction


class ConnectGeometry(BuilderAction):
    """Connect geometries within containers.

    Source container will connect to the target containers, by searching for
    matching geometry IDs (cbid).
    Source containers are of family; "animation" and "pointcache".
    The connection with be done with a live world space blendshape.
    """

    label = "Connect Geometry"
    icon = "link"
    color = "white"

    def process(self):
        print(cmds.ls())