# -*- coding: utf-8 -*-

"""
import export command
"""
import maya.cmds as cmds
import maya.mel as mel
import maya.standalone as standalone
import logging, os, sys, time, subprocess, fnmatch, re, platform
import sgtk

from tank.util import shotgun
from tank import TankError
from tank_vendor import yaml

import ppma
import ppma.action.ppImpExpAnim as ppImpExpAnim
import ppma.core.ppSceneManagement as ppSceneManagement
import ppma.core.ppScene as ppScene
import ppma.core.ppNode as ppNode
import ppma.core.ppPlugins as ppPlugins


from ppSgtkLibs import ppSgtkPublisher
from optparse import OptionParser

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppma.action.ppAssetUpdate')
logger.setLevel(logging.INFO)

def get_pathFromSgPathDict(sgPathDict):

	# get path from os
	system = sys.platform
	path = sgPathDict['local_path_windows']

	if system == "darwin":
		path = sgPathDict['local_path_mac']

	if system == "linux2":
		path = sgPathDict['local_path_linux']

	return path


class AssetUpdater(object):
	"""docstring for AssetUpdater"""
	def __init__(self):

		self.tk = None
		self.ctx = None
		self.projectPath = None

		self.system = sys.platform

		self.mayaScene = None
		self.mayaScenePath = None
		self.entityType=None
		self.entityName=None
		self.task=None
		self.step=None
		self.publishName=None

		# set default publish arg
		self.defaultPublishArgs = {
									'tags':['auto-publish']
		}


	def get_sgtkInstance(self):
		""" """
		currentSn = cmds.file(query=True, sn=True)
		self.tk = sgtk.sgtk_from_path(currentSn)

	def do_assetUpdate(self, projectPath, entityType=None, entityName=None, task=None, publishName=None, version='latest', publishedFileId=None, asset=[], publish=False, exportAnim=[]):
		""" blah """

		# init sgtk
		if not os.path.exists(projectPath):
			logger.error("project path not exist at: {projectPath}".format(projectPath=projectPath))

		self.projectPath = projectPath
		self.tk = sgtk.sgtk_from_path(self.projectPath)

		##
		logger.info('do_assetUpdate:\n\
\t projectPath={projectPath}\n\
\t entityType={entityType}\n\
\t entityName={entityName}\n\
\t task={task}\n\
\t publishName={publishName}\n\
\t version={version}\n\
\t publishedFileId={publishedFileId}\n\
\t asset={asset}\n\
\t publish={publish}\n\
\t exportAnim={exportAnim}'.format(projectPath=projectPath, entityType=entityType, entityName=entityName, task=task, publishName=publishName, version=version, publishedFileId=publishedFileId, asset=asset, publish=publish, exportAnim=exportAnim))

		# get maya scene
		self.mayaScene = self.get_publishedFile(entityType=entityType, entityName=entityName, task=task, publishName=publishName, version=version, publishedFileId=publishedFileId)
		if not self.mayaScene:
			logger.error("Can't find a Maya Scene for entityType={entityType}, entityName={entityName}, task={task}, publishName={publishName}, version={version}, publishedFileId={publishedFileId})".format(entityType=entityType, entityName=entityName, task=task, publishName=publishName, version=version, publishedFileId=publishedFileId))
			return False

		if self.mayaScene:
			# acquire scene information
			self.mayaScenePath = get_pathFromSgPathDict(sgPathDict=self.mayaScene['path'])
			self.entityType=self.mayaScene['entity']['type']
			self.entityName=self.mayaScene['entity']['name']
			self.task=self.mayaScene['task']['name']
			self.step=self.mayaScene['task.Task.step']['name']
			self.publishName=self.mayaScene['name']

		# open maya scene
		if not self.do_openMayaScene(pf=self.mayaScene):
			logger.error("Can't Open Maya Scene")
			return

		# select node and replace
		logger.info("Do Replacement Reference, asset: {asset}".format(asset=asset))
		replacementResult = []
		for i in xrange(0, len(asset), 2):

			node = asset[i]
			pFId = asset[i+1]

			logger.info("Do Replacement Reference, node:{node}, pFId:{pFId}".format(node=node, pFId=pFId))

			# launch replacement
			r = self.do_referenceReplacement(node=node, pFId=pFId)

			replacementResult.append("Replacement Reference - Status={r} for node:{node} > Published File Id:{pFId}".format(r=r, node=node, pFId=pFId))

		# print replacement result
		logger.info("Replacement Reference - Result:")
		for line in replacementResult:
			logger.info("\t%s" % line)

		# publish scene
		if publish and not exportAnim:
			logger.info("Publish Scene: Active")
			r = self.do_publishScene(comment=replacementResult)
			if r:
				logger.info("Publish Scene: Done")

		# export animation
		if exportAnim:
			self.do_exportAnimation(exportAnim=exportAnim)

		return True

	def do_exportAnimation(self, exportAnim):
		""" """

		if exportAnim:
			anm = ppImpExpAnim.Animation()
			anm.initTk()
			anm.do_exportAnimation(nodes=exportAnim, subProcessMode="renderfarm", taskName=self.task)

		else:
			logger.info("Please Select something")
			return False

	def get_publishedFile(self, entityType=None, entityName=None, task=None, publishName=None, version=None, publishedFileId=None):
		""" retrieve information about published file."""

		logger.info("get_publishedFile(entityType={entityType}, entityName={entityName}, task={task}, publishName={publishName}, version={version}, publishedFileId={publishedFileId})".format(entityType=entityType, entityName=entityName, task=task, publishName=publishName, version=version, publishedFileId=publishedFileId))

		if not self.tk:
			self.get_sgtkInstance()

		if not self.tk:
			return

		# construct filter
		filters = [['sg_status_list', 'is_not', 'omt']]
		fieldsReturn = ['path', 'entity', 'task', 'task.Task.step', 'name']
		order = [{'field_name':'created_at','direction':'desc'}]

		if publishedFileId:
			filters.append(['id', 'is', int(publishedFileId)])

		else:
			if not entityType and not entityName and not task and not publishName and not version:
				return
			else:
				# construct filter
				filters.append(['entity', 'type_is', entityType])
				filters.append(['entity.{entityType}.code'.format(entityType=entityType), 'is', entityName])
				filters.append(['task.Task.content', 'is', task])
				filters.append(['name', 'is', publishName])

				# if latest provided for version number we don't need to specify a version number.
				if not version == "latest":
					filters.append(['version_number', 'is', int(version)])

		pf = self.tk.shotgun.find_one('PublishedFile', filters, fieldsReturn, order)
		logger.info("Published File found: {pf}".format(pf=pf))
		return pf

	def do_openMayaScene(self, pf):
		""" """

		# get path from os
		system = sys.platform
		snPath = get_pathFromSgPathDict(sgPathDict=pf['path'])

		if not os.path.exists(snPath):
			logger.error("Maya Scene Path not exist on disk: {snPath}".format(snPath=snPath))
			return

		# open scene
		logger.info("Open Scene: %s" % snPath)
		cmds.file(snPath, open=True, force=True)

		logger.info("End of Maya Opening, Scene Path: {snPath}".format(snPath=snPath))

		return True

	def do_referenceReplacement(self, node, pFId):
		""" this awesome command update reference filename by the provided publishedFileId."""

		# check if node exist in the scene
		if not cmds.objExists(node):
			logger.error("object node not exist: {node}".format(node=node))
			return False

		# check if publishedFile exist
		snPath = None
		pf = self.get_publishedFile(publishedFileId=pFId)

		if pf:
			snPath = get_pathFromSgPathDict(sgPathDict=pf['path'])

		if os.path.exists(snPath):

			logger.info("Replace Reference Attached to Node - START !!: {node} with snPath: {snPath}".format(node=node, snPath=snPath))
			# do replacement
			ppNode.do_replaceReferencedNodeByMyFile(node=node, filename=snPath, forceRemapping=False)

			logger.info("Replace Reference Attached to Node - DONE !!: {node} with snPath: {snPath}".format(node=node, snPath=snPath))

			return True

		else:
			return False

	def do_publishScene(self, comment):
		"""
		"""

		# init local var for export
		self.sysytem = sys.platform
		self.rootLocalFolder = "d:"
		if self.system == "linux2":
			self.rootLocalFolder = os.environ['HOME']

		try:
			self.rootLocalFolder = os.environ['DRIVE_DATA']
		except:
			logger.warning("The Env Var 'DRIVE_DATA' not exist")

		self.localFolder = "%s/pp/tmpExportAnimation" % self.rootLocalFolder



		logger.info("Publish Scene")
		# file export all @
		if not os.path.exists(self.localFolder):
			os.makedirs(self.localFolder)

		# get current scene
		currentSn = cmds.file(query=True, sn=True)

		# build local scene
		self.localScene = "%s/%s" % (self.localFolder, os.path.basename(currentSn))
		snExtension = self.localScene.split('.')[len(self.localScene.split('.'))-1]

		if os.path.exists(self.localScene):
			logger.info("Remove existing work scene: %s" % self.localScene)
			os.remove(self.localScene)

		snType = 'mayaAscii'
		if snExtension == 'ma':
			snType = 'mayaAscii'
		if snExtension == 'mb':
			snType = 'mayaBinary'

		# file export all
		logger.info("Export Scene for Publish: %s" % (self.localScene))
		res = cmds.file(self.localScene, force=True, options="v=1", type=snType, preserveReferences=True, exportAll=True)

		if res:

			# get dependency paths
			dependencies = ppSceneManagement.scanScene()

			# build publish arg
			commentSn = "\n".join(comment)
			publishArgs = {
							'project':self.projectPath,
							'filePath':self.localScene,
							'fileType':"maya_scene",
							'linkType':self.entityType,
							'linkName':self.entityName,
							'publishName': self.publishName,
							'stepName':self.step,
							'taskName':self.task,
							'comment':commentSn,
							'dependencies':dependencies,
							'tags':self.defaultPublishArgs['tags']
							}

			logger.info("Do Publish: %s" % self.localScene)
			logger.info("Publish Args: %s" % publishArgs)

			# do publish scene
			self.sgPublishedScene = ppSgtkPublisher.publishFile(project=publishArgs['project'], filePath=publishArgs['filePath'], fileType=publishArgs['fileType'], linkType=publishArgs['linkType'], linkName=publishArgs['linkName'], publishName=publishArgs['publishName'], stepName=publishArgs['stepName'], taskName=publishArgs['taskName'], comment=publishArgs['comment'], dependencies=publishArgs['dependencies'], tags=publishArgs['tags'])
			logger.info("Published Result %s" % (self.sgPublishedScene))

			# delete tmp file
			logger.info("delete tmp maya scene: %s" % publishArgs['filePath'])
			os.remove(publishArgs['filePath'])

			return self.sgPublishedScene

		else:
			return None


def main():
	"""
	Main function dedicated to import or export animation
	"""

	parser = OptionParser()

	parser.add_option("-p", "--projectPath", dest="projectPath", help="project path like c:/prod/project/HOTSPOT")

	parser.add_option("-t", "--entityType", dest="entityType", default="Shot", help="define which type of entity: Asset or Shot.")
	parser.add_option("-n", "--entityName", dest="entityName", default=None, help="define the name like dragon for Asset or 001_0005 for a Shot.")
	parser.add_option("-k", "--task", dest="task", default=None, help="define the task name linked to entity.")
	parser.add_option("-l", "--publishName", dest="publishName", default="basic", help="define the publish name to use for retrieve file.")
	parser.add_option("-v", "--version", dest="version", default="latest", help="define the publish version to use for retrieve file. if you specify 'latest' the latest published file is used.")

	parser.add_option("-f", "--publishedFileId", dest="publishedFileId", help="the shotgun published file id, if you specified this arg we don't care about entityType, entityName, publishName, version")


	parser.add_option("-a", "--asset",
										dest="asset",
										default=[],
										help="define an asset list with represent a node,a publishedFileId. the node is a maya node used for retrieve the reference node and the published file id is used for retrieve the new path for the reference. 'Exemple: -a dragon001:model:root,1234,dragon002:root,456' ",
					)

	parser.add_option("", "--publish", dest="publish", default=False, help="publish file after update", action="store_true")

	parser.add_option("", "--exportAnim",
										dest="exportAnim",
										default=[],
										help="fill this arg by the name of each node you want to export like dragon001:model:root,dragon002:model:root"
					)

	(options, args) = parser.parse_args()


	# check arg and launch
	if not options.projectPath:
		logger.error("please provide a projectPath like /prod/project/MON_SUPER_PROJET")
		return
	if not options.asset:
		logger.error("please provide an asset list to update like -a dragon001:model:root,1235")
		return

	if not options.entityType and not options.entityName and not options.task and not options.publishName and not options.version and not options.publishedFileId:
		logger.error("please specify a maya scene to update by using entityType, entityName, task, publishName, version or simply specify a published file id.")
		return

	projectPath = options.projectPath

	entityType = options.entityType
	entityName = options.entityName
	task = options.task
	publishName = options.publishName
	version = options.version

	publishedFileId = options.publishedFileId

	asset = options.asset.strip().split(',')
	# check if asset have a valid format
	if not len(asset) >= 2:
		logger.error("please provide an asset list to update like -a dragon001:model:root,1235")
		return

	publish = options.publish

	exportAnim = options.exportAnim
	if isinstance(exportAnim, str):
		exportAnim = exportAnim.split(',')

	# init maya standalone
	standalone.initialize()

	# init updater
	ass = AssetUpdater()
	r = ass.do_assetUpdate(projectPath=projectPath, entityType=entityType, entityName=entityName, task=task, publishName=publishName, version=version, publishedFileId=publishedFileId, asset=asset, publish=publish, exportAnim=exportAnim)

	return r

if __name__ == "__main__":
	exit (main())


# debug
# pp-launch-mayapy ppAssetUpdate.py -p /prod/project/PEUGEOT_208_DRAGON_15_019 -t Shot -n 001_0018 -k anim -l basic -a dragon001:root,25180,dragon002:root,25180,dragon003:root,25180 --exportAnim dragon001:model:root,dragon002:model:root,dragon003:model:root
# pp-launch-mayapy ppAssetUpdate.py -p /prod/project/PEUGEOT_208_DRAGON_15_019 -t Shot -n 001_0018 -k anim -l basic -a dragon001:root,25180,dragon002:root,25180,dragon003:root,25180 --exportAnim dragon001:model:root,dragon002:model:root,dragon003:model:root