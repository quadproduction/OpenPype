# -*- coding: utf-8 -*-

"""
    multimixer
        Florentin LUCE
    =================================================

    Version 4.0

    Select nodes and read and launch the tool to create
    a multimixer node

    To add nodes to the multimixer, select them and click
    on 'Add Inputs'

    Every exposed parameters drive others ones with
    expressions and all the script is contains inside
    the multimixer node;
    So this multimixer is faster and independant from
    this script

"""

import os
import re
import tempfile
import nuke


def write_script(end_lines):
    """retun this script as a string

    Arguments:
        end_lines {string} -- command line you want to add after the script
    Returns:
        string -- all the script
    """

    file_path = os.path.splitext(os.path.realpath(__file__))[0] + '.py'

    with open(file_path, 'rb') as script:
        all_script = script.read()
        all_script += "\n%s" % end_lines

        return "%s" % all_script


def get_valid_nodes(selection=None):
    """Find if selected nodes have a read

    Arguments:
        selection {list} -- All nodes selected (default: {None})
    Returns:
        dict -- As key the node and value, his name or file name if is a read
    """

    ignore = ['BackdropNode', 'Viewer', 'StickyNote']

    valid_nodes = {}

    for node in selection:
        # Si c'est un read, on recupere le nom du fichier
        if node.Class() == 'Read':
            file_name = os.path.splitext(os.path.basename(node['file'].getValue()))[0]

            # Clean file name
            try:
                name = re.findall(r'_v\d+[\w]*', file_name)[0]
                version = re.findall(r'_v\d+_', name)[0]
                name = name.replace(version, "")
                name += " (%s)" % version.replace("_", "")
            except Exception:
                name = ''.join(c for c in file_name if c.isalnum() or c == "_")

            valid_nodes[node] = name

        # sinon, on cherche le read pour verifier que le node a une image
        elif node.Class not in ignore:
            topnode_name = nuke.tcl("full_name [topnode %s]" % node.name())
            topnode = nuke.toNode(topnode_name)
            if topnode.Class() == "Read":
                valid_nodes[node] = node.name()

    return valid_nodes


def unlock_knobs(node, state):
    """change all knobs state

    Arguments:
        node {Node} -- The node to operate
        state {Bool} -- True to unlock, False to lock
    """

    for knob in node.allKnobs():
        knob.setEnabled(state)


def get_frame_range(input_nodes):
    """Get average frame range for all inputs node

    Arguments:
        input_nodes {dict} -- a dict where key are nodes with frame range
    Returns:
        tuple -- the most common frame range as (start, end)
    """

    ranges = [(node["first"].value(), node["last"].value()) for node in input_nodes.keys()
              if node.Class() == "Read"]
    if ranges:
        most_common = max(set(ranges), key=ranges.count)
    else:
        most_common = 1, 1

    return most_common


def get_common_name(input_nodes):
    """Get the common name of all input nodes

    Arguments:
        input_nodes {dict} -- a dict where key are nodes and values the name used in multimixer ui
    Returns:
        string -- the suffixe of multimixer name
    """

    list_names = [c.split('_') for c in input_nodes.values()]

    # a set with unique words in all list_names
    common_words = set(list_names[0]).intersection(*map(set, list_names))

    # write the new name with the unique common words
    common = "_".join([c for c in list_names[0] if c in common_words])

    return "_%s" % common.split(' ')[0]


def get_common_format(input_nodes):
    """Find the largest input formats

    Arguments:
        input_nodes {dict} -- a dict where key are nodes and values the name used in multimixer ui
    Returns:
        string -- the largest input format as "width height pixel_aspect name"
    """

    all_formats = [node["format"].value() for node in input_nodes.keys() if node.knob("format")]

    if all_formats:
        common_format = max(set(all_formats), key=lambda f: [g.width() for g in all_formats].count(f.width()))
    else:
        # get root format
        common_format = nuke.root()

    return "%s %s %s %s" % (
        common_format.width(),
        common_format.height(),
        common_format.pixelAspect(),
        common_format.name()
    )

####################################################################################################


def create_inputs(multimix_node, input_nodes, node_merge, start_index=1):
    """create passes knobs + inputs and merge inside mulimixer node

    Arguments:
        multimix_node {Node} -- Multimixer node
        input_nodes {dict} -- a dict where key are nodes and values the name used in multimixer ui
        node_merge {Node} -- the last node to merge with the new input
    Keyword Arguments:
        start_index {int} -- which number the input must start (default: {1})
    Returns:
        Node -- the first input node if exists
        list -- all inputs relations to connect after
        Node -- last node created
    """

    # Create Passes Knobs
    for index, input_name in enumerate(input_nodes.values()):
        index += start_index

        if len(input_name) > 10:
            label_knob = nuke.Text_Knob(input_name)
            label_knob.setFlag(nuke.ENDLINE)
            multimix_node.addKnob(label_knob)
            input_name = ""

        mult_knob = nuke.Double_Knob("mult_%s" % index, input_name)
        mult_knob.setValue(1)
        mult_knob.setRange(0, 5)
        multimix_node.addKnob(mult_knob)

        solo_knob = nuke.Boolean_Knob("solo_%s" % index, "Solo")
        multimix_node.addKnob(solo_knob)

        mute_knob = nuke.Boolean_Knob("mute_%s" % index, "Mute")
        mute_knob.clearFlag(nuke.STARTLINE)
        multimix_node.addKnob(mute_knob)

    # Add inputs inside
    first_input = None
    all_inputs_relations = []

    for index, (node, node_name) in enumerate(input_nodes.iteritems()):
        index += start_index
        node_input = nuke.nodes.Input(name="Input%s" % index)
        # set a dict with all input relationship
        input_relations = {}
        input_relations['source'] = node
        input_relations['destination'] = node_input
        input_relations['index'] = index
        all_inputs_relations.append(input_relations)
        if index == 1:
            first_input = node_input

        # node grade
        node_grade = nuke.nodes.Grade(name="Grade%s" % index,
                                      inputs=[node_input])

        node_grade['white'].setExpression("%s.mult_%s" % (multimix_node.name(), index))

        # node merge
        node_merge = nuke.nodes.Merge2(name="Merge%s" % index,
                                       operation="plus",
                                       bbox="intersection",
                                       inputs=[node_merge, node_grade])

        # set expression for merge
        node_merge['operation'].setExpression("%s.operation" % multimix_node.name())
        solomode = " + ".join("[value solo_{}]".format(i) for i in range(1, len(input_nodes) + 1))
        node_merge["disable"].setExpression("max((({0}) ? 1 - [value solo_{1}] : [value mute_{1}]), ![value mult_{1}])".format(solomode, index))

    return first_input, all_inputs_relations, node_merge


def connect_inputs(all_inputs_relations, multimix_node):
    """connect and set the inputs to the multimixer

    Arguments:
        all_inputs_relations {list} -- all inputs relations to connect
        multimix_node {Node} -- Multimixer node
    """

    # sort by index
    all_inputs_relations = sorted(all_inputs_relations, key=lambda i: i['index'])

    # find if empty input exists and get their indexes
    empty_index = [i for i in range(multimix_node.inputs()) if not multimix_node.input(i)]

    for input_relations in all_inputs_relations:
        # if empty index exist assign them to the first input relation element
        # and remove it from the list in order to don't have empty input
        if empty_index:
            index = empty_index.pop(0)
            multimix_node.setInput(index, input_relations['source'])
            continue
        multimix_node.setInput(input_relations['index'] - 1, input_relations['source'])


def create_multimixer_ui(multimix_node, inputs):
    """set the multimixer node ui and properties

    Arguments:
        multimix_node {Node} -- the multimixer on which you want to set the properties
        inputs {dict} -- a dict where key are nodes and values the name used in multimixer ui
    """

    multimix_node.addKnob(nuke.Tab_Knob("MultiMix"))

    # Titre
    multimix_node.addKnob(nuke.Text_Knob('title', '', '<img src=":qrc/images/ToolbarMerge.png"> <font size="5"> MultiMix v4.0 </font>'))
    multimix_node.addKnob(nuke.Text_Knob('div1', ''))

    # Format connected to constant node inside
    format_knob = nuke.Link_Knob("format", "Format", get_common_format(inputs))
    multimix_node.addKnob(format_knob)

    # Frames range connected to frameRange node inside
    first_knob = nuke.Link_Knob("first", "Frame Range")
    multimix_node.addKnob(first_knob)
    last_knob = nuke.Link_Knob("last", " ")
    last_knob.clearFlag(nuke.STARTLINE)
    multimix_node.addKnob(last_knob)

    # Operation
    modes = [
        "atop", "Ab+B(1-a)",
        "average", "(A+B)/2",
        "color-burn", "darken B towards A",
        "color-dodge", "Brighten B towards A",
        "conjoint-over", "A+B(1-a)/b, A if a>b",
        "copy", "A",
        "difference", "abs(A-B)",
        "disjoint-over", "A+B(1-a)/b, A+B if a+b<1",
        "divide", "A/B, 0 if A<0 and B<0",
        "exclusion", "A+B-2AB",
        "from", "B-A",
        "geometric", "2AB/(A+B)",
        "hard-light", "multiply if A<.5, screen if A>.5",
        "hypot", "diagonal sqrt(A*A+B*B)",
        "in", "Ab",
        "mask", "Ba",
        "matte", "Aa+B(1-a) (unpremultiplied over)",
        "max", "max(A,B)",
        "min", "min(A,B)",
        "minus", "A-B",
        "multiply", "AB, A if A<0 and B<0",
        "out", "A(1-b)",
        "over", "A+B(1-a)",
        "overlay", "multiply if B<.5, screen if B>.5",
        "plus", "A+B",
        "screen", "A+B-AB if A and B between 0-1, else A if A>B else B",
        "soft-light", "B(2A+(B(1-AB))) if AB<1, 2AB otherwise (less extreme than hard-light)",
        "stencil", "B(1-a)",
        "under", "A(1-b)+B",
        "xor", "A(1-b)+B(1-a)",
    ]

    mode_names, mode_desc = modes[::2], modes[1::2]
    operation_knob = nuke.Enumeration_Knob("operation", "operation", mode_names)
    operation_knob.setTooltip("\n".join(" ".join(["<b>{}</b>".format(n), d]) for n, d in zip(mode_names, mode_desc)))
    operation_knob.setValue("plus")
    multimix_node.addKnob(operation_knob)

    # Alpha activation
    alpha_knob = nuke.Boolean_Knob("alpha", " enable alpha", True)
    alpha_knob.setFlag(nuke.STARTLINE)
    multimix_node.addKnob(alpha_knob)

    multimix_node.addKnob(nuke.Text_Knob("div2", ""))

    # Duplicate node
    duplicate_script = """%s""" % write_script("duplicate(nuke.thisGroup())")
    dup = nuke.PyScript_Knob('dup', ' duplicate MultiMixer ', duplicate_script)
    dup.setFlag(nuke.STARTLINE)
    multimix_node.addKnob(dup)

    # copy values
    copy_script = """%s""" % write_script("copy_values(nuke.thisGroup())")
    cop = nuke.PyScript_Knob('cop', ' Copy values ', copy_script)
    cop.setFlag(nuke.STARTLINE)
    multimix_node.addKnob(cop)

    # paste values
    paste_script = """%s""" % write_script("paste_values(nuke.thisGroup())")
    pas = nuke.PyScript_Knob('pas', ' Paste values ', paste_script)
    pas.clearFlag(nuke.STARTLINE)
    multimix_node.addKnob(pas)

    multimix_node.addKnob(nuke.Text_Knob("div2", ""))

    # Add input
    add_script = """%s""" % write_script("add_inputs(nuke.thisNode())")
    add_knob = nuke.PyScript_Knob("add_input", " Add inputs ", add_script)
    multimix_node.addKnob(add_knob)

    # delete input
    remove_script = """%s""" % write_script("remove_inputs(nuke.thisNode())")
    remove_knob = nuke.PyScript_Knob("remove_input", " Remove inputs ", remove_script)
    multimix_node.addKnob(remove_knob)

    # Solo all
    solo_script = """multimix = nuke.thisNode()
knobs = [knob for knob in multimix.knobs() if "solo_" in knob and not knob == "solo_all"]
new_value = sum(multimix[knob].value() for knob in knobs) < len(knobs)
[multimix[knob].setValue(new_value) for knob in knobs]
"""
    solo_all_knob = nuke.PyScript_Knob("solo_all", " Solo All ", solo_script)
    solo_all_knob.setFlag(nuke.STARTLINE)
    multimix_node.addKnob(solo_all_knob)

    # Mute all
    mute_script = """multimix = nuke.thisNode()
knobs = [knob for knob in multimix.knobs() if "mute_" in knob and not knob == "mute_all"]
new_value = sum(multimix[k].value() for k in knobs) < len(knobs)
need_change = [k for k in knobs if multimix[k].value() != new_value]
[multimix[k].setValue(new_value) for k in knobs]
"""
    mute_all_knob = nuke.PyScript_Knob("mute_all", " Mute All ", mute_script)
    mute_all_knob.clearFlag(nuke.STARTLINE)
    multimix_node.addKnob(mute_all_knob)


def create_multimixer(input_nodes):
    """create a multimixer from selected nodes

    Arguments:
        input_nodes {dict} -- a dict where key are nodes and values the name used in multimixer ui
    Returns:
        Node -- the multimixer node created
    """

    # Get a valid name
    name = "MultiMix%s" % get_common_name(input_nodes)

    if nuke.toNode(name):
        nb = 1
        while nuke.toNode("%s%s" % (name, nb)):
            nb += 1
        name += str(nb)

    # Get position
    all_x = [node.xpos() for node in input_nodes.keys()]
    all_y = [node.ypos() for node in input_nodes.keys()]
    xpos = sum(all_x) / len(input_nodes)
    ypos = max(all_y) + 150

    # Create the group and set the values of the group"s default knobs
    multimix_node = nuke.nodes.Group(name=name,
                                     tile_color=2154094847,
                                     hide_input=True,
                                     xpos=xpos,
                                     ypos=ypos,
                                     postage_stamp=False)

    # UI
    create_multimixer_ui(multimix_node, input_nodes)

    # Add nodes inside
    multimix_node.begin()

    # constant node
    constant_node = nuke.nodes.Constant(name="Black_Constant",
                                        format=get_common_format(input_nodes),
                                        channels="rgba",
                                        postage_stamp=False)
    multimix_node["format"].makeLink(constant_node.name(), "format")
    node_merge = constant_node

    # inputs and merge nodes
    first_input, all_inputs_relations, last_merge = create_inputs(multimix_node, input_nodes, node_merge)

    # ShuffleCopy node
    shuffle_node = nuke.nodes.ShuffleCopy(name="Alpha_ShuffleCopy",
                                          red="red2",
                                          green="green2",
                                          blue="blue2",
                                          inputs=[last_merge, first_input])
    shuffle_node['alpha'].setExpression("%s.alpha ? 4 : 5" % multimix_node.name())

    # Framerange node
    first, last = get_frame_range(input_nodes)
    frame_range_node = nuke.nodes.FrameRange(name="Custom_FrameRange",
                                             first_frame=first,
                                             last_frame=last,
                                             inputs=[shuffle_node])
    multimix_node["first"].makeLink(frame_range_node.name(), "first_frame")
    multimix_node["last"].makeLink(frame_range_node.name(), "last_frame")

    # Output node
    nuke.nodes.Output(inputs=[frame_range_node])
    multimix_node.end()

    connect_inputs(all_inputs_relations, multimix_node)

    # Enabled knobs locked in nuke assist
    unlock_knobs(multimix_node, True)

    return multimix_node


def duplicate(node):

    inputs = [node.input(i) for i in range(node.inputs())]
    nuke.root().begin()
    orig_selection = nuke.root().selectedNodes()  # store selection
    for n in orig_selection:
        n.setSelected(0)  # deselect all

    node.setSelected(1)  # select node
    nuke.nodeCopy('%clipboard%')  # copy
    node.setSelected(0)  # deselect

    nuke.nodePaste('%clipboard%')  # paste
    new_node = nuke.selectedNode()

    for n in nuke.selectedNodes():
        n.setSelected(0)  # deselect all
    for n in orig_selection:
        n.setSelected(1)  # select original selection

    for i, inp in enumerate(inputs):
        new_node.setInput(i, inp)

    new_node.autoplace()

    return new_node


def copy_values(node):

    knobs = node.knobs()
    mult_solo_mute_knobs = [n for n in knobs if any((n.startswith(i) for i in ('mult_', 'solo_', 'mute_')))]
    data = {k: node[k].value() for k in mult_solo_mute_knobs}

    temp_file_path = os.path.join(tempfile.gettempdir(), 'multimixer_temp.txt')

    with open(temp_file_path, 'w') as f:
        f.write(str(data))


def paste_values(node):

    temp_file_path = os.path.join(tempfile.gettempdir(), 'multimixer_temp.txt')

    if os.path.isfile(temp_file_path):
        with open(temp_file_path, 'r') as f:
            data = eval(f.read())
            for k in node.knobs():
                if k in data:
                    node[k].setValue(data[k])
    else:
        nuke.message('Copy first.')


def add_inputs(multimix):
    """Add selected nodes and plug them into multimixer

    Arguments:
        multimix {Node} -- Multimixer node
    """

    multimix.end()
    input_nodes = get_valid_nodes(selection=nuke.selectedNodes())

    index = int(max([re.findall(
        r'\d',
        input_node.name()
    )[0] for input_node in nuke.allNodes(group=multimix) if input_node.Class() == "Input"]))
    last_node_merge = [node for node in nuke.allNodes(group=multimix) if node.name() == "Merge%s" % index][0]

    multimix.begin()
    first_input, all_inputs_relations, last_merge = create_inputs(
        multimix,
        input_nodes,
        last_node_merge,
        start_index=index + 1
    )
    shuffle_node = nuke.toNode("Alpha_ShuffleCopy")
    shuffle_node.setInput(0, last_merge)
    multimix.end()

    connect_inputs(all_inputs_relations, multimix)

    # Enabled knobs locked in nuke assist
    unlock_knobs(multimix, True)


def remove_inputs(multimix):
    """Remove inputs by deleting linked nodes and knobs of selected input nodes

    Arguments:
        multimix {Node} -- Multimixer node
    """

    multimix.end()
    input_nodes = get_valid_nodes(selection=nuke.selectedNodes())

    all_index = [int(v.split('_')[-1]) for (v, knob) in multimix.knobs().items()
                 if knob.label() in input_nodes.values()]

    knobs_list = ['mult', 'solo', 'mute']
    nodes_list = ['Input', 'Grade', 'Merge']

    for index in all_index:
        # remove knob
        for knob in knobs_list:
            multimix.removeKnob(multimix["%s_%s" % (knob, index)])

        # delete node inside group
        multimix.begin()
        for name in nodes_list:
            node = nuke.toNode("%s%s" % (name, index))
            if not node:
                continue
            nuke.delete(node)
        multimix.end()

        # disconnect input
        multimix.setInput(index - 1, None)

####################################################################################################


def run():
    """Create a dynamic multimixer"""

    inputs = get_valid_nodes(selection=nuke.selectedNodes())

    if not inputs:
        nuke.message("No valid Read Node could be found")
        return

    create_multimixer(inputs)
