# -*- coding: utf-8 -*-

"""
All utils functions for Nuke
"""

import nuke


def unlock_all():
    """Unlock all knob for every node in the scene"""

    for node in nuke.allNodes():
        for knob in node.knobs().values():
            knob.setEnabled(True)


def set_format(from_node, to_node):
    """set origin node format no another node

    Arguments:
        from_node {Node} -- node with reference format
        to_node {Node} -- node on which you want apply format
    Returns:
        Format -- nuke format object
    """

    img_format = from_node['format'].value()

    if to_node.knob('format'):
        to_node['format'].setValue(img_format)

    return img_format


def get_linked_nodes_from_class(node, node_class, node_list):
    """climb up in tree to get all nodes matching a class

    Arguments:
        node {Node} -- starting node
        node_class {string} -- node class wanted
        node_list {list} -- initial list with matching nodes
    Returns:
        list -- all matching nodes
    """

    for index in range(node.inputs()):
        parent_node = node.input(index)
        if parent_node.Class() == node_class and parent_node not in node_list:
            node_list.append(parent_node)
        else:
            node_list = get_linked_nodes_from_class(
                parent_node,
                node_class,
                node_list
            )
    return node_list


def get_used_reads():
    """Get all reads used in a comp

    Returns;
        list -- all read nodes
    """

    all_write = nuke.allNodes('Write')
    all_reads = []

    for write in all_write:
        all_reads += get_linked_nodes_from_class(write, "Read", all_reads)
    all_reads = set(all_reads)

    return list(all_reads)
