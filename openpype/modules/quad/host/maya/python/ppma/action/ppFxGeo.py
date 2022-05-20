# -*- coding: utf-8 -*-

import maya.cmds as cmds
import maya.mel as mel
import ppma.core.ppFxGeoLib as ppFxGeoLib

"""create follicles from selection"""


def averagePointArray(listPoint):
    averagePosX = 0.0
    averagePosY = 0.0
    averagePosZ = 0.0
    
    for i in range(0, len(listPoint), 1):
        averagePosX = averagePosX + listPoint[i][0]
        averagePosY = averagePosY + listPoint[i][1]
        averagePosZ = averagePosZ + listPoint[i][2]
        
    centroidPointX = averagePosX / len(listPoint)
    centroidPointY = averagePosY / len(listPoint)
    centroidPointZ = averagePosZ / len(listPoint)
    
    centroidPoint = [centroidPointX, centroidPointY, centroidPointZ]
    return centroidPoint
    

def addFollicleOnsurface(object, listOfPositions):
    for pos in listOfPositions:
        posTmp = ppFxGeoLib.getClosestPoint(object, pos)
        UV = ppFxGeoLib.getUVAtPoint(object, posTmp, 'map1')
                                                                                                                         
        folShape = cmds.createNode('follicle')
        folTranform = cmds.listRelatives(folShape, p=1)
        
        objectShape = cmds.listRelatives(object, s=1)

        cmds.setAttr(folShape + '.parameterU', UV[0])
        cmds.setAttr(folShape + '.parameterV', UV[1])

        cmds.connectAttr((objectShape[0] + '.outMesh'), (folShape + '.inputMesh'))
        cmds.connectAttr((objectShape[0] + '.worldMatrix[0]'), (folShape + '.inputWorldMatrix'))

        cmds.connectAttr((folShape + '.outTranslate'), (folTranform[0] + '.translate'))
        cmds.connectAttr((folShape + '.outRotate'), (folTranform[0] + '.rotate'))


def createFollicleFromVertex():
    """convert selection to vertex"""
    cmd = 'PolySelectConvert 3'
    mel.eval(cmd)
    sel = cmds.ls(sl=1, fl=1)
    posArray = []
    
    if(len(sel) > 0):
        for tmp in sel:
            pos = cmds.xform(tmp, q=1, ws=1, t=1)
            posArray.append((pos[0], pos[1], pos[2]))
        
        centroidpos = []
        centroidpos.append(averagePointArray(posArray))
        tmp = sel[0].split('.')
        object = tmp[0]
        
        addFollicleOnsurface(object, centroidpos)
        
    else:
        
        print 'select vertex, edges or faces of an object'
