# -*- coding: utf-8 -*-

"""
usefull classe management about plugins
"""

import maya.cmds as cmds
import maya.mel as mel
import fnmatch, logging

# loggger
#=======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('core.ppPlugins')
logger.setLevel(logging.INFO)

class Plugins():

	def __init__(self):

		self.pluginLoaded	= {}

	def getPluginsLoaded(self):

		res	= cmds.pluginInfo(query=True, listPlugins=True)
		if res:
			for pluginName in res:
				self.pluginLoaded[pluginName] = {'loaded': True}
			logger.debug("Plugin Loaded: %s" % self.pluginLoaded)

		return self.pluginLoaded

	def loadPlugins(self, pluginNameList=['fbxmaya']):

		self.getPluginsLoaded()

		# Plugin is Loaded?
		pluginLoadResult = {}
		for pluginName in pluginNameList:

			logger.info("Load Plugin %s" % pluginName)
			pluginLoadResult[pluginName]	= {}

			if not pluginName in self.pluginLoaded.keys():
				try:
					cmds.loadPlugin(pluginName)
					pluginLoadResult[pluginName] = {'loaded':True}
				except:
					logger.warning("Can't load plugin: %s" % pluginName)
					pluginLoadResult[pluginName] = {'loaded':False}
			else:
				pluginLoadResult[pluginName] = {'loaded':True}
				logger.info("Plugin %s already loaded" % pluginName)

		logger.debug("Plugin Load Result: %s" % pluginLoadResult)
		return pluginLoadResult


def getPluginsLoaded():
	"""
	return a dict wich represent the loaded plugins
	"""

	p = Plugins()
	return p.getPluginsLoaded()

def loadPlugins(pluginNameList=['fbxmaya']):
	"""
	return a dict wich represent the loaded plugins
	"""
	p = Plugins()
	return p.loadPlugins(pluginNameList=pluginNameList)