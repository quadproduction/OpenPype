# -*- coding: utf-8 -*-

"""
Utilizy methods to manipulate nuke
"""

import os
import nuke
import random

# the default size of a node in the node graph.
# can't read it from the preferences so we set it here.
# WARGNING : for read nodes use DEFAULT_READ_NODE_SIZE
DEFAULT_TILE_SIZE = (80, 18)
DEFAULT_READ_NODE_SIZE = (80, 80)


# ==========
# in terminal mode
# ==========


def terminal_get_node_size(node):
    """in terminal mode we can't get screenWidth()/screenHeight() so we use this method
    :param node: the node whose size to get
    :type node: Node
    :return; the size of the node
    :rtype: tuple
    """
    return DEFAULT_READ_NODE_SIZE if node.Class() == 'Read' else DEFAULT_TILE_SIZE


def terminal_autoBackdrop():
    """
    Automatically puts a backdrop behind the selected nodes.
    The backdrop will be just big enough to fit all the select nodes in, with room at the top for some text in large font.
    Inherited from : https://www.thefoundry.co.uk/products/nuke/developers/100/pythonreference/nukescripts.autobackdrop-pysrc.html
    because screenWidth() and screenHeight() methods are not working in terminal mode
    """
    selectedNodes = nuke.selectedNodes()
    if not selectedNodes:
        return None
    # Calculate bounds for the backdrop nodes
    bdX = min([node.xpos() for node in selectedNodes])
    bdY = min([node.ypos() for node in selectedNodes])
    bdW = max([node.xpos() + terminal_get_node_size(node)[0] for node in selectedNodes]) - bdX
    bdH = max([node.ypos() + terminal_get_node_size(node)[1] for node in selectedNodes]) - bdY

    # expand the bounds to leave a little border
    left, top, right, bottom = (-10, -80, 10, 10)
    bdX += left
    bdY += top
    bdW += (right - left)
    bdH += (bottom - top)

    zOrder = 0
    selectedBackdropNodes = nuke.selectedNodes('BackdropNode')
    # if there are backdropNodes selected put the new one immediately behind the farthest one
    if len(selectedBackdropNodes):
        zOrder = min([node.knob("z_order").value() for node in selectedBackdropNodes]) - 1

    n = nuke.nodes.BackdropNode(
        xpos=bdX,
        bdwidth=bdW,
        ypos=bdY,
        bdheight=bdH,
        z_order=zOrder,
        tile_color=int((random.random() * (16 - 10))) + 10,
        note_font_size=42)

    # revert to previous selection
    n.knob('selected').setValue(True)
    for node in selectedNodes:
        node.knob('selected').setValue(True)

    return n


def terminal_get_nodes_in_backdrop(node):
    """
    get all the nodes located in the backdrop node specified
    :param BackdropNode node: the backdrop node where to look
    :returns: the nodes in the backdrop
    :rtype: list
    """
    nodes = []
    xmin = node.knob('xpos').value()
    xmax = xmin + node.knob('bdwidth').value()
    ymin = node.knob('ypos').value()
    ymax = ymin + node.knob('bdheight').value()
    node.knob('selected').setValue(True)
    for i in [i for i in nuke.allNodes() if i is not node]:
        node_size = terminal_get_node_size(node)
        ixmin = i.knob('xpos').value()
        ixmax = ixmin + node_size[0]
        iymin = i.knob('ypos').value()
        iymax = iymin + node_size[1]

        if (ixmin >= xmin and ixmax < xmax) and (iymin >= ymin and iymax < ymax):
            nodes.append(i)
    return nodes


# ==========
# misc
# ==========


def get_nodes_in_backdrop(node):
    """
    get all the nodes located in the backdrop node specified
    :param BackdropNode node: the backdrop node where to look
    """
    nodes = []

    xmin = node.knob('xpos').value()
    xmax = xmin + node.knob('bdwidth').value()
    ymin = node.knob('ypos').value()
    ymax = ymin + node.knob('bdheight').value()
    node.knob('selected').setValue(True)
    for i in [i for i in nuke.allNodes() if i is not node]:
        ixmin = i.knob('xpos').value()
        ixmax = ixmin + i.screenWidth()
        iymin = i.knob('ypos').value()
        iymax = iymin + i.screenHeight()

        if (ixmin >= xmin and ixmax < xmax) and (iymin >= ymin and
        iymax < ymax):
            nodes.append(i)

    return nodes


def deselectAllNodes():
    """deselect all nodes in the current composition"""
    for n in nuke.allNodes():
        n.knob('selected').setValue(False)


def get_nodes_by_class(class_name):
    """Get nodes of a class in selection if there is one or entire script
    :param class_name: the name of the class of nodes to search
    :type class_name: str
    :returns: all nodes of the class specified
    :rtype: list
    """
    nodes = list()
    if len(nuke.selectedNodes()) > 0:
        nodes = nuke.selectedNodes(class_name)
    else:
        nodes = nuke.allNodes(class_name)
    return nodes


def create_reads_from_writes(write_nodes=None):
    """Create read nodes with write's outputs as inputs
    :param write_nodes: the write nodes
    :type write_nodes: list
    :returns: the read nodes created
    :rtype list
    """
    actual_write_nodes = list()
    if not write_nodes:
        write_nodes = nuke.selectedNodes()
    # check that there are actually write nodes in the input
    for node in write_nodes:
        if node.Class() in ['Write', 'WriteTank']:
            actual_write_nodes.append(node)
    if len(actual_write_nodes) == 0:
        nuke.message('No write node selected')
    # create read nodes
    read_nodes = list()
    start = int(nuke.root().knob('first_frame').value())
    last = int(nuke.root().knob('last_frame').value())
    for write_node in actual_write_nodes:
        read_node = nuke.createNode('Read', inpanel=False)
        read_node.knob('name').setValue('Read_From_Write_' + write_node.knob('name').value())
        file_path = str()
        if write_node.Class() == 'Write':
            file_path = write_node.knob('file').value()
        elif write_node.Class() == 'WriteTank':
            file_path = write_node.knob('cached_path').value()
        read_node.knob('file').setValue(file_path)
        read_node.knob('first').setValue(start)
        read_node.knob('last').setValue(last)
        read_node.knob('xpos').setValue(write_node.knob('xpos').value() + read_node.screenWidth() + 100)
        read_node.knob('ypos').setValue(write_node.knob('ypos').value())
        read_nodes.append(read_node)
    return read_nodes


# ==========
# Shotgun related
# ==========


def get_writeTank_file(writeTank_node):
    """Computes the file value where the writeTank node will write
    :param writeTankNode: the node fron where to extract the file
    :type writeTankNode: Node of class WriteTank
    :returns: the path of the file where the node will write
    :rtype: str
    :raises: TypeError
    """
    if writeTank_node.Class() != 'WriteTank':
        raise TypeError('node class must be WriteTank')
    return os.path.join(
        writeTank_node.knob('path_context').value(),
        writeTank_node.knob('path_local').value(),
        writeTank_node.knob('path_filename').value())
