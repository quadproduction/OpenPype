# -*- coding: utf-8 -*-
"""
Python script to create a slate frame from nuke
"""

import os
import nuke
import re
import pyseq
from ppnk.utils import ppNukeUtils


def create_text_nodes(text_bd_name, slate_args_values):
    """Creates the text nodes in the context of a slate creation"""
    ppNukeUtils.deselectAllNodes()
    text_bd = nuke.toNode(text_bd_name)
    # first remove existing nodes if there are any
    text_nodes = ppNukeUtils.terminal_get_nodes_in_backdrop(text_bd)
    for node in text_nodes:
        nuke.delete(node)
    xpos = text_bd.knob('xpos').value() + 100
    ypos = text_bd.knob('ypos').value() + 150
    x_margin = 120
    y_margin = 50
    slate_value_node = None
    for (slate_name, slate_desc) in slate_args_values.iteritems():
        slate_label_node = nuke.createNode('Text2', inpanel=False)
        slate_label_node_name = '{0}_Label'.format(slate_name)
        slate_label_node.knob('name').setValue(slate_label_node_name)
        slate_label_node.knob('message').setValue(slate_name + ' : ')
        slate_label_node.knob('xpos').setValue(xpos)
        slate_label_node.knob('ypos').setValue(ypos)
        slate_label_node.knob('xjustify').setValue('right')
        slate_label_node.knob('yjustify').setExpression('Settings.enum_justify_vertical')
        label_bbox_x_expression = 'Settings.enum_left_margin *  [python nuke.root().knob(\'format\').value().width()] / 100'
        label_bbox_y_expression = '[python nuke.root().knob(\'format\').value().height()] - (Settings.title_top_margin + Settings.title_bot_margin + (Settings.enum_top_margin + Settings.enum_left_block_size.1 + Settings.enum_top_margin) * {0}) * [python nuke.root().knob(\'format\').value().height()] / 100'.format(slate_desc['order'] -1)
        label_bbox_r_expression = '(Settings.enum_left_margin + Settings.enum_left_block_size.0) * [python nuke.root().knob(\'format\').value().width()] / 100'
        label_bbox_t_expression = '{0}.box.1 - (Settings.enum_left_block_size.1) * [python nuke.root().knob(\'format\').value().height()] / 100'.format(slate_label_node_name)
        slate_label_node.knob('box').setExpression(label_bbox_x_expression, 0)
        slate_label_node.knob('box').setExpression(label_bbox_y_expression, 1)
        slate_label_node.knob('box').setExpression(label_bbox_r_expression, 2)
        slate_label_node.knob('box').setExpression(label_bbox_t_expression, 3)
        slate_label_node.knob('font').setValue("Liberation Sans", "Regular")
        slate_label_node.knob('global_font_scale').setExpression('Settings.enum_font_size')
        slate_value_node = nuke.createNode('Text2', inpanel=False)
        slate_value_node_name = '{0}_Value'.format(slate_name)
        slate_value_node.knob('name').setValue(slate_value_node_name)
        if slate_desc['computed_value'].encode('utf-8') != str(None):
            slate_value_node.knob('message').setValue(slate_desc['computed_value'].encode('utf-8'))
        slate_value_node.knob('xpos').setValue(xpos + x_margin)
        slate_value_node.knob('ypos').setValue(ypos)
        slate_value_node.knob('xjustify').setValue('left')
        slate_value_node.knob('yjustify').setExpression('Settings.enum_justify_vertical')
        value_bbox_x_expression = '({0}.box.2 + Settings.enum_gap_size) * [python nuke.root().knob(\'format\').value().width()] / 100'.format(slate_value_node_name)
        value_bbox_y_expression = label_bbox_y_expression
        value_bbox_r_expression = '{0}.box.0 + Settings.enum_gap_size + Settings.enum_right_block_size.0 * [python nuke.root().knob(\'format\').value().width()] / 100'.format(slate_value_node_name)
        value_bbox_t_expression = '{0}.box.1 - Settings.enum_right_block_size.1 * [python nuke.root().knob(\'format\').value().height()] / 100'.format(slate_value_node_name)
        slate_value_node.knob('box').setExpression(value_bbox_x_expression, 0)
        slate_value_node.knob('box').setExpression(value_bbox_y_expression, 1)
        slate_value_node.knob('box').setExpression(value_bbox_r_expression, 2)
        slate_value_node.knob('box').setExpression(value_bbox_t_expression, 3)
        slate_value_node.knob('global_font_scale').setExpression('Settings.enum_font_size')
        slate_value_node.knob('font').setValue("Liberation Sans", "Regular")
        ypos += y_margin
    return slate_value_node


def create_slate_frame_from_template(template_path, title_values, slate_args_values, frames_path, slate_path, final_width, final_height, frame_rate=None):
    """Creates a slate frame using a template composition and the project
    slate settings
    :param template_path: the path to the template composition
    :type template_path: str
    :param title_values: dict with slate options project settings key and
    computed value as key and value
    :type title_values: dict
    :param slate_args_values: dict with slate arguments project settings key
    and computed value as key and value
    :type slate_args_values: dict
    :param frames_path: the path to the frames to slate
    :type frames_path:str
    :param slate_path: the path where to save the slate frame
    :type slate_path: str
    :param final_width: the width of the frame to compute
    :type final_width: int
    :param final_height: the height of the frame to compute
    :type final_height: int
    :param frame_rate: the comp frame rate, used also to write metadatas
    :type frame_rate: float
    """
    title_node_name = 'Title_Value'
    thumbnail_read_node_name = 'Reader_Thumbnail'
    thumbnail_reformat_node_name = 'Reformat_Thumbnail'
    thumbnail_transform_node_name = 'Transform_Thumbnail'
    logo_reformat_node_name = 'Reformat_Logo_Studio'
    colorChartBars_read_node_name = 'ColorBars'
    colorChartGradient_read_node_name = 'Gradient_Constant'
    text_bd_name = 'Text_BD'
    first_merge_name = 'Merge_Text_and_Thumbnail'
    write_node_name = 'Write_slate'
    nuke.scriptClear()
    nuke.load(template_path)
    ppNukeUtils.deselectAllNodes()
    # 1. set comp format
    comp_format_name = 'slate_format'
    nuke.addFormat("{0} {1} 1.0 {2}".format(final_width, final_height, comp_format_name))
    nuke.root().knob('format').setValue(comp_format_name)
    nuke.root().knob('fps').setValue(frame_rate)
    # 2. set title node
    title_node = nuke.toNode(title_node_name)
    title_node.knob('message').setValue(title_values['title']['computed_value'])
    title_node.knob('yjustify').setValue('center')
    title_node.knob('font').setValue("Liberation Sans", "Regular")
    # 3. create thumbnail node
    file_seqs = pyseq.get_sequences(os.path.dirname(frames_path))
    for seq in file_seqs:
        if seq.format("%h%p%t") == os.path.basename(frames_path):
            thumbnail_frame_number = seq.end()
            digits_part = re.search('%\d*d', frames_path).group(0)
            thumbnail_path = frames_path.replace(digits_part, digits_part % thumbnail_frame_number)
            break
    thumbnail_read_node = nuke.toNode(thumbnail_read_node_name)
    thumbnail_reformat_node = nuke.toNode(thumbnail_reformat_node_name)
    thumbnail_transform_node = nuke.toNode(thumbnail_transform_node_name)
    thumbnail_read_node.knob('file').setValue(thumbnail_path)
    thumbnail_reformat_node.knob('format').setExpression('[python nuke.root().knob(\'format\').value()')
    thumbnail_transform_node.knob('scale').setExpression('Settings.thumbnail_scale')
    thumbnail_transform_node.knob('translate').setExpression('[python nuke.root().knob(\'format\').value().width()] * (1 - Settings.thumbnail_scale) - Settings.thumbnail_right_margin * [python nuke.root().knob(\'format\').value().width()] /100', 0)
    thumbnail_transform_node.knob('translate').setExpression('[python nuke.root().knob(\'format\').value().height()] * (1 - Settings.thumbnail_scale) - Settings.thumbnail_top_margin * [python nuke.root().knob(\'format\').value().height()] /100', 1)
    # 4. create and set text nodes
    ppNukeUtils.deselectAllNodes()
    last_slate_value_node = create_text_nodes(text_bd_name, slate_args_values)
    # merge
    if last_slate_value_node:
        first_merge = nuke.toNode(first_merge_name)
        first_merge.setInput(0, last_slate_value_node)
    # 5. logo
    nuke.toNode(logo_reformat_node_name).knob('format').setExpression('[python nuke.root().knob(\'format\').value()')
    # 6. color chart
    nuke.toNode(colorChartBars_read_node_name).knob('format').setExpression('[python nuke.root().knob(\'format\').value()')
    nuke.toNode(colorChartGradient_read_node_name).knob('format').setExpression('[python nuke.root().knob(\'format\').value()')
    # 7. render
    write_node = nuke.toNode(write_node_name)
    file_ext = os.path.splitext(str(frames_path))[1][1:]
    write_node.knob('file').setValue(slate_path)
    write_node.knob('file_type').setValue(file_ext)
    nuke.render(write_node, thumbnail_frame_number, thumbnail_frame_number)
