import nuke
import logging
import os
from ppnk.utils import ppNukeUtils
from ppnk.core import ppActions
from ppUtils import ppPath


# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('pp_import_cameras')
logger.setLevel(logging.INFO)


class CamerasImporter(object):

	# BACKDROP SETTINGS
	NOTE_FONT_SIZE = 42.0
	CAMERAS_BACKDROP_NAME = 'bd_cameras'
	CAMERAS_BACKDROP_LABEL = 'CAMERAS'
	BACKDROP_DEFAULT_SIZE = (260, 180)  # minimum size to place 1 reader
	# CAMERA READERS SETTINGS
	CAMERA_READERS_MARGIN_LEFT = 50
	CAMERA_READERS_MARGIN_BOT = 100

	def __init__(self, sg):
		"""Loads cameras in camera nodes
		"""
		super(CamerasImporter, self).__init__()
		self.sg = sg

	def import_cameras(self, cameras_ids):
		"""Creates the backdrop node and read nodes for the cameras
		:param cameras_ids: the id of the cameras published file to read
		:cameras_ids: list
		"""
		if len(cameras_ids) > 0:
			cameras_nodes_list = self._create_cameras_nodes(cameras_ids)
			# create a backdrop with all those nodes using autoBackdrop
			ppNukeUtils.deselectAllNodes()
			for node in cameras_nodes_list:
				node.knob('selected').setValue(True)
			bd_cameras = ppNukeUtils.terminal_autoBackdrop()
		else:
			# create an empty backdrop
			bd_cameras = nuke.createNode('BackdropNode')
			most_left_node = sorted(nuke.allNodes(), key=lambda node: node.knob('xpos').value())[0]
			most_top_node = sorted(nuke.allNodes(), key=lambda node: node.knob('ypos').value())[0]
			xpos = most_left_node.knob('xpos').value() - ppNukeUtils.DEFAULT_TILE_SIZE[0]
			ypos = most_top_node.knob('ypos').value() - ppNukeUtils.DEFAULT_TILE_SIZE[1] - 50
			bd_cameras.knob('xpos').setValue(xpos)
			bd_cameras.knob('ypos').setValue(ypos)
		# set backdrop
		bd_cameras.knob('name').setValue(CamerasImporter.CAMERAS_BACKDROP_NAME)
		bd_cameras.knob('label').setValue(CamerasImporter.CAMERAS_BACKDROP_LABEL)
		bd_cameras.knob('note_font_size').setValue(CamerasImporter.NOTE_FONT_SIZE)
		if bd_cameras.knob('bdwidth').value() < CamerasImporter.BACKDROP_DEFAULT_SIZE[0]:
			bd_cameras.knob('bdwidth').setValue(CamerasImporter.BACKDROP_DEFAULT_SIZE[0])
		if bd_cameras.knob('bdheight').value() < CamerasImporter.BACKDROP_DEFAULT_SIZE[1]:
			bd_cameras.knob('bdheight').setValue(CamerasImporter.BACKDROP_DEFAULT_SIZE[1])

	def _create_cameras_nodes(self, cameras_ids):
		"""Creates a read node for each camera
		:param cameras_ids: the id of the cameras published file to read
		:cameras_ids: list
		:return: the backdrop node
		:rtype: dict
		"""
		cameras_nodes = list()
		most_left_node = sorted(nuke.allNodes(), key=lambda node: node.knob('xpos').value())[0]
		most_top_node = sorted(nuke.allNodes(), key=lambda node: node.knob('ypos').value())[0]
		xpos = most_left_node.knob('xpos').value() - len(cameras_ids) * ppNukeUtils.DEFAULT_TILE_SIZE[0]
		ypos = most_top_node.knob('ypos').value() - ppNukeUtils.DEFAULT_TILE_SIZE[1] - CamerasImporter.CAMERA_READERS_MARGIN_BOT
		action = ppActions.Action()
		for camera_id in cameras_ids:
			published_file_data = self.sg.find_one(
				'PublishedFile',
				[['id', 'is', camera_id]],
				['path', 'code'])
			path = ppPath.get_sg_path_from_current_platform(published_file_data['path'])
			n = action._create_camera_reader(path)
			n.knob('xpos').setValue(xpos)
			n.knob('ypos').setValue(ypos)
			n.knob('name').setValue(os.path.splitext(published_file_data['code'])[0])
			#
			cameras_nodes.append(n)
			# increments
			xpos += ppNukeUtils.DEFAULT_READ_NODE_SIZE[0] + CamerasImporter.CAMERA_READERS_MARGIN_LEFT
		return cameras_nodes
