# -*- coding: utf-8 -*-
import os
import nuke


def run(root_path=None, dest_root=None):
    all_images = os.listdir(root_path)
    read_nodes = []
    to_delete = []
    flag = True

    for img in all_images:
        if os.path.splitext(img)[1] == '.exr':
            read_node = nuke.nodes.Read(file= os.path.join(root_path , img))
            read_nodes.append(read_node)
            if flag:
                file_name = os.path.splitext(img)[0].rsplit('/')[-1]
                file_name = file_name.split('_')
                file_name.pop(-1)
                file_name = '_'.join(file_name)
                flag = False

    to_delete.extend(read_nodes)
    deselect_all()
    select_nodes(read_nodes)

    merge_node = nuke.createNode("Merge2", inpanel=False)
    merge_node.knob('also_merge').setValue('all')

    mrg_ypos = merge_node.ypos() + 500
    mrg_xpos = merge_node.xpos() + 100
    merge_node.setXYpos(mrg_xpos, mrg_ypos)

    write_node = nuke.createNode('Write', inpanel=False)
    write_node.setInput(0, merge_node)
    write_node.knob('channels').setValue('all')
    write_node.knob('file_type').setValue('exr')
    write_node.knob('datatype').setValue('32')
    write_node.knob('compression').setValue('Zip (16 scanline)')
    write_node.knob('metadata').setValue('all metadata')

    dest_file_name = "{}_assemble.exr".format(file_name)
    ensure_dir(dest_root)

    dest_final_path = os.path.join(dest_root, dest_file_name)
    write_node.knob('file').setValue(dest_final_path)

    to_delete.append(merge_node)
    to_delete.append(write_node)
    #execute node
    nuke.execute(write_node, 1, 1, 1)
    deselect_all()

    for node in to_delete:
        nuke.delete(node)

    nuke.clearRAMCache()
    nuke.Undo.undoTruncate(100)

    print("DONE!")


def select_nodes(nodes_list = None):
    for node in nodes_list:
        node.setSelected(True)


def deselect_all():
    """diselect all nodes
    """
    selected_nodes = nuke.selectedNodes()
    if not selected_nodes:
        return
    for node in selected_nodes:
        node.setSelected(False)


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
