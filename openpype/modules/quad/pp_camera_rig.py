# -*- coding: utf-8 -*-

import maya.cmds as cmds


def push_camera_position_to_rig():
    """ push camera position to rig
    """
    selection = cmds.ls(sl=True, l=True)
    if not selection:
        message_box("Please select a camera!")
        return

    # get camera and camera shape
    camera = selection[0]
    camera_shape = None

    if cmds.nodeType(camera) == "transform":
        children = cmds.listRelatives(camera, children=True)
        if children:
            if cmds.nodeType(children[0]) == "camera":
                camera_shape = children[0]
    elif cmds.nodeType(camera) == "camera":
        camera_shape = camera
        camera = cmds.listRealtives(camera_shape, parent=True)[0]

    if not camera_shape:
        message_box("Please select a camera!")
        return

    # get namespace if there is one
    namespace = None
    if ":" in camera:
        node_short = camera
        # split by :
        if "|" in camera:
            node_short = camera.split('|')[len(camera.split('|')) - 1]
        splitted_node = node_short.split(":")
        splitted_node.pop(len(splitted_node) - 1)
        namespace = ":".join(splitted_node)

    # get camera position
    world_translation = cmds.xform(
        camera, query=True, worldSpace=True, translation=True
    )
    world_rotation = cmds.xform(
        camera, query=True, worldSpace=True, rotation=True
    )

    # set world translation to triangle_ctrl
    if cmds.objExists(_get_ctrl_name(namespace, "triangle")):
        # set attr
        cmds.xform(
            _get_ctrl_name(namespace, "triangle"),
            worldSpace=True,
            translation=world_translation
        )
        cmds.setAttr(
            "{}.rotate".format(_get_ctrl_name(namespace, "triangle")),
            0,
            0,
            0
        )

    # set world rotation Y to circle
    if cmds.objExists(_get_ctrl_name(namespace, "circle")):
        # set attr
        rotation = [0, world_rotation[1], 0]
        cmds.xform(
            _get_ctrl_name(namespace, "circle"),
            worldSpace=True,
            translation=world_translation
        )
        cmds.setAttr(
            "{}.rotate".format(_get_ctrl_name(namespace, "circle")),
            rotation[0],
            rotation[1],
            rotation[2]
        )

    # set world rotation X to square
    if cmds.objExists(_get_ctrl_name(namespace, "square")):
        # set attr
        rotation = [world_rotation[0], 0, 0]
        cmds.xform(
            _get_ctrl_name(namespace, "square"),
            worldSpace=True,
            translation=world_translation
        )
        cmds.setAttr(
            "{}.rotate".format(_get_ctrl_name(namespace, "square")),
            rotation[0],
            rotation[1],
            rotation[2]
        )

    # set world rotation Z to cross
    if cmds.objExists(_get_ctrl_name(namespace, "cross")):
        # set attr
        rotation = [0, 0, world_rotation[2]]
        cmds.xform(
            _get_ctrl_name(namespace, "cross"),
            worldSpace=True,
            translation=world_translation
        )
        cmds.setAttr(
            "{}.rotate".format(_get_ctrl_name(namespace, "cross")),
            rotation[0],
            rotation[1],
            rotation[2]
        )

    # set target
    if cmds.objExists(_get_ctrl_name(namespace, "target")):
        # set attr translation same as camera
        cmds.xform(
            _get_ctrl_name(namespace, "target"),
            worldSpace=True,
            translation=world_translation
        )
        # set attr translateZ -10
        cmds.setAttr(
            "{}.translateZ".format(_get_ctrl_name(namespace, "target")),
            cmds.getAttr("{}.translateZ".format(
                _get_ctrl_name(namespace, "target")
            )) - 10,
        )

    # reset value to camera
    cmds.setAttr("{}.translate".format(camera), 0, 0, 0)
    cmds.setAttr("{}.rotate".format(camera), 0, 0, 0)

    return True


def _get_ctrl_name(self, namespace, name):
    """ get ctrl name
    """
    ctrl = {
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

    if namespace:
        return "{}:{}".format(
            self.namespace,
            ctrl.get(name)
        )
    else:
        return ctrl.get(name)


def message_box(message=""):
    """ a simple message box
    """
    if cmds.about(batch=True):
        return

    kwargs = {
        "title": "Error",
        "message": message,
        "icon": "information",
        "button": "OK",
        "cancelButton": None,
    }
    cmds.confirmDialog(**kwargs)
