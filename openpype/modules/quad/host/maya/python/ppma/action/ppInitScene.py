# -*- coding: utf-8 -*-

"""
import export command
"""

import maya.cmds as cmds
import logging
import ppma.action.ppLibrary as ppLibrary
import ppma.core.ppSceneManagement as ppSceneManagement
import ppma.core.ppActions as ppActions
import ppma.core.ppScene as ppScene
import ppma.core.ppNode as ppNode

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppma.action.ppInitScene')
logger.setLevel(logging.INFO)


class Init_Scene(object):
	"""docstring for InitScene"""
	def __init__(self):

		self.sS = ppSceneManagement.Scene_Structure()
		self.sn = ppScene.Scene()

		# scenario
		self.settings = {

							'default': [
											{'cmd': 'self.init_group_structure', 'kwargs': {'structure_type': None}},
											'self.init_scene_settings',
											'self.get_reference'
										],
							'model_character_human': [
											{'cmd': 'self.init_scene_settings', 'kwargs': {}},
											{'cmd': 'self.init_group_structure', 'kwargs': {'structure_type': 'model'}},
											{'cmd': 'self.get_reference', 'kwargs': {'reference_type': 'character_human'}},
										],
							'model_prop': [
											{'cmd': 'self.init_scene_settings', 'kwargs': {}},
											{'cmd': 'self.init_group_structure', 'kwargs': {'structure_type': 'model'}},
											{'cmd': 'self.get_reference', 'kwargs': {}},
											{'cmd': 'self.init_display_layer', 'kwargs': {'structure_type': 'model'}},
											{'cmd': 'cmds.editDisplayLayerMembers', 'kwargs': {}, 'list': ['model', 'root']}
										],
							'rig_prop': [
											{'cmd': 'self.init_scene_settings', 'kwargs': {}},
											{'cmd': 'self.init_group_structure', 'kwargs': {'structure_type': 'rig'}},
											{'cmd': 'self.init_display_layer', 'kwargs': {'structure_type': 'rig'}},
											{'cmd': 'cmds.editDisplayLayerMembers', 'kwargs': {}, 'list': ['ctrl', 'grp_ctrl']}
										],
							'shading_prop': [
											{'cmd': 'self.init_scene_settings', 'kwargs': {}},
											{'cmd': 'self.init_group_structure', 'kwargs': {'structure_type': 'shading'}}
										],
							'turntable': [
											{'cmd': 'self.init_scene_settings', 'kwargs': {}},
											{'cmd': 'self.init_group_structure', 'kwargs': {'structure_type': 'turntable'}},
											{'cmd': 'ppLibrary.get_turntable_camera', 'kwargs': {}},
											{'cmd': 'cmds.parent', 'kwargs': {}, 'list': ['turntable001:root', 'grp_turntable_camera']},
											{'cmd': 'ppLibrary.get_cyclo', 'kwargs': {}},
											{'cmd': 'cmds.parent', 'kwargs': {}, 'list': ['cyclo001:root', 'grp_cyclo']},
											{'cmd': 'cmds.playbackOptions', 'kwargs': {'animationStartTime': 101, 'animationEndTime': 200, 'minTime': 101, 'maxTime': 200}},
											{'cmd': 'cmds.parentConstraint', 'list': ['turntable001:object_ctrl', 'grp_reference_asset'], 'kwargs': {'maintainOffset': True, 'weight': 1}},
										],
							'previz': [
											{'cmd': 'self.init_scene_settings', 'kwargs': {}},
											{'cmd': 'self.init_group_structure', 'kwargs': {'structure_type': 'previz'}},
											{'cmd': 'ppLibrary.get_camera', 'kwargs': {}},
											{'cmd': 'cmds.parent', 'kwargs': {}, 'list': ['cam001:root', 'grp_cameras']},
											{'cmd': 'ppLibrary.get_light', 'kwargs': {'step': 'previz'}},
											{'cmd': 'cmds.parent', 'kwargs': {}, 'list': ['lightRigPreviz001:root', 'grp_lights']},
											{'cmd': 'cmds.playbackOptions', 'kwargs': {'animationStartTime': 101, 'animationEndTime': 200, 'minTime': 101, 'maxTime': 200}},
											{'cmd': 'ppActions.execute_action', 'kwargs': {'action': 'get_project_render_settings'}},
										],
							'lighting': [
											{'cmd': 'self.init_scene_settings', 'kwargs': {}},
											{'cmd': 'self.init_group_structure', 'kwargs': {'structure_type': 'lighting'}},
											{'cmd': 'self._set_persp_non_renderable', 'kwargs': {}},
											{'cmd': 'cmds.playbackOptions', 'kwargs': {'animationStartTime': 101, 'animationEndTime': 200, 'minTime': 101, 'maxTime': 200}},
											{'cmd': 'ppActions.execute_action', 'kwargs': {'action': 'get_project_render_settings'}},
										],
		}

	def get_settings_available(self):
		"""
		retrieve step available for scene initialisation.
		"""
		return sorted(self.settings.keys())

	def init_scene(self, settings):
		""" """

		if not settings in self.get_settings_available():
			logger.error("Can't find the stettings {s} in available settings list. the available settings are : {sa}".format(s=settings, sa=self.get_settings_available()))

		# get action list
		actions = self.settings[settings]

		for action in actions:

			# build command
			eval_cmd = "{cmd}(".format(cmd=action['cmd'], kwargs=action['kwargs'])

			if 'list' in action.keys():
				if action['list']:
					for i in range(0, len(action['list'])):
						eval_cmd += "'{value}'".format(value=action['list'][i])
						if not i == len(action['list'])-1:
							eval_cmd += ", "

			if 'kwargs' in action.keys():
				if action['kwargs']:
					
					#  add , before adding kwargs
					if 'list' in action.keys():
						if action['list']:
							eval_cmd += ", "

					for i in range(0, len(action['kwargs'].keys())):
						arg = action['kwargs'].keys()[i]
						if type(action['kwargs'][arg]) is str:
							eval_cmd += "{arg}='{value}'".format(arg=arg, value=action['kwargs'][arg])
						else:
							eval_cmd += "{arg}={value}".format(arg=arg, value=action['kwargs'][arg])

						if not i == len(action['kwargs'].keys())-1:
							eval_cmd += ", "

			eval_cmd += ")"
			logger.info("Cmd : '{cmd}'".format(cmd=eval_cmd))
			eval(eval_cmd)

	def init_group_structure(self, structure_type=None):
		""" """

		# create default group
		for grp in self.sS.get_structure(step=structure_type)['group']:

			ppNode.create_group(path=grp)

	def init_display_layer(self, structure_type=None):
		""" """

		# create default group
		if 'layer' in self.sS.get_structure(step=structure_type):
			for layer_attr in self.sS.get_structure(step=structure_type)['layer']:

				l = cmds.createDisplayLayer(name=layer_attr['name'], empty=True)
				if layer_attr['color']:
					cmds.setAttr('{n}.color'.format(n=l), layer_attr['color'])

	def init_scene_settings(self):
		"""
		retrieve scene from shotgun project
		"""
		self.sn.set_project_settings_to_maya()

	def _set_persp_non_renderable(self):
		"""
		"""
		objList = ["perspShape"]
		
		# if persp exist
		for obj in objList:
			if cmds.objExists("{n}.renderable"):
				logger.info("Set {n} non renderable".format(n=obj))
				cmds.setAttr("{n}.renderable".format(n=obj), 0)

	def get_reference(self, reference_type=None):
		"""
		"""
		self.create_bbox_reference_size()

	def create_bbox_reference_size(self):
		""" create bbox reference size """

		# settings
		settings = {
						"humanSize": [90, 180, 30],
						'name': 'human_character_BBoxReference'
		}

		if not cmds.objExists(settings['name']):

			# determine factor scale if we are in another unit than cm
			factorScaleTemplate = {
									'mm': 10.0,
									'cm': 1.0,
									'm': 0.00001,
									'km': 1.0,
									'in': 0.393700787,
									'ft': 0.032808399,
									'yd': 0.010936133,
									'mi': 0.0000062137
								}
			factorScale = factorScaleTemplate[self.sn.unit]

			# create box
			bboxReferenceNode = cmds.polyCube(width=1, height=1, depth=1, name=settings['name'])

			# scale at the good size
			cmds.setAttr("%s.scaleX" % bboxReferenceNode[0], settings['humanSize'][0]*factorScale)
			cmds.setAttr("%s.scaleY" % bboxReferenceNode[0], settings['humanSize'][1]*factorScale)
			cmds.setAttr("%s.scaleZ" % bboxReferenceNode[0], settings['humanSize'][2]*factorScale)

			# set translate
			cmds.setAttr("%s.translateY" % bboxReferenceNode[0], (settings['humanSize'][1]*factorScale)/2)

			# parent to wip group
			if cmds.objExists('grp_wip'):
				cmds.parent(bboxReferenceNode[0], 'grp_wip')

			return bboxReferenceNode[0]

		else:
			logger.info('%s already exist int the scene' % settings['name'])
			return settings['name']


def init_scene(settings="model_prop"):
	"""init scene structure from current context"""

	initSn = Init_Scene()
	initSn.init_scene(settings=settings)
