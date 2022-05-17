# -*- coding: utf-8 -*-

"""
    zdefocus
        Florentin LUCE
    =================================================

    Version 1.0

    create a zdefocus node that work on nuke assist
    generate chromatic aberration

    Every parameters is driven by expression unless
    the defocus picker that use python script. But
    this node is totally independant from this script
    after it was generated

    Global parameter are used to set the number of
    cut in convolution
"""

import nuke

DIV = 100
INTERVAL = 1.0/DIV


def set_ui(zdefocus_node):
    """set all knobs on node

    Args:
        zdefocus_node (Node): node on which ui is set
    """

    zdefocus_node.addKnob(nuke.Tab_Knob("ZDefocus"))

    # titre
    zdefocus_node.addKnob(nuke.Text_Knob("title", "", '<img src=":qrc/images/ToolbarMerge.png"> <font size="5"> ZDefocus Nuke Assist v1.0 </font>'))
    zdefocus_node.addKnob(nuke.Text_Knob("div1", ""))

    # remove channel
    remove = nuke.Boolean_Knob("remove", "remove z channel")
    zdefocus_node.addKnob(remove)

    # focal point
    focal_knob = nuke.XY_Knob("focus_position", "focus point")
    focal_knob.setTooltip("coordinates of focus position in viewer")
    focal_knob.setFlag(nuke.NO_ANIMATION)
    zdefocus_node.addKnob(focal_knob)

    # focal value, invisible, use only for expression
    fvalue_knob = nuke.Double_Knob("focal_value", "focal value")
    fvalue_knob.setTooltip("value of depth.Z that is focused")
    zdefocus_node.addKnob(fvalue_knob)

    # dof radius
    dof_knob = nuke.Double_Knob("dof", "depth of field")
    dof_knob.setRange(0, 0.1)
    dof_knob.setTooltip("value of a range where everything in depth will be in focus")
    zdefocus_node.addKnob(dof_knob)

    # visualisation
    output_knob = nuke.Enumeration_Knob("display", "display as", ["result", "focal plane setup"])
    zdefocus_node.addKnob(output_knob)

    # blur size
    zdefocus_node.addKnob(nuke.Text_Knob('div1', ''))
    size_knob = nuke.Double_Knob("size")
    size_knob.setRange(0, 50)
    size_knob.setTooltip("homogeneous blur on each convolution circle")
    zdefocus_node.addKnob(size_knob)
    intensity_knob = nuke.Double_Knob("intensity")
    intensity_knob.setTooltip("amount of blur added for each convolution circle")
    zdefocus_node.addKnob(intensity_knob)

    # anti aliasing
    zdefocus_node.addKnob(nuke.Text_Knob('div1', ''))
    aliasing_knob = nuke.Double_Knob("anti_aliasing")
    aliasing_knob.setRange(0, 20)
    zdefocus_node.addKnob(aliasing_knob)

    # aberration chromatique
    zdefocus_node.addKnob(nuke.Text_Knob("div1", ""))
    ac_red_knob = nuke.Double_Knob("red_scale", "red scale")
    ac_red_knob.setValue(1)
    ac_red_knob.setRange(0.99, 1.01)
    zdefocus_node.addKnob(ac_red_knob)
    ac_green_knob = nuke.Double_Knob("green_scale", "green scale")
    ac_green_knob.setRange(0.99, 1.01)
    ac_green_knob.setValue(1)
    zdefocus_node.addKnob(ac_green_knob)
    ac_blue_knob = nuke.Double_Knob("blue_scale", "blue scale")
    ac_blue_knob.setRange(0.99, 1.01)
    ac_blue_knob.setValue(1)
    zdefocus_node.addKnob(ac_blue_knob)

    # abberation mask
    ac_mask_knob = nuke.Double_Knob("mask_scale", "mask blur")
    ac_mask_knob.setValue(0.46)
    zdefocus_node.addKnob(ac_mask_knob)

    # callbacks
    nuke.callbacks.addKnobChanged(on_focus_changed, node=zdefocus_node)


def set_nodes(zdefocus_node):
    """create all nodes inside defocus node

    Args:
        zdefocus_node (Node): node group where used nodes are populated
    """

    zdefocus_node.begin()

    input_node = nuke.nodes.Input(name="Input_zdefocus")

    shuffle_node = nuke.nodes.Shuffle(name='separate_z',
                                      red='red2',
                                      green='red2',
                                      blue='red2',
                                      alpha='alpha',
                                      in2="depth",
                                      inputs=[input_node])

    background_node = nuke.nodes.Constant(name='z_background',
                                          channels='rgba',
                                          color=1)

    merge_node = nuke.nodes.Merge2(also_merge="all",
                                   inputs=[background_node, shuffle_node])

    aliasing_node = nuke.nodes.Blur(name="anti_aliasing",
                                    channel='all',
                                    crop=False,
                                    inputs=[merge_node])
    aliasing_node['size'].setExpression("parent.anti_aliasing")

    alpha_node = nuke.nodes.Shuffle(name="to_alpha",
                                    alpha="red",
                                    inputs=[aliasing_node])

    for n in range(1, DIV + 1):
        if n == 1:
            blur_node = input_node

        grade_node = nuke.nodes.Grade(name="Grade%s" % n,
                                      channel='rgba',
                                      inputs=[alpha_node])

        blur_node = nuke.nodes.Blur(name="Blur%s" % n,
                                    channel='rgba',
                                    filter='box',
                                    crop=False,
                                    inputs=[blur_node, grade_node])

        # masque entre arriere plan et focus
        if n < DIV * (1. / 2):
            grade_node['blackpoint'].setExpression("Grade%s.blackpoint + %s" % (str(n + 1), INTERVAL))
            grade_node['whitepoint'].setExpression("blackpoint + %s" % str(INTERVAL * 2.))
            blur_node['size'].setExpression("Blur%s.size + parent.intensity" % str(n + 1))

        # dernier masque d'arriere plan
        elif n >= DIV * (1. / 2) and n < DIV * (1. / 2) + 1:
            grade_node['blackpoint'].setExpression("parent.focal_value + parent.dof")
            grade_node['whitepoint'].setExpression("blackpoint + %s" % str(INTERVAL * 2.))
            blur_node['size'].setExpression("parent.size")

            blue_node = create_colored_mask(grade_node, [0, 0, 1, 0], "blue")

        # premier masque d'avant plan
        elif n >= DIV * (1. / 2) + 1 and n < DIV * (1. / 2) + 2:
            grade_node['blackpoint'].setExpression("parent.focal_value - parent.dof")
            grade_node['whitepoint'].setExpression("blackpoint - %s" % str(INTERVAL * 2.))
            blur_node['size'].setExpression("Blur%s.size" % str(n - 1))

            merge_node = nuke.nodes.Merge2(inputs=[grade_node, nuke.toNode("Grade%s" % str(n - 1))])
            invert_node = nuke.nodes.Invert(inputs=[merge_node])
            green_node = create_colored_mask(invert_node, [0, 1, 0, 0], "green")
            red_node = create_colored_mask(grade_node, [1, 0, 0, 0], "red")

        # masque entre focus et avant plan
        elif n >= DIV * (1. / 2) + 2:
            grade_node['blackpoint'].setExpression("Grade%s.blackpoint - %s" % (str(n - 1), INTERVAL))
            grade_node['whitepoint'].setExpression("blackpoint - %s" % str(INTERVAL * 2.))
            blur_node['size'].setExpression("Blur%s.size + parent.intensity" % str(n - 1))

    # focus plane setup
    merge = nuke.nodes.Merge2(name="merge_rgb_focusplane",
                              inputs=[red_node, green_node, None, blue_node])

    switch_node = nuke.nodes.Switch(inputs=[blur_node, merge])
    switch_node["which"].setExpression("parent.display")

    # aberration chromatique
    width = nuke.root().width()
    height = nuke.root().width()

    node_reset = nuke.nodes.Remove(name="ac_reset", inputs=[switch_node])

    node_radial = nuke.nodes.Radial(name="ac_mask", inputs=[node_reset])
    node_radial["area"].setExpression("parent.focus_position.x - (%s/2)" % width, channel=0)
    node_radial["area"].setExpression("parent.focus_position.y - (%s/2)" % height, channel=1)
    node_radial["area"].setExpression("%s + area.x" % width, channel=2)
    node_radial["area"].setExpression("%s + area.y" % height, channel=3)
    node_radial["softness"].setExpression("parent.mask_scale")

    red = aberration_color_node(switch_node, "red", 1, node_radial)
    green = aberration_color_node(switch_node, "green", 16711935, node_radial)
    blue = aberration_color_node(switch_node, "blue", 65535, node_radial)

    ac_shuffle_copy = nuke.nodes.ShuffleCopy(red="red",
                                             green="green2",
                                             blue=0,
                                             inputs=[green, red])
    ac_shuffle_copy = nuke.nodes.ShuffleCopy(red="red",
                                             green="green",
                                             blue="blue2",
                                             inputs=[blue, ac_shuffle_copy])

    inject_alpha = nuke.nodes.ShuffleCopy(name="inject_alpha",
                                          red="red",
                                          green="green",
                                          blue="blue",
                                          alpha="alpha2",
                                          inputs=[switch_node, ac_shuffle_copy])

    remove_node = nuke.nodes.Remove(name="remove_z", channels="depth", inputs=[inject_alpha])
    remove_node["disable"].setExpression("1-parent.remove")

    nuke.nodes.Output(inputs=[remove_node])
    zdefocus_node.end()


def on_focus_changed():
    """set zdepth focused value from selected pixels on viewport"""

    if nuke.thisKnob().name() == "focus_position":
        zdefocus_node = nuke.thisNode()

        focus = zdefocus_node["focus_position"].getValue()
        focus_value = zdefocus_node.sample("depth.Z", focus[0], focus[1])
        zdefocus_node["focal_value"].setValue(focus_value)


def create_colored_mask(input_node, rgba_value, name):
    """create a colored mask

    Arguments:
        input_node {Node} -- input node
        rgba_value {list} -- 4 floats as rgba values
        name {string} -- color name

    Returns:
        Node -- the last node created (a Merge2 node) as colored mask output
    """

    constant_node = nuke.nodes.Constant(name=name)
    constant_node["color"].setValue(rgba_value)

    merge_node = nuke.nodes.Merge2(name="merge_%s" % name,
                                   operation="multiply",
                                   inputs=[input_node, constant_node])

    return merge_node


def aberration_color_node(input_node, color, tile_color, mask):
    """seperate a color and add a transform node

    Arguments:
        input_node {Node} -- The input node
        color {string} -- name color you want to extract (red, green or blue)
        tile_color {int} -- node tile color
        mask {Node} -- The mask used as a lens distorsion to attenuate aberration on image center

    Returns:
        Node -- the last node created (merge node)
    """

    node_shuffle = nuke.nodes.Shuffle(name="ac_%s" % color,
                                      tile_color=tile_color,
                                      red=color,
                                      green=color,
                                      blue=color,
                                      alpha="white",
                                      inputs=[input_node])

    node_transform = nuke.nodes.Transform(name="%s_transform" % color,
                                          tile_color=tile_color,
                                          inputs=[node_shuffle])
    node_transform["scale"].setExpression("parent.%s_scale" % color)

    node_mask = nuke.nodes.Merge2(name="%s_merge_msk" % color,
                                  tile_color=tile_color,
                                  operation="mask",
                                  inputs=[node_shuffle, mask])

    node_merge = nuke.nodes.Merge2(name="%s_merge" % color,
                                   tile_color=tile_color,
                                   inputs=[node_transform, node_mask])

    return node_merge


def run():
    """Create zdefocus node"""

    # CREATE NODE GROUP
    zdefocus_node = nuke.nodes.Group(name="ZDefocus", tile_color=1795118591)
    set_ui(zdefocus_node)
    set_nodes(zdefocus_node)
