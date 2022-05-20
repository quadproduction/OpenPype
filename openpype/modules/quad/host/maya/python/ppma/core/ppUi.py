# -*- coding: utf-8 -*-

"""
common classes and functions about ui / hack ui, hud
"""

import maya.cmds as cmds
import maya.mel as mel
import datetime
import sgtk
import os
import logging
import fnmatch
try:
	from shiboken2 import wrapInstance
except ImportError:
	from shiboken import wrapInstance

if not cmds.about(batch=True):
	from Qt import QtCore, QtGui
	import maya.OpenMayaUI as omui


# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppma.action.ppUi')
logger.setLevel(logging.INFO)

hudVar = {
			"ppHudProject": {'default': 'Fix|Studio', 'envSystem': 'PP_HUD_PROJECT'},
			"ppHudUser": {'default': 'Fix|Studio', 'envSystem': 'PP_HUD_USER'},
			"ppHudDate": {'default': 'Fix|Studio', 'envSystem': 'PP_HUD_DATE'},
			"entityType": {'default': 'EntityType', 'envSystem': 'PP_HUD_ENT_TYPE'},
			"entityName": {'default': 'EntityName', 'envSystem': 'PP_HUD_ENT_NAME'},
			"cameraName": {'default': 'CameraName', 'envSystem': 'PP_HUD_CAMERA_NAME'}
}


# dedicated function for headUpDisplay

def getStaticValue(hudName=None):
	"""
	blah
	"""
	var = hudVar[hudName]['default']

	# get project
	try:
		var = os.environ[hudVar[hudName]['envSystem']]
	except:
		pass

	return var


def getProject(*args):
	"""
	get a formatted project name
	"""
	return getStaticValue(hudName='ppHudProject')


def getUser(*args):
	"""
	get a formatted user name
	"""
	return getStaticValue(hudName='ppHudUser')


def getDate(*args):
	"""
	get a formatted date name
	"""
	return getStaticValue(hudName='ppHudDate')


def getContext(*args):
	"""
	get a formatted shot name like shotName|camera|focal
	"""
	entType = hudVar['entityType']['default']
	entName = hudVar['entityName']['default']
	camName = hudVar['cameraName']['default']
	focal = "##"

	# get ent type
	try:
		entType = os.environ[hudVar['entityType']['envSystem']]
	except:
		pass

	# get ent type
	try:
		entName = os.environ[hudVar['entityName']['envSystem']]
	except:
		pass

	# get camera name
	try:
		camName = os.environ[hudVar['cameraName']['envSystem']]
	except:
		pass

	# get camera focal
	if not camName == hudVar['cameraName']['default']:
		focal = getCurrentFocal(camera=camName)

	# formatting result like this "Shot-001_0001|cam5D_001:camera-50mm"
	result = "%s-%s|%s-%smm" % (entType, entName, camName, focal)

	return result


def getCurrentFrame(*args):
	"""
	get the current frame
	"""
	return "Frame: %s" % cmds.currentTime(query=True)


#

def getCurrentFocal(camera=None):
	""" get the current focal.
	:param camera: (str) the camera name transform or shape
	"""
	focalAttr = "focalLength"
	focalValue = "##"
	if cmds.objExists("%s.%s" % (camera, focalAttr)):
		focalValue = "%.01f" % float(cmds.getAttr("%s.%s" % (camera, focalAttr)))

	return focalValue


def getSociety():

	if os.environ["PP_SITE"] == "brussels":
		return "Benuts"
	else:
		return "Fix|Studio"


def getCurrentDate():
	""" get Date formatted for Hud"""
	return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Hud(object):
	"""docstring for Hud"""
	def __init__(self):

		# get current engine
		self.engine = sgtk.platform.current_engine()

		self.createdExprNode = []

		self.hudList = {

								"ppHudShot": {
												"isActive":True,
												"isStatic":False,
												"section":5,
												"block":2,
												"blockAlignment": "left",
												"blockSize": "medium",
												"label": "",
												"labelFontSize": "large",
												"dataFontSize": "large",
												"event": "timeChanged",
												"command":getContext
								},
								"ppHudProject": {
												"isActive":True,
												"isStatic":True,
												"value":None,
												"section":7,
												"block":2,
												"blockAlignment": "left",
												"blockSize": "medium",
												"label": "",
												"labelFontSize": "large",
												"dataFontSize": "large",
												"event":None,
												"command":getProject
								},
								"ppHudUser": {
												"isActive":True,
												"isStatic":True,
												"value":None,
												"section":8,
												"block":1,
												"blockAlignment": "left",
												"blockSize": "medium",
												"label": "",
												"labelFontSize": "large",
												"dataFontSize": "large",
												"event":None,
												"command":getUser
								},
								"ppHudDate": {
												"isActive":True,
												"isStatic":True,
												"value":None,
												"section":1,
												"block":1,
												"blockAlignment": "left",
												"blockSize": "medium",
												"label": "",
												"labelFontSize": "large",
												"dataFontSize": "large",
												"event":None,
												"command":getDate
								},
								"ppHudFrame": {
												"isActive":True,
												"isStatic":False,
												"section":3,
												"block":1,
												"blockAlignment": "left",
												"blockSize": "medium",
												"label": "",
												"labelFontSize": "large",
												"dataFontSize": "large",
												"event": "timeChanged",
												"command":getCurrentFrame
								}
		}

		# dict store maya hud
		self.mayaHud	= {}
		self.mayaHud["selectDetailsVisibility"] = {"optionVar": "selectDetailsVisibility", "command": "setSelectDetailsVisibility", "origValue":0}
		self.mayaHud["objectDetailsVisibility"] = {"optionVar": "objectDetailsVisibility", "command": "setObjectDetailsVisibility", "origValue":0}
		self.mayaHud["polyCountVisibility"] = {"optionVar": "polyCountVisibility", "command": "setPolyCountVisibility", "origValue":0}
		self.mayaHud["animationDetailsVisibility"] = {"optionVar": "animationDetailsVisibility", "command": "setAnimationDetailsVisibility", "origValue":0}
		self.mayaHud["hikDetailsVisibility"] = {"optionVar": "hikDetailsVisibility", "command": "setHikDetailsVisibility", "origValue":0}
		self.mayaHud["frameRateVisibility"] = {"optionVar": "frameRateVisibility", "command": "setFrameRateVisibility", "origValue":0}
		self.mayaHud["currentFrameVisibility"] = {"optionVar": "currentFrameVisibility", "command": "setCurrentFrameVisibility", "origValue":0}
		self.mayaHud["sceneTimecodeVisibility"] = {"optionVar": "sceneTimecodeVisibility", "command": "setSceneTimecodeVisibility", "origValue":0}
		self.mayaHud["currentContainerVisibility"] = {"optionVar": "currentContainerVisibility", "command": "setCurrentContainerVisibility", "origValue":0}
		self.mayaHud["cameraNamesVisibility"] = {"optionVar": "cameraNamesVisibility", "command": "setCameraNamesVisibility", "origValue":0}
		self.mayaHud["focalLengthVisibility"] = {"optionVar": "focalLengthVisibility", "command": "setFocalLengthVisibility", "origValue":0}
		self.mayaHud["viewAxisVisibility"] = {"optionVar": "viewAxisVisibility", "command": "setViewAxisVisibility", "origValue":0}


	def initStaticValues(self):
		"""
		get and set static hud value like user, project, date.
		"""
		self.engine = sgtk.platform.current_engine()

		#  init static values
		# set Project
		try:
			os.environ[hudVar['ppHudProject']['envSystem']] = '%s - %s' % (getSociety(), self.engine.context.project['name'])
		except:
			os.environ[hudVar['ppHudProject']['envSystem']] = '%s' % (getSociety())

		# set User Hud
		# get template_path for retrieving the scene name
		sn = cmds.file(q=True, sn=True)
		t = self.engine.sgtk.template_from_path(sn)
		# get fields from path
		f = t.get_fields(sn)

		try:
			ppHudUser = "{u} | {s} - {n}".format(u=self.engine.context.user['name'], s=f["Step"], n=f["name"])
			os.environ[hudVar['ppHudUser']['envSystem']] = ppHudUser
		except:
			os.environ[hudVar['ppHudUser']['envSystem']] = ""

		# set Date
		try:
			os.environ[hudVar['ppHudDate']['envSystem']] = getCurrentDate()
		except:
			os.environ[hudVar['ppHudDate']['envSystem']] = ""

		# Static Values for Dynamic Values
		# set Entity type and name, and store into env var
		try:
			os.environ[hudVar['entityType']['envSystem']] = self.engine.context.entity['type']
		except:
			os.environ[hudVar['entityType']['envSystem']] = hudVar['entityType']['default']

		try:
			os.environ[hudVar['entityName']['envSystem']] = self.engine.context.entity['name']
		except:
			os.environ[hudVar['entityName']['envSystem']] = hudVar['entityName']['default']



	def setCamera(self, cameraName=None):
		""" set the usable camera to retrieve focal data"""
		try:
			os.environ[hudVar['cameraName']['envSystem']] = cameraName
		except:
			os.environ[hudVar['cameraName']['envSystem']] = hudVar['cameraName']['default']

	def setHudActive(self, hudName=None):
		"""
		set an hud active. get the hud list with self.getHudAvailable()
		:param hudName: (str) hud Name
		"""
		# check if hud exist
		if hudName in self.hudList.keys():

			# set active
			self.hudList[hudName]['isActive'] = True
			return True
		else:
			logger.error("can't set hud: %s active, it does not exist" % hudName)
			return False

	def setHudInactive(self, hudName=None):
		"""
		set an hud inactive. get the hud list with self.getHudAvailable()
		:param hudName: (str) hud Name
		"""
		# check if hud exist
		if hudName in self.hudList.keys():

			# set active
			self.hudList[hudName]['isActive'] = False
			return True
		else:
			logger.error("can't set hud: %s inactive, it does not exist" % hudName)
			return False

	def storeMayaHud(self):
		"""
		store maya hud.
		"""
		for item in self.mayaHud.keys():
			self.mayaHud[item]["origValue"]	= cmds.optionVar(query=self.mayaHud[item]["optionVar"])

	def hideMayaHud(self):
		"""
		hide maya hud.
		"""
		# before we save the current hud
		self.storeMayaHud()
		for item in self.mayaHud.keys():
			# hide hud
			mel.eval("%s(0)" % self.mayaHud[item]["command"])

	def restoreMayaHud(self):
		"""
		restore maya hud.
		"""
		# restore value from dict
		for item in self.mayaHud.keys():
			mel.eval("%s(%s)" % (self.mayaHud[item]["command"], self.mayaHud[item]["origValue"]))

	def createAll(self, cameraName=None):
		"""
		create all hud.
		"""
		# init static values
		self.initStaticValues()

		# set camera name
		if cameraName:
			self.setCamera(cameraName=cameraName)

		# hide the current maya hud
		self.hideMayaHud()

		# display ours hud
		for hud in self.getHudAvailable():

			# create hud
			self.create(name=hud)

	def deleteAll(self):
		"""
		delete all hud.
		"""
		# hide the current maya hud
		self.restoreMayaHud()

		# delete each hud
		for hud in self.getHudAvailable():

			# delete hud
			self.delete(name=hud)

		# lokking for delete expression node
		self.deleteExpression()

	def deleteExpression(self):
		"""
		research and delete expression string match
		"""

		# check expression node in self.createdExprNode
		for exprNode in self.createdExprNode:
			if cmds.objExists(exprNode):
				logger.debug("delete hud expr node")
				cmds.delete(exprNode)

		# check if an old expression hud node exist
		for en in cmds.ls(type='expression'):
			for hud in self.getHudAvailable():
				if fnmatch.fnmatch(en, "%s_expr*" % hud):
					cmds.delete(en)

	def getHudAvailable(self):
		"""
		retrieve custom Hud available.
		"""
		return sorted(self.hudList.keys())

	def getHudStatus(self):
		"""
		retrieve the hud status (isActive).
		"""
		res = {}
		for hudName in sorted(self.hudList.keys()):

			res[hudName] = self.hudList['isActive']

		return res

	def create(self, name=None):
		"""
		create specific hud.
		:param name:
		"""
		logger.info("create hud: %s" % name)
		if name in self.getHudAvailable():

			# get hud data
			hud = self.hudList[name]

			# check ppHUD already exist
			if name in cmds.headsUpDisplay(listHeadsUpDisplays=True):

				# set visibility on
				cmds.headsUpDisplay(name, edit=True, visible=True)

			else:
				# remove current hud
				cmds.headsUpDisplay(removePosition=(hud['section'], hud['block']))

				try:
					cmds.headsUpDisplay(name, remove=True)
				except:
					pass

				# check if it's a static or dynamic hud
				if hud['isStatic']:
					logger.info("name={name}, section={section}, block={block}, blockSize={blockSize}, label={label}, labelFontSize={labelFontSize}, dataFontSize={dataFontSize}".format(name=name, section=hud['section'], block=hud['block'], blockSize=hud['blockSize'], label=hud['label'], labelFontSize=hud['labelFontSize'], dataFontSize=hud['dataFontSize']))
					hudNode = cmds.headsUpDisplay(name, section=hud['section'], block=hud['block'], blockSize=hud['blockSize'], label=hud['label'], labelFontSize=hud['labelFontSize'], dataFontSize=hud['dataFontSize'], command=hud['command'])

				else:
					logger.info("name={name}, section={section}, block={block}, blockSize={blockSize}, label={label}, labelFontSize={labelFontSize}, dataFontSize={dataFontSize}".format(name=name, section=hud['section'], block=hud['block'], blockSize=hud['blockSize'], label=hud['label'], labelFontSize=hud['labelFontSize'], dataFontSize=hud['dataFontSize']))
					hudNode = cmds.headsUpDisplay(name, section=hud['section'], block=hud['block'], blockSize=hud['blockSize'], label=hud['label'], labelFontSize=hud['labelFontSize'], dataFontSize=hud['dataFontSize'], event='%s' % hud['event'], command=hud['command'], attachToRefresh=False)

					# create expression for force the refresh of the hud
					exprNode = "%s_expr" % name
					expression = 'if (`about -batch` ==0) {\nif (`headsUpDisplay -ex %s`) {\r\n\theadsUpDisplay -refresh %s;\r\n}}' % (name, name)
					#kill previsous expression
					if cmds.objExists(exprNode):
						cmds.delete(exprNode)
					# create expression
					exprNode = cmds.expression(name=exprNode, s=expression)
					self.createdExprNode.append(exprNode)


	def delete(self, name=None):
		"""
		delete specific hud
		"""
		if cmds.headsUpDisplay(name, query=True, exists=True):
			cmds.headsUpDisplay(name, rem=True)
			return True
		return True


def wrapinstance(ptr, base=None):
	"""
	Utility to convert a pointer to a Qt class instance (PySide/PyQt compatible)
	:param ptr: Pointer to QObject in memory
	:type ptr: long or Swig instance
	:param base: (Optional) Base class to wrap with (Defaults to QObject, which should handle anything)
	:type base: QtGui.QWidget
	:return: QWidget or subclass instance
	:rtype: QtGui.QWidget
	"""
	if ptr is None:
		return None
	ptr = long(ptr)

	# if 'shiboken' in globals().keys():
	# 	if base is None:
	# 		qObj = shiboken.wrapInstance(long(ptr), QtCore.QObject)
	# 		metaObj = qObj.metaObject()
	# 		cls = metaObj.className()
	# 		superCls = metaObj.superClass().className()
	# 		if hasattr(QtGui, cls):
	# 			base = getattr(QtGui, cls)
	# 		elif hasattr(QtGui, superCls):
	# 			base = getattr(QtGui, superCls)
	# 		else:
	# 			base = QtGui.QWidget
	# 	return shiboken.wrapInstance(long(ptr), base)
	# else:
	# 	return None

	if 'wrapInstance' in globals().keys():
		if base is None:
			qObj = wrapInstance(long(ptr), QtCore.QObject)
			metaObj = qObj.metaObject()
			cls = metaObj.className()
			superCls = metaObj.superClass().className()
			if hasattr(QtGui, cls):
				base = getattr(QtGui, cls)
			elif hasattr(QtGui, superCls):
				base = getattr(QtGui, superCls)
			else:
				base = QtGui.QWidget
		return wrapInstance(long(ptr), base)
	else:
		return None

def get_parent_ui():
	"""
	this func retrieve the wrap instance of maya main ui.
	"""
	main_window_ptr = omui.MQtUtil.mainWindow()
	return wrapinstance(long(main_window_ptr), QtGui.QWidget)


def set_all_viewport_in(renderer="default"):
	"""
	"""
	renderer_mapping = {
							"default": "base_OpenGL_Renderer",
							"viewport2": "ogsRenderer",
							"highQuality": "hwRender_OpenGL_Renderer"
	}

	if renderer not in renderer_mapping.keys():
		logger.error("Renderer '{renderer}' not exist in list. Use {renderer_list}".format(renderer=renderer, renderer_list=renderer_mapping.keys()))
		return

	# get panel in maya
	model_panels = cmds.getPanel(type='modelPanel')

	for model_panel in model_panels:

		cmds.modelEditor(model_panel, edit=True, rnm=renderer_mapping[renderer])


def message_dialog(title, message, message_type="information", button=None, cancel_button=None):
	"""
	"""
	result = False
	if not cmds.about(batch=True):

		kwargs = {
			"title": title,
			"message": message,
			"icon": message_type,
			"button": button,
			"cancelButton": cancel_button
		}

		r = cmds.confirmDialog(**kwargs)
		if r == button:
			result = True

	return result
