# -*- coding: utf-8 -*-

"""
Modified version of file /prod/studio/pipeline/latest/maya/common/python/ppma/core/ppNode.py from old Fix Studio pipeline.
'delete_locked_nodes' function extracted for openPype integration.
Confirmation popup added with locked nodes list.
"""

__author__ = 'OBLET jeremy'
__email__ = 'jeremy.oblet@fixstudio.com'

import maya.cmds as cmds

def delete_locked_node():
	locked_nodes = cmds.ls(lockedNodes=True)
	if locked_nodes:
		confirmation = cmds.confirmDialog(  title='Confirm',
											message="SOME LOCKED NODES WERE FOUND IN SCENE:\n\n{nodes}\n\nDELETE IT ? (CHILDREN WILL BE DELETED WITH...)".format(nodes='\n'.join(locked_nodes)),
											button=['Yes','No'],
											defaultButton='Yes',
											cancelButton='No',
											dismissString='No'
										)
		if confirmation == 'Yes':
			cmds.lockNode(locked_nodes, lock=False)
			for node in locked_nodes:
				if cmds.nodeType(node) == "camera":
					cmds.camera(node, edit=True, startupCamera=False)
			cmds.delete(locked_nodes)
	else:
		cmds.warning( "No locked nodes in scene." )