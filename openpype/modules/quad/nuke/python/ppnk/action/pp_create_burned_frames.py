# -*- coding: utf-8 -*-
"""
Python script to be executed by Nuke to create a comp creating burned frames
"""

import os
import nuke
from ppnk.utils import ppNukeUtils


def create_burned_frames_from_template(template_path, burn_args_values, final_width, final_height, first_frame, cut_frame, frame_rate, frames_to_burn_path, destination_folder):
    """Creates a burned frames using a template composition and the project
    burn settings
    :param template_path: the path to the template composition
    :type template_path: str
    :param burn_args_values: dict with burn args project settings key and
    computed value as key and value
    :type burn_args_values: dict
    :param final_width: the width of the frame to compute
    :type final_width: int
    :param final_height: the height of the frame to compute
    :type final_height: int
    :param first_frame: the comp's plates first visible frame
    :type first_frame: int
    :param cut_frame: the comp's plates last visible frame
    :type cut_frame: int
    :param frame_rate: the comp frame rate
    :type frame_rate: float
    :param frames_to_burn: path to the frames to burn
    :type frames_to_burn_path: str
    :param destination_folder: destination path folder
    :type destination_folder: str
    """
    read_node_name = 'FRAMEBURN_READER'
    write_node_name = 'FRAMEBURN_WRITER'
    # 0. set root
    nuke.load(template_path)
    ppNukeUtils.deselectAllNodes()
    nuke.root().knob('first_frame').setValue(first_frame)  # slate
    nuke.root().knob('last_frame').setValue(cut_frame)
    comp_format_name = 'burn_format'
    nuke.addFormat("{0} {1} 1.0 {2}".format(final_width, final_height, comp_format_name))
    nuke.root().knob('format').setValue(comp_format_name)
    nuke.root().knob('fps').setValue(frame_rate)
    # 1. import the slap comp render result
    frames_reader = nuke.toNode(read_node_name)
    frames_reader.knob('file').setValue(frames_to_burn_path)
    frames_reader.knob('first').setValue(first_frame)
    frames_reader.knob('last').setValue(cut_frame)
    # 2. fill the burn nodes
    for (burn_arg_name, burn_arg_desc) in burn_args_values:
        if burn_arg_name != 'image_reference':
            burn_arg_node = nuke.toNode(burn_arg_name)
            burn_arg_node.knob('name').setValue(burn_arg_name)
            burn_arg_node.knob('message').setValue(burn_arg_desc)
    # 3. create write node
    write_node = nuke.toNode(write_node_name)
    file_ext = os.path.splitext(frames_to_burn_path)[1][1:]
    destination_path = os.path.join(
        destination_folder,
        os.path.basename(frames_to_burn_path))
    write_node.knob('file').setValue(destination_path)
    write_node.knob('file_type').setValue(file_ext)
    nuke.render(write_node, first_frame, cut_frame)
