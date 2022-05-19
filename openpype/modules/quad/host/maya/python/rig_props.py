# coding: utf-8
#
# - rig_props -
#
# Autorig and skin for props
#
# Copyright © FixStudio
#             All rights reserved
#
# This file is part of the project *pipeline-studio*
#
# *pipeline-studio* can not be copied and / or distributed without the express
# permission of FixStudio.


import maya.cmds as cmds
from maya import mel


window_name = "auto_rig_props"
window_title = "Simple Rig"
window_w = 400
window_h = 80


def create_window():
    """definit UI"""
    if cmds.window(window_name, query=True, exists=True):
        cmds.deleteUI(window_name)

    cmds.window(window_name)
    cmds.window(
        window_name,
        edit=True,
        w=window_w+2,
        h=window_h,
        title=window_title
    )

    cmds.columnLayout("main_column", w=window_w, h=window_h)

    create_customUI()
    cmds.showWindow(window_name)


def create_customUI():
    """créer UI"""
    cmds.separator(h=10)
    cmds.rowColumnLayout(adj=1, w=window_w, nc=2)
    cmds.button(l="Create Rig", c=createRig, w=window_w/2)
    cmds.button(l="Create Skin", c=bindskin, w=window_w/2)
    cmds.rowColumnLayout(adj=1, w=window_w)
    cmds.separator(h=10)
    cmds.button(l="Rig All", c=rig_All, w=window_w)


def bindskin(*args):
    """ Créer un autoskin avec une commande MEL.
        L'utilisateur sélectionne la géométrie qu'il souhaite skin
        puis ensuite le script vient select le joint avant
        de lancer la commande pour le skin. """

    sel = cmds.ls(sl=True)
    cmds.select(sel, 'joint_{}_prop'.format(sel[0].split(":", 1)[1]))

    if not sel:
        cmds.confirmDialog(
            title="Empty Selection",
            message="You have to select the mesh",
            button=['Ok']
        )
        return

    mel.eval('createSkinCluster "-mi 5 -dr 4"')


def createRig(*args):
    """ Créer automatiquement le rig mais sans le skinning.
        On vient récupérer les positions du mesh selectionné dans la scène.
        Et aprés on set les curves qu'on vient contraindre au joint. """

    selected = cmds.ls(sl=True, transforms=True)

    if not selected:
        cmds.confirmDialog(
            title="Empty Selection",
            message="You have to select the mesh",
            button=['Ok']
        )
        return

    for item in selected:

        rot = cmds.xform(item, ws=1, q=1, rp=1)
        print(rot)

        translate_x_value = rot[0]
        translate_y_value = rot[1]
        translate_z_value = rot[2]

        grp_rig = cmds.group(
            empty=True,
            world=True,
            name='grp_{}_ctrl'.format(item.split(":", 1)[1])
        )
        cmds.xform(t=(
            translate_x_value,
            translate_y_value, translate_z_value)
        )

        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)

        cmds.parent(grp_rig, selected)

        joint_root = cmds.joint(p=(
            translate_x_value,
            translate_y_value,
            translate_z_value),
            n='joint_{}_prop'.format(item.split(":", 1)[1])
        )

        newCtrl_01 = cmds.circle(
            nr=(1, 0, 0),
            c=(0, 0, 0),
            r=1,
            n='c_{}_OBJECT'.format(item.split(":", 1)[1])
        )
        cmds.xform(t=(
            translate_x_value,
            translate_y_value,
            translate_z_value)
        )
        cmds.rotate(0, 0, 90)
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)
        cmds.parent(newCtrl_01, grp_rig)

        # Create Drawing override and Enabe override
        cmds.select(newCtrl_01[0])
        selected_items = cmds.ls(selection=True)
        if selected_items:
            shapes = cmds.listRelatives(selected_items[0], shapes=True)
            # Active la possibilité de mettre des couleurs
            cmds.setAttr(selected_items[0]+".overrideEnabled", 1)
            # Permet d'ajouter des couleurs aux curves
            cmds.setAttr(selected_items[0]+".overrideColor", 19)

        groupe_ctrl = cmds.group(
            n="root_{}_WORLD".format(item.split(":", 1)[1]),
            empty=True,
            world=True
        )
        cmds.xform(t=(
            translate_x_value,
            translate_y_value,
            translate_z_value)
        )
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)

        cmds.parent(groupe_ctrl, grp_rig)
        cmds.parent(newCtrl_01, groupe_ctrl)
        cmds.parent(joint_root, newCtrl_01)

        cmds.select(newCtrl_01[0])
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)

        newCtrl_02 = cmds.circle(
            nr=(0.8, 0, 0),
            c=(0, 0, 0), r=1.5,
            n='c_{}_WALK'.format(item.split(":", 1)[1])
        )
        cmds.xform(t=(
            translate_x_value,
            translate_y_value,
            translate_z_value)
        )
        cmds.rotate(0, 0, 90)
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)

        cmds.parent(newCtrl_02, groupe_ctrl)
        cmds.parent(newCtrl_01, newCtrl_02)

        cmds.select(newCtrl_02[0])
        selected_items = cmds.ls(selection=True)
        if selected_items:
            shapes = cmds.listRelatives(selected_items[0], shapes=True)
            cmds.setAttr(selected_items[0]+".overrideEnabled", 1)
            cmds.setAttr(selected_items[0]+".overrideColor", 19)
            if shapes:
                print(shapes[0])

        newCtrl_03 = cmds.circle(
            nr=(1, 0, 0),
            c=(0, 0, 0),
            r=2,
            n='c_{}_WORLD'.format(item.split(":", 1)[1])
        )
        cmds.xform(t=(
            translate_x_value,
            translate_y_value,
            translate_z_value)
        )
        cmds.rotate(0, 0, 90)
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)
        cmds.parent(newCtrl_03, groupe_ctrl)
        cmds.parent(newCtrl_02, newCtrl_03)

        groupe_c_walk = cmds.group(
            n="root_{}_WALK".format(item.split(":", 1)[1]),
            empty=True,
            world=True
        )
        cmds.xform(t=(
            translate_x_value,
            translate_y_value,
            translate_z_value)
        )
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)
        cmds.parent(groupe_c_walk, newCtrl_03)
        cmds.parent(newCtrl_02, groupe_c_walk)

        groupe_c_object = cmds.group(
            n="root_{}_OBJECT".format(item.split(":", 1)[1]),
            empty=True,
            world=True
        )
        cmds.xform(t=(
            translate_x_value,
            translate_y_value,
            translate_z_value)
        )
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)
        cmds.parent(groupe_c_object, newCtrl_02)
        cmds.parent(newCtrl_01, groupe_c_object)

        cmds.select(newCtrl_03[0])
        selected_items = cmds.ls(selection=True)
        if selected_items:
            shapes = cmds.listRelatives(selected_items[0], shapes=True)
            cmds.setAttr(selected_items[0]+".overrideEnabled", 1)
            cmds.setAttr(selected_items[0]+".overrideColor", 17)
            if shapes:
                print(shapes[0])

        if cmds.objExists("grp_rig"):

            cmds.parent(grp_rig, "grp_rig")
        else:
            cmds.group(empty=True, world=True, name='grp_rig')
            cmds.parent(grp_rig, "grp_rig")
            cmds.parent("grp_rig", "root")


def rig_All(*args):
    """ Comme la fonction au dessus sauf que cette on ajoute le skin """

    selected = cmds.ls(sl=True, transforms=True)

    if not selected:
        cmds.confirmDialog(
            title="Empty Selection",
            message="You have to select the mesh",
            button=['Ok']
        )
        return

    for item in selected:

        rot = cmds.xform(item, ws=1, q=1, rp=1)
        print(rot)

        translate_x_value = rot[0]
        translate_y_value = rot[1]
        translate_z_value = rot[2]

        grp_rig = cmds.group(
            empty=True,
            world=True,
            name='grp_{}_ctrl'.format(item.split(":", 1)[1])
        )
        cmds.xform(t=(
            translate_x_value,
            translate_y_value,
            translate_z_value)
        )
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)

        cmds.parent(grp_rig, selected)

        joint_root = cmds.joint(p=(
            translate_x_value,
            translate_y_value,
            translate_z_value),
            n='joint_{}_prop'.format(item.split(":", 1)[1])
        )

        newCtrl_01 = cmds.circle(
            nr=(1, 0, 0),
            c=(0, 0, 0),
            r=1,
            n='c_{}_OBJECT'.format(item.split(":", 1)[1])
        )
        cmds.xform(t=(
            translate_x_value,
            translate_y_value,
            translate_z_value)
        )
        cmds.rotate(0, 0, 90)
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)
        cmds.parent(newCtrl_01, grp_rig)

        cmds.select(newCtrl_01[0])
        selected_items = cmds.ls(selection=True)
        if selected_items:
            cmds.setAttr(selected_items[0]+".overrideEnabled", 1)
            cmds.setAttr(selected_items[0]+".overrideColor", 19)

        groupe_ctrl = cmds.group(
            n="root_{}_WORLD".format(item.split(":", 1)[1]),
            empty=True,
            world=True
        )
        cmds.xform(t=(
            translate_x_value,
            translate_y_value,
            translate_z_value)
        )
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)

        cmds.parent(groupe_ctrl, grp_rig)
        cmds.parent(newCtrl_01, groupe_ctrl)
        cmds.parent(joint_root, newCtrl_01)

        cmds.select(newCtrl_01[0])
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)

        newCtrl_02 = cmds.circle(
            nr=(0.8, 0, 0),
            c=(0, 0, 0),
            r=1.5,
            n='c_{}_WALK'.format(item.split(":", 1)[1])
        )
        cmds.xform(t=(
            translate_x_value,
            translate_y_value,
            translate_z_value)
        )
        cmds.rotate(0, 0, 90)
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)

        cmds.parent(newCtrl_02, groupe_ctrl)
        cmds.parent(newCtrl_01, newCtrl_02)

        cmds.select(newCtrl_02[0])
        selected_items = cmds.ls(selection=True)
        if selected_items:
            cmds.setAttr(selected_items[0]+".overrideEnabled", 1)
            cmds.setAttr(selected_items[0]+".overrideColor", 19)

        newCtrl_03 = cmds.circle(
            nr=(1, 0, 0),
            c=(0, 0, 0),
            r=2,
            n='c_{}_WORLD'.format(item.split(":", 1)[1])
        )
        cmds.xform(t=(
            translate_x_value,
            translate_y_value,
            translate_z_value)
        )
        cmds.rotate(0, 0, 90)
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)
        cmds.parent(newCtrl_03, groupe_ctrl)
        cmds.parent(newCtrl_02, newCtrl_03)

        groupe_c_walk = cmds.group(
            n="root_{}_WALK".format(item.split(":", 1)[1]),
            empty=True,
            world=True
        )
        cmds.xform(t=(
            translate_x_value,
            translate_y_value,
            translate_z_value)
        )
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)
        cmds.parent(groupe_c_walk, newCtrl_03)
        cmds.parent(newCtrl_02, groupe_c_walk)

        groupe_c_object = cmds.group(
            n="root_{}_OBJECT".format(item.split(":", 1)[1]),
            empty=True,
            world=True
        )
        cmds.xform(t=(
            translate_x_value,
            translate_y_value,
            translate_z_value)
        )
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=2)
        cmds.parent(groupe_c_object, newCtrl_02)
        cmds.parent(newCtrl_01, groupe_c_object)

        cmds.select(newCtrl_03[0])
        selected_items = cmds.ls(selection=True)
        if selected_items:

            cmds.setAttr(selected_items[0]+".overrideEnabled", 1)
            cmds.setAttr(selected_items[0]+".overrideColor", 17)

        if cmds.objExists("grp_rig"):

            cmds.parent(grp_rig, "grp_rig")
        else:
            cmds.group(empty=True, world=True, name='grp_rig')
            cmds.parent(grp_rig, "grp_rig")
            cmds.parent("grp_rig", "root")

    cmds.select(joint_root, selected)
    mel.eval('createSkinCluster "-mi 5 -dr 4"')
