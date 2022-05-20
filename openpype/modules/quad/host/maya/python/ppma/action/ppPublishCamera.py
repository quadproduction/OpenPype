# -*- coding: utf-8 -*-

"""
usefull command for camera publish
"""

import maya.cmds as cmds
import maya.mel as mel
import ppma.core.ppScene as ppScene
import ppma.core.ppNode as ppNode
import ppma.core.ppPlugins as ppPlugins
import ppma.core.ppIO as ppIO
import logging
import os
import sys
import sgtk
import fnmatch
from ppSgtkLibs import ppSgtkPublisher

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppma.action.ppPublishCamera')
logger.setLevel(logging.INFO)


class Publish(object):

    """ Publish Camera schema.

    For a Camera:
    # bake camera in worldspace
    ## create new camera
    ## create image plane
    ## contraint new camera
    ## link attribute from source to new (for transform, shape, imageplane)
    ## bake newcamera
    # get current maya scene publish id
    # publish camera as (create dependency for each publish)
    ## maya scene
    ## fbx scene
    ## alembic scene
    """

    def __init__(self):

        """ init class.
        """

        self.defaultPublishName = {
                                        'publishName': {
                                                        'cambaked': 'cambaked',
                                                        'camtrack': 'camtrack'
                                                        },
                                        'camera': 'ppCam',
                                        'imagePlane': 'ppImagePlane'
        }

        self.default_bake_list = {
                            'transform': ["visibility", "translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ"],
                            'camera': ["nearClipPlane", "farClipPlane", "horizontalFilmAperture", "verticalFilmAperture", "focalLength", "lensSqueezeRatio", "preScale", "filmTranslateH", "filmTranslateV", "horizontalRollPivot", "verticalRollPivot", "filmRollValue", "postScale", "filmFitOffset", "horizontalFilmOffset", "verticalFilmOffset"],
                            'imagePlane': ["frameExtension", "type", "frameCache", "frameExtension", "frameOffset", "coverageX", "coverageY", "coverageOriginX", "coverageOriginY", "depth", "squeezeCorrection", "sizeX", "sizeY", "offsetX", "offsetY", "centerX", "centerY", "centerZ", "width", "height", "rotate"]
        }
        # define attr to bake only is anim cuvre is plugged
        self.optional_bake_list = {
                            'transform': [],
                            'camera': ["centerOfInterest", "focusDistance"],
                            'imagePlane': []
        }

        self.additional_bake_list = {
                            'transform': [],
                            'camera': [],
                            'imagePlane': []
        }

        self.publishTypeMayaPluginsMapping = {
                                                'abc': 'AbcExport',
                                                'fbx': 'fbxmaya'
        }

        # Usefull info from Scene
        self.scene = ppScene.Scene()
        self.camera = ppNode.Camera()

        #  init var
        self.newTransform = None
        self.newShape = None
        self.newImagePlane = None
        self.cameraType = 'cambaked'

        self.listAttr = []
        self.handle = 30

        self.system = sys.platform

        # app instance from sgtk
        self._app = None

        # get data
        self.getSceneInfo()

        # Get Export Selection Command
        self.export_selection_cmd = ppIO.ExportSelection()

    def initApp(self, app=None):
        """
        retrieve or set sgtk instance
        :param app: sgtk instancen usually retrieve with sgtk.platform.current_bundle()
        """

        if app:
            self._app = app
        else:
            self._app = sgtk.platform.current_engine()

        if self._app:
            return True
        else:
            return False

    def setHandle(self, handle=30):
        """
        define bake handle
        """
        if handle:
            self.handle = handle

    def getHandle(self):
        """
        retireve handle
        """
        return self.handle

    def getSceneInfo(self):
        """Get Maya Scene Information needed by the ui"""
        self.scene.getAnimationSettings()

    def getCameraTypeAvailable(self):
        """
        this func return the camera type list available for arg.
        """

        return sorted(self.defaultPublishName['publishName'].keys())

    def publish_camera(self, camera=None, maya=True, abc=True, fbx=True, processMode='internal', cameraType='cambaked'):
        """
        publish camera
        :param camera: str camera name
        :param maya:
        :param abc:
        :param fbx:
        :param processMode: 'internal', 'external', 'renderfarm'
        :param cameraType: 'cambaked', 'camtrack', 'camera' use self.getCameraType to get this list.
        """
        # check camera exist:
        if not camera:
            logger.error("Please fill camera arg")
            return False
        else:
            logger.info("Publish Camera: %s / maya:%s, abc:%s, fbx:%s" % (camera, maya, abc, fbx))

        if not self._app:
            self.initApp()

        # get info from camera
        if not self.camera.getDataFromCamera(node=camera):
            logger.error("can't get data from camera: %s" % camera)
            return False

        self.cameraType = cameraType

        if processMode == 'internal':

            cmds.refresh(suspend=True)

            #  bake camera
            try:
                if not self._bake_camera():
                    cmds.refresh(suspend=False)
                    return False
            except RuntimeError, e:
                cmds.refresh(suspend=False)
                logger.error("Publish Error {e}".format(e=e))

            # publish
            try:
                publishTypeList = []
                if maya:
                    publishTypeList.append('ma')
                if abc:
                    publishTypeList.append('abc')
                if fbx:
                    publishTypeList.append('fbx')

                r = self.do_publish(node=self.newTransform, specificVersion=None, publishType=publishTypeList)
                if r:
                    logger.info("Delete camera baked")
                    cmds.delete(self.newTransform)
            except RuntimeError, e:
                cmds.refresh(suspend=False)
                logger.error("Publish Error {e}".format(e=e))

            cmds.refresh(suspend=False)

        if processMode == 'external':
            # export selection in temp file

            # send an external process
            # arg
            pass
        if processMode == 'renderfarm':
            pass

    def _pre_bake_camera(self):
        """
        """

        # set camera renderable
        if self.camera.shape:
            # get renderable value
            if not cmds.getAttr("{cam}.renderable".format(cam=self.camera.shape)):
                # check if lock
                if cmds.lockNode("{cam}.renderable".format(cam=self.camera.shape), query=True, lock=True):
                    # unlock before
                    cmds.lockNode("{cam}.renderable".format(cam=self.camera.shape), lock=False)

                # set renderable
                cmds.setAttr("{cam}.renderable".format(cam=self.camera.shape), 1)

        return True

    def _bake_camera(self):
        """
        """
        # do pre bake before
        self._pre_bake_camera()

        # create new camera
        if not self.createCam():
            logger.error("can't create camera")
            return False

        # create image plane
        if self.camera.imagePlane:
            if not self.createImagePlane():
                logger.error("can't create imagePlane")
                return False

        # camera transform + shape init by self.camera.getDataFromCamera
        # camera newTransform + newShape init by self.camera.getDataFromCamera
        # connectAttributes
        sourceList = [self.camera.transform, self.camera.shape]
        destinationList = [self.newTransform, self.newShape]

        if self.newImagePlane:
            sourceList.append(self.camera.imagePlane)
            destinationList.append(self.newImagePlane)

        # link cameras
        if not self.link_unlink_attributes(source=sourceList, destination=destinationList, mode='connect'):
            return False

        # bake camera
        self.bake_attributes(transform=self.newTransform, camera=self.newShape, imagePlane=self.newImagePlane)

        # unlink camera
        if not self.link_unlink_attributes(source=sourceList, destination=destinationList, mode='disconnect'):
            return False

        self.set_image_attribute(source=sourceList, destination=destinationList)

        return True

    def createCam(self):
        """
        """
        # check if shotCam already exist
        if cmds.objExists(self.defaultPublishName['camera']):
            # rename like
            cmds.rename(self.defaultPublishName['camera'], "%s__renammed_001" % self.defaultPublishName['camera'])

        # create Camera
        camRes = cmds.camera()

        # rename Camera
        self.newTransform = cmds.rename(camRes[0], self.defaultPublishName['camera'])
        self.newShape = cmds.listRelatives(self.newTransform, shapes=True)[0]

        logger.info("New Camera: %s %s" % (self.newTransform, self.newShape))

        return [self.newTransform, self.newShape]

    def createImagePlane(self):
        """
        create image plane
        """
        # check if image plane already exist
        if cmds.objExists(self.defaultPublishName['imagePlane']):
            # rename like
            cmds.rename(self.defaultPublishName['imagePlane'], "%s__renammed_001" % self.defaultPublishName['imagePlane'])

        # since maya 2014 the image plane schema changed
        if int(cmds.about(version=True).split(' ')[0]) == 2012:
            self.newImagePlane = cmds.createNode('imagePlane', name=self.defaultPublishName['imagePlane'])
        else:
            self.newImagePlane = cmds.imagePlane(name=self.defaultPublishName['imagePlane'], camera=self.newShape)[1]

        logger.info("New Image Plane: %s" % self.newImagePlane)

        return self.newImagePlane

    def set_image_attribute(self, source=[], destination=[]):
        for i in range(0, len(source)):
            # Set Image Plane
            if cmds.nodeType(source[i]) == 'imagePlane':
                self.imagePath = cmds.getAttr("%s.imageName" % source[i])
                # set value
                logger.info("Set ImagePath to New Image Plane: {imagePlane}.imageName / {path}".format(imagePlane=destination[i], path=self.imagePath))
                try:
                    cmds.setAttr("%s.imageName" % destination[i], self.imagePath, type="string")
                except Exception:
                    logger.warning("Can't Set ImagePath to New Image Plane: {imagePlane}.imageName / {path}".format(imagePlane=destination[i], path=self.imagePath))

    def link_unlink_attributes(self, source=[], destination=[], mode='connect'):
        """
        this step constraint and link source camera to worldspace camera
        :param source: (list) this list must start with cameraTransform beacause we use it for constraint, usually [transform, shape, imageplane(optional)]
        :param destination: (list) this list must start with cameraTransform beacause we use it for constraint, usually [transform, shape, imageplane(optional)]
        """
        logger.info("mode: %s" % mode)

        # check
        if not source and not destination:
            return False

        # constraint camera
        if mode == 'connect':
            logger.info("Constraint Parent: %s > %s" % (source[0], destination[0]))
            parentConstraint = cmds.parentConstraint(source[0], destination[0])

        # unconstraint camera
        if mode == 'disconnect':
            logger.info("Delete Constraint: %s" % (destination[0]))
            cmds.delete(destination[0], constraints=True)

        logger.info("source: %s" % source)
        logger.info("destination: %s" % destination)

        # link attributes
        for i in range(0, len(source)):

            # connect Attribute from Source to Destination
            listAttr = cmds.listAttr(source[i], settable=True)
            if listAttr:
                self.listAttr.extend(listAttr)

            # remove duplicated name
            self.listAttr = list(set(self.listAttr))
            logger.debug("ListAttr for %s: %s" % (source[i], self.listAttr))

            for attr in self.listAttr:

                # skip attr like translate, rotate, scale, we use constraint for this
                if not fnmatch.fnmatch(attr, "translate*") and not fnmatch.fnmatch(attr, "rotate*") and not fnmatch.fnmatch(attr, "scale*") and not fnmatch.fnmatch(attr, "imageName*"):

                    # Check if attribute exist on destination node
                    if cmds.objExists("%s.%s" % (destination[i], attr)):

                        # check optional attr to bake
                        for key in self.optional_bake_list.keys():
                            if attr in self.optional_bake_list[key]:
                                if cmds.objExists("{node}.{attr}".format(node=source[i], attr=attr)):
                                    if cmds.listConnections("{node}.{attr}".format(node=source[i], attr=attr), source=True, destination=False):
                                        # append to addtional bake list
                                        self.additional_bake_list[key].append(attr)

                        if not cmds.connectionInfo("%s.%s" % (destination[i], attr), isLocked=True):

                            if mode == 'connect':
                                # Try to connect source.attr to distination.attr
                                try:
                                    cmds.connectAttr("%s.%s" % (source[i], attr), "%s.%s" % (destination[i], attr), force=True)
                                    logger.info("{mode} : {source_node}.{source_attr} > {destination_node}.{destination_attr}".format(mode=mode, source_node=source[i], source_attr=attr, destination_node=destination[i], destination_attr=attr))
                                except RuntimeError:
                                    logger.debug("Can't Connect %s.%s to %s.%s" % (source[i], attr, destination[i], attr))
                            if mode == 'disconnect':
                                # Try to disconnect source.attr to distination.attr
                                try:
                                    cmds.disconnectAttr("%s.%s" % (source[i], attr), "%s.%s" % (destination[i], attr))
                                    logger.info("{mode} : {source_node}.{source_attr} > {destination_node}.{destination_attr}".format(mode=mode, source_node=source[i], source_attr=attr, destination_node=destination[i], destination_attr=attr))
                                except RuntimeError:
                                    logger.debug("Can't Connect %s.%s to %s.%s" % (source[i], attr, destination[i], attr))
                    else:
                        logger.debug("Attr '%s' not Exist on Destination Node %s" % (attr, destination[i]))

            # Set Image Plane
            if cmds.nodeType(source[i]) == 'imagePlane' and mode == 'connect':
                self.imagePath = cmds.getAttr("%s.imageName" % source[i])
                # set value
                logger.info("Set ImagePath to New Image Plane: {imagePlane}.imageName / {path}".format(imagePlane=destination[i], path=self.imagePath))
                try:
                    cmds.setAttr("%s.imageName" % destination[i], self.imagePath, type="string")
                except:
                    logger.warning("Can't Set ImagePath to New Image Plane: {imagePlane}.imageName / {path}".format(imagePlane=destination[i], path=self.imagePath))

            # Connect imagePlane and Camera
            if cmds.nodeType(source[i]) == 'imagePlane' and self.newImagePlane and mode == 'disconnect':
                try:
                    cmds.connectAttr("%s.message" % self.newImagePlane, "%s.imagePlane" % self.newShape)
                except:
                    logger.warning("Can't Connect Image Plane to Camera")

        # return
        return True

    def bake_attributes(self, transform=None, camera=None, imagePlane=None):
        """
        bake attribute for
        """
        logger.info("Bake")
        self.attr_list = []

        # we don't want to bake all attributes
        # so we build a shapAttribute list
        bakeDict = {}
        if transform:
            bakeDict[transform] = self.default_bake_list['transform']

        if camera:
            bakeDict[camera] = self.default_bake_list['camera']

        if imagePlane:
            bakeDict[imagePlane] = self.default_bake_list['imagePlane']

        for node in bakeDict.keys():
            for attr in bakeDict[node]:
                if cmds.objExists("%s.%s" % (node, attr)):
                    self.attr_list.append("%s.%s" % (node, attr))

        # special case if this attr list is animated, if not we do nothing.
        for key in self.additional_bake_list.keys():
            add_attr = False
            node = None
            if key == "transform" and transform:
                add_attr = True
                node = transform
            if key == "camera" and camera:
                add_attr = True
                node = camera
            if key == "imagePlane" and imagePlane:
                add_attr = True
                node = imagePlane
            if add_attr:
                for attr in self.additional_bake_list[key]:
                    # add attr to bake list
                    self.attr_list.append("%s.%s" % (node, attr))

        #check start / end
        if not self.scene.minTime or self.scene.maxTime:
            self.getSceneInfo()

        #if not batch mode desactive
        # bake only this selection
        logger.info("Bake list : %s" % sorted(self.attr_list))
        cmds.bakeResults(self.attr_list, time=(self.scene.minTime-self.handle, self.scene.maxTime+self.handle), simulation=True, sampleBy=1)

        # Get Rotate AnimCurve connected to Camera and apply Euler Filter
        rotateCameraAnimCurveList = []
        for attr in ["rotateX", "rotateY", "rotateZ"]:

            # Get animCurve
            cons = cmds.listConnections("%s.%s" % (transform, attr), destination=False, source=True)
            if cons:
                for con in cons:
                    if cmds.nodeType(con) == "animCurveTA":
                        rotateCameraAnimCurveList.append(con)

        logger.info("Apply Euler Filter on animCurve")
        cmds.filterCurve(rotateCameraAnimCurveList)

    def do_publish(self, node=None, specificVersion=None, publishType=['ma', 'abc', 'fbx']):
        """
        select the camera and publish it.
        :param node: camera node. default=None if not specify we try to get name from self.newTransform
        :param specificVersion: specify a number version
        """
        publishNode = node
        if not publishNode:
            publishNode = self.newTransform

        if not self.newTransform:
            logger.info("No Camera found, please specify camera in arg node.")
            return False

        if not self._app:
            self.initApp(app=self._app)

        # load maya plugins / it takes some so we need to do this before.
        for pbType in publishType:

            if pbType in self.publishTypeMayaPluginsMapping.keys():

                # Load plugins fbxmaya
                pluginName = self.publishTypeMayaPluginsMapping[pbType]
                res = ppPlugins.loadPlugins(pluginNameList=[pluginName])
                if not res[pluginName]['loaded']:
                    logger.error("Can't Load plugins %s" % pluginName)
                    return False

        # store previous in file_type we have already publish a camera.
        previousPublishVersion = None
        publishResult = {}
        file_type = "camera_file"
        for pbType in publishType:
            logger.info("Publish: %s / node: %s" % (pbType, publishNode))

            # set comment
            publish_comment = "%s - Auto Camera Publish\n" % (pbType)
            publish_comment += "-----------\n"
            # add information about in and out
            publish_comment += "in out with handles\n{inHandles} - {outHandles} / length : {length}\n".format(inHandles=self.scene.minTime-self.handle, outHandles=self.scene.maxTime+self.handle, length=(self.scene.maxTime+self.handle) - (self.scene.minTime-self.handle)+1)
            publish_comment += "-----------\n"
            publish_comment += "details\n"
            publish_comment += "in out timeslider\n{minTime} - {maxTime} / length : {length}\n".format(minTime=self.scene.minTime, maxTime=self.scene.maxTime, length=self.scene.maxTime-self.scene.minTime+1)
            publish_comment += "handles : {handles}".format(handles=self.handle)

            path_result = None

            if pbType == 'ma':
                # export selection as ma file
                path_result = self.export_selection_cmd._export_ma(selection=self.newTransform, path=None, file_type=file_type)

            elif pbType == 'fbx':
                # export selection as ma file
                path_result = self.export_selection_cmd._export_fbx(selection=self.newTransform, path=None, file_type=file_type)

            elif pbType == 'abc':
                # export selection as ma file
                path_result = self.export_selection_cmd._export_abc(selection=self.newTransform, path=None, handle=self.handle, file_type=file_type)

            # check path result
            if not path_result:
                logger.error("Couldn't publish, the local file to publish not exist %s: %s" % (pbType, path_result))
                return False

            else:
                # build publish arg
                publishArgs = {
                                    'project': self._app.sgtk.roots['primary'],
                                    'filePath': path_result,
                                    'fileType': file_type,
                                    'linkType': self._app.context.entity['type'],
                                    'linkName': self._app.context.entity['name'],
                                    'publishName': "%s%s" % (self.defaultPublishName['publishName'][self.cameraType], pbType.capitalize()),
                                    'stepName': self._app.context.step['name'],
                                    'taskName': self._app.context.task['name'],
                                    'comment': publish_comment,
                                    'dependencies': [],
                                    'version': None,
                                    'sg_additional_fields': {'sg_status_list': 'apr'}
                                }

                # if previous publish done, we use his version_number to have ma, abc, fbx with the same version number.
                if previousPublishVersion:
                    publishArgs['version'] = previousPublishVersion

                logger.info("Do Publish: %s" % path_result)
                logger.info("Publish Args: %s" % publishArgs)

                # do publish scene
                publishResultId = ppSgtkPublisher.publishFile(project=publishArgs['project'], filePath=publishArgs['filePath'], fileType=publishArgs['fileType'], linkType=publishArgs['linkType'], linkName=publishArgs['linkName'], publishName=publishArgs['publishName'], stepName=publishArgs['stepName'], taskName=publishArgs['taskName'], comment=publishArgs['comment'], dependencies=publishArgs['dependencies'], version=publishArgs['version'], sg_additional_fields=publishArgs['sg_additional_fields'])
                logger.info("Published Result %s: %s" % (pbType, publishResultId))

                if not publishResultId:
                    logger.error("No File Published")
                    return False
                else:
                    publishResult[pbType] = publishResultId

                if 'version_number' in publishResultId.keys():
                    previousPublishVersion = publishResultId["version_number"]
                # Published Result exemple ma: {'version_number': 1, 'task': {'type': 'Task', 'id': 29963, 'name': 'previz'}, 'description': 'Camera Publish', 'type': 'PublishedFile', 'published_file_type': {'type': 'PublishedFileType', 'id': 12, 'name': 'Camera file'}, 'created_by': {'type': 'HumanUser', 'id': 40, 'name': 'Marc Dubrois'}, 'entity': {'type': 'Shot', 'id': 16794, 'name': '800_0001'}, 'project': {'type': 'Project', 'id': 726, 'name': 'HOTSPOT_OPTIMUM_SAISON3_14_182'}, 'code': '800_0001_previz_camera_v001.ma', 'path': {'local_path_windows': 'c:\\prod\\project\\HOTSPOT_OPTIMUM_SAISON3_14_182\\sequences\\800\\800_0001\\previz\\publish\\camera\\800_0001_previz_camera_v001.ma', 'name': '800_0001_previz_camera_v001.ma', 'local_path_linux': '/prod/project/HOTSPOT_OPTIMUM_SAISON3_14_182/sequences/800/800_0001/previz/publish/camera/800_0001_previz_camera_v001.ma', 'url': 'file://c:\\prod\\project\\HOTSPOT_OPTIMUM_SAISON3_14_182\\sequences\\800\\800_0001\\previz\\publish\\camera\\800_0001_previz_camera_v001.ma', 'local_storage': {'type': 'LocalStorage', 'id': 11, 'name': 'primary'}, 'local_path': 'c:\\prod\\project\\HOTSPOT_OPTIMUM_SAISON3_14_182\\sequences\\800\\800_0001\\previz\\publish\\camera\\800_0001_previz_camera_v001.ma', 'content_type': None, 'local_path_mac': '/prod/project/HOTSPOT_OPTIMUM_SAISON3_14_182/sequences/800/800_0001/previz/publish/camera/800_0001_previz_camera_v001.ma', 'type': 'Attachment', 'id': 52253, 'link_type': 'local'}, 'path_cache': 'HOTSPOT_OPTIMUM_SAISON3_14_182/sequences/800/800_0001/previz/publish/camera/800_0001_previz_camera_v001.ma', 'id': 3193, 'name': 'camera'} #

        return publishResult


def publishSelectedCamera(maya=True, abc=True, fbx=True, processMode='internal', cameraType='cambaked', c4d=False):
    """ publish the selected camera """
    res = cmds.ls(sl=True)
    # Gwilherm Monin 30-04-2019 :: Rotation -90 pour Cinema 4D
    if not res:
        return
    elif c4d:
        cmds.setAttr('%s.rotateAxisY' % res[0], -90)

    publishCamera(camera=res[0], maya=maya, abc=abc, fbx=fbx, processMode=processMode, cameraType=cameraType)

    if c4d:
        cmds.setAttr('%s.rotateAxisY' % res[0], 0)


def publishCamera(camera=None, maya=True, abc=True, fbx=True, processMode='internal', cameraType='cambaked'):
    """ publish camera
    :param camera:None
    :param maya=True
    :param abc=True
    :param fbx=True
    :param processMode='internal'
    :param cameraType: cambaked or camtrack or camera
    """

    p = Publish()
    p.publish_camera(camera=camera, maya=maya, abc=abc, fbx=fbx, processMode=processMode, cameraType=cameraType)
