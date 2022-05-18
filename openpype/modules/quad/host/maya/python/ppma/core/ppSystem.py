# -*- coding: utf-8 -*-

"""
this module is dedicated to system manipulation under maya and especially the paths mapping.
"""

import maya.cmds as cmds
import os, logging
import ppUtils.ppPath


def do_pathMapping():
	""" this func retireve a path list from the module ppUtils.ppPath and the mapping with the maya func's dirmap."""

	logging.info('do_pathMapping')

	# get paths list
	paths = ppUtils.ppPath.getMapping()

	# do path mapping
	for path in paths:

		cmds.dirmap(m=(path["from"], path["to"]))

	# set dirmap enable
	cmds.dirmap(en=True)
