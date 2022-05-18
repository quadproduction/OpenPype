# -*- coding: utf-8 -*-

import maya.mel as mel
import os


def source_Hda_scrtips():
    """ define HDA's path """
    pipepath = os.environ['PP_PIPE_PATH']
    hdaPath =  pipepath + '/houdini/common/otls'
    houdiniVersion = os.environ['PP_HOUDINI_ENGINE_MAYA_PLUGIN_VERSION']
    mayaVersion = os.environ['PP_MAYA_VERSION']
    mayaVersionClean = mayaVersion.split('.')
    sourceAETemplate = ('source "/prod/softprod/apps/houdini/' + houdiniVersion + '/linux/engine/maya/maya' + mayaVersionClean[0] + '/scripts/AEhoudiniAssetTemplate.mel";')
    mel.eval(sourceAETemplate)
    return hdaPath

def create_Hda_Node(hdaPath, hdaName, hdaNodeName):
    cmds = ('houdiniAsset -loadAsset "' + hdaPath + '/' + hdaName + '" "' + hdaNodeName + '";')
    createdNode = mel.eval(cmds)
    return createdNode