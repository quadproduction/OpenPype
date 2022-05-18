# -*- coding: utf-8 -*-

"""
common classes and functions about entities like asset, assetInstance, shot, sequence
"""

import logging

import maya.cmds as cmds
import maya.mel as mel

import ppSgtkLibs.ppProjectUtils
import ppUtils.ppNotifier as ppNotifier
import ppUtils.ppIcons

logger = logging.getLogger(__name__)


class Scene():

    def __init__(self):

        # we're in batch ?
        self.batch = cmds.about(batch=True)

        # init project setting object
        self.ps = ppSgtkLibs.ppProjectUtils.Project_Settings()

        # animation settings
        self.handle = 30
        self.minTime = None
        self.maxTime = None
        self.animationStartTime = None
        self.animationEndTime = None
        self.playbackSpeed = None

        # scene settings
        self.fps = None
        self.fpsMaya = None
        self.fpsMapping = {
            "game": 15,
            "film": 24,
            "pal": 25,
            "ntsc": 30,
            "show": 48,
            "palf": 50,
            "ntscf": 60,
            "40 ps": 40,
            "100fps": 100,
        }
        self.unit = 'centimeter'
        self.angle = 'degree'

        # render settings
        self.width = 1280
        self.height = 720
        self.pixelAspectRatio = 1.0

        self.render_settings = {
            "render_render_renderer": None,
            "render_render_width": None,
            "render_render_height": None,
            "render_render_pixelAspectRatio": None,
            "render_render_frame_padding": None,
            "render_render_image_format": None,
            "render_render_frame_name_ext": None,
            "render_render_image_naming": None
        }

        self.rendererNodeSettings = {
            "Vray": "vraySettings",
            "Maxwell": "maxwellRenderOptions",
            "MentalRay": "defaultResolution",
            "Maya": "defaultResolution",
            "Arnold": "defaultArnoldRenderOptions"
        }

        self.frame_name_ext_mapping = {
            'name.#.ext': {
                "defaultRenderGlobals.animation": 1,
                "defaultRenderGlobals.animationRange": 1,
                "defaultRenderGlobals.outFormatControl": 0,
                "defaultRenderGlobals.useMayaFileName": 1,
                "defaultRenderGlobals.useFrameExt": 0,
                "defaultRenderGlobals.fieldExtControl": 0,
                "defaultRenderGlobals.putFrameBeforeExt": 1,
            }
        }

        self.image_format_mapping = {
            'GIF': 0,
            'SoftImage': 1,
            'RLA': 2,
            'Tiff': 3,
            'Tiff16': 4,
            'SGI': 5,
            'Alias PIX': 6,
            'Maya IFF': 7,
            'JPEG': 8,
            'EPS': 9,
            'Maya16 IFF': 10,
            'Cineon': 11,
            'Quantel': 12,
            'SGI16': 13,
            'Targa': 19,
            'Windows Bitmap': 15,
            'SGI Movie': 16,
            'Quicktime': 17,
            'AVI': 18,
            'MacPaint': 30,
            'PSD': 20,
            'PNG': 21,
            'QuickDraw': 22,
            'QuickTime Image': 23,
            'DDS': 24,
            'PSD Layered': 25,
            'OpenEXR': 31,
            'IMF plugin': 50,
            'Custom Image Format': 28,
            'Macromedia SWF': 60,
            'Adobe Illustrator': 30,
            'SVG': 31,
            'Swift3DImporter': 32,
        }

        self.renderer_node_mapping = {
            "arnold": {
                'attr_mapping': {
                    # resolution
                    "render_render_renderer": {"node": "defaultRenderGlobals.currentRenderer", "type": "string"},
                    "render_render_width": {"node": "defaultResolution.width", "type": "int"},
                    "render_render_height": {"node": "defaultResolution.height", "type": "int"},
                    "render_render_pixelAspectRatio": {"node": None, "type": "float"},
                    "render_render_deviceAspectRatio": {"node": "defaultResolution.deviceAspectRatio", "type": "float"},
                    "render_render_image_naming": {"node": "defaultRenderGlobals.imageFilePrefix", "type": "string"},
                    "render_render_image_format": {"node": "defaultRenderGlobals.imageFormat", "type": "int"},
                    "render_render_frame_name_ext": {"node": "defaultRenderGlobals.useFrameExt", "type": "int"},
                    "render_render_frame_padding": {"node": "defaultRenderGlobals.extensionPadding", "type": "int"},
                    # render settings
                    "arnold_arnold_autotx": {"node": 'defaultArnoldRenderOptions.autotx', 'type': 'int'},
                    "arnold_arnold_use_existing_tiled_textures": {"node": "defaultArnoldRenderOptions.use_existing_tiled_textures", "type": "int"},
                    "arnold_arnold_autotile": {"node": "defaultArnoldRenderOptions.autotile", "type": "int"},
                    "arnold_arnold_textureAcceptUnmipped": {"node": "defaultArnoldRenderOptions.textureAcceptUnmipped", "type": "int"},
                    "arnold_arnold_use_sample_clamp": {"node": "defaultArnoldRenderOptions.use_sample_clamp", "type": "int"},
                    "arnold_arnold_use_sample_clamp_AOVs": {"node": "defaultArnoldRenderOptions.use_sample_clamp_AOVs", "type": "int"},
                    "arnold_arnold_AASampleClamp": {"node": "defaultArnoldRenderOptions.AASampleClamp", "type": "int"},
                    "arnold_arnold_indirectSampleClamp": {"node": "defaultArnoldRenderOptions.indirectSampleClamp", "type": "int"},
                    "arnold_arnold_bucketSize": {"node": "defaultArnoldRenderOptions.bucketSize", "type": "int"},
                    "arnold_arnold_log_to_console": {"node": "defaultArnoldRenderOptions.log_to_console", "type": "int"},
                    "arnold_arnold_log_verbosity": {"node": "defaultArnoldRenderOptions.log_verbosity", "type": "int"},
                },
            },
            "vray": {
                "resolution": "vraySettings",
                "settings": "vraySettings",
                "attr_mapping": {
                    # resolution
                    "render_render_renderer": {"node": "defaultRenderGlobals.currentRenderer", "type": "string"},
                    "render_render_width": {"node": "defaultResolution.width", "type": "int"},
                    "render_render_height": {"node": "defaultResolution.height", "type": "int"},
                    "render_render_pixelAspectRatio": {"node": None, "type": "float"},
                    "render_render_deviceAspectRatio": {"node": "defaultResolution.deviceAspectRatio", "type": "float"},
                    "render_render_image_naming": {"node": "defaultRenderGlobals.imageFilePrefix", "type": "string"},
                    "render_render_image_format": {"node": "defaultRenderGlobals.imageFormat", "type": "int"},
                    "render_render_frame_name_ext": {"node": "defaultRenderGlobals.useFrameExt", "type": "int"},
                    "render_render_frame_padding": {"node": "defaultRenderGlobals.extensionPadding", "type": "int"},
                    # render settings
                    "maxwell_maxwell_render_time": {"node": "maxwellRenderOptions.renderTime", "type": "float"},
                    "maxwell_maxwell_sampling_level": {"node": "maxwellRenderOptions.samplingLevel", "type": "int"},
                    "maxwell_maxwell_motion_type": {"node": "maxwellRenderOptions.motionBlur", "type": "int"},
                    "maxwell_maxwell_multilight": {"node": "maxwellRenderOptions.multiLight", "type": "int"},
                    "maxwell_maxwell_write_mxs": {"node": "maxwellRenderOptions.persistentMXS", "type": "int"},
                    "maxwell_maxwell_write_mxi": {"node": "maxwellRenderOptions.writeMXI", "type": "int"},
                    "maxwell_maxwell_displacement": {"node": "maxwellRenderOptions.displacement", "type": "int"},
                    "maxwell_maxwell_dispersion": {"node": "maxwellRenderOptions.dispersion", "type": "int"},
                    "maxwell_maxwell_sky": {"node": "maxwellRenderOptions.skyType", "type": "int"},
                    "maxwell_maxwell_sun_power": {"node": "maxwellRenderOptions.sunPower", "type": "int"},
                    "maxwell_maxwell_use_image_based": {"node": "maxwellRenderOptions.useEnvironment", "type": "int"},
                    "maxwell_maxwell_image_intensity_multiplier": {"node": "maxwellRenderOptions.envWeight", "type": "float"},
                    "maxwell_maxwell_image_path": {"node": "maxwellRenderOptions.environment[0].envTexture", "type": "string"},
                    "maxwell_maxwell_render_type": {"node": "maxwellRenderOptions.renderType", "type": "int"},
                    "maxwell_maxwell_channels": {"node": "maxwellRenderOptions", "type": "int"},
                    "maxwell_maxwell_denoise_useGPU": {"node": "maxwellRenderOptions.denoiseGPU", "type": "int"},
                },
            },
            "maxwell": {
                "resolution": "defaultResolution",
                "settings": "maxwellRenderOptions",
                "attr_mapping": {
                    # resolution
                    "render_render_renderer": {"node": "defaultRenderGlobals.currentRenderer", "type": "string"},
                    "render_render_width": {"node": "defaultResolution.width", "type": "int"},
                    "render_render_height": {"node": "defaultResolution.height", "type": "int"},
                    "render_render_pixelAspectRatio": {"node": None, "type": "float"},
                    "render_render_deviceAspectRatio": {"node": "defaultResolution.deviceAspectRatio", "type": "float"},
                    "render_render_image_naming": {"node": "defaultRenderGlobals.imageFilePrefix", "type": "string"},
                    "render_render_image_format": {"node": "defaultRenderGlobals.imageFormat", "type": "int"},
                    "render_render_frame_name_ext": {"node": "defaultRenderGlobals.useFrameExt", "type": "int"},
                    "render_render_frame_padding": {"node": "defaultRenderGlobals.extensionPadding", "type": "int"},
                    # render settings
                    "maxwell_maxwell_render_time": {"node": "maxwellRenderOptions.renderTime", "type": "float"},
                    "maxwell_maxwell_sampling_level": {"node": "maxwellRenderOptions.samplingLevel", "type": "int"},
                    "maxwell_maxwell_motion_type": {"node": "maxwellRenderOptions.motionBlur", "type": "int"},
                    "maxwell_maxwell_multilight": {"node": "maxwellRenderOptions.multiLight", "type": "int"},
                    "maxwell_maxwell_write_mxs": {"node": "maxwellRenderOptions.persistentMXS", "type": "int"},
                    "maxwell_maxwell_write_mxi": {"node": "maxwellRenderOptions.writeMXI", "type": "int"},
                    "maxwell_maxwell_displacement": {"node": "maxwellRenderOptions.displacement", "type": "int"},
                    "maxwell_maxwell_dispersion": {"node": "maxwellRenderOptions.dispersion", "type": "int"},
                    "maxwell_maxwell_sky": {"node": "maxwellRenderOptions.skyType", "type": "int"},
                    "maxwell_maxwell_sun_power": {"node": "maxwellRenderOptions.sunPower", "type": "int"},
                    "maxwell_maxwell_use_image_based": {"node": "maxwellRenderOptions.useEnvironment", "type": "int"},
                    "maxwell_maxwell_image_intensity_multiplier": {"node": "maxwellRenderOptions.envWeight", "type": "float"},
                    "maxwell_maxwell_image_path": {"node": "maxwellRenderOptions.environment[0].envTexture", "type": "string"},
                    "maxwell_maxwell_render_type": {"node": "maxwellRenderOptions.renderType", "type": "int"},
                    "maxwell_maxwell_channels": {"node": "maxwellRenderOptions", "type": "int"},
                    "maxwell_maxwell_denoise_useGPU": {"node": "maxwellRenderOptions.denoiseGPU", "type": "int"},
                },
                "channels_mapping": {
                    "render_colors": "maxwellRenderOptions.renderChannel",
                    "embed_channels": "maxwellRenderOptions.embedAlpha",
                    "alpha": "maxwellRenderOptions.alphaChannel",
                    "opaque_alpha": "maxwellRenderOptions.opaqueChannel",
                    "deep": "maxwellRenderOptions.deepChannel",
                    "depth": "maxwellRenderOptions.depthChannel",
                    "shadow": "maxwellRenderOptions.shadowChannel",
                    "object_id": "maxwellRenderOptions.objIDChannel",
                    "material_id": "maxwellRenderOptions.matIDChannel",
                    "motion_vector": "maxwellRenderOptions.motionVectorChannel",
                    "roughness": "maxwellRenderOptions.roughnessChannel",
                    "fresnel": "maxwellRenderOptions.fresnelChannel",
                    "normals": "maxwellRenderOptions.normalsChannel",
                    "normal_space": "maxwellRenderOptions.normalsChannelSpace",
                    "position": "maxwellRenderOptions.positionChannel",
                    "position_space": "maxwellRenderOptions.positionChannelSpace",
                    "uv": "maxwellRenderOptions.uvChannel",
                    "reflectance": "maxwellRenderOptions.reflectanceChannel",
                    "custom_alpha": "maxwellRenderOptions.customAlphaChannel",
                }
            },
            "mentalRay": {
                "resolution": "defaultResolution",
                "settings": "maxwellRenderOptions",
            },
            "mayaSoftware": {
                "resolution": "defaultResolution",
                "settings": "defaultRenderGlobals",
                "attr_mapping": {
                    "render_render_renderer": {"node": "defaultRenderGlobals.currentRenderer", "type": "string"},
                    "render_render_width": {"node": "defaultResolution.width", "type": "int"},
                    "render_render_height": {"node": "defaultResolution.height", "type": "int"},
                    "render_render_pixelAspectRatio": {"node": None, "type": "float"},
                    "render_render_deviceAspectRatio": {"node": "defaultResolution.deviceAspectRatio", "type": "float"},
                    "render_render_image_naming": {"node": "defaultRenderGlobals.imageFilePrefix", "type": "string"},
                    "render_render_image_format": {"node": "defaultRenderGlobals.imageFormat", "type": "int"},
                    "render_render_frame_name_ext": {"node": "defaultRenderGlobals.useFrameExt", "type": "int"},
                    "render_render_frame_padding": {"node": "defaultRenderGlobals.extensionPadding", "type": "int"},
                }
            }
        }

        self.unit = cmds.currentUnit(query=True, linear=True)
        self.angle = cmds.currentUnit(query=True, angle=True)
        self.fpsMaya = cmds.currentUnit(query=True, time=True)
        self.fps = self.fpsMapping[self.fpsMaya]

        self.color_management = cmds.colorManagementPrefs(q=True, cmEnabled=True)

        # sceneConfiguartionScriptNode
        self.scene_configuration_node = "sceneConfigurationScriptNode"

    # ---
    # obsolete methods
    def getAnimationSettings(self):
        """ deprecated function use get_animation_settings """
        self.get_maya_project_settings()

    def getRenderSettings(self):
        self.get_maya_render_render_settings()

    # ---
    # methods

    def get_animation_settings(self):

        self.get_maya_project_settings()

    def get_maya_project_settings(self):
        """
        Get Maya Project Settings like info start, end, frameRate
        """
        self.unit = cmds.currentUnit(query=True, linear=True)
        self.angle = cmds.currentUnit(query=True, angle=True)
        self.fpsMaya = cmds.currentUnit(query=True, time=True)
        self.fps = self.fpsMapping[self.fpsMaya]

        self.minTime = cmds.playbackOptions(query=True, minTime=True)
        self.maxTime = cmds.playbackOptions(query=True, maxTime=True)
        self.animationStartTime = cmds.playbackOptions(query=True, animationStartTime=True)
        self.animationEndTime = cmds.playbackOptions(query=True, animationEndTime=True)
        self.playbackSpeed = cmds.playbackOptions(query=True, playbackSpeed=True)

    def get_maya_render_render_settings(self):
        """
        Get Render Settings width, height, pixelAspectRatio // no engine dependance
        """
        self.width = cmds.getAttr("%s.width" % self.rendererNodeSettings["Maya"])
        self.height = cmds.getAttr("%s.height" % self.rendererNodeSettings["Maya"])
        self.pixelAspectRatio = cmds.getAttr("%s.pixelAspect" % self.rendererNodeSettings["Maya"])

    def set_current_renderer(self, renderer='mayaSoftware'):
        """
        set the current renderer.
        """
        # we retrieve the current renderer from the maya defaultRenderGlobals.
        r = self.set_render_value(renderer="mayaSoftware", attr="render_render_renderer", value=renderer)
        if r:
            self.renderer = renderer

        # sepcial case init renderer
        if self.renderer == "maxwell":
            # execute maxwell command
            mel.eval("maxwellCreateGlobalNodes")

        return r

    def get_current_renderer(self):
        """
        get the current renderer.
        """
        # we retrieve the current renderer from the maya defaultRenderGlobals.
        self.renderer = self.get_render_value(renderer="mayaSoftware", attr="renderer")

        return self.renderer

    def get_render_value(self, renderer="current", attr=None):
        """
        this function retrieve the value of a renderer.
        """
        # get renderer
        if renderer == "current":
            self.renderer = self.get_current_renderer()
        else:
            if renderer not in self.renderer_node_mapping.keys():
                return
            else:
                self.renderer = renderer

        # check if attr exist
        if attr not in self.renderer_node_mapping[self.renderer]["attr_mapping"].keys():
            return

        value = cmds.getAttr(self.renderer_node_mapping[self.renderer]["attr_mapping"][attr]["node"])

        # retrieve data
        # special case
        special_case_attr = [
            "render_render_image_format",
        ]
        if attr not in special_case_attr:
            return value

        else:
            if attr == "render_render_image_format":
                # return beauty image format.
                for image_format_attr, image_format_value in self.renderer_node_mapping[self.renderer]["image_format_mapping"].iteritems():
                    if image_format_value == value:
                        return image_format_attr

    def set_render_value(self, renderer="current", attr=None, value=None):
        """
        this function is dedicated to set render settings on renderer. each renderer have his node so this func set the attr on the good node with the good attr.
        """

        logger.info('set_render_render_value(renderer={renderer}, attr={attr}, value={value})'.format(renderer=renderer, attr=attr, value=value))

        # get renderer
        if renderer == "current":
            self.renderer = self.get_current_renderer()
        else:
            if renderer not in self.renderer_node_mapping.keys():
                return
            else:
                self.renderer = renderer

        # check if attr exist
        if attr not in self.renderer_node_mapping[self.renderer]["attr_mapping"].keys():
            logger.error("bad news, the attribute {attr} for renderer {renderer} not exist into self.renderer_node_mapping".format(attr=attr, renderer=self.renderer))
            return

        # set data
        # special case
        special_case_attr = [
            "render_render_image_format",
            "render_render_frame_name_ext",
            "render_render_pixelAspectRatio",
            "maxwell_maxwell_channels"
        ]

        if attr not in special_case_attr:
            logger.debug("\t attr type : {t}".format(t=self.renderer_node_mapping[self.renderer]["attr_mapping"][attr]["type"]))

            if self.renderer_node_mapping[self.renderer]["attr_mapping"][attr]["type"] == "string":
                if not value:
                    logger.info('For string Value None convert to "".'.format(renderer=renderer, attr=attr, value=value))
                    value = ""
                cmds.setAttr(self.renderer_node_mapping[self.renderer]["attr_mapping"][attr]["node"], value, type="string")
            else:
                node, attribute = self.renderer_node_mapping[self.renderer]["attr_mapping"][attr]["node"].split(".")[:2]
                if cmds.attributeQuery(attribute, node=node, exists=True):
                    cmds.setAttr(self.renderer_node_mapping[self.renderer]["attr_mapping"][attr]["node"], value)
                else:
                    logger.info("node '%s' does not have attribute '%s'." % (node, attribute))
        else:
            if attr == "render_render_image_format":
                logger.info('\t set image_format node={node}, format={format}, maya_code={maya_code})'.format(node=self.renderer_node_mapping[self.renderer]["attr_mapping"][attr]["node"], format=value, maya_code=self.image_format_mapping[value]))
                cmds.setAttr(self.renderer_node_mapping[self.renderer]["attr_mapping"][attr]["node"], self.image_format_mapping[value])

            if attr == "render_render_pixelAspectRatio":
                # get device aspect ratio and multiply from width / height by the pixelAspectRatio aka value
                width = self.render_settings['render_render_width']
                height = self.render_settings['render_render_height']
                deviceAspectRatio = float(width) / float(height)
                new_render_render_deviceAspectRatio = deviceAspectRatio * value
                cmds.setAttr(self.renderer_node_mapping[self.renderer]["attr_mapping"]["render_render_deviceAspectRatio"]["node"], new_render_render_deviceAspectRatio)

            if attr == "render_render_frame_name_ext":
                # frame name ext need a special setup
                logger.info('\t set frame_name_ext value={value})'.format(value=value))
                # case name.#.ext
                if value == 'name.#.ext':
                    if value in self.frame_name_ext_mapping.keys():
                        for node_attr in self.frame_name_ext_mapping[value]:

                            cmds.setAttr(node_attr, self.frame_name_ext_mapping[value][node_attr])

            if attr == "maxwell_maxwell_channels":
                logger.info("Special Case Channel")
                # for each value set attr
                for v in value:

                    # each v are dict wich represent channel and value.
                    # the var self.renderer_node_mapping[self.renderer]["channels_mapping"] do the mapping betwween human name and maya node.
                    # get keys from v
                    key = v.keys()[0]
                    key_value = v[key]
                    logger.info("\tSet Channel {key} {key_value}".format(key=key, key_value=key_value))
                    cmds.setAttr(self.renderer_node_mapping[self.renderer]["channels_mapping"][key], key_value)

        return True

    def get_project_settings(self):
        """

        """
        self.ps.get_project_settings()

        # store it
        if 'final_final_unit' in self.ps.settings.keys():
            self.unit = self.ps.settings['final_final_unit']['value']

        if 'final_final_angle' in self.ps.settings.keys():
            self.angle = self.ps.settings['final_final_angle']['value']

        if 'final_final_framerate' in self.ps.settings.keys():
            self.fps = self.ps.settings['final_final_framerate']['value']
            for key in self.fpsMapping.keys():
                if self.fps == self.fpsMapping[key]:
                    self.fpsMaya = key

        if 'final_final_width' in self.ps.settings.keys():
            self.width = self.ps.settings['final_final_width']['value']

        if 'final_final_height' in self.ps.settings.keys():
            self.height = self.ps.settings['final_final_height']['value']

        if 'final_final_pixelAspectRatio' in self.ps.settings.keys():
            self.pixelAspectRatio = self.ps.settings['final_final_pixelAspectRatio']['value']

        if 'color_management_maya_enable_color_management' in self.ps.settings.keys():
            self.color_management = self.ps.settings['color_management_maya_enable_color_management']['value']

        # copy render settings from self.ps.settings
        for key in self.render_settings.keys():
            if key in self.ps.settings.keys():
                self.render_settings[key] = self.ps.settings[key]['value']

        return True

    def set_project_settings_to_maya(self):
        """
        apply to the scene the project settings retrieve from shotgun.
        """
        if not self.ps:
            self.get_project_settings()
        if not self.ps.settings:
            self.get_project_settings()

        logger.info("set linear : {v}".format(v=self.unit))
        cmds.currentUnit(linear=self.unit)
        logger.info("set angle : {v}".format(v=self.angle))
        cmds.currentUnit(angle=self.angle)
        logger.info("set time : {v} : {fps} fps".format(v=self.fpsMaya, fps=self.fps))
        cmds.currentUnit(time=self.fpsMaya)

        logger.info("set color management : {v}".format(v=self.color_management))
        cmds.colorManagementPrefs(edit=True, cmEnabled=self.color_management)

        if not self.batch:
            text = "Set Unit : {u}\nSet Angle : {a}\nSet Fps : {f}".format(u=self.unit, a=self.angle, f=self.fps)
            ppNotifier.notify(title="Set Project Main Settings", text=text, image=ppUtils.ppIcons.get_icon_path(name='settings'), time=1000)

        return True

    def set_project_render_settings_to_maya(self):
        """
        """
        # check if project settings object self.ps exist
        if not self.ps:
            self.get_project_settings()

        # check if settings already get
        if not self.ps.settings:
            self.get_project_settings()

        # if no render set exit.
        if 'render_render_renderer' not in self.render_settings.keys():
            return
        else:
            # check if value is not None
            if not self.render_settings['render_render_renderer']:
                return

        # set renderer
        self.set_current_renderer(renderer=self.render_settings['render_render_renderer'])

        # init text for the notifier
        text = ""

        # apply render settings to scene
        # all render settings must set into self.render_settings for each key we applied the value via the command set_render_value
        logger.info("Render Settings : {rs}".format(rs=self.render_settings))

        for key in self.render_settings.keys():

            if self.set_render_value(renderer=self.render_settings['render_render_renderer'], attr=key, value=self.render_settings[key]):
                logger.debug("set {k} : {v}".format(k=key, v=self.render_settings[key]))

                text += "{k}, ".format(k=key.replace("render_render_", ""))
            else:
                logger.warning("can't set {k} : {v}".format(k=key, v=self.render_settings[key]))

        if not self.batch:
            ppNotifier.notify(title="Set Project Render Settings", text=text, image=ppUtils.ppIcons.get_icon_path(name='render_render_settings'), time=4000)

        # now apply engine settings if exist, like maxwell
        engine_settings = self.ps.get_settings(category=self.render_settings['render_render_renderer'])
        if not engine_settings:
            logger.info("No Engine Settings")

        else:
            # init text for the notifier
            text = ""

            # special case init render before apply
            for key in engine_settings.keys():

                if self.set_render_value(renderer=self.render_settings['render_render_renderer'], attr=key, value=engine_settings[key]["value"]):
                    logger.debug("set {k} : {v}".format(k=key, v=engine_settings[key]))

                    text += "{k}, ".format(k=key.replace("render_render_", ""))
                else:
                    logger.warning("can't set {k} : {v}".format(k=key, v=engine_settings[key]))

            if not self.batch:
                ppNotifier.notify(title="Set Project Render Settings", text=text, image=ppUtils.ppIcons.get_icon_path(name='render_render_settings'), time=4000)

        return True

    def create_sceneConfigurationScriptNode(self):
        """
        """
        #  check if node exist
        n = self.scene_configuration_node
        if not cmds.objExists(self.scene_configuration_node):

            # create node
            n = cmds.createNode("script", name=self.scene_configuration_node)

        # force update timeslider
        # retrieve currentScene info
        self.get_maya_project_settings()

        # syntax
        syntax = "playbackOptions -min {min} -max {max} -ast {ast} -aet {aet}".format(min=self.minTime, max=self.maxTime, ast=self.animationStartTime, aet=self.animationEndTime)
        cmds.scriptNode(n, edit=True, scriptType=6, beforeScript=syntax, sourceType="mel")

        return True


def create_sceneConfigurationScriptNode():
    """
    """

    s = Scene()
    return s.create_sceneConfigurationScriptNode()
