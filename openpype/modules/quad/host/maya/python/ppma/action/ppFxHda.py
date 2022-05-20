# -*- coding: utf-8 -*-

import maya.cmds as cmds
import maya.mel as mel
import ppma.core.ppFxHdaLib as ppFxHdaLib


def create_fix_scatter_hda():
    """ define HDA's path """
    hdaName = 'fix_scatter.hda'
    hdaNodeName = 'SideFX::Object/copy'
    infos = ppFxHdaLib.source_Hda_scrtips()

    # integration scripts
    sel = cmds.ls(sl = True)
    growthMesh = sel[0]
    instancerGroup = sel[1]
    createdNode = ppFxHdaLib.create_Hda_Node(infos,hdaName,hdaNodeName)
    cmds.select(sel[0])
    mel.eval('AEhoudiniAssetSetInputToSelection "' + createdNode + '.input[0]";')

    instanceGeoms = cmds.listRelatives(sel[1],c = True)
    chidrenNode = cmds.listRelatives(createdNode,ad = True,f = True)
    
    nParticleNode = ""
    
    for tmp in chidrenNode:
        if cmds.nodeType(tmp) == 'nParticle':
            nParticleNode = tmp
        
    createInstancerCmds = 'particleInstancer -addObject '
           
    for tmp in instanceGeoms:
        createInstancerCmds += '-object  ' + tmp
        
    createInstancerCmds += '-cycle None -cycleStep 1 -cycleStepUnits Frames -levelOfDetail Geometry -rotationUnits Degrees -rotationOrder XYZ -position worldPosition -rotation rotationPP -scale scalePP -objectIndex indexPP -age age ' +  nParticleNode + ';'
    instancerName = mel.eval(createInstancerCmds)
    
    # group parenting
    groupName = cmds.group(em = True)
    cmds.parent(nParticleNode,groupName)
    cmds.parent(instancerName,groupName)
    cmds.parent(createdNode,groupName)

    # renamer
    print "node created"
    cmds.rename(createdNode,'fix_scatter_hda')


def create_fix_pixelizer_hda():
    """ define HDA's path """
    hdaName = 'fix_pixelizer.hda'
    hdaNodeName = 'Object/fix_pixelizer'
    infos = ppFxHdaLib.source_Hda_scrtips()

    sel = cmds.ls(sl = True)
    groupName = cmds.group(em = True)

    for tmp in sel:
        tmpDuplicate = cmds.duplicate(tmp,rr = True)
        tmpBlendShape = cmds.blendShape(tmp,tmpDuplicate[0],o = 'world',tc = 0,w = [(0,1)])
        createdNode = ppFxHdaLib.create_Hda_Node(infos, hdaName, hdaNodeName)
        cmds.select(sel[0])
        mel.eval('AEhoudiniAssetSetInputToSelection "|' + createdNode + '.input[0]";')
        cmds.parent(tmpDuplicate[0],groupName)
        cmds.parent('|' + createdNode,groupName)