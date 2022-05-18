# -*- coding: utf-8 -*-

"""
import export command
"""

import maya.cmds as cmds
import logging
import math
import ppma.action.ppCreateNode as ppCreateNode

# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppTools')
logger.setLevel(logging.INFO)


def convert3dPointTo2dScreenSpacePoint(camera=None, pointList=[], useRenderSettings=True, pointCoord="upperleft"):
	""" convert 3d point to 2d screenspace point.
	:param camera: specify the camera name transform or shape.
	:param pointList: point list like [[0.0, 1.0, 2.0], 'tutu']
	"""

	# get camera infos
	if not cmds.objExists(camera):
		return False

	# get film fit
	cFilmFit = cmds.getAttr("{camera}.filmFit".format(camera=camera))

	#
	renderSize = []
	resolutionNode = "defaultResolution"

	if cmds.objExists(resolutionNode):
		renderSize.append(cmds.getAttr("{resolutionNode}.width".format(resolutionNode=resolutionNode)))
		renderSize.append(cmds.getAttr("{resolutionNode}.height".format(resolutionNode=resolutionNode)))
		renderSize.append(cmds.getAttr("{resolutionNode}.deviceAspectRatio".format(resolutionNode=resolutionNode)))

	# get camera world inverse matrix
	cWorldInverseMatrix = cmds.getAttr("{camera}.worldInverseMatrix".format(camera=camera))

	# get horizontal field of view
	horizontalFilmAperture = cmds.getAttr("{camera}.horizontalFilmAperture".format(camera=camera)) * 25.4 # multiply  by 25.4 for switch from inch to mm
	verticalFilmAperture = cmds.getAttr("{camera}.verticalFilmAperture".format(camera=camera)) * 25.4 # multiply  by 25.4 for switch from inch to mm
	focalLength = cmds.getAttr("{camera}.focalLength".format(camera=camera))

	horizontalFieldOfView =  2.0 * math.atan(horizontalFilmAperture / (2.0 * focalLength)) # express in radian
	verticalFieldOfView =  2.0 * math.atan(verticalFilmAperture / (2.0 * focalLength)) # express in radian

	# for each point convert it to 2d screenspace
	screenSpacePoint = []
	for rawP in pointList:

		p = None

		# check if it's list, string
		# if list
		if isinstance(rawP, list):
			if len(rawP) == 3:
				p = rawP

		# if string get world space position
		if isinstance(rawP, str):
			# get world space position
			if not cmds.objExists(rawP):
				return False
			p = cmds.xform(rawP, query=True, worldSpace=True, matrix=True)
			print p


		if not p:
			return False

		# change repere
		# multiply matrix by position
		pCam = multiplyMatrix(p, cWorldInverseMatrix, matrixSize=4)

		# do conversion on pointX
		# p camera translation
		pCamTx = pCam[len(pCam)-4]
		pCamTy = pCam[len(pCam)-3]
		pCamTz = pCam[len(pCam)-2]

		pX = (((pCamTx / -pCamTz) / math.tan(horizontalFieldOfView/2.0)) / 2.0 )
		pY = (((pCamTy / -pCamTz) / math.tan(verticalFieldOfView/2.0)) / 2.0)

		print "pt: \t\t", pX, pY

		pX_remap = 0
		pY_remap = 0

		# if useRenderSettings
		if useRenderSettings and renderSize:

			sensorAspect = horizontalFilmAperture / verticalFilmAperture

			# if camera fit type == 0 - fill or 1 - horizontal
			#
			if cFilmFit == 0 or cFilmFit == 1:
				pY = (pY * (renderSize[2] / sensorAspect))
				print"ptY: ", pY

			# if camera fit type == 2 - vertical or 3 - overscan
			if cFilmFit == 2 or cFilmFit == 3:
				pX = (pX / (renderSize[2] / sensorAspect))
				print"ptX: ", pX

		if pointCoord == "upperleft":
			pX_remap = pX + 0.5
			pY_remap = abs(pY - 0.5)
		if pointCoord == "center":
			pX_remap = pX
			pY_remap = pY

		print "pt_remap: \t", pX_remap, pY_remap
		screenSpacePoint.append([pX_remap, pY_remap])

	return screenSpacePoint


def multiplyMatrix(matA, matB, matrixSize=3):
	""" """
	# init result
	r = [0] * (matrixSize * matrixSize)

	rangeCol = range(0, matrixSize)
	rangeRow = []
	for e in range(0, matrixSize): rangeRow.append(e * matrixSize)

	incrementA = 0
	incrementB = 0

	for i in range(0, (matrixSize*matrixSize)):

		modulo_i = i % (matrixSize+1)
		matA_id = 0
		matB_id = 0

		incrementA = (i / matrixSize) * matrixSize

		for j in range(0, matrixSize):

			matA_id = rangeCol[j] + incrementA
			matB_id = rangeRow[j] + incrementB
			r[i] += matA[matA_id] * matB[matB_id]

		if matB_id+1 == (matrixSize*matrixSize):
			incrementB = 0
		else:
			incrementB += 1

	return r


def snap(source, destination=None, snap_method="snap_transform"):
	"""
	snap object
	"""

	if snap_method == "snap_transform":
		cmds.parentConstraint(source, destination, skipTranslate="none", skipRotate="none", maintainOffset=False)
		cmds.scaleConstraint(source, destination, maintainOffset=False)
		cmds.delete(destination, constraints=True)
		return True

	if snap_method == "constraint_t_r_s":
		constraint_translate = False
		constraint_rotate = False
		constraint_scale = False
		# split constraint
		constraint = snap_method.replace('constraint_', '')
		if "t" in constraint:
			constraint_translate = True
		if "r" in constraint:
			constraint_rotate = True
		if "s" in constraint:
			constraint_scale = True

		if constraint_translate or constraint_rotate:
			# set
			skipTranslate = "none"
			skipRotate = "none"
			if not constraint_translate:
				skipTranslate = ["x", "y", "z"]
			if not constraint_rotate:
				skipRotate = ["x", "y", "z"]

			cmds.parentConstraint(source, destination, skipTranslate=skipTranslate, skipRotate=skipRotate, maintainOffset=True)

		if constraint_scale:
			cmds.scaleConstraint(source, destination, maintainOffset=True)
		
		return True

	return


def create_outMesh_inMesh(source, destination=None):
	"""
	this awesome function, connect source.outMesh to destination.inMesh
	if destination not specified we create a polyCube and connect outMesh to it.
	"""

	# check name
	if cmds.objExists("{source}.outMesh".format(source=source)):

		if not destination:
			# create polyCube
			destination = "{source}_inMesh".format(source=source)
			destination = cmds.polyCube(name=destination, ch=False)[0]

			# snap mesh to source
			snap(source=source, destination=destination, snap_method="snap_transform")

		if cmds.objExists("{destination}.inMesh".format(destination=destination)):

			# try connect to conncet
			cmds.connectAttr("{source}.outMesh".format(source=source), "{destination}.inMesh".format(destination=destination), force=True)

		else:
			logging.error("No destination object found, can't perform connection.")
			return
	else:
		logging.error("Can't create outMesh inMesh without {source}.outMesh")
		return


def create_outMesh_inMesh_selection():
	"""
	this awesome function, connect source.outMesh to destination.inMesh
	if destination not specified we create a polyCube and connect outMesh to it.
	"""

	# get selection
	sels = cmds.ls(sl=True, l=True)

	if sels:

		if len(sels) == 1:
			return create_outMesh_inMesh(source=sels[0], destination=None)
		elif len(sels) == 2:
			return create_outMesh_inMesh(source=sels[0], destination=sels[1])


def create_controller_from_node(node, shape_controller="locator", translate=True, rotate=True, scale=True):
	"""
	this function create a controller based on the world matrix transform node provided.
	"""
	controller = None
	
	# create controller
	if shape_controller == "locator":
		controller = cmds.spaceLocator(name="{node}_ctrl".format(node=node))[0]

	if not controller:
		return
	# snap to
	snap(source=node, destination=controller, snap_method="snap_transform")
	# freeze transform
	cmds.makeIdentity(controller, apply=True, translate=True, rotate=True, scale=True)

	# constraint node by controller
	snap(source=controller, destination=node, snap_method="constraint_t_r_s")

	# return


def create_controller_for_selection(shape_type="locator", constraint_node_to_controller=True, parent_node_to_controller=False):
	"""
	blah
	"""

	sel = cmds.ls(sl=True)

	for n in sel:
		created_node = ppCreateNode.Node()
		created_node.create_controller(n, shape_type="locator", constraint_node_to_controller=constraint_node_to_controller, parent_node_to_controller=parent_node_to_controller)


def snap_selection(snap_method="snap_transform"):
	"""
	this awesome function, snap an object to an other.
	"""

	# get selection
	sels = cmds.ls(sl=True, l=True)

	if sels:
		if len(sels) == 2:
			return snap(source=sels[0], destination=sels[1], snap_method=snap_method)
		else:
			logging.error("Can't snap")
			return
	else:
		logging.error("Can't snap")
		return


def set_near_far_based_on_scene():
	"""
	"""
	sl = cmds.ls(assemblies=True)

	bbox = cmds.exactWorldBoundingBox(sl, ignoreInvisible=True)
	size = []
	size.append(bbox[3]-bbox[0])
	size.append(bbox[4]-bbox[1])
	size.append(bbox[5]-bbox[2])
	maxSize = max(size)

	# get cameras
	cameras = cmds.ls(type="camera")

	min_value = int(maxSize*3/10000.0)
	max_value = int(maxSize*3)
	if min_value < 0.001:
		min_value = 0.001
	
	for c in cameras:
		cmds.setAttr("{c}.nearClipPlane".format(c=c), min_value)
		cmds.setAttr("{c}.farClipPlane".format(c=c), max_value)

	return True


def set_camera_to_pin_hole():
	"""
	"""
	cameras = cmds.ls(type="camera")
	for c in cameras:
		if cmds.objExists("{c}.mxLensType".format(c=c)):
			try:
				cmds.setAttr("{c}.mxLensType".format(c=c), 1)
			except:
				logger.warning("Can't set Pin Hole on Camera : {c}".format(c=c))

	return True
