import maya.cmds as cmds
import math


def set_near_far():
	"""
	"""
	animStart = cmds.playbackOptions(query=True,animationStartTime=True)
	animEnd = cmds.playbackOptions(query=True,animationEndTime=True) 

	sl = cmds.ls(assemblies=True)
	maxSize = 0.0

	for frame in range(int(animStart),int(animEnd)):
		cmds.currentTime(frame)
		bbox = cmds.exactWorldBoundingBox(sl, ignoreInvisible=True)
		size = []
		size.append(bbox[3]-bbox[0])
		size.append(bbox[4]-bbox[1])
		size.append(bbox[5]-bbox[2])
		maxSize = max(maxSize,math.sqrt(size[0]*size[0]+size[1]*size[1]+size[2]*size[2])*2)

		
	# get cameras
	cameras = cmds.ls(type="camera")

	max_value = maxSize
	min_value = maxSize/3333.3333
	min_value = max(min_value,0.001)
	
	for c in cameras:
		cmds.setAttr("{c}.nearClipPlane".format(c=c), min_value)
		cmds.setAttr("{c}.farClipPlane".format(c=c), max_value)

	return True