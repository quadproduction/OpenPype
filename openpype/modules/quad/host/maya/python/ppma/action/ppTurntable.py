# -*- coding: utf-8 -*-

"""
common classes and functions about node
"""

import maya.cmds as cmds
import maya.mel as mel
import sys
import shotgun_api3 as shotgunApi
import logging
import ppUtils.ppSettings as ppSettings

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppma.action.ppInitScene')
logger.setLevel(logging.INFO)


class Turntable(object):
	"""docstring for Turntable"""
	def __init__(self):
		super(Turntable, self).__init__()

	def get_camera_turntable(self):
		"""
		"""
		sg = shotgunApi.Shotgun(ppSettings.SHOTGUN["serverPath"], ppSettings.SHOTGUN["scriptName"], ppSettings.SHOTGUN["scriptKey"])

		publishedFileType = "maya_scene"
		sgRequestFields = {
			"PublishedFile": ["id", "code", "sg_status_list", "description", "name", "task", "created_by", "sg_pp_meta_data", "path", "published_file_type", "published_file_type.PublishedFileType.short_name", "tag_list", "project"],
			}

		# get latest published file
		sgFilter = [['published_file_type.PublishedFileType.short_name', 'is', publishedFileType]]
		sgFilter.extend([["entity.Asset.code", "is", "turntable"], ['name', 'is', 'basic']])
		sgFields = sgRequestFields["PublishedFile"]
		sgOrder = [{'field_name': 'id', 'direction': 'desc'}]

		publishedFile = sg.find_one("PublishedFile", sgFilter, sgFields, sgOrder)

		# get path from previous published file
		path = publishedFile['path']['local_path_windows']
		if sys.platform == "darwin":
			path = publishedFile['path']['local_path_mac']
		if sys.platform == "linux2":
			path = publishedFile['path']['local_path_linux']

		#  create reference
		filename = cmds.file(path, namespace="turntable", reference=True)

		return filename


def get_turntable_camera():
	"""
	"""

	t = Turntable()
	t.get_camera_turntable()
