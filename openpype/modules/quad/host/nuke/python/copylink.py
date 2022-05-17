# -*- coding: utf-8 -*-

"""
    copylink
        Florentin LUCE
    =================================================

    Duplicate selected graph preserving connections

"""

import nuke
import nukescripts


def delete_temp(node):
    """Delete temporary knob

    Arguments:
        node {Node} -- node on which script runs
    """

    attr = ["temp_tab", "connectionTemp"]
    match = [knob for knob in node.allKnobs() if any([a in knob.name() for a in attr])]

    for knob in match:
        node.removeKnob(knob)


def run():
    """Run the script"""

    nodes_to_copy = nuke.selectedNodes()

    # copy paste each node one by one
    pasted_nodes = []

    for copy_node in nodes_to_copy:

        # remove temp_tab if exists
        if copy_node.knob('temp_tab'):
            delete_temp(copy_node)

        # deselect all
        nukescripts.misc.clear_selection_recursive()

        copy_node.setSelected(True)
        nukescripts.node_copypaste()
        pasted_nodes.append(nuke.selectedNode())

        # move node with an offset.
        nuke.selectedNode().setXYpos(copy_node.xpos()-80, copy_node.ypos()-80)

    # set nodes connections
    for i, node in enumerate(pasted_nodes):

        # get the node that copy one come from
        from_node = nodes_to_copy[i]

        for input_index in range(from_node.inputs()):

            input_node = from_node.input(input_index)

            if input_node not in nodes_to_copy:
                # get parent nodes tha wasn't copied
                input_node = input_node
            else:
                input_node = pasted_nodes[nodes_to_copy.index(input_node)]

            # for locked node only
            locked_node = False
            if node.knob("lock_inputs"):
                locked_node = True
                node["lock_inputs"].setValue(0)

            node.setInput(input_index, input_node)
            node.setSelected(True)

            # for locked node only
            if locked_node:
                node["lock_inputs"].setValue(1)
