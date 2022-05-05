# -*- coding: utf-8 -*-
"""
Python script to create a quicktime movie from nuke
"""

import nuke
from ppUtils import ppTimecodeConverter
from ppnk.utils import ppNukeUtils
import ppSgtkLibs.ppSgtkCmds as ppSgtkCmds
import logging

# loggger
# =======================================================================
LOG_FORMAT = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger('pp_create_quicktime_movie')
logger.setLevel(logging.DEBUG)


def create_movie_from_template(template_path, slate_path, frames_path, first_frame, cut_frame, frame_rate, width, height, qt_type, dest_path, published_file_id=None):
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
    :param width: the width of the frame to compute
    :type width: int
    :param height: the height of the frame to compute
    :type height: int
    :param qt_type: the type of qt wanted
    :type qt_type: str
    :param dest_path: the path where to save the movie
    :type dest_path: str
    """
    settings_node_name = 'Settings'
    slate_reader_node_name = 'SLATE_READER'
    frame_reader_node_name = 'FRAME_READER'
    published_file_node_name = 'PUBLISHEDFILE_READER'
    time_code_node_name = 'AddTimeCode1'

    nuke.scriptClear()
    nuke.load(template_path)

    ppNukeUtils.deselectAllNodes()

    settings_node = nuke.toNode(settings_node_name)

    # 1. set comp format
    comp_format_name = 'movie_format'
    nuke.addFormat("{0} {1} 1.0 {2}".format(width, height, comp_format_name))
    nuke.root().knob('format').setValue(comp_format_name)
    nuke.root().knob('fps').setValue(frame_rate)

    # 2. set readers
    # 2.a slate reader
    slate_frame_number = -1
    if slate_path:
        slate_frame_number = first_frame - 1
        slate_reader_node = nuke.toNode(slate_reader_node_name)
        slate_reader_node.knob('file').setValue(slate_path)
        slate_reader_node.knob('first').setValue(slate_frame_number)
        slate_reader_node.knob('last').setValue(slate_frame_number)
        slate_reader_node.knob('before').setValue('black')
        slate_reader_node.knob('after').setValue('black')
        settings_node.knob('slate_frame_at').setValue(slate_frame_number)

    # 2.b frames reader
    frames_reader_node = nuke.toNode(frame_reader_node_name)
    frames_reader_node.knob('file').setValue(frames_path)
    frames_reader_node.knob('first').setValue(first_frame)
    frames_reader_node.knob('last').setValue(cut_frame)

    if published_file_id:
        logger.debug("--- published_file id: %s" % published_file_id)
        sgCmds = ppSgtkCmds.Cmds(int(published_file_id))
        sg_published_file = sgCmds.get_one_published_file(int(published_file_id))
        logger.debug("--- published_file data:\n %s" % sg_published_file)
        published_file_path = sg_published_file.get('path').get('local_path')

        if published_file_path:
            try:
                published_file_node = nuke.toNode(published_file_node_name)
                published_file_node.knob('file').setValue(published_file_path)
                published_file_node.knob('first').setValue(first_frame)
                published_file_node.knob('last').setValue(cut_frame)

                time_code_node = nuke.toNode(time_code_node_name)
                tc = nuke.toNode('PUBLISHEDFILE_READER').metadata()['input/timecode']
                logger.debug("--- TC: %s" % tc)
                frames = ppTimecodeConverter.timecode_to_frame(tc, 24)
                new_tc = ppTimecodeConverter.frame_to_timecode(frames - 1, 24)
                time_code_node.knob('startcode').setValue(new_tc)
                logger.debug("--- TC: %s" % new_tc)
            except Exception:
                logger.info("Failed to add tc...")

    # 3. set the time code node
    else:
        time_code_node = nuke.toNode(time_code_node_name)
        movie_first_frame = slate_frame_number if slate_frame_number != -1 else first_frame
        time_code = ppTimecodeConverter.frame_to_timecode(
            movie_first_frame,
            frame_rate)
        time_code_node.knob('startcode').setValue(time_code)

    # 4. render
    write_node_name = '{0}_WRITER'.format(qt_type.upper())
    write_node = nuke.toNode(write_node_name)
    write_node.knob('file').setValue(dest_path)
    write_node.knob('mov64_fps').setValue(frame_rate)
    if slate_path:
        nuke.render(write_node, slate_frame_number, cut_frame)
    else:
        nuke.render(write_node, first_frame, cut_frame)
