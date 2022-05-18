# -*- coding: utf-8 -*-

"""
common classes and functions about node
"""

import maya.cmds as cmds
import sys
import shotgun_api3 as shotgunApi
import logging
import ppUtils.ppSettings as ppSettings

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppma.action.ppLibrary')
logger.setLevel(logging.INFO)


class Library(object):
	"""docstring for Turntable"""
	def __init__(self):
		super(Library, self).__init__()
		pass

	def retrieve_published_file(self, code, publish_name, status=None):
		"""
		"""
		sg = shotgunApi.Shotgun(ppSettings.SHOTGUN["serverPath"], ppSettings.SHOTGUN["scriptName"], ppSettings.SHOTGUN["scriptKey"])

		published_file_type = "maya_scene"
		sgRequestFields = {
			"PublishedFile": ["id", "code", "sg_status_list", "description", "name", "task", "created_by", "sg_pp_meta_data", "path", "published_file_type", "published_file_type.PublishedFileType.short_name", "tag_list", "project"],
			}

		# get latest published file
		sgFilter = [['published_file_type.PublishedFileType.short_name', 'is', published_file_type], ['project.Project.name', 'is', 'LIBRARY_14_081']]
		sgFilter.extend([["entity.Asset.code", "is", code], ['name', 'is', publish_name]])
		if status:
			sgFilter.append(["sg_status_list", "is", status])

		sgFields = sgRequestFields["PublishedFile"]
		sgOrder = [{'field_name': 'id', 'direction': 'desc'}]

		published_file = sg.find_one("PublishedFile", sgFilter, sgFields, sgOrder)

		# get path from previous published file
		path = published_file['path']['local_path_windows']
		if sys.platform == "darwin":
			path = published_file['path']['local_path_mac']
		if sys.platform == "linux2":
			path = published_file['path']['local_path_linux']

		return path

	def get_camera_turntable(self):
		"""
		"""
		code = "turntable"
		publish_name = "basic"
		namespace = "{code}001".format(code=code)
		path = self.retrieve_published_file(code, publish_name)
		
		#  create reference
		filename = cmds.file(path, namespace=namespace, reference=True)

		return filename

	def get_camera(self):
		"""
		"""
		code = "cam"
		publish_name = "basic"
		status = "apr"
		namespace = "{code}001".format(code=code)
		path = self.retrieve_published_file(code, publish_name, status="apr")
		
		#  create reference
		filename = cmds.file(path, namespace=namespace, reference=True)

		return filename

	def get_light(self, step="previz"):
		"""
		"""
		code = "lightRigPreviz"
		publish_name = "basic"
		status = "apr"

		if step == "previz":
			code = "lightRigPreviz"
			publish_name = "basic"
			status = "apr"

		namespace = "{code}001".format(code=code)
		path = self.retrieve_published_file(code, publish_name, status=status)
		
		#  create reference
		filename = cmds.file(path, namespace=namespace, reference=True)

		return filename

	def get_cyclo(self):
		"""
		"""
		code = "cyclo"
		publish_name = "basic"
		namespace = "{code}001".format(code=code)
		path = self.retrieve_published_file(code, publish_name)
		
		#  create reference
		filename = cmds.file(path, namespace=namespace, reference=True)

		return filename


def get_turntable_camera():
	"""
	"""
	t = Library()
	t.get_camera_turntable()


def get_camera():
	"""
	"""
	t = Library()
	t.get_camera()

def get_light(step="previz"):
	"""
	"""
	t = Library()
	t.get_light(step="previz")

def get_cyclo():
	"""
	"""
	t = Library()
	t.get_cyclo()
