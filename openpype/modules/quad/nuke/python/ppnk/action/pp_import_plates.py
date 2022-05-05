import nuke
import logging
from tank_vendor import yaml
from ppnk.utils import ppNukeUtils
from ppnk.core import ppActions
from ppUtils import ppPath


# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('pp_import_plates')
logger.setLevel(logging.INFO)


class PlatesImporter(object):

	# BACKDROP SETTINGS
	NOTE_FONT_SIZE = 42.0
	PLATES_BACKDROP_NAME = 'bd_plates'
	PLATES_BACKDROP_LABEL = 'PLATES'
	BACKDROP_DEFAULT_SIZE = (260, 180)  # minimum size to place 1 reader
	# PLATE READERS SETTINGS
	PLATE_READERS_MARGIN_LEFT = 50
	PLATE_READERS_MARGIN_BOT = 100

	def __init__(self, sg):
		"""Loads plates in read nodes
		"""
		super(PlatesImporter, self).__init__()
		self.sg = sg

	def import_plates(self, plate_ids):
		"""Creates the backdrop node and read nodes for the plates
		:param plate_ids: the id of the plates to read
		:plate_ids: list
		"""
		if len(plate_ids) > 0:
			plates_nodes_list = self._create_plates_nodes(plate_ids)
			# create a backdrop with all those nodes using autoBackdrop
			ppNukeUtils.deselectAllNodes()
			for node in plates_nodes_list:
				node.knob('selected').setValue(True)
			bd_plates = ppNukeUtils.terminal_autoBackdrop()
		else:
			# create an empty backdrop
			bd_plates = nuke.createNode('BackdropNode')
			most_left_node = sorted(nuke.allNodes(), key=lambda node: node.knob('xpos').value())[0]
			most_top_node = sorted(nuke.allNodes(), key=lambda node: node.knob('ypos').value())[0]
			xpos = most_left_node.knob('xpos').value() - ppNukeUtils.DEFAULT_TILE_SIZE[0]
			ypos = most_top_node.knob('ypos').value() - ppNukeUtils.DEFAULT_TILE_SIZE[1] - 50
			bd_plates.knob('xpos').setValue(xpos)
			bd_plates.knob('ypos').setValue(ypos)
		# set backdrop
		bd_plates.knob('name').setValue(PlatesImporter.PLATES_BACKDROP_NAME)
		bd_plates.knob('label').setValue(PlatesImporter.PLATES_BACKDROP_LABEL)
		bd_plates.knob('note_font_size').setValue(PlatesImporter.NOTE_FONT_SIZE)
		if bd_plates.knob('bdwidth').value() < PlatesImporter.BACKDROP_DEFAULT_SIZE[0]:
			bd_plates.knob('bdwidth').setValue(PlatesImporter.BACKDROP_DEFAULT_SIZE[0])
		if bd_plates.knob('bdheight').value() < PlatesImporter.BACKDROP_DEFAULT_SIZE[1]:
			bd_plates.knob('bdheight').setValue(PlatesImporter.BACKDROP_DEFAULT_SIZE[1])

	def _create_plates_nodes(self, plate_ids):
		"""Creates a read node for each plate
		:param plate_ids: the id of the plates to read
		:plate_ids: list
		:return: the backdrop node
		:rtype: dict
		"""
		plate_nodes = list()
		most_left_node = sorted(nuke.allNodes(), key=lambda node: node.knob('xpos').value())[0]
		most_top_node = sorted(nuke.allNodes(), key=lambda node: node.knob('ypos').value())[0]
		xpos = most_left_node.knob('xpos').value() - len(plate_ids) * ppNukeUtils.DEFAULT_TILE_SIZE[0]
		ypos = most_top_node.knob('ypos').value() - ppNukeUtils.DEFAULT_TILE_SIZE[1] - PlatesImporter.PLATE_READERS_MARGIN_BOT
		action = ppActions.Action()
		for plate_id in plate_ids:
			published_file_data = self.sg.find_one(
				'PublishedFile',
				[['id', 'is', plate_id]],
				['path', 'sg_pp_meta_data'])
			path = ppPath.get_sg_path_from_current_platform(published_file_data['path'])
			metadata = yaml.load(published_file_data['sg_pp_meta_data'])
			params = {
				"name": "plate_reader_"
			}
			n = action._create_read_img(path, params, published_file_data)
			n.knob('xpos').setValue(xpos)
			n.knob('ypos').setValue(ypos)
			n.knob('selected').setValue(True)
			n.knob('name').setValue(n.knob('name').value() + str(plate_id))
			n.knob('first').setValue(metadata['start'])
			n.knob('last').setValue(metadata['end'])
			#
			plate_nodes.append(n)
			# increments
			xpos += ppNukeUtils.DEFAULT_READ_NODE_SIZE[0] + PlatesImporter.PLATE_READERS_MARGIN_LEFT
		return plate_nodes
