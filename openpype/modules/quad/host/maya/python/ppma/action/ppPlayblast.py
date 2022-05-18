# -*- coding: utf-8 -*-

"""
common classes and functions about playblast in maya
"""

__version__ = "1.1.0"

import maya.cmds as cmds
import ppma.core.ppScene
import ppma.core.ppNode
import ppma.core.ppUi
import logging
import os
import sys
import sgtk
from tank_vendor import yaml
import time
import shutil
from tank import TankError
import subprocess
from ppSgtkLibs import ppSgtkPublisher

import ppma.core.ppSceneManagement as ppSceneManagement
import ppma.core.ppActions as ppActions
import ppSgtkLibs.ppSgtkCmds as ppSgtkCmds

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppma.action.ppPlayblast')
logger.setLevel(logging.INFO)

class Playblast(object):

    """ Playblast schema below.

------------------
Schema
------------------
init
-> get_sceneInfo # get animation range
-> get_cameras # get all cameras available
-> getHud # get hud available from module ppma.core.ppUi
-> get_sound # get timeslider's sound + sound offset
-> getPlayblastConfigNode # get settings from scene
-> getLocalPlayblast # scan disk structure for find previous playblast

set camera playblastable and range
-> update self.cameras[camera]['playblast'] = True
set display

set visibility
-> update self.settings['display'][key] = value

set cameraDisplay
-> update self.settings['cameraDisplay'][key] = value

set hud
-> update hud visibility self.settings['hud'][key] = value

do playblast
-> create playblast view
-> custom playblast view
-> create local folder
-> save scene locally
-> setup playblast render size
-> for each camera
--> do playblast
--> renumber frame if needed
--> create yml file wich store sound info likek soundPath & soundOffset
--> update local playblast info
-> write publish package file # usefull

view playblast
-> get previous and next Shot
-> build rv command
-> push rv command

publish playblast
-> publish local maya scene
--> update local yml dependant to this mayascene with sgtk mayascene id
-> if sound not yet published
--> publish sound
--> update local yml dependant to this sound with sgtk mayascene id
-> publish image sequence
--> link image sequence to mayascene + sound

"""

    def __init__(self):
        super(Playblast, self).__init__()

        """ init class.
        """

        self.action = ppActions.Action()

        # Usefull info from Scene
        self.sgCmds = ppSgtkCmds.Cmds()
        self.scene = ppma.core.ppScene.Scene()
        self.cams = ppma.core.ppNode.Camera()
        self.snds = ppma.core.ppNode.Sound()
        self.pbcn = PlayblastConfigNode()
        self.pl = None

        # app instance from sgtk
        self._app = None

        # init hud
        self.hud = ppma.core.ppUi.Hud()

        # init player path configuration
        self.playerPath = {
            'player': None,
            'push': None
        }

        # Define Playblast Settings
        self.engine = {
            "default": "real-time",
            "highQuality": "real-time",
            "viewport2":
            "real-time",
            "mayaSoftware": "offline"} # "mentalRay":"offline"

        self.settings = {
            "resolution": {
                "width": 1280,
                "height": 720,
                "pixelAspectRatio": 1.0
            },
            "renderer": {
                "engine":{
                    "default": "default",
                    "list": sorted(self.engine.keys())}
            },
            "renderDisplay": {
                "displayTextures": False,
                "displayAppearance": {
                    "default": "smoothShaded",
                    "list": [
                        "wireframe",
                        "points",
                        "boundingBox",
                        "smoothShaded",
                        "flatShaded"]
                },
                "displayLights": {
                    "default": "default",
                    "list": [
                        "selected",
                        "active",
                        "all",
                        "default",
                        "none"
                    ]
                },
                "shadows": False
            },
            "cameraDisplay": {
                "displayFilmGate": False,
                "displayResolution": True,
                "displayGateMask": True,
                "displayGateMaskOpacity": 1,
                "displayGateMaskColor": [(0, 0, 0)],
                "displayFieldChart": False,
                "displaySafeAction": True,
                "displaySafeTitle": False,
                "displayFilmPivot": False,
                "displayFilmOrigin": False,
                "overscan": 1.0,
            },
            "viewDisplay": {
                "nurbsCurves": False,
                "nurbsSurfaces": False,
                "polymeshes": True,
                "subdivSurfaces": False,
                "planes": False,
                "lights": False,
                "imagePlane": True,
                "cameras": False,
                "joints": False,
                "ikHandles": False,
                "deformers": False,
                "dynamics": False,
                "fluids": False,
                "hairSystems": False,
                "nCloths": False,
                "follicles": False,
                "nParticles": False,
                "nRigids": False,
                "dynamicConstraints": False,
                "locators": False,
                "dimensions": False,
                "pivots": False,
                "handles": False,
                "textures": False,
                "strokes": False,
                "motionTrails": False,
                "manipulators": False,
                "cv": False,
                "hulls": False,
                "grid": False,
                "hud": True,
                "sel": False,
                "greasePencils": False
            },

            "hud": {
                "societyName": "Fix Studio",
                "showDateTime": True,
                "showCamera": True,
                "showFrame": True,
                "showStep": True,
                "showProject": True,
                "showArtist": True
            },
            "extra": {
                "save_scene": True,
                "save_playblastInfo": True
            }

        }

        # this var define wich camera is available for playblast and her playblast range
        # camera item is like self.cameras["|camera1_group|camera1"] = {"playblast":False, "shape":"|blah", "start":101, "end":120}
        self.cameras = {}
        self.soundPath = None
        self.soundOffset = 0
        self.published = {}

        self.playblastInfoData = {
            "soundPath": self.soundPath,
            "soundOffset": self.soundOffset,
            "framerate": None
        }

        # output
        self.scenePlayblastPath = None
        self.imgPlayblastPath = None
        self.playblastInfoPath = None

        # get data
        self.get_sceneInfo()
        self.get_cameras()
        self.get_sound()
        self.get_settingsFromPbcn()

        # init shot, shots, version info
        self.shot = None
        self.neighborsShot = None
        self.publishedVersions = {}

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

    def initTk(self, mode='currentScene'):
        """
        """
        if mode == 'currentScene':
            logger.info("init tk")

            self.sgCmds.do_initTk()
            self.tk = self.sgCmds.tk
            self.ctx = self.sgCmds.ctx

            logger.info("Current Context: %s" % self.ctx)

            self.pl = PublishLocal(tk=self.tk, ctx=self.ctx, parent=self)

    def get_settingsFromPbcn(self):
        """Get Settings from the Playblast Config Node."""
        if self.pbcn.findNode():
            self.pbcn.getDataFromNode()
            # check if settings exist in extraAttr
            if 'settings' in self.pbcn.extraAttr.keys():
                # parse data and update self.settings
                for category in self.pbcn.extraAttr['settings']['classic'].keys():
                    # check if already exist in self.settings
                    if not category in self.settings.keys():
                        self.settings[category] = {}

                    # category always have children try to retrieve it
                    # check if children exists
                    if  self.pbcn.extraAttr['settings']['classic'][category].keys():

                        for attr in self.pbcn.extraAttr['settings']['classic'][category].keys():
                            # get value
                            value = self.pbcn.extraAttr['settings']['classic'][category][attr]
                            # check if attr exist in self.settings too
                            if not attr in self.settings[category].keys():
                                # create attr in self.settings
                                self.settings[category][attr] = {}
                            # update attr in self.settings
                            self.settings[category][attr] = self.pbcn.extraAttr['settings']['classic'][category][attr]
        else:
            #  push data to pbcn and create ndoe
            self.pbcn.extraAttr['settings']['classic'] = self.settings
            # if not exist create node, createNode pushData2Node too
            self.pbcn.createNode()

    def do_pushSettings2Pbcn(self):
        """push settings to Playblast config node."""
        self.pbcn.extraAttr['settings']['classic'] = self.settings
        self.pbcn.pushData2Node()

    def get_sceneInfo(self):
        """Get Maya Scene Information needed by the ui"""
        self.scene.getAnimationSettings()

    def get_cameras(self):
        """ Get the available camera for playblast"""
        # get cameras from module node
        self.cams.getCameras(filter="noFpst")

        for item in self.cams.cameras.keys():

            # check if cameras already exist in dict
            # if exist do nothing
            # if not exist create
            logger.debug("check item: %s\ncameras list: %s" % (item, self.cameras.keys()))
            if not item in self.cameras.keys():

                # check if camera is active
                cameraIsActive = ppSceneManagement.objectIsTaggedBy(tagName="active_camera", node=self.cams.cameras[item]['name'])

                self.cameras[item] = {
                    "playblast":cameraIsActive,
                    "shape":self.cams.cameras[item]['shape'],
                    "shortShape":self.cams.cameras[item]['shortShape'],
                    "shortName":self.cams.cameras[item]['shortName'],
                    "name":self.cams.cameras[item]['name'],
                    "start":self.scene.minTime,
                    "end":self.scene.maxTime,
                    "preRoll":0
                }

        # check if camera in dict ever exist
        for key in self.cameras.keys():

            if not cmds.objExists(key):
                # remove camera in the dict
                del self.cameras[key]


    def get_sound(self):
        """ Get the available sound for playblast"""
        # get sound from module node
        if self.snds.getSounds(activeInTimeSlider=True):
            soundNode = self.snds.sounds.keys()[0]
            self.soundPath = self.snds.sounds[soundNode]['path']
            self.soundOffset = self.snds.sounds[soundNode]['offset']
        else:
            logger.debug("Can't retrieve Sound Node in activeInTimeSlider")
            self.soundPath = None
            self.soundOffset = 0

    def get_existingPlayblast(self):
        """ retrieve the existing playblast.
        we use self.pl = PublishLocal class to do this
        the result is store in self.pl.existingPlayblast"""

        return self.pl.get_existingPlayblast()

    def get_neighborsShot(self):
        """ retrieve the other shot of our shot."""

        # check if we have a shotgun connection
        if not self.ctx:
            self.initTk()

        if self.tk and self.ctx:

            # get Sequence

            # get sequence and our cut order linked to shot
            self.ourShot = self.tk.shotgun.find_one(self.pl.ctx.entity['type'], [['id', 'is', self.ctx.entity['id']]], ['sg_sequence.Sequence.code', 'sg_cut_order'])

            # get shot list linked to the sequence
            filters = [['sg_sequence.Sequence.code', 'is', self.ourShot['sg_sequence.Sequence.code']], ['project.Project.name', 'is', self.ctx.project['name']], ['sg_status_list', 'is_not', 'omt']]
            fieldsReturn = ['id', 'code', 'sg_cut_order']
            order = [{'field_name':'sg_cut_order','direction':'asc'}]
            self.neighborsShot = self.tk.shotgun.find('Shot', filters, fieldsReturn, order)

        return self.neighborsShot

    def get_versionList(self, shot):
        """ retrieve version linked to shot"""

        if not self.ctx:
            self.initTk()

        if self.tk and self.ctx:

            logger.info("Get Version for Shot: %s " % shot)

            # get version
            filters = [['entity.Shot.id', 'is', shot['id']], ['project.Project.name', 'is', self.ctx.project['name']], ['sg_status_list', 'is_not', 'omt']]
            fieldsReturn = ['id', 'code', 'sg_path_to_movie', 'user', 'created_at']
            order = [{'field_name':'id','direction':'desc'}]
            sgVersions = self.tk.shotgun.find('Version', filters, fieldsReturn, order)

            logger.debug("Version found: %s" % sgVersions)

            # check if the version is available
            self.publishedVersions[shot['id']] = []
            for sgVersion in sgVersions:
                if sgVersion['sg_path_to_movie']:
                    self.publishedVersions[shot['id']].append(sgVersion)

            # sgPfPath = sgPf['path']['local_path_windows']
            # if self.system == "darwin":
            #   sgPfPath = sgPf['path']['local_path_mac']
            # if self.system == "linux2":
            #   sgPfPath = sgPf['path']['local_path_linux']


    # Create Playblast
    def do_playblast(self, viewPlayblast=True, publish=False):
        """ do the playblast
        """
        logger.info("Do Playblast")
        # init result
        self.playblastResult = []

        # refresh sound in use
        self.get_sound()

        # Check if we use a real-time render or not.
        # if self.settings['renderer']['engine']['default'] == "Maya Software"
        renderer = self.settings['renderer']['engine']['default']
        rendererType = self.engine[renderer]

        if rendererType == "real-time":
            # Create View
            self.view = PlayblastView()
            self.view.createView()

            # Setup View & Hud
            msg = "Apply Playblast Settings to Custom View"
            logger.info(msg)
            self.view.customizeView(renderer=self.settings['renderer']['engine']['default'], renderDisplay=self.settings['renderDisplay'], viewDisplay=self.settings['viewDisplay'])

        # create local folder
        self.pl.createNewVersionFolder()

        # save scene with images
        if self.settings['extra']['save_scene']:

            self.scenePlayblast = self.pl.get_scenePath()
            msg = "Backup Playblast Scene as: %s" % self.scenePlayblast
            logger.info(msg)
            cmds.file(self.scenePlayblast, type='mayaAscii', exportAll=True, preserveReferences=True, exportUnloadedReferences=True)

        # For each Camera
        for camKey in sorted(self.cameras.keys()):

            if self.cameras[camKey]['playblast']:

                if rendererType == "real-time":

                    # looking through Camera
                    self.view.lookThrough(camera=camKey)

                    # store and custom camera settings
                    cam = CameraPlayblast()
                    cam.customizeCamera(camera=camKey, cameraDisplay=self.settings['cameraDisplay'], storeOrigSettings=True)

                # clear selection
                cmds.select(clear=True)

                # do Playblast
                currentShortCam = camKey.split('|')[len(camKey.split('|'))-1].replace(':', '_')
                self.pl.fields['Camera'] = currentShortCam
                self.imgPlayblastPath = self.pl.getImgName(camera=currentShortCam)

                msg = "Playblast Camera: %s" % self.cameras[camKey]['shortName']
                logger.info(msg)

                compression = self.pl.get_frameExtension()
                framePadding = self.pl.getImgPadding()

                if rendererType == "real-time":
                    # set camera in ours custom hud
                    self.hud.setCamera(cameraName=self.cameras[camKey]['shortName'])
                    # create hud
                    self.hud.createAll()

                logger.info("Playblast: %s | %s - %s | %s" % (currentShortCam, self.cameras[camKey]['start'], self.cameras[camKey]['end'], self.imgPlayblastPath))

                if rendererType == "real-time":
                    pbres = cmds.playblast(startTime= self.cameras[camKey]["start"], endTime= self.cameras[camKey]["end"], format="image", forceOverwrite=True, compression=compression, viewer=False, fp=framePadding, rawFrameNumbers=False, offScreen=True, percent=100, width=self.settings["resolution"]["width"], height=self.settings["resolution"]["height"], showOrnaments=True, filename=self.imgPlayblastPath)
                    logger.info("Playblast Result: %s" % pbres)

                if rendererType == "offline":
                    # render images
                    self.do_renderEngine(engineName=renderer, camera=camKey, startTime=self.cameras[camKey]["start"], endTime=self.cameras[camKey]["end"], imageExtension=compression, fp=framePadding, width=self.settings["resolution"]["width"], height=self.settings["resolution"]["height"], filename=self.imgPlayblastPath )

                if rendererType == "real-time":
                    # restore camera settings
                    cam.customizeCamera(camera=camKey, cameraDisplay=cam.cameraSettingsOriginal, storeOrigSettings=False)

                # append playblast to playblastresult
                self.playblastResult.append({'version':self.pl.currentVersion, 'camera':currentShortCam})

            else:
                logger.info("Do not playblast camera: %s" % camKey)

        # create yml file wich store playlast info likek soundPath & soundOffset, framerate
        if self.settings['extra']['save_playblastInfo']:
            self.createPlayblastInfoFile()

        if rendererType == "real-time":
            # delete hud
            self.hud.deleteAll()

            # delete view
            self.view.deleteView()

        # build and print msg
        msg = "Playblast"
        for pb in self.playblastResult:
            msg = "Playblast |v%04d / %s" % (pb['version'], pb['camera'])
            cmds.inViewMessage(amg=msg, pos='midCenter', fade=True, fadeOutTime=500)


        # for return, view playblast and publish we build a version list which represent the created playblast
        versionList = []
        for pb in self.playblastResult:
            versionList.append({'version': int(pb['version']), 'camera': pb['camera']})

        #
        logger.info("Version List: %s" % versionList)

        # viewPlayblast
        if viewPlayblast:
            #
            self.do_playInRv(versionList=versionList, mode='player', previousShotMovie=[], nextShotMovie=[])

        # publish each playblast if active
        if publish:

            self.do_publishPlayblast(versionList=versionList)

        return versionList

    def do_renderEngine(self, engineName="mayaSoftware", camera="persp", startTime=101, endTime=102, imageExtension="png", fp=4, width=1280, height=1024, filename=""):
        """ """
        logger.info('do_renderEngine(engineName={engineName}, startTime={startTime}, endTime={endTime}, imageExtension={imageExtension}, fp={fp}, width={width}, height={height}, filename={filename}'.format(engineName=engineName, startTime=startTime, endTime=endTime, imageExtension=imageExtension, fp=fp, width=width, height=height, filename=filename))

        self.rendererNodeSettings   = {
            "resolution":{
                "mayaHardware":"defaultResolution",
                "mayaHardware2":"defaultResolution",
                "mayaSoftware":"defaultResolution",
                "mentalRay":"defaultResolution"
            },
            "renderGlobals":{
                "mayaHardware":"defaultRenderGlobals",
                "mayaHardware2":"defaultRenderGlobals",
                "mayaSoftware":"defaultRenderGlobals",
                "mentalRay":"defaultRenderGlobals"
            },
            "extension":{
                "jpg":8,
                "png":32
            }
        }

        # setup renderer
        cmds.setAttr("{renderGlobals}.currentRenderer".format(renderGlobals=self.rendererNodeSettings['renderGlobals'][engineName]), engineName, type="string")

        # setup image path
        cmds.setAttr("{renderGlobals}.imageFilePrefix".format(renderGlobals=self.rendererNodeSettings['renderGlobals'][engineName]), filename, type="string")
        cmds.setAttr("{renderGlobals}.imageFormat".format(renderGlobals=self.rendererNodeSettings['renderGlobals'][engineName]), self.rendererNodeSettings['extension'][imageExtension])

        # set frame/anim ext
        cmds.setAttr("{renderGlobals}.animation".format(renderGlobals=self.rendererNodeSettings['renderGlobals'][engineName]), 1)

        cmds.setAttr("{renderGlobals}.outFormatControl".format(renderGlobals=self.rendererNodeSettings['renderGlobals'][engineName]), 0)
        cmds.setAttr("{renderGlobals}.putFrameBeforeExt".format(renderGlobals=self.rendererNodeSettings['renderGlobals'][engineName]), 1)
        cmds.setAttr("{renderGlobals}.periodInExt".format(renderGlobals=self.rendererNodeSettings['renderGlobals'][engineName]), 1)

        cmds.setAttr("{renderGlobals}.extensionPadding".format(renderGlobals=self.rendererNodeSettings['renderGlobals'][engineName]), fp)

        for frame in range(int(startTime), int(endTime)+1):

            cmds.currentTime(frame)
            logger.info("Render Frame # {engineName} - {camera} - {frame}".format(engineName=engineName, camera=camera, frame=frame))
            cmds.render(camera, x=width, y=height)

            # rename image
            framePad = "%0{number}d".format(number=fp) % (frame)

            renderImagePath = "{filename}.{frame}_tmp.{extension}".format(filename=filename, frame=framePad, extension=imageExtension)
            goodImagePath = "{filename}.{frame}.{extension}".format(filename=filename, frame=framePad, extension=imageExtension)


            logger.info("looking for img: {img}".format(img=renderImagePath))

            os.rename(renderImagePath, goodImagePath)


    def createPlayblastInfoFile(self, outputPath=None):
        """
        create playblast info file who store info like framerate, soundPath, soundOffset.

        :param outputPath: (str)
        """
        # build dict
        self.playblastInfoData  = {
                                    "soundPath":self.soundPath,
                                    "soundOffset":self.soundOffset,
                                    "framerate":self.scene.fps,
                                    "published": self.published
        }

        # get path
        self.playblastInfoPath = outputPath

        if not outputPath:
            self.playblastInfoPath = self.pl.get_playblastInfoPath()

        # yaml data
        ymlDatas = yaml.dump(self.playblastInfoData, default_flow_style=True)

        # write data to file
        f = open(self.playblastInfoPath,'w')
        f.write(ymlDatas)
        f.close()
        logger.info("Playblast Info wrote: %s" % self.playblastInfoPath)

    def getPlayblastInfoFile(self, filepath=None):
        """
        retrieve data from playblast info file like, framerate, soundOffset, soundPath
        :param filepath: (str) file path to read
        """
        # read info file which describe framerate, soundoffset, soundpath
        if os.path.exists(filepath):
            f = open(filepath,'r')
            data = f.read()
            f.close()
            infodata = yaml.load(data)

            if infodata:
                if 'framerate' in infodata.keys():
                    self.playblastInfoData['framerate'] = float(infodata['framerate'])
                if 'soundOffset' in infodata.keys():
                    self.playblastInfoData['soundOffset'] = infodata['soundOffset']
                if 'soundPath' in infodata.keys():
                    self.playblastInfoData['soundPath'] = infodata['soundPath']
                if 'published' in infodata.keys():
                    self.playblastInfoData['published'] = infodata['published']
            else:
                logger.warning("Can't Find Info Path at: %s" % filepath)

        return True

    def addSoundToExistingPlayblast(self, versionList):
        """
        this func add the active audio in timeslider to an existing playblast
        :param versionList: (list) list like this [{'version':001}, {'version':004}]
        """

        #  get Sound Info
        self.get_sound()

        # check if existing playblast available
        if not self.pl.existingPlayblast:
            self.get_existingPlayblast()

        # for each version try to retrive info file
        for item in versionList:

            # get version and camera
            version = item['version']

            # get some data from publish file
            infoPath = self.pl.existingPlayblast[version]['info']

            #  read existing data
            self.getPlayblastInfoFile(filepath=infoPath)

            # update info
            if self.playblastInfoData['framerate']:
                self.scene.fps = self.playblastInfoData['framerate']

            self.createPlayblastInfoFile(outputPath=infoPath)

        return True

    def do_addPublishedInfoToExistingPlayblast(self, publishInfo, version):
        """
        this func add the active audio in timeslider to an existing playblast
        :param version: dict like {'version':001, 'camera':'camera1'}
        """

        # check if existing playblast available
        if not self.pl.existingPlayblast:
            self.get_existingPlayblast()

        versionId = version['version']
        camera = version['camera']

        # for each version try to retrive info file
        if version in self.pl.existingPlayblast.keys():

            # file info path
            infoPath = self.pl.existingPlayblast[version]['info']

            # read existing data
            self.getPlayblastInfoFile(filepath=infoPath)

            # update publish info
            if not version in self.playblastInfoData.keys():
                self.playblastInfoData[version]= {}
            self.playblastInfoData[version] [camera] =  publishInfo

            #
            self.createPlayblastInfoFile(outputPath=infoPath)

        return True

    def getPathPlayer(self, mode='player', forceRefresh=False):
        """ get the player's path.
        :param mode: different mode availaible, player, push
        """
        # init path mapping
        app_path_mapping = {
                                'player':{"linux2": "rv_path_linux", "darwin": "rv_path_mac", "win32": "rv_path_windows"},
                                'push':{"linux2": "pp_rvpush_path_linux", "darwin": "pp_rvpush_path_mac", "win32": "pp_rvpush_path_windows"},
        }
        if self.playerPath[mode] and not forceRefresh:
            return self.playerPath[mode]

        if self._app:

            # get player path from template
            system = sys.platform
            app_path = None
            try:
                app_setting = app_path_mapping[mode][system]
                app_path = self._app.get_setting(app_setting)
                if not app_path:
                   raise KeyError()
            except KeyError:
                 raise TankError("Platform '%s' is not supported." % system)

            if app_path:
                self.playerPath[mode] = app_path
        else:
            logger.error("self._app not exist, please fill self._app before")

        return self.playerPath[mode]

    def do_playInRv(self, versionList=[], mode='player', previousShotMovie=[], nextShotMovie=[]):

        """ play version in rv
        :param versionList: represent a list with the schema below [
                                                                    {'version':02, 'camera':'persp'}
                                                                    ]
        :param previousShotMovie: list with a path to the movie. for example ['/prod/project/toto/tutu.mov', '/prod/project/toto/tata.mov']
        :param nextShotMovie: list with a path to the movie. for example ['/prod/project/toto/tutu.mov', '/prod/project/toto/tata.mov']
        """

        # if no version, no play :)
        if not versionList:
            return

        logger.info("do_playInRv versionList=%s, mode=%s, previousShotMovie=%s, nextShotMovie=%s" % (versionList, mode, previousShotMovie, nextShotMovie))

        # get player path
        app_path = None
        if mode == 'compare':
            app_path = self.getPathPlayer(mode='player')
        else:
            app_path = self.getPathPlayer(mode=mode)

        # init command with compare mode active
        cmd = [app_path]

        # check mode
        if mode == 'player':
            cmd.extend(['-l', '-play'])
        # check mode
        if mode == 'compare':
            cmd.extend(['-tile', '-l', '-play'])
        # check mode
        if mode == 'push':
            cmd.extend(['merge'])

        # update existing playblast
        self.get_existingPlayblast()

        # for each version get data
        for item in versionList:

            # add previous Shot to cmd
            if previousShotMovie:
                for previousShot in previousShotMovie:
                    cmd.extend(['%s' % previousShot])

            #------------------------------
            # init imgSeqCmd
            imgSeqCmd = []
            # add our working shot
            # get version and camera
            version = item['version']
            camera = item['camera']

            # get some data from publish file
            imgPath = self.pl.existingPlayblast[version]['cameras'][camera]
            scenePath = self.pl.existingPlayblast[version]['scene']
            infoPath = self.pl.existingPlayblast[version]['info']

            logger.info("-------------- %s" % imgPath)

            framerate = None
            soundOffset = None
            soundPath = None

            # read info fie which describe framerate, soundoffset, soundpath
            if os.path.exists(infoPath):
                f = open(infoPath,'r')
                data = f.read()
                f.close()
                infodata = yaml.load(data)

                if infodata:

                    if 'framerate' in infodata.keys():
                        framerate =  float(infodata['framerate'])
                    if 'soundOffset' in infodata.keys():
                        soundOffset =  infodata['soundOffset']
                    if 'soundPath' in infodata.keys():
                        soundPath =  infodata['soundPath']

            # append image sequence
            imgSeqCmd.extend(['[', '-fps', "%s" % framerate, imgPath['thumbnail'], '-in', "%s" % imgPath['start'], '-out', "%s" % imgPath['end']])

            # if sound append it
            if soundPath:
                if os.path.exists(soundPath):

                    # calc sound offset in second in relation to imSeq
                    audioOffset = (soundOffset - imgPath['start']) / framerate
                    imgSeqCmd.append('-ao')
                    imgSeqCmd.append("%s" % audioOffset)


                    #  append sound path
                    imgSeqCmd.append(soundPath)

            # close source
            imgSeqCmd.append(']')

            # append image sequence to command
            cmd.extend(imgSeqCmd)


            # add previous Shot to cmd
            if nextShotMovie:
                for nextShot in nextShotMovie:
                    cmd.extend(['%s' % nextShot])

        #cmd.append('-noSequence')

        # launc rv
        logger.info("Launch Player: %s - %s" % (mode, versionList))
        logger.info("Cmd: %s" % (" ".join(cmd)))
        subprocess.Popen(cmd)

    def do_publishPlayblast(self, versionList=[]):
        """ publish playblast in sgtk.
        :param versionList: versionList follow the schema [ {'version':02, 'camera':'persp', 'comment':'blah'}, {'version':01, 'camera':'persp'}]
        """
        # check if existing playblast available
        if not self.pl.existingPlayblast:
            self.get_existingPlayblast()

        scenePathPublishId = None
        previousVersionPublished = None

        # for each version get data
        for item in versionList:

            # get version and camera
            version = item['version']
            camera = item['camera']
            comment = None
            if "comment" in item.keys():
                comment = item['comment']

            # get some data from publish file
            imgPath = self.pl.existingPlayblast[version]['cameras'][camera]
            scenePath = self.pl.existingPlayblast[version]['scene']
            infoPath = self.pl.existingPlayblast[version]['info']

            framerate = None
            soundOffset = 0
            audioOffset = 0
            soundPath = None
            soundActive = False

            if not scenePath:
                logger.error("We can't publish a playblast without a scene associated. Please do a classic playblast.")
                return False

            # read info file which describe framerate, soundoffset, soundpath
            if os.path.exists(infoPath):
                f = open(infoPath,'r')
                data = f.read()
                f.close()
                infodata = yaml.load(data)

                if infodata:
                    if 'framerate' in infodata.keys():
                        framerate =  float(infodata['framerate'])
                    if 'soundOffset' in infodata.keys():
                        soundOffset =  infodata['soundOffset']
                        if soundOffset and framerate:
                            if soundOffset != 0:
                                audioOffset = (soundOffset - imgPath['start']) / framerate
                    if 'soundPath' in infodata.keys():
                        soundPath =  infodata['soundPath']
            else:
                logger.warning("Can't Find Info Path at: %s" % infoPath)

            # get sound
            if soundPath:
                if os.path.exists(soundPath):
                    #
                    soundActive = True

            self.projectPath = self.tk.roots['primary']

            # publish scene
            # check if scene already published
            if not scenePathPublishId and previousVersionPublished != version:
                comment_sn = comment
                if not comment_sn:
                    comment_sn = "auto-publish before playblast"
                params = {
                            "comment": comment_sn
                        }

                scenePathPublishId = self.action._publish_scene(params=params, pre_publish=True, copy_mode="copy", set_status="apr", separate_process=False)

            publishImgArgs = {
                                'project': self.projectPath,
                                'filePath': str(imgPath['imgSeq']),
                                'fileType': "playblast_image",
                                'linkType': self._app.context.entity['type'],
                                'linkName': self._app.context.entity['name'],
                                'publishName': camera.replace('_', ''),
                                'stepName': self._app.context.step['name'],
                                'taskName': self._app.context.task['name'],
                                'comment': comment,
                                'daily': True,
                                'dependencies': [scenePathPublishId.get('id')],
                                'audioFile': soundPath,
                                'audioOffset': audioOffset,
                                'colorSpace': 'srgb',
                                'frameRate': framerate,
                                }
            logger.info("Publish Args: %s" % publishImgArgs)

            # new method not deploy
            # imgPublishedId = ppSgtkPublisher.publish_file_thread(publishImgArgs, separate_process=False)

            # publish images
            imgPublishedId = ppSgtkPublisher.publishFile(**publishImgArgs)
            logger.info("Image Playblast Published: %s" % imgPublishedId)


class PlayblastConfigNode(object):
    """docstring for PlayblastConfigNode"""
    def __init__(self):
        # defaut prefix name
        self.prefix = "pp"
        # default node name
        self.defaultName = "%s_playblastConfigNode" % self.prefix

        # define extra attribute
        self.extraAttr = {
                            "settings": {
                                        'classic':None,
                                        'yml':None
                            }

        }

        # current node in use
        self.node = None

    def createNode(self):
        """
        create playblast config node and push self.datas to it
        """
        # check if playblast config node already exist
        if not self.findNode():
            # create node
            self.node = cmds.createNode("objectSet", name=self.defaultName)

            # create Attr
            for key in self.extraAttr.keys():
                attr = "%s_%s" % (self.prefix, key)
                # check if attr already exist
                if not cmds.objExists("%s.%s" % (self.node,attr)):
                    resAddAttr = cmds.addAttr(self.node, ln=attr, dt="string")

            # update node with datas
            self.pushData2Node()

            return self.node
        else:
            logger.warning("%s already exist" % self.defaultName)
            logger.info("retieve data")
            self.getDataFromNode()
            return self.node

    def findNode(self):
        """
        find node playblastConfig from scene
        """
        if cmds.objExists(self.defaultName):
            self.node = self.defaultName
            return self.node
        else:
            return False

    def pushData2Node(self):
        """
        push data from arg datas to node
        :param datas: dict
        """
        # check if node exist
        if not self.node:
            self.findNode()
            if not self.node:
                return False

        # for each attr push data
        for key in self.extraAttr.keys():

            if self.extraAttr[key]['classic']:

                # serialized data and store it
                self.extraAttr[key]['yml'] = yaml.dump(self.extraAttr[key]['classic'], default_flow_style=True)
                # push yaml on node
                cmds.setAttr("%s.%s_%s" % (self.node, self.prefix, key), self.extraAttr[key]['yml'], type='string')
            else:
                logger.warning("No data to push on node")

        return True

    def getDataFromNode(self):
        """
        push data from arg datas to node
        :param datas: dict
        """
        # check if node exist
        if not self.node:
            self.findNode()
            if not self.node:
                return False

        # for each attr push data
        for key in self.extraAttr.keys():

            #  check attr exist on node
            if cmds.objExists("%s.%s_%s" % (self.node, self.prefix, key)):

                # get data from node.attr
                ymlData = cmds.getAttr("%s.%s_%s" % (self.node, self.prefix, key))
                # try to unserialized data
                classicData = None
                try:
                    classicData = yaml.load(ymlData)
                except:
                    logger.error("Can't retrieve yaml data from node. ymlData = %s" % ymlData)


                # push yaml to var
                if ymlData:
                    self.extraAttr[key]['classic'] = classicData
                    self.extraAttr[key]['yml'] = ymlData

            else:
                logger.warning("Attr %s not exist on node %s"%(key, self.node))

        return True




class PlayblastView(object):
    """build a special viewport dedicate to playblast"""
    def __init__(self):

        # var name
        self.windowName         = "ppPlayblast_window"
        self.frameLayout        = "ppPlayblast_framelayout"
        self.paneLayout         = "ppPlayblast_paneLayout"
        self.modelPanelName     = "ppPlayblast_panel"

        # resolution
        self.width = 1280
        self.height = 720

        # extra data
        self.sizeOffset = 50
        self.camera = "persp"
        self.cameraSettingsOriginal = {}

    def createView(self, width=1280, height=720):
        """ create special view for playblast
        @param width (int) width of the viewport
        @param height (int) height of the viewport
        """
        logger.info("Create View")

        self.width = width
        self.height = height

        # Create Window
        if not cmds.window(self.windowName, exists=True):
            self.windowName     = cmds.window(self.windowName, title=self.windowName, width=self.width+self.sizeOffset, height=self.height+self.sizeOffset)
        else:
            cmds.window(self.windowName, edit=True, width=self.width+self.sizeOffset, height=self.height+self.sizeOffset)

        # Create Pane Layout
        if not cmds.paneLayout(self.paneLayout, exists=True):
            self.paneLayout = cmds.paneLayout(self.paneLayout, parent=self.windowName)
        else:
            cmds.paneLayout(self.paneLayout, edit=True, parent=self.windowName)

        if not cmds.modelPanel(self.modelPanelName, exists=True):
            self.modelPanelName     = cmds.modelPanel(self.modelPanelName, label=self.modelPanelName, camera=self.camera, parent=self.paneLayout)
        else:
            cmds.modelPanel(self.modelPanelName, edit=True, camera=self.camera, parent=self.paneLayout)

        cmds.showWindow(self.windowName)
        cmds.setFocus(self.modelPanelName)

    def customizeView(self, renderer=None, renderDisplay={}, viewDisplay={}):
        """ customize view / setup display and create hud
        @param renderer
        @param viewDisplay (dict) it's a dict key:value for setup display. example for set invisible polygon set "polymeshes":False
        """

        if renderer:
            #=======================================================================
            # Set Renderer # "default", "highQuality", "viewport2"
            logger.debug("customizeView: Set Renderer: %s" % renderer)

            if renderer == "highQuality":
                cmds.modelEditor(self.modelPanelName, edit=True, rnm="hwRender_OpenGL_Renderer")

            if renderer == "viewport2":
                cmds.modelEditor(self.modelPanelName, edit=True, rnm="ogsRenderer")
                # if viewport2 wait 2sec for init viewport
                time.sleep(2)

            else:
                cmds.modelEditor(self.modelPanelName, edit=True, rnm="base_OpenGL_Renderer")

        if renderDisplay:
            #=======================================================================
            # Set Display Appearance
            for key in renderDisplay:
                # Set Blast Value
                value = renderDisplay[key]
                logger.debug("Set Render Display: %s = %s" % (key, renderDisplay[key]))
                if isinstance(value, bool) or isinstance(value, float) or isinstance(value, int):
                    eval("cmds.modelEditor('%s', edit=True, %s=%s)" % (self.modelPanelName, key, value))

                if isinstance(value, dict):
                    eval("cmds.modelEditor('%s', edit=True, %s='%s')" % (self.modelPanelName, key, value['default']))

        if viewDisplay:
            #=======================================================================
            # Set Display Appearance
            for key in viewDisplay:
                # Set Blast Value
                value = viewDisplay[key]
                logger.debug("Set View Display: %s = %s" % (key, viewDisplay[key]))
                if isinstance(value, bool) or isinstance(value, float) or isinstance(value, int):
                    eval("cmds.modelEditor('%s', edit=True, %s=%s)" % (self.modelPanelName, key, value))

                if isinstance(value, dict):
                    eval("cmds.modelEditor('%s', edit=True, %s='%s')" % (self.modelPanelName, key, value['default']))


    def lookThrough(self, camera=None):
        """ Set View to look Through the given camera
        @param camera (str) camera name like persp
        """

        # check if camera exist
        if cmds.objExists(camera):
            self.camera = camera
            self.createView(width=self.width, height=self.height)


        else:
            return False

    def deleteView(self):
        """ delete view
        """
        cmds.deleteUI("%s" % self.windowName, window=True)

class CameraPlayblast(object):
    """docstring for CameraPlayblast"""
    def __init__(self):
        self.camera = "persp"
        self.cameraSettingsOriginal = {}

    def customizeCamera(self, camera=None, cameraDisplay={}, storeOrigSettings=False):
        """ customize camera settings
        - store original settingss
        - apply playblast settings
        - restore original settings
        :param camera: (str) camera or cameraShape
        :param cameraDisplay: (dict) it's a dict key:value for setup display. example active safe action  cameraDisplay['displaySafeAction']=True
        """

        if camera and cameraDisplay:
            self.camera = camera

            #=======================================================================
            # Set Display on Camera
            for cameraDisplayKey in cameraDisplay.keys():

                # store original settings
                if storeOrigSettings:
                    self.cameraSettingsOriginal[cameraDisplayKey] = cmds.getAttr("%s.%s" % (camera, cameraDisplayKey))

                #  decode type of data
                value = cameraDisplay[cameraDisplayKey]

                logger.debug("Set Camera Value: %s = %s" % (cameraDisplayKey, value))
                if isinstance(value, bool) or isinstance(value, float) or isinstance(value, int):
                    eval("cmds.setAttr('%s.%s', %s)" % (self.camera, cameraDisplayKey, value))
                if isinstance(value, list):
                    eval("cmds.setAttr('%s.%s', %s, %s, %s, type='float3')" % (self.camera, cameraDisplayKey, value[0][0], value[0][1], value[0][2]))


class PublishLocal(object):
    """ Publish Locally Files """

    def __init__(self, tk=None, ctx=None, parent=None):

        # init sgtk api instance
        self.tk = tk
        self.ctx = ctx

        self.fields = {}
        self.publishPath = None
        self.currentVersion = None
        self.template_path = None

        self.projectPath = None

        self.templateChooser = {
                                    "Asset": {
                                                "work": "pp_maya_asset_playblast",
                                                "img": "pp_maya_asset_playblast_img",
                                                "scene": "pp_maya_asset_playblast_scene",
                                                "info": "pp_maya_asset_playblast_playInfo"
                                            },
                                    "Shot": {
                                                "work": "pp_maya_shot_playblast",
                                                "img": "pp_maya_shot_playblast_img",
                                                "scene": "pp_maya_shot_playblast_scene",
                                                "info": "pp_maya_shot_playblast_playInfo"
                                            }
        }
        self.existingPlayblast = {}
        self.framePadding = None

    def getContextFromCurrentScene(self):
        """get context from the current maya scene path"""
        self.ctx = self.tk.context_from_path(cmds.file(query=True, sn=True))

        return self.ctx

    def get_templateAndFields(self, what='img', camera=None, useCurrentVersion=False):
        """
        """

        # get template from context
        self.template_path = self.tk.templates[self.templateChooser[self.ctx.entity['type']][what]]

        # get template from current scene and retrieve fields=
        template = self.tk.template_from_path(cmds.file(query=True, sn=True))
        rawFields = template.get_fields(cmds.file(query=True, sn=True))

        # Asset Case sg_asset_type
        if self.ctx.entity['type'] == "Asset":

            self.fields = {
                            'current_user_name': os.getlogin(),
                            'Asset': self.ctx.entity['name'],
                            'Step': self.ctx.step['name'],
                            'Task': self.ctx.task['name'],
                            'sg_asset_type': rawFields['sg_asset_type']
            }
            if camera:
                self.fields['Camera'] = camera
        # Shot Case
        if self.ctx.entity['type'] == "Shot":
            # get sequence linked to shot
            result = self.tk.shotgun.find_one(self.ctx.entity['type'], [['id', 'is', self.ctx.entity['id']]], ['sg_sequence.Sequence.code'])

            self.fields = {
                            'current_user_name': os.getlogin(),
                            'Sequence': result['sg_sequence.Sequence.code'],
                            'Shot': self.ctx.entity['name'],
                            'Task': self.ctx.task['name'],
                            'Step': self.ctx.step['name']
            }
            if camera:
                self.fields['Camera'] = camera

        if useCurrentVersion:
            self.fields['version'] = self.currentVersion

    def get_existingPlayblast(self):
        """get the existing playblast available in the work area.

        get_existingPlayblast return a dict like
        {
            '40':{
                    'scene':'',
                    'info':'',
                    'cameras':{
                                'cameraA':{
                                            'thumbnail':None,
                                            'start':None,
                                            'end':None
                                            }
                                'cameraB':{
                                            'thumbnail':None,
                                            'start':None,
                                            'end':None
                                            }
                            }
            }

        }

        """
        self.existingPlayblast = {}

        # init template and fields
        self.get_templateAndFields(what='img', camera='persp', useCurrentVersion=False)

        # get existing version image
        existingVersions = self.tk.paths_from_template(self.template_path, self.fields, ['version', 'Camera'])

        # get nb version
        fieldsExistingsVersions = []

        # get entity type like Asset or Shot
        entityType = self.ctx.entity['type']

        # get version number available and store it into self.existingPlayblast[versionId] = {}
        for v in sorted(existingVersions):

            fields = self.template_path.get_fields(v)
            fieldsExistingsVersions.append(fields)

            vId = fields['version']
            cam = fields['Camera']

            # create version number into dict
            if not vId in self.existingPlayblast.keys():
                self.existingPlayblast[vId] = {
                                            'scene': '',
                                            'info': '',
                                            'cameras': {},
                                            'soundPath': None,
                                            'soundOffset': 0,
                                            'soundSecond': 0,
                                            'framerate': None
                                            }

            # add camera to existing playblast dict
            if not cam in self.existingPlayblast[vId]['cameras'].keys():
                # init camera data
                self.existingPlayblast[vId]['cameras'][cam] = {
                                                                'thumbnail': v,
                                                                'imgSeq': None,
                                                                'start': None,
                                                                'end': None,
                                                                'published': {},
                                                                'image_path_init': v
                                                            }

        # fill existingPlayblast
        for vId in sorted(self.existingPlayblast.keys()):

            for cam in sorted(self.existingPlayblast[vId]['cameras'].keys()):
                # image path
                thumbnail = self.existingPlayblast[vId]['cameras'][cam]['thumbnail']

                # get padding
                # we assuming image padding is the length character between the 2 last
                image_number = thumbnail.split('.')[len(thumbnail.split('.'))-2]
                image_padding = len(image_number)

                # store image path with padding information included
                format_padding = "%0{p}d".format(p=image_padding)
                imgSeq = thumbnail.replace(".{im}.".format(im=image_number), ".{im}.".format(im=format_padding))

                self.existingPlayblast[vId]['cameras'][cam]['imgSeq'] = imgSeq

                # set thumbnail
                self.existingPlayblast[vId]['cameras'][cam]['thumbnail'] = thumbnail

                # init image number list
                imgList = []
                # store each image number
                for item in fieldsExistingsVersions:
                    if item['version'] == vId and item['Camera'] == cam:
                        imgList.append(int(item['SEQ']))

                # get start and end image
                if imgList:
                    self.existingPlayblast[vId]['cameras'][cam]['start'] = min(imgList)
                    self.existingPlayblast[vId]['cameras'][cam]['end'] = max(imgList)

        # for each vId / retrieve scene backup + info
        # get existing scene
        self.get_templateAndFields(what='scene', useCurrentVersion=False)
        existingScene = self.tk.paths_from_template(self.template_path, self.fields, ['version'])

        # append scene to self.existingPlayblast
        for sn in existingScene:
            snVersion = self.template_path.get_fields(sn)['version']
            if snVersion in self.existingPlayblast.keys():
                self.existingPlayblast[snVersion]['scene'] = sn

        self.get_templateAndFields(what='info', useCurrentVersion=False)
        existingInfo = self.tk.paths_from_template(self.template_path, self.fields, ['version'])

        # append info to self.existingPlayblast
        for info in existingInfo:
            infoVersion = self.template_path.get_fields(info)['version']
            if infoVersion in self.existingPlayblast.keys():
                self.existingPlayblast[infoVersion]['info'] = info

                # read info fie which describe framerate, soundoffset, soundpath
                if os.path.exists(info):
                    f = open(info,'r')
                    data = f.read()
                    f.close()
                    infodata = yaml.load(data)

                    if infodata:
                        if 'framerate' in infodata.keys():
                            self.existingPlayblast[infoVersion]['framerate'] =  float(infodata['framerate'])
                        if 'soundOffset' in infodata.keys():
                            self.existingPlayblast[infoVersion]['soundOffset'] =  infodata['soundOffset']
                        if 'soundPath' in infodata.keys():
                            self.existingPlayblast[infoVersion]['soundPath'] =  infodata['soundPath']

        return self.existingPlayblast

    def createNewVersionFolder(self):
        """
        :param fields: (dict) template fields
        """

        # get template and fields from context // self.template
        self.get_templateAndFields(what='img', camera='persp')
        existingVersions = self.tk.paths_from_template(self.template_path, self.fields, ['version'])

        maxVersion = 0
        if existingVersions:
            maxVersionFile = max(existingVersions, key=lambda v: int(self.template_path.get_fields(v)['version']))
            maxVersion = int(self.template_path.get_fields(maxVersionFile)['version'])

        # Get the latest version through the Tank Published File
        self.fields['version'] = maxVersion + 1
        self.publishPath = self.template_path.apply_fields(self.fields)

        # Get the latest version through the existing directories
        while True:
            if os.path.isdir(os.path.dirname(self.publishPath)):
                self.fields['version'] += 1
                self.publishPath = self.template_path.apply_fields(self.fields)
            else:
                break

        # Create the directory that correponds to the version
        try:
            print("Create directory: %s" % os.path.dirname(self.publishPath))
            os.makedirs(os.path.dirname(self.publishPath))
            self.currentVersion = self.fields['version']
            return self.fields['version']
        except OSError,e:
            raise RuntimeError("Couldn't create %s: %s" % (self.publishPath, e))

    def getImgName(self, camera='persp'):
        """

        """
        self.get_templateAndFields(what='img', useCurrentVersion=True, camera=camera)
        imgName = self.template_path.apply_fields(self.fields).split(self.template_path.keys['SEQ'].default)[0]
        imgName = imgName.replace('.', '')
        return imgName

    def getImgPadding(self):
        """
        """
        self.get_templateAndFields(what='img', camera='persp', useCurrentVersion=True)
        fp = self.template_path.keys['SEQ'].default
        fp = int(fp.replace('%', '').replace('d', ''))
        self.framePadding = fp
        return self.framePadding

    def get_frameExtension(self):
        self.get_templateAndFields(what='img', camera='persp', useCurrentVersion=True)
        self.publishPath = self.template_path.apply_fields(self.fields)
        fe = self.publishPath.split('.')[len(self.publishPath.split('.'))-1]
        return fe

    def get_scenePath(self):
        """
        """
        self.get_templateAndFields(what='scene', useCurrentVersion=True)
        self.publishPath = self.template_path.apply_fields(self.fields)
        return self.publishPath

    def get_playblastInfoPath(self):
        """
        """
        self.get_templateAndFields(what='info', useCurrentVersion=True)
        self.publishPath = self.template_path.apply_fields(self.fields)
        return self.publishPath

    def do_deleteAllWorkVersion(self):
        """ this func delete the work version."""

        # init template and fields
        self.get_templateAndFields(what='work', useCurrentVersion=False)

        # get version ['/prod/project/PEUGEOT_DKR_14_241/sequences/002/002_0011/previz/work/maya/images/playblast/v001', '/prod/project/PEUGEOT_DKR_14_241/sequences/002/002_0011/previz/work/maya/images/playblast/v003']
        existingVersion = self.tk.paths_from_template(self.template_path, self.fields, ['version'])

        # delete each directory
        for v in existingVersion:

            # try delete directory
            try:
                logger.info("Delete Version: {version} at path {path}".format(version=os.path.basename(v), path=v))
                shutil.rmtree(v)
            except:
                logger.error("can't delete directory: %s" % v)

        return existingVersion
