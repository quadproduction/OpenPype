# -*- coding: utf-8 -*-

"""
Modified version of reload Current Scene from old Fix Studio pipeline.
warning popup added.
"""

__author__ = 'OBLET jeremy'
__email__ = 'jeremy.oblet@fixstudio.com'

import maya.cmds as cmds

def reload_current_scene():
    confirmation = cmds.confirmDialog(title='Confirm', message='Reload current scene?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No')
    if confirmation == 'Yes':
        scene_name = cmds.file(query=True, sceneName=True)
        cmds.file( scene_name, force=True, open=True)
