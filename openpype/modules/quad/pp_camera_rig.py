# -*- coding: utf-8 -*-

import logging

import maya.cmds as cmds


# logger
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('pp_camera_rig')
logger.setLevel(logging.DEBUG)


class Camera(object):
    """ a usefull class for manipulate camera rig.
    """
    def __init__(self, camera):
        super(Camera, self).__init__()

        self.camera = camera
        self.camera_shape = None

        self.namespace = None

        self.ctrl = {
            # ctrl
            "triangle": "triangle_ctrl",
            "circle": "circle_ctrl",
            "square": "square_ctrl",
            "cross": "cross_ctrl",
            "translateZ": "translateZ_ctrl",
            "translateY": "translateY_ctrl",
            # target
            "target": "target_ctrl",
            "targetUp": "targetUp_ctrl",
            # focus
            "focus": "focus_ctrl"
        }

        self.init_rig()

    def init_rig(self):
        """
        """
        # init camera shape
        if cmds.nodeType(self.camera) == "transform":
            self.camera_shape = self._get_camera_shape(transform=self.camera)
        elif cmds.nodeType(self.camera) == "camera":
            # user as provided a camera shape
            # we are smart and flexible
            self.camera_shape = self.camera
            self.camera = cmds.listRealtives(self.camera_shape, parent=True)[0]

        # init namespace
        self.namespace = self._get_namespace(node=self.camera)

    def _get_namespace(self, node):
        """
        """
        self.namespace = None
        if ":" in node:
            node_short = node
            # split by :
            if "|" in node:
                node_short = node.split('|')[len(node.split('|')) - 1]
            splitted_node = node_short.split(":")
            splitted_node.pop(len(splitted_node) - 1)
            self.namespace = ":".join(splitted_node)

        return self.namespace

    def _get_ctrl_name(self, name):
        """
        """
        if self.namespace:
            return "{namespace}:{ctrl}".format(
                namespace=self.namespace,
                ctrl=self.ctrl.get(name)
            )
        else:
            return self.ctrl.get(name)

    def _get_camera_shape(self, transform):
        """
        """
        self.camera_shape = None
        children = cmds.listRelatives(transform, children=True)
        if children:
            if cmds.nodeType(children[0]) == "camera":
                self.camera_shape = children[0]

        return self.camera_shape

    def push_camera_position_to_rig(self):
        """
        """
        # get camera position
        world_translation = cmds.xform(
            self.camera, query=True, worldSpace=True, translation=True
        )
        world_rotation = cmds.xform(
            self.camera, query=True, worldSpace=True, rotation=True
        )

        # set world translation to triangle_ctrl
        if cmds.objExists(self._get_ctrl_name("triangle")):
            # set attr
            cmds.xform(
                self._get_ctrl_name("triangle"),
                worldSpace=True,
                translation=world_translation
            )
            cmds.setAttr(
                "{n}.rotate".format(n=self._get_ctrl_name("triangle")),
                0,
                0,
                0
            )

        # set world rotation Y to circle
        if cmds.objExists(self._get_ctrl_name("circle")):
            # set attr
            rotation = [0, world_rotation[1], 0]
            cmds.xform(
                self._get_ctrl_name("circle"),
                worldSpace=True,
                translation=world_translation
            )
            cmds.setAttr(
                "{n}.rotate".format(n=self._get_ctrl_name("circle")),
                rotation[0],
                rotation[1],
                rotation[2]
            )

        # set world rotation X to square
        if cmds.objExists(self._get_ctrl_name("square")):
            # set attr
            rotation = [world_rotation[0], 0, 0]
            cmds.xform(
                self._get_ctrl_name("square"),
                worldSpace=True,
                translation=world_translation
            )
            cmds.setAttr(
                "{n}.rotate".format(n=self._get_ctrl_name("square")),
                rotation[0],
                rotation[1],
                rotation[2]
            )

        # set world rotation Z to cross
        if cmds.objExists(self._get_ctrl_name("cross")):
            # set attr
            rotation = [0, 0, world_rotation[2]]
            cmds.xform(
                self._get_ctrl_name("cross"),
                worldSpace=True,
                translation=world_translation
            )
            cmds.setAttr(
                "{n}.rotate".format(n=self._get_ctrl_name("cross")),
                rotation[0],
                rotation[1],
                rotation[2]
            )

        # set target
        if cmds.objExists(self._get_ctrl_name("target")):
            # set attr translation same as camera
            cmds.xform(
                self._get_ctrl_name("target"),
                worldSpace=True,
                translation=world_translation
            )
            # set attr translateZ -10
            cmds.setAttr(
                "{n}.translateZ".format(n=self._get_ctrl_name("target")),
                cmds.getAttr("{n}.translateZ".format(n=self._get_ctrl_name("target"))) - 10,
            )

        # reset value to camera
        cmds.setAttr("{n}.translate".format(n=self.camera), 0, 0, 0)
        cmds.setAttr("{n}.rotate".format(n=self.camera), 0, 0, 0)

        return True


def push_camera_position_to_rig_selection():
    """
    """
    selection = cmds.ls(sl=True, l=True)
    if selection:
        return push_camera_position_to_rig(camera=selection[0])

    return False


def push_camera_position_to_rig(camera):
    """
    """
    if is_a_camera(camera):
        c = Camera(camera)
        c.push_camera_position_to_rig()
        return True
    else:
        if not cmds.about(batch=True):
            kwargs = {
                "title": "Error",
                "message": "Please select a camera!",
                "icon": "information",
                "button": "OK",
                "cancelButton": None,
            }
            cmds.confirmDialog(**kwargs)

    return False


def is_a_camera(node):
    """
    check if node provided contain camera directly or as first children.
    """
    if cmds.nodeType(node) == "transform":
        children = cmds.listRelatives(node, children=True)
        if children:
            if cmds.nodeType(children[0]) == "camera":
                return True
    elif cmds.nodeType(node) == "camera":
        return True

    return False
