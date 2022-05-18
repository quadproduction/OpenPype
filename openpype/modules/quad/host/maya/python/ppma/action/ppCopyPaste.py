# -*- coding: utf-8 -*-

import maya.cmds as cmds
import ppUtils.ppPath as ppPath


class CopyPaste(object):
	"""docstring for CopyPaste"""
	def __init__(self):
		super(CopyPaste, self).__init__()

		self.scene_type_mapping = {
								"ma": "mayaAscii",
								"mb": "mayaBinary",
								"abc": "Alembic"
		}
		
		self.file_type = "maya_scene"
		self.ext = "ma"
		self.root_directory = ppPath.get_tmp_directory(file_type=self.file_type)
		self.copy_paste_scene = "{root}/ppCopyPaste_{file_type}.{ext}".format(root=self.root_directory, file_type=self.file_type, ext=self.ext)

	def copy(self):
		"""
		"""
		# export selection to file
		cmds.file(self.copy_paste_scene, force=True, options="v=1", type=self.scene_type_mapping.get(self.ext), preserveReferences=True, exportUnloadedReferences=True, exportSelected=True, uiConfiguration=False)

		# return True
		return True

	def paste(self):
		"""
		"""
		cmds.file(self.copy_paste_scene, i=True, ignoreVersion=True, type=self.scene_type_mapping.get(self.ext), preserveReferences=True, mergeNamespacesOnClash=False)
		return True


def copy():
	cp = CopyPaste()
	cp.copy()


def paste():
	cp = CopyPaste()
	cp.paste()
