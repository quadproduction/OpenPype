import maya.cmds as cmds
import os
import logging
import ppSgtkLibs.ppSgtkUtils
import ppma.core.ppScene as ppScene

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppInitNuke')
logger.setLevel(logging.INFO)


class Init(ppSgtkLibs.ppSgtkUtils.InitTk):
	"""docstring for ClassName"""
	def __init__(self, arg=None):
		super(Init, self).__init__()
		self.scene = ppScene.Scene()

	def _set_project_settings(self):
		"""
		this functions retiev from shotgun all the project settings declared.
		"""
		self.scene.set_project_settings_to_maya()

	def _set_resolutions_format(self):
		"""
		this functions retrieve from shotgun the project resolution declared.
		"""
		self.settings._set_project_resolutions()

	def init_scene(self):
		"""
		"""
		self._set_project_settings()


def init_script():
	"""
	this awesome function initialize nuke.
	"""
	i = Init()
	i.init_scene()
