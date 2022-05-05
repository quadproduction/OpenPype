# -*- coding: utf-8 -*-
"""
Python script to create a io frames from nuke
"""

import nuke
from ppnk.utils import ppNukeUtils
from ppnk.core import ppTools
import logging

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('pp_create_io_frames')
logger.setLevel(logging.INFO)


def create_io_qt_frames_from_template(template_path, frames_path, first_frame, cut_frame, frame_rate, final_width, final_height, output_type, destination_path, lut_path=None, cdl_path=None):
    """Creates the io frames using a template composition
    :param template_path: the path to the template composition
    :type template_path: str
    :param frames_path: path to the frames to compute
    :type frames_path: str
    :param first_frame: the comp's plates first visible frame
    :type first_frame: int
    :param cut_frame: the comp's plates last visible frame
    :type cut_frame: int
    :param frame_rate: the comp frame rate
    :type frame_rate: float
    :param final_width: the width of the frame to compute
    :type final_width: int
    :param final_height: the height of the frame to compute
    :type final_height: int
    :param output_type: the type of output wanted
    :type output_type: str
    :param destination_path: the path where to save the io frames
    :type destination_path: str
    :param lut_path: path to the OCIO lut
    :type lut_path: str
    :param cdl_path: path to the OCIO cdl
    :type cdl_path: str

    . set lut and cdl
    . set comp format and fps
    . set reader
    . render
    """
    nuke.scriptClear()
    logger.info("Load template file : {0}".format(template_path))
    # nuke.load(template_path)
    nuke.scriptOpen(template_path)
    ppNukeUtils.deselectAllNodes()
    # 1. set lut and cdl
    params_node_name = 'PARAMS'
    params_node = nuke.toNode(params_node_name)
    if lut_path:
        params_node.knob('lut').setValue(lut_path)
        params_node.knob('cdl_inactive').setValue(False)
    else:
        params_node.knob('lut_inactive').setValue(True)
    if cdl_path:
        params_node.knob('cdl').setValue(cdl_path)
        params_node.knob('cdl_inactive').setValue(False)
    else:
        params_node.knob('cdl_inactive').setValue(True)
    # 1.1 set ocio context based on nuke current sgtk context
    ppTools.auto_set_context_ocio_node()
    # 2. set comp format and fps
    comp_format_name = 'io_format'
    nuke.addFormat("{0} {1} 1.0 {2}".format(final_width, final_height, comp_format_name))
    nuke.root().knob('format').setValue(comp_format_name)
    nuke.root().knob('fps').setValue(frame_rate)
    # 3. set reader
    reader_node_name = '{0}_READER'.format(output_type.upper())
    reader_node = nuke.toNode(reader_node_name)
    reader_node.knob('file').setValue(frames_path)
    reader_node.knob('first').setValue(first_frame)
    reader_node.knob('last').setValue(cut_frame)
    # 4. render
    write_node_name = '{0}_WRITER'.format(output_type.upper())
    write_node = nuke.toNode(write_node_name)
    write_node.knob('file').setValue(destination_path)
    nuke.render(write_node, first_frame, cut_frame)
