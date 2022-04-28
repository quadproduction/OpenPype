# -*- coding: utf-8 -*-

import sys

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMayaRender as OpenMayaRender
import maya.OpenMayaUI as OpenMayaUI


# init node info
nodeType = "ppCameraPlaneShape"
nodeId = OpenMaya.MTypeId(0x870484)

glRenderer = OpenMayaRender.MHardwareRenderer.theRenderer()
glFT = glRenderer.glFunctionTable()


class ppCameraPlaneShape(OpenMayaMPx.MPxLocatorNode):
    """ ppCameraPlaneShape Class
    """
    a_camera_matrix = OpenMaya.MObject()
    a_horizontal_aperture = OpenMaya.MObject()
    a_vertical_aperture = OpenMaya.MObject()
    a_focal_length = OpenMaya.MObject()
    a_fStop = OpenMaya.MObject()
    a_focus_distance = OpenMaya.MObject()
    a_plane_opacity = OpenMaya.MObject()
    a_focus_range_scale = OpenMaya.MObject()

    a_horizontal_film_offset = OpenMaya.MObject()
    a_vertical_film_offset = OpenMaya.MObject()

    def __init__(self):
        """ ppCameraPlaneShape class constructor
        """
        OpenMayaMPx.MPxLocatorNode.__init__(self)

    def compute(self, plug, dataBlock):
        return OpenMaya.kUnknownParameter

    def draw(self, view, path, style, status):

        thisNode = self.thisMObject()

        # ---
        # get attr from node
        # horizontal_film_offset
        plug = OpenMaya.MPlug(thisNode, self.a_horizontal_film_offset)
        horizontal_film_offset = plug.asDouble()

        # vertical_film_offset
        plug = OpenMaya.MPlug(thisNode, self.a_vertical_film_offset)
        vertical_film_offset = plug.asDouble()

        # camera matrix
        plug = OpenMaya.MPlug(thisNode, self.a_camera_matrix)
        omat = plug.asMObject()
        dmat = OpenMaya.MFnMatrixData(omat)
        camera_matrix = OpenMaya.MMatrix()
        camera_matrix = dmat.matrix()

        # fStop
        plug = OpenMaya.MPlug(thisNode, self.a_fStop)
        fStop = plug.asDouble()

        # focus distance
        plug = OpenMaya.MPlug(thisNode, self.a_focus_distance)
        focus_distance = plug.asDouble()

        # horizontal aperture
        plug = OpenMaya.MPlug(thisNode, self.a_horizontal_aperture)
        horizontal_aperture = plug.asDouble()
        # vertical aperture
        plug = OpenMaya.MPlug(thisNode, self.a_vertical_aperture)
        vertical_aperture = plug.asDouble()

        # focal length
        plug = OpenMaya.MPlug(thisNode, self.a_focal_length)
        focal_length = plug.asDouble()

        # OPACITY
        plug = OpenMaya.MPlug(thisNode, self.a_plane_opacity)
        plane_opacity = plug.asDouble()

        # focus range scale
        plug = OpenMaya.MPlug(thisNode, self.a_focus_range_scale)
        focus_range_scale = plug.asDouble()

        # horizontal and vertical field of view
        horizontal_field_of_view = horizontal_aperture * 0.5 / (focal_length * 0.03937)
        vertical_field_of_view = vertical_aperture * 0.5 / (focal_length * 0.03937)

        # set circle of confusion value
        circle_of_confusion = 0.0298
        # ---
        # calculate hyperfocale
        hyperfocale = (focal_length*focal_length) / (fStop*circle_of_confusion)

        # ---
        # calculate depth of field
        # ---
        # DOF = 2NcffDD / f.exp(4) - NNcc DD
        # f = focale mm
        # N = ouverture du diaphragme = fStop
        # c = cercle de confusion. 0,0298

        # ---
        # Approximation
        # DOF = 2NcDD / ff
        # depth_of_field = (2.0 * fStop * circle_of_confusion * (focus_distance * focus_distance)) / (focal_length * focal_length)

        # calculate near focus distance
        near_focus_distance = (hyperfocale * focus_distance) / (hyperfocale + focus_distance)
        near_focus_distance = focus_distance - ((focus_distance - near_focus_distance) * focus_range_scale)

        # calculate far focus distance
        far_focus_distance = 0
        if focus_distance >= hyperfocale:
            far_focus_distance = hyperfocale
        else:
            far_focus_distance = (hyperfocale * focus_distance) / (hyperfocale - focus_distance)
            far_focus_distance = focus_distance + ((far_focus_distance - focus_distance) * focus_range_scale)
        # ---
        # set data focus and color for plane
        focus_data = {
            "focus_distance": focus_distance,
            "rgba": [1.0, 1.0, 1.0, 1.0]
        }
        near_focus_data = {
            "focus_distance": near_focus_distance,
            "rgba": [1.0, 1.0, 0.0, 1.0]
        }
        # far focus data
        far_focus_data = {
            "focus_distance": far_focus_distance,
            "rgba": [0.0, 0.0, 1.0, 1.0]
        }
        if focus_distance >= hyperfocale:
            far_focus_data["rgba"] = [0.5, 0.0, 1.0, 1.0]

        # define plane list
        plane_list = [
            focus_data,
            near_focus_data,
            far_focus_data
        ]

        for data in plane_list:

            distance = data.get("focus_distance")
            r = data.get("rgba")[0]
            g = data.get("rgba")[1]
            b = data.get("rgba")[2]
            a = data.get("rgba")[3]

            # calc film offset
            horizontal_film_offset_length = (horizontal_film_offset / (focal_length * 0.03937)) * distance
            vertical_film_offset_length = (vertical_film_offset / (focal_length * 0.03937)) * distance

            # calculate max right point and max top point
            right = distance * horizontal_field_of_view
            top = distance * vertical_field_of_view

            # corners list
            # a b
            # c d
            corner_a = OpenMaya.MPoint(-right + horizontal_film_offset_length, top + vertical_film_offset_length, -distance)
            corner_a *= camera_matrix
            corner_b = OpenMaya.MPoint(right + horizontal_film_offset_length, top + vertical_film_offset_length, -distance)
            corner_b *= camera_matrix
            corner_c = OpenMaya.MPoint(right + horizontal_film_offset_length, -top + vertical_film_offset_length, -distance)
            corner_c *= camera_matrix
            corner_d = OpenMaya.MPoint(-right + horizontal_film_offset_length, -top + vertical_film_offset_length, -distance)
            corner_d *= camera_matrix

            corner_list = [corner_a, corner_d, corner_c, corner_b, corner_a]

            # ---
            # START OPEN GL
            view.beginGL()

            # ---
            # setup openGL
            glFT.glPushAttrib(OpenMayaRender.MGL_ALL_ATTRIB_BITS)
            glFT.glClearDepth(1.0)
            glFT.glEnable(OpenMayaRender.MGL_BLEND)
            glFT.glEnable(OpenMayaRender.MGL_DEPTH_TEST)
            glFT.glDepthFunc(OpenMayaRender.MGL_LEQUAL)
            glFT.glShadeModel(OpenMayaRender.MGL_SMOOTH)
            glFT.glBlendFunc(OpenMayaRender.MGL_SRC_ALPHA, OpenMayaRender.MGL_ONE_MINUS_SRC_ALPHA)
            glFT.glDepthMask(OpenMayaRender.MGL_FALSE)
            glFT.glColor4f(r, g, b, a * plane_opacity)

            # draw MGL_POLYGON
            glFT.glBegin(OpenMayaRender.MGL_POLYGON)
            for i in range(len(corner_list)-1):
                glFT.glVertex3f(corner_list[i].x,  corner_list[i].y,  corner_list[i].z)
                glFT.glVertex3f(corner_list[i+1].x,  corner_list[i+1].y,  corner_list[i+1].z)
            glFT.glEnd()
            glFT.glPopAttrib()

            # setup openGL for draw line
            glFT.glBegin(OpenMayaRender.MGL_LINES)

            if status == OpenMayaUI.M3dView.kDormant:
                glFT.glColor3f(1.0, 0.0, 0.0)

            # draw border line
            for i in range(len(corner_list)-1):
                glFT.glVertex3f(corner_list[i].x,  corner_list[i].y,  corner_list[i].z)
                glFT.glVertex3f(corner_list[i+1].x, corner_list[i+1].y, corner_list[i+1].z)
            glFT.glEnd()

            view.endGL()

    def isBounded(self):
        return False

    def drawLast(self):
        return True

    def excludeAsLocator(self):
        return True

    def isTranparent(self):
        return True


# creator
def nodeCreator():
    return OpenMayaMPx.asMPxPtr(ppCameraPlaneShape())


# initializer
def nodeInitializer():
    matAttr = OpenMaya.MFnTypedAttribute()
    ppCameraPlaneShape.a_camera_matrix = matAttr.create("cameraMatrix", "cm", OpenMaya.MFnData.kMatrix)
    matAttr.setConnectable(True)
    ppCameraPlaneShape.addAttribute(ppCameraPlaneShape.a_camera_matrix)

    numAttr = OpenMaya.MFnNumericAttribute()
    ppCameraPlaneShape.a_fStop = numAttr.create("fStop", "fs", OpenMaya.MFnNumericData.kDouble, 6.7)
    numAttr.setConnectable(True)
    numAttr.setStorable(True)
    numAttr.setChannelBox(True)
    ppCameraPlaneShape.addAttribute(ppCameraPlaneShape.a_fStop)

    numAttr = OpenMaya.MFnNumericAttribute()
    ppCameraPlaneShape.a_focus_distance = numAttr.create("focusDistance", "fd", OpenMaya.MFnNumericData.kDouble, 6.7)
    numAttr.setConnectable(True)
    numAttr.setStorable(True)
    numAttr.setChannelBox(True)
    ppCameraPlaneShape.addAttribute(ppCameraPlaneShape.a_focus_distance)

    numAttr = OpenMaya.MFnNumericAttribute()
    ppCameraPlaneShape.a_horizontal_aperture = numAttr.create("horizontalFilmAperture", "hfa", OpenMaya.MFnNumericData.kDouble)
    numAttr.setConnectable(True)
    ppCameraPlaneShape.addAttribute(ppCameraPlaneShape.a_horizontal_aperture)

    numAttr = OpenMaya.MFnNumericAttribute()
    ppCameraPlaneShape.a_vertical_aperture = numAttr.create("verticalFilmAperture", "vfa", OpenMaya.MFnNumericData.kDouble)
    numAttr.setConnectable(True)
    ppCameraPlaneShape.addAttribute(ppCameraPlaneShape.a_vertical_aperture)

    numAttr = OpenMaya.MFnNumericAttribute()
    ppCameraPlaneShape.a_horizontal_film_offset = numAttr.create("horizontalFilmOffset", "hfo", OpenMaya.MFnNumericData.kDouble)
    numAttr.setConnectable(True)
    ppCameraPlaneShape.addAttribute(ppCameraPlaneShape.a_horizontal_film_offset)

    numAttr = OpenMaya.MFnNumericAttribute()
    ppCameraPlaneShape.a_vertical_film_offset = numAttr.create("verticalFilmOffset", "vfo", OpenMaya.MFnNumericData.kDouble)
    numAttr.setConnectable(True)
    ppCameraPlaneShape.addAttribute(ppCameraPlaneShape.a_vertical_film_offset)

    numAttr = OpenMaya.MFnNumericAttribute()
    ppCameraPlaneShape.a_focal_length = numAttr.create("focalLength", "fl", OpenMaya.MFnNumericData.kDouble, 1.0)
    numAttr.setConnectable(True)
    ppCameraPlaneShape.addAttribute(ppCameraPlaneShape.a_focal_length)

    numAttr = OpenMaya.MFnNumericAttribute()
    ppCameraPlaneShape.a_plane_opacity = numAttr.create("planeOpacity", "po", OpenMaya.MFnNumericData.kDouble, 0.5)
    numAttr.setStorable(True)
    numAttr.setKeyable(True)
    ppCameraPlaneShape.addAttribute(ppCameraPlaneShape.a_plane_opacity)

    numAttr = OpenMaya.MFnNumericAttribute()
    ppCameraPlaneShape.a_focus_range_scale = numAttr.create("focusRangeScale", "frs", OpenMaya.MFnNumericData.kDouble, 10.0)
    numAttr.setStorable(True)
    numAttr.setKeyable(True)
    ppCameraPlaneShape.addAttribute(ppCameraPlaneShape.a_focus_range_scale)

# initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject, "pp", "1.0", "Any")
    try:
        mplugin.registerNode(nodeType, nodeId, nodeCreator, nodeInitializer, OpenMayaMPx.MPxNode.kLocatorNode)
    except:
        sys.stderr.write("Failed to register node: %s" % nodeType)


# uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode(nodeId)
    except:
        sys.stderr.write("Failed to deregister node: %s" % nodeType)


def connect_ppCameraPlane(camera_node):
    """This function connect properly to the provided camera_node a ppCameraPlaneShape.

    :param camera_node: the camera shape name.
    :type camera_node: str.
    :returns:  str -- the created ppCameraPlaneShape.
    :raises: AttributeError, KeyError
    """
    try:
        cmds.loadPlugin("ppCameraPlane")
    except:
        pass

    camera_plane_shape = cmds.createNode("ppCameraPlaneShape")

    # do connections between camera and ppCameraPlaneShape
    connection_list = [
        {"source": "worldMatrix", "destination": "cameraMatrix", "force": True},
        {"source": "focalLength", "destination": "focalLength", "force": True},
        {"source": "fStop", "destination": "fStop", "force": True},
        {"source": "focusDistance", "destination": "focusDistance", "force": True},
        {"source": "cameraAperture.horizontalFilmAperture", "destination": "horizontalFilmAperture", "force": True},
        {"source": "cameraAperture.verticalFilmAperture", "destination": "verticalFilmAperture", "force": True},
        {"source": "filmOffset.horizontalFilmOffset", "destination": "horizontalFilmOffset", "force": True},
        {"source": "filmOffset.verticalFilmOffset", "destination": "verticalFilmOffset", "force": True}
    ]

    for connection in connection_list:
        # connect world_matrix
        cmds.connectAttr(
            "{n}.{source}".format(n=camera_node, source=connection.get("source")),
            "{cps}.{destination}".format(cps=camera_plane_shape, destination=connection.get("destination")),
            force=connection.get("force")
        )

    return camera_plane_shape


def connect_to_selected_camera():
    """This function connect a ppCameraPlane to the selected camera."""

    # get selection
    sel = cmds.ls(sl=True)

    for n in sel:

        # check if it's a transform or a camera
        if cmds.nodeType(n) == "camera":
            connect_ppCameraPlane(camera_node=n)
        elif cmds.nodeType(n) == "transform":
            # try to retrieve a camera shape as a child
            r = cmds.listRelatives(n, allDescendents=True, type="camera")
            if r:
                connect_ppCameraPlane(camera_node=r[0])
