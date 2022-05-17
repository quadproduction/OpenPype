# -*- coding: utf-8 -*-

"""
    set_read_expression
        Florentin LUCE
    =================================================

    Change frame expression on all reads to set 
    25 or 50 fps

"""

import nuke


def get_lighting_reads():
    """get read with lighting pass comming from Maya

    Returns:
        list: all reads
    """

    return [r for r in nuke.allNodes("Read") if "lighting" in r["file"].value()]


def set_50fps(reads):
    for read in reads:
        read["frame"].setValue("")
    nuke.Root()["fps"].setValue(50)


def set_25fps(reads, start_frame=0):
    for read in reads:
        read["frame"].setValue("frame*2-%s" % start_frame)
    nuke.Root()["fps"].setValue(25)


def run():
    """Execute script"""

    all_reads = get_lighting_reads()
    fps = nuke.Root()["fps"].value()

    if fps == 25:
        set_50fps(all_reads)
    elif fps == 50:
        start_frame = nuke.Root()["first_frame"].value()
        set_25fps(all_reads, start_frame=start_frame)
