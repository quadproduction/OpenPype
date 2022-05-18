# -*- coding: utf-8 -*-

"""
common classes and functions about node
"""

import maya.cmds as cmds
import maya.mel as mel
import logging
import random
import ppma.core.ppTools as ppTools

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppma.action.ppInitScene')
logger.setLevel(logging.INFO)


class Autorig(object):
	"""docstring for Autorig"""
	def __init__(self):
		super(Autorig, self).__init__()

		# settings
		self.settings = {
										"main_ctrl": {"node": "main_ctrl", "shape": "cross", "size": 1.0},
										"sub_ctrl": {"node": "sub_ctrl", "shape": "cross", "size": 0.9},
										"escape_list": ['grp_wip', 'grp_blendShape'],
										"grp_ctrl": {"node": "grp_ctrl"},
										"ctrl_set": {"node": "ctrl_set"}
						}

		# init self.controllers
		self.controllers = []

		# init top_node var
		self.top_node = None

	def start_autorig(self, top_node, rig_type):
		"""
		"""
		logger.info("start_autorig(top_node={top_node}, rig_type={rig_type})".format(top_node=top_node, rig_type=rig_type))

		# init controllers
		self.controllers = []

		# set top_node
		cmds.select(top_node, replace=True)
		self.top_node = cmds.ls(sl=True, l=True)[0]
		
		# create default controller
		self.create_default_controller(top_node=top_node)

		# scan_hierarchy
		self.target_nodes = self.scan_hierarchy(top_node=top_node)

		# create controllers
		self.target_nodes_to_controlers(target_nodes=self.target_nodes)

		# parent main_ctrl to grp_ctrl
		if cmds.objExists(self.settings["grp_ctrl"]["node"]):
			cmds.parent(self.settings["main_ctrl"]["node"], self.settings["grp_ctrl"]["node"])

		# create ctrl_set
		self.create_ctrl_set()

		# add controllers to ctrl_set
		self.add_controllers_to_ctrl_set()

	def create_ctrl_set(self):
		"""
		"""
		if not cmds.objExists(self.settings["ctrl_set"]["node"]):
			ctrl_set = cmds.createNode("objectSet", name=self.settings["ctrl_set"]["node"])

	def add_controllers_to_ctrl_set(self):
		"""
		"""
		if not cmds.objExists(self.settings["ctrl_set"]["node"]):
			self.create_ctrl_set()

		# add controllers
		controllers = []
		for c in self.controllers:
			controllers.append(c["name"])
			
		controllers.reverse()

		cmds.sets(controllers, addElement=self.settings["ctrl_set"]["node"])

	def scan_hierarchy(self, top_node):
		"""
		"""
		logger.info("scan_hierarchy(top_node={top_node})".format(top_node=top_node))

		# get chidlren of top_node
		nodes_tmp = cmds.listRelatives(top_node, allDescendents=True, type='transform', fullPath=True)
		# sort for graph by deep
		nodes_tmp.sort()
		# init result var
		nodes = []

		# for each node try determine if it's a good name for ctrl
		for n in nodes_tmp:

			# check if it's a group and not in escape list
			if cmds.listRelatives(n, type="transform"):
				escape_word_found = False
				
				for escape_word in self.settings["escape_list"]:
					if n.find(escape_word) >= 0:
						escape_word_found = True
				if not escape_word_found:
					nodes.append(n)

		return nodes

	def create_default_controller(self, top_node):
		"""
		"""
		logger.info("create_default_controller(top_node={top_node})".format(top_node=top_node))

		# set top_node
		cmds.select(top_node, replace=True)
		self.top_node = cmds.ls(sl=True, l=True)[0]
		
		# create main
		self.create_controllers(name=self.settings["main_ctrl"]["node"], target_node=self.top_node, parent_ctrl=None, shape=self.settings["main_ctrl"]["shape"], size=self.settings["main_ctrl"]["size"], constraint_mode=None)

		# create sub
		self.create_controllers(name=self.settings["sub_ctrl"]["node"], target_node=self.top_node, parent_ctrl=self.settings["main_ctrl"]["node"], shape=self.settings["sub_ctrl"]["shape"], size=self.settings["sub_ctrl"]["size"])

	def target_nodes_to_controlers(self, target_nodes):
		"""
		"""
		logger.info("target_nodes_to_controlers(target_nodes={target_nodes})".format(target_nodes=target_nodes))
		
		self.target_nodes = target_nodes

		if not self.top_node:
			return False

		# get sub_ctrl full path
		cmds.select(self.settings["sub_ctrl"]["node"], replace=True)
		sub_ctrl_l = cmds.ls(sl=True, l=True)[0]

		#  for each node get target_node path
		for target_node in self.target_nodes:

			# remove top_node from path
			target_node_strip_root = target_node.replace(self.top_node, "")
			
			# retrieve controller name
			short_target_node = target_node_strip_root.split('|')[len(target_node_strip_root.split('|'))-1]
			controller_name = short_target_node.split(':')[len(short_target_node.split(':'))-1]
			controller_name = controller_name.replace("grp_", "")

			if not "ctrl" in controller_name:
				controller_name = "{c}_ctrl".format(c=controller_name)

			logger.info("controller_name : {c}".format(c=controller_name))

			# build create controller command
			constraint_mode = "t_r_s"
			parent_ctrl = None
			shape = "circleY"
			size = 1.0

			# retrieve parent_ctrl
			# remove latest
			
			# replace root by sub_ctrl
			parent_ctrl_tmp = target_node.replace(self.top_node, sub_ctrl_l)

			for item in self.controllers:
				if "short_target_node" in item.keys():
					if item["short_target_node"]:
						parent_ctrl_tmp = parent_ctrl_tmp.replace(item["short_target_node"], item["name"])
			
			# remove latest object
			parent_ctrl_tmp_split = parent_ctrl_tmp.split('|')
			parent_ctrl_tmp_split.pop(len(parent_ctrl_tmp_split)-1)
			parent_ctrl_tmp = "|".join(parent_ctrl_tmp_split)

			print parent_ctrl_tmp
			if cmds.objExists(parent_ctrl_tmp):
				parent_ctrl = parent_ctrl_tmp

			self.create_controllers(name=controller_name, target_node=target_node, constraint_mode=constraint_mode, parent_ctrl=parent_ctrl, shape=shape, size=size)

	def create_controllers(self, name, target_node=None, constraint_mode="t_r_s", parent_ctrl=None, shape="cross", size=1.0):
		"""
		"""
		logger.info("create_controllers(name={name}, target_node={target_node}, constraint_mode={constraint_mode}, parent_ctrl={parent_ctrl}, shape={shape}, size={size})".format(name=name, target_node=target_node, constraint_mode=constraint_mode, parent_ctrl=parent_ctrl, shape=shape, size=size))
		
		#  check if controller already exist
		if cmds.objExists(name):
			return True

		# make selection clear
		cmds.select(clear=True)

		# Get bounding box
		bbox = cmds.exactWorldBoundingBox(target_node, ignoreInvisible=True)
		scaleX = (bbox[3] - bbox[0]) / 2.0
		scaleY = (bbox[4] - bbox[1]) / 2.0
		scaleZ = (bbox[5] - bbox[2]) / 2.0
		bboxScale = scaleX
		if scaleY > bboxScale:
			bboxScale = scaleY
		if scaleZ > bboxScale:
			bboxScale = scaleZ
		# compense comet cross extra large
		if shape == "cross":
			bboxScale = bboxScale / 2.0

		# source mel from comet
		mel.eval('source "wireShape.mel"')

		# create shape
		if shape == "locator":
			name = cmds.spaceLocator(name=name)[0]
		else:
			mel.eval('wireShape("%s")' % shape)
			tmp_name = cmds.ls(sl=True)[0]
			logger.info("{s} name {n}".format(s=shape, n=tmp_name))
			logger.info("rename {old_name} - {new_name}".format(old_name=tmp_name, new_name=name))
			name = cmds.rename(tmp_name, name)

		# Set scale based on bbox
		logger.info("Set Size to : {s}".format(s=size))
		cmds.setAttr("{n}.scaleX".format(n=name), bboxScale)
		cmds.setAttr("{n}.scaleY".format(n=name), bboxScale)
		cmds.setAttr("{n}.scaleZ".format(n=name), bboxScale)

		# Freeze scale
		cmds.makeIdentity(name, apply=True, translate=True, rotate=True, scale=True, normal=False, preserveNormals=True)

		# Set size definied by arg
		logger.info("Set Size to : {s}".format(s=size))
		cmds.setAttr("{n}.scaleX".format(n=name), size)
		cmds.setAttr("{n}.scaleY".format(n=name), size)
		cmds.setAttr("{n}.scaleZ".format(n=name), size)

		cmds.makeIdentity(name, apply=True, translate=True, rotate=True, scale=True, normal=False, preserveNormals=True)

		# set position
		if target_node:
			ppTools.snap(source=target_node, destination=name, snap_method="snap_transform")

			# freeze translate
			cmds.makeIdentity(name, apply=True, translate=True, rotate=False, scale=True, normal=False, preserveNormals=True)

		# parent ctrl
		if parent_ctrl:
			cmds.parent(name, parent_ctrl)

		# constraint
		if target_node and constraint_mode:
			# connect to target node
			constraint_translate = False
			constraint_rotate = False
			constraint_scale = False
			
			# split constraint
			if "t" in constraint_mode:
				constraint_translate = True
			if "r" in constraint_mode:
				constraint_rotate = True
			if "s" in constraint_mode:
				constraint_scale = True

			if constraint_translate or constraint_rotate:
				# set
				skipTranslate = "none"
				skipRotate = "none"
				if not constraint_translate:
					skipTranslate = ["x", "y", "z"]
				if not constraint_rotate:
					skipRotate = ["x", "y", "z"]

				cmds.parentConstraint(name, target_node, skipTranslate=skipTranslate, skipRotate=skipRotate, maintainOffset=True)

			if constraint_scale:
				cmds.scaleConstraint(name, target_node, maintainOffset=True)

		# set color
		# get shape node
		shape_node = cmds.listRelatives(name, children=True)
		if shape_node:

			shape_node = shape_node[0]

			# define color RGB
			random.seed(len(name))
			r = random.randrange(0, 10)/10.0

			random.seed(10*r)
			g = random.randrange(0, 10)/10.0

			random.seed(100*g)
			b = random.randrange(0, 10)/10.0

			# set attributes
			cmds.setAttr("{shape_node}.overrideEnabled".format(shape_node=shape_node), True)
			cmds.setAttr("{shape_node}.overrideRGBColors".format(shape_node=shape_node), True)
			
			cmds.setAttr("{shape_node}.overrideColorR".format(shape_node=shape_node), r)
			cmds.setAttr("{shape_node}.overrideColorG".format(shape_node=shape_node), g)
			cmds.setAttr("{shape_node}.overrideColorB".format(shape_node=shape_node), b)

		# add controller to self.controllers
		short_target_node = target_node
		if short_target_node:
			short_target_node = target_node.split('|')[len(target_node.split('|'))-1]

		c = {
				"name": name,
				"target_node": target_node,
				"short_target_node": short_target_node,
				"constraint_mode": constraint_mode,
				"parent_ctrl": parent_ctrl,
				"shape": shape,
				"size": size
		}

		self.controllers.append(c)


def autorig(top_node, rig_type="prop"):
	"""
	"""
	a = Autorig()
	a.start_autorig(top_node=top_node, rig_type=rig_type)


def autorig_selection(rig_type="prop"):
	"""
	"""

	n = cmds.ls(sl=True, l=True)
	if n:
		r = autorig(top_node=n[0], rig_type=rig_type)
		return r

	return False
