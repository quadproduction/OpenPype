import maya.cmds as cmds
import math

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

def set_near_far_based_on_scene_no_int_cast():
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

	min_value = maxSize/3333.3333
	max_value = maxSize*3
	if min_value < 0.001:
		min_value = 0.001
	
	for c in cameras:
		cmds.setAttr("{c}.nearClipPlane".format(c=c), min_value)
		cmds.setAttr("{c}.farClipPlane".format(c=c), max_value)

	return True

def set_near_far_based_on_scene_diagonal():
	"""
	"""
	sl = cmds.ls(assemblies=True)

	bbox = cmds.exactWorldBoundingBox(sl, ignoreInvisible=True)
	size = []
	size.append(bbox[3]-bbox[0])
	size.append(bbox[4]-bbox[1])
	size.append(bbox[5]-bbox[2])
	maxSize = math.sqrt(size[0]*size[0]+size[1]*size[1]+size[2]*size[2])*2

	# get cameras
	cameras = cmds.ls(type="camera")

	max_value = maxSize
	min_value = maxSize/10000.0
	if min_value < 0.001:
		min_value = 0.001
	
	for c in cameras:
		cmds.setAttr("{c}.nearClipPlane".format(c=c), min_value)
		cmds.setAttr("{c}.farClipPlane".format(c=c), max_value)

	return True