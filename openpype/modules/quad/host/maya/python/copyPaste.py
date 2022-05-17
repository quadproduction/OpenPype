# -*- coding: utf-8 -*-

"""
Modified version of file /prod/studio/pipeline/latest/maya/common/python/ppma/action/ppCopyPaste.py from old Fix Studio pipeline.
Import of ppPath removed for openPype integration.
"""

__author__ = 'OBLET jeremy'
__email__ = 'jeremy.oblet@fixstudio.com'

import os
import maya.cmds as cmds

class CopyPaste(object):
	def __init__(self):
		super(CopyPaste, self).__init__()

		self.file_type = "maya_scene"
		self.root_directory = '/mnt/data/pp/maya_scene'
		self.ext = "mb"
		
		if not os.path.exists(self.root_directory):
			os.makedirs(self.root_directory)

		self.copy_paste_scene = "{root}/CopyPaste_{file_type}.{ext}".format(root=self.root_directory, file_type=self.file_type, ext=self.ext)

	def copy(self):
		cmds.file(self.copy_paste_scene, force=True, options="v=1", type=self.ext, preserveReferences=True, exportUnloadedReferences=True, exportSelected=True, uiConfiguration=False)
		return

	def paste(self):
		cmds.file(self.copy_paste_scene, i=True, ignoreVersion=True, type=self.ext, preserveReferences=True, mergeNamespacesOnClash=False)
		return


def copy():
	cp = CopyPaste()
	cp.copy()

def paste():
	cp = CopyPaste()
	cp.paste()