# -*- coding: utf-8 -*-
'''
FIX MultiMixer

Creation Date : 17 Dec 2017
Version : 3.0
Changes : Add alpha and bbox preservation
Author : Benoit Delaunay
Author Email : delaunay.ben@gmail.com
Author Website : www.bendelaunay.com

Purpose : Easily manage multiple lighting layers

Usage : Select one or more Read nodes, then create node (MultiMixer)

Install : Copy this file to one of your Nuke_Path locations. If you add it to
          a subfolder, make sure this subfolder is browsed by appending
          nuke.pluginAddPath('subfolder_name') to the parent folder's init.py.
          Then append these lines to the menu.py:

import FIX_MultiMixer
nuke.menu('Nodes').addCommand('FIX/MultiMixer', 'reload(FIX_MultiMixer);FIX_MultiMixer.MultiMixer()')

          Restart Nuke and you should be able to create MultiMixers from the
          left toolbar, right-clic menu or by pressing tab.
'''


import os
import re
import tempfile
import nuke


def find_read(node):
    inputs = {node}
    reads = set()
    while inputs:
        reads |= {n for n in inputs if n.Class() == 'Read'}
        inputs = {n.input(i) for n in inputs for i in range(n.inputs())}
    if len(reads) == 1:
        read = list(reads)[-1]
        file_path = read['file'].value()
        name = os.path.split(file_path)[-1]
    else:
        name = node['name'].value()

    return {'reads': frozenset(reads or [node]), 'name': name}


def get_common_name(valid_inputs):
    try:
        first = [re.findall(r'(Lgt.*?)\.', name['name'])[0] for (r, name) in valid_inputs]
        common = list(set(first))[0]
    except Exception:
        common = ""

    return "_%s" % common


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


def MultiMixer():
    '''
    uugu
    '''
    selection = nuke.selectedNodes()

    ignore = ['BackdropNode', 'Viewer', 'StickyNote']  # node classes not to take into account
    valid_inputs = [n for n in selection if n.Class() not in ignore]

    if not valid_inputs:
        nuke.message('Select at least one Read node.')
        return

    valid_inputs = [(n, find_read(n)) for n in valid_inputs]
    valid_inputs.sort(key=lambda n: n[1]['name'])  # sort by name of read if there is one, or name of input node

    formats = [r['format'].value() for n in valid_inputs for r in n[1]['reads'] if r.knob('format')]
    if formats:
        fmt = max(set(formats), key=lambda f: [g.width() for g in formats].count(f.width()))
    else:
        fmt = valid_inputs[0][0]['fmt'].value()
    fmt = '{} {} {} {}'.format(fmt.width(), fmt.height(), fmt.pixelAspect(), fmt.name())
    constant = nuke.nodes.Constant(selected=1, channels='rgba', format=fmt)
    constant_name = constant['name'].value()

    merge = nuke.nodes.Merge2(selected=1, operation='plus', bbox="intersection")
    merge.setInput(0, constant)  # connect Constant to Merge as B
    first_merge = merge

    passes = []

    for i, n in enumerate(selection):
        n.setSelected(0)  # deselect

    for i, (n, read) in enumerate(valid_inputs):
        file_name = read['name']
        if '.' in file_name:
            file_name, file_ext = os.path.splitext(file_name)  # split filename and ext

        render_pass = file_name.replace(' ', '_').replace('.', '_')  # remove dots and spaces
        frame_nb = re.findall('_%0?\d?d$', render_pass)  # check for frame numbers and remove it
        if frame_nb:
            render_pass = render_pass.replace(frame_nb[0], '')

        file_version = re.findall('_v\d+_', render_pass, re.IGNORECASE)  # check for version number in the filename
        if file_version:
            render_pass = render_pass.split(file_version[0])  # keep everything after version
            render_pass = file_version[0].join(render_pass[1:]).split('_')
            render_pass = '_'.join(render_pass[1:])  # remove version name (MasterTest)

        if render_pass in passes:  # handle duplicates
            render_pass += '({})'.format(i)

        passes.append(render_pass)

    solomode = ' + '.join('[value solo_{}]'.format(p) for p in passes)

    for i, (n, read) in enumerate(valid_inputs):
        render_pass = passes[i]
        m = nuke.nodes.Multiply(selected=1, inputs=[n])  # connect Read to Multiply
        m['value'].setExpression('[value mult_{0}]'.format(render_pass))
        merge.setInput(1, m)  # connect Multiply to Merge
        merge['disable'].setExpression('max((({0}) ? 1 - [value solo_{1}] : [value mute_{1}]), ![value mult_{1}])'.format(solomode, render_pass))
        if i < len(valid_inputs) - 1:
            merge = nuke.nodes.Merge2(selected=1, operation='plus',bbox="intersection", inputs=(merge,))

    ranges = [(r['first'].value(), r['last'].value()) for n in valid_inputs for r in n[1]['reads'] if r.knob('first') and r.knob('last')]
    if ranges:
        most_common = max(set(ranges), key=ranges.count)
    else:
        most_common = 1, 1

    shuffle_node = nuke.nodes.ShuffleCopy(selected=1,
                                          name="Alpha_ShuffleCopy",
                                          red="red2",
                                          green="green2",
                                          blue="blue2",
                                          alpha="alpha",
                                          inputs=[merge, first_merge])

    first, last = most_common
    frange = nuke.nodes.FrameRange(selected=1, first_frame=first, last_frame=last, inputs=[shuffle_node])
    frange_name = frange['name'].value()

    node = nuke.collapseToGroup(show=False)  # create group

    name = 'MultiMixer%s' % get_common_name(valid_inputs)
    if nuke.toNode(name):
        nb = 1
        while nuke.toNode('{}{}'.format(name, nb)):
            nb += 1
        name += str(nb)

    node['name'].setValue(name)
    node['tile_color'].setValue(2154094847)
    node['hide_input'].setValue(1)
    node['lock_connections'].setValue(1)
    node['postage_stamp'].setValue(1)
    node['label'].setValue(r'<b>[expr {[value lock_inputs] ? "inputs locked" : "<font color=\"red\">inputs unlocked</font>"}]</b>')
    all_x = sum(n[0].xpos() for n in valid_inputs)
    all_y = sum(n[0].ypos() for n in valid_inputs)
    node.setXYpos(all_x / len(valid_inputs), all_y / len(valid_inputs) + 150)

    node.addKnob(nuke.Tab_Knob('MultiMixer'))
    node.addKnob(nuke.Text_Knob('title', '', 'MultiMixer for ROLEX v3.0'))
    node.addKnob(nuke.Text_Knob('div1', ''))

    lock = nuke.Boolean_Knob('lock_inputs', 'lock inputs')
    lock.setValue(1)
    lock.setTooltip('Prevent input changes while the MultiMixer is selected')
    lock.setFlag(nuke.STARTLINE)
    # lock.setFlag(nuke.INVISIBLE)
    node.addKnob(lock)

    fmt = nuke.Link_Knob('format')
    fmt.makeLink(constant_name, 'format')
    node.addKnob(fmt)

    first = nuke.Link_Knob('frame range')
    first.makeLink(frange_name, 'first_frame')
    node.addKnob(first)

    last = nuke.Link_Knob('')
    last.makeLink(frange_name, 'last_frame')
    last.clearFlag(nuke.STARTLINE)
    node.addKnob(last)

    modes = ['atop', 'Ab+B(1-a)',
             'average', '(A+B)/2',
             'color-burn', 'darken B towards A',
             'color-dodge', 'Brighten B towards A',
             'conjoint-over', 'A+B(1-a)/b, A if a>b',
             'copy', 'A',
             'difference', 'abs(A-B)',
             'disjoint-over', 'A+B(1-a)/b, A+B if a+b<1',
             'divide', 'A/B, 0 if A<0 and B<0',
             'exclusion', 'A+B-2AB',
             'from', 'B-A',
             'geometric', '2AB/(A+B)',
             'hard-light', 'multiply if A<.5, screen if A>.5',
             'hypot', 'diagonal sqrt(A*A+B*B)',
             'in', 'Ab',
             'mask', 'Ba',
             'matte', 'Aa+B(1-a) (unpremultiplied over)',
             'max', 'max(A,B)',
             'min', 'min(A,B)',
             'minus', 'A-B',
             'multiply', 'AB, A if A<0 and B<0',
             'out', 'A(1-b)',
             'over', 'A+B(1-a)',
             'overlay', 'multiply if B<.5, screen if B>.5',
             'plus', 'A+B',
             'screen', 'A+B-AB if A and B between 0-1, else A if A>B else B',
             'soft-light', 'B(2A+(B(1-AB))) if AB<1, 2AB otherwise (less extreme than hard-light)',
             'stencil', 'B(1-a)',
             'under', 'A(1-b)+B',
             'xor', 'A(1-b)+B(1-a)',
             ]

    mode_names, mode_desc = modes[::2], modes[1::2]
    op = nuke.Enumeration_Knob('operation', 'operation', mode_names)
    op.setTooltip('\n'.join(' '.join(['<b>{}</b>'.format(n), d]) for n, d in zip(mode_names, mode_desc)))
    op.setValue('plus')
    node.addKnob(op)

    duplicate_script = '''
n = nuke.thisGroup()
locked = n['lock_inputs'].value()
n['lock_inputs'].setValue(0)
new_node = FIX_MultiMixer_alpha.duplicate(n)
new_node['lock_inputs'].setValue(locked)
n['lock_inputs'].setValue(locked)
'''
    dup = nuke.PyScript_Knob('dup', ' duplicate MultiMixer ', duplicate_script)
    dup.setFlag(nuke.STARTLINE)
    node.addKnob(dup)

    copy_script = '''
n = nuke.thisGroup()
reload(FIX_MultiMixer_alpha)
FIX_MultiMixer_alpha.copy_values(n)
'''
    cop = nuke.PyScript_Knob('cop', ' Copy values ', copy_script)
    cop.setFlag(nuke.STARTLINE)
    node.addKnob(cop)

    paste_script = '''
n = nuke.thisGroup()
reload(FIX_MultiMixer_alpha)
FIX_MultiMixer_alpha.paste_values(n)
'''
    pas = nuke.PyScript_Knob('pas', ' Paste values ', paste_script)
    pas.clearFlag(nuke.STARTLINE)
    node.addKnob(pas)

    alpha = nuke.Boolean_Knob("alpha", " enable alpha", True)
    alpha.setFlag(nuke.STARTLINE)
    node.addKnob(alpha)

    node.addKnob(nuke.Text_Knob('div2', ''))

    solo_script = '''
node = nuke.thisGroup()
knobs = [k for k in node.knobs() if 'solo_' in k]
new_value = sum(node[k].value() for k in knobs) < len(knobs)
[node[k].setValue(new_value) for k in knobs]
'''
    solosolo = nuke.PyScript_Knob('solosolo', ' solo all ', solo_script)
    solosolo.setFlag(nuke.STARTLINE)
    node.addKnob(solosolo)



    mute_script = '''
node = nuke.thisGroup()
knobs = [k for k in node.knobs() if 'mute_' in k]
new_value = sum(node[k].value() for k in knobs) < len(knobs)
need_change = [k for k in knobs if node[k].value() != new_value]
[node[k].setValue(new_value) for k in knobs]
'''
    mutemute = nuke.PyScript_Knob('mutemute', ' mute all ', mute_script)
    mutemute.clearFlag(nuke.STARTLINE)
    node.addKnob(mutemute)



    for p in passes:
        mult = nuke.Double_Knob('mult_{}'.format(p), p)
        mult.setRange(0, 5)
        mult.setValue(1)
        node.addKnob(mult)
        solo = nuke.Boolean_Knob('solo_{}'.format(p), 'solo')
        node.addKnob(solo)
        mute = nuke.Boolean_Knob('mute_{}'.format(p), 'mute')
        mute.clearFlag(nuke.STARTLINE)
        node.addKnob(mute)



    knob_change = '''
node = nuke.thisNode()
knob = nuke.thisKnob()
k_name = knob.name()
render_pass = '_'.join(k_name.split('_')[1:])
k_value = knob.value()


if k_name.startswith('mute_'):
    node['mult_'+render_pass].setEnabled(not(k_value))

elif k_name.startswith('solo_'):
    node['mult_'+render_pass].setEnabled(k_value or not(node['mute_'+render_pass].value()))
    node['mute_'+render_pass].setEnabled(not(k_value))

elif k_name == 'operation':
    for n in node.nodes():
        if n.Class() == 'Merge2':
            n['operation'].setValue(k_value)

elif k_name == 'inputChange' and node['lock_inputs'].value() and node['selected'].value():
    nuke.Undo().undo()

elif k_name == 'alpha':
    node_shuffle = nuke.toNode("Alpha_ShuffleCopy")
    if knob.getValue():
        node_shuffle.knob("alpha").setValue("alpha")
    else:
        node_shuffle.knob("alpha").setValue(0)

'''


    node['knobChanged'].setValue(knob_change)

    return node
