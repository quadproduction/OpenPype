# -*- coding: utf-8 -*-

import maya.OpenMaya as cmds

"""convert node name to dagPath"""


def nameToDag(name):
	sel = cmds.MSelectionList()
	sel.add(name)
	node = cmds.MDagPath()
	sel.getDagPath(0,node)
	return node

"""
get mesh infos
----------------------------------------------------
"""

def getClosestPoint(object,pos):
	point = cmds.MPoint(pos[0],pos[1],pos[2])
	meshFn = cmds.MFnMesh(nameToDag(object))
	closestPoint = cmds.MPoint()
	meshFn.getClosestPoint(point,closestPoint,cmds.MSpace.kWorld)
	Position = [closestPoint[0],closestPoint[1],closestPoint[2]]
	return Position

def getClosestNormal(object,pos):
	point = cmds.MPoint(pos[0],pos[1],pos[2])
	meshFn = cmds.MFnMesh(nameToDag(object))
	closestNormal = cmds.MVector()
	meshFn.getClosestNormal(point,closestNormal,cmds.MSpace.kWorld)
	Normal = cmds.MVector(closestNormal[0],closestNormal[1],closestNormal[2])
	return Normal

def getUVAtPoint(object,pos,UVSet):
	point = cmds.MPoint(pos[0],pos[1],pos[2])
	meshFn = cmds.MFnMesh(nameToDag(object))
	MSUtil = cmds.MScriptUtil()
	MSUtil.createFromList([0.0, 0.0], 2)
	uvPoint = MSUtil.asFloat2Ptr()
	meshFn.getUVAtPoint(point,uvPoint,cmds.MSpace.kWorld,UVSet)
	uv0 = cmds.MScriptUtil.getFloat2ArrayItem(uvPoint,0,0)
	uv1 = cmds.MScriptUtil.getFloat2ArrayItem(uvPoint,0,1)
	return [uv0,uv1]

def closestIntersectionPoint(object,posSource,rayDir,maxParam):
    raySource = cmds.MFloatPoint(posSource[0],posSource[1],posSource[2]) 
    rayDirection = cmds.MFloatVector(rayDir[0],rayDir[1],rayDir[2]) 
    mfnMesh = cmds.MFnMesh(nameToDag(object))
    sortIds = False
    maxDist = maxParam
    bothDirections = False
    noFaceIds = None
    noTriangleIds = None
    noAccelerator = None
    noHitParam = None
    noHitFace = None
    noHitTriangle = None
    noHitBary1 = None
    noHitBary2 = None 
    space = cmds.MSpace.kWorld
    toleran = 0.000001     
    hitPoint = cmds.MFloatPoint()
    Hit = mfnMesh.closestIntersection(raySource,rayDirection,noFaceIds,noTriangleIds,sortIds,space,maxDist,bothDirections,noAccelerator,hitPoint,noHitParam,noHitFace,noHitTriangle,noHitBary1,noHitBary2)
    return [hitPoint[0],hitPoint[1],hitPoint[2]]

def closestFaceIntersection(object,posSource,rayDir,maxParam):
    raySource = cmds.MFloatPoint(posSource[0],posSource[1],posSource[2]) 
    rayDirection = cmds.MFloatVector(rayDir[0],rayDir[1],rayDir[2]) 
    mfnMesh = cmds.MFnMesh(nameToDag(object))
    sortIds = False

def getMeshVertexInfo(object,space):
	dagObject = nameToDag(object)
	
	obj = cmds.MFnMesh(dagObject)
	
	vertexArray = cmds.MFloatPointArray()
	polyCounts = cmds.MIntArray()
	polyConnects = cmds.MIntArray()
	
	vertexNumber = obj.numVertices()
	polygonNumbers = obj.numPolygons()
	obj.getPoints(vertexArray,space)
	obj.getVertices(polyCounts,polyConnects)
	
	return vertexNumber,polygonNumbers,vertexArray,polyCounts,polyConnects


def getVertexList():
    selection = cmds.MSelectionList()
    cmds.MGlobal.getActiveSelectionList( selection );
    iter = cmds.MItSelectionList ( selection, cmds.MFn.kGecmdsetric );
    
    while not iter.isDone():
    
            vertexListTmp = []
            polyList = []
    
            dagPath = cmds.MDagPath()
            iter.getDagPath(dagPath)
    
            mObj = cmds.MObject()
            iter.getDependNode( mObj )
    
            iterPolys = cmds.MItMeshPolygon( mObj )
    
            while not iterPolys.isDone():
    
                    polyList.append (iterPolys.index())     
    
                    verts = cmds.MIntArray()
                    iterPolys.getVertices( verts )
    
                    for i in range( verts.length() ):
                            vertexListTmp.append (verts[i])
    
                    iterPolys.next()
    
            iter.next()
            
    vertexList = sorted(list(set(vertexListTmp)))
            
    return vertexList



"""
get volumes infos
----------------------------------------------------
"""

def BBVolume(object):

    bb = mc.xform(object,bb = True,q =True)
    X = bb[3] - bb[0]
    Y = bb[4] - bb[1]
    Z = bb[5] - bb[2]
    volume = X * Y * Z
    
    return volume



"""
get curves infos
----------------------------------------------------
"""

def getClosestPointOnCurve(object,pos):

    point = cmds.MPoint(pos[0],pos[2],pos[2])
    curveFn = cmds.MFnNurbsCurve(nameToDag(object))
    result  = cmds.MPoint()

    p = cmds.MScriptUtil()
    pointer = p.asDoublePtr()
    cmds.MScriptUtil.setDouble (pointer, 0.0)
    
    result = curveFn.closestPoint (point, pointer, 0.0,cmds.MSpace.kWorld)
    return result

