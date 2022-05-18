# -*- coding: utf-8 -*-

import maya.cmds as cmds
import maya.mel as mel
import logging
import sys
import os
import ppUtils.ppPath as ppPath
import ppma.core.ppScene as ppScene


# loggger
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppIO')
logger.setLevel(logging.INFO)


class IO(object):
    """docstring for IO"""
    def __init__(self):
        super(IO, self).__init__()

        # ppPath
        self.tmp_ppPath = ppPath.TmpPath()

        # default_extension = "ma"
        self.default_extension = "ma"

        # file type mapping for maya
        self.file_type_mapping = {
            "ma": "mayaAscii",
            "mb": "mayaBinary",
            "abc": "Alembic",
            "fbx": "FBX"
        }

        # check if the extension is good
        # self.extension_by_step = {
        #                           'model': {'from': '.ma', 'to': '.mb'}
        # }

        # get platform
        self.system = sys.platform
        self.local_path_mapping = {
            "linux2": "local_path_linux",
            "win32": "local_path_windows",
            "mac": "local_path_mac"
        }

        # Get Scene Info
        self.scene = ppScene.Scene()
        self.scene.getAnimationSettings()

    def get_maya_extension_from_step(self, step):
        """
        this function return the good extension to use in maya by step.
        """
        
        if step in self.extension_by_step.keys():
            return self.extension_by_step[step]["to"]
        else:
            return self.default_extension


class ExportSelection(IO):
    """docstring for ExportSelection"""
    def __init__(self):
        super(ExportSelection, self).__init__()
        pass

    def check_path(self, path, file_type, file_extension):
        """
        This function check if the path is provided.
        If the path is provided it check if we must create the directory tree.
        And if the path is not provided it return a tmp path
        """
        # check if path defined
        if not path:
            # get tmp path from lib ppUtils.ppPath TmpPath()
            tmp_dir = self.tmp_ppPath.get_tmp_directory(file_type=self.tmp_ppPath.published_file_type[file_type]["local_dir_name"])
            tmp_name = self.tmp_ppPath.get_tmp_name(file_type=self.tmp_ppPath.published_file_type[file_type]["local_dir_name"])

            path = "{tmp_dir}/{tmp_name}.{file_extension}".format(tmp_dir=tmp_dir, tmp_name=tmp_name, file_extension=file_extension)

        else:
            # check path exist
            if not os.path.exists(os.path.dirname(path)):
                # create directory
                os.makedirs(os.path.dirname(path))

        return path

    def _export_maya(self, selection, path=None, file_extension="ma", file_type="camera_file"):
        """
        export selection as ma file.
        """

        # Select Selection
        try:
            cmds.select(selection, replace=True)
        except:
            logging.info("Can't Select: {s}".format(s=selection))
            return False

        # check path
        path = self.check_path(path=path, file_type=file_type, file_extension=file_extension)

        # resume before export
        logging.info("Export Selection - Maya - file_type: {file_type}\
            \n\t selection: {sel}\
            \n\t path: {path}".format(file_type=file_type, sel=selection, path=path))

        # file_type camera_file
        if file_type == "default":
            cmds.file(path, force=True, es=True, op="v=1", typ=self.file_type_mapping[file_extension], pr=False)
        if file_type == "camera_file":
            cmds.file(path, force=True, es=True, op="v=1", typ=self.file_type_mapping[file_extension], pr=False)

        # check file exist
        if os.path.exists(path):
            return path
        else:
            return

    def _export_ma(self, selection, path=None, file_type="camera_file"):
        """
        export selection as ma file.
        """
        r = self._export_maya(selection=selection, path=path, file_extension="ma", file_type=file_type)
        return r

    def _export_mb(self, selection, path=None, file_type="camera_file"):
        """
        export selection as ma file.
        """
        r = self._export_maya(selection=selection, path=path, file_extension="mb", file_type=file_type)
        return r

    def _export_abc(self, selection, path=None, handle=0, file_type="camera_file"):
        """
        export selection as abc file.
        """
        # Select Selection
        try:
            cmds.select(selection, replace=True)
        except:
            logging.info("Can't Select: {s}".format(s=selection))
            return False

        # check path
        path = self.check_path(path=path, file_type=file_type, file_extension="abc")

        # resume before export
        logging.info("Export Selection - Alembic - file_type: {file_type}\
            \n\t selection: {sel}\
            \n\t path: {path}".format(file_type=file_type, sel=selection, path=path))

        # build cmd
        export_result = None

        if file_type == "camera_file" or file_type == "default":
            abcCmd = 'AbcExport -j "-frameRange {minTime} {maxTime} -worldSpace -stripNamespaces -writeVisibility -eulerFilter -root {root} -file {path}"'.format(minTime=self.scene.minTime-handle, maxTime=self.scene.maxTime+handle, root=selection, path=path)
            logging.info("Export Abc Cmd: %s" % abcCmd)
            export_result = mel.eval(abcCmd)

        if not export_result and os.path.exists(path):
            return path
        else:
            return

    def _export_fbx(self, selection, path=None, file_type="camera_file", fbx_version="FBX201400"):
        """ This function export the selected node as fbx file.

        :param selection: node list
        :type name: str
        :param path: the path were you want to export
        :type path: str
        :param file_type: "camera_file" or "default"
        :type file_type: str
        :param fbx_version: the fbx version, you could retrieve the available fbx version
        https://knowledge.autodesk.com/support/maya/learn-explore/caas/CloudHelp/cloudhelp/2016/ENU/Maya/files/GUID-6CCE943A-2ED4-4CEE-96D4-9CB19C28F4E0-htm.html
        :type fbx_version: str
        :returns: the path
        :rtype: str
        """

        # Select Selection
        try:
            cmds.select(selection, replace=True)
        except:
            logging.info("Can't Select: {s}".format(s=selection))
            return False

        # check path
        path = self.check_path(path=path, file_type=file_type, file_extension="fbx")

        # resume before export
        logging.info("Export Selection - FBX - file_type: {file_type}\
            \n\t selection: {sel}\
            \n\t path: {path}".format(file_type=file_type, sel=selection, path=path))

        # build cmd
        export_result = None

        if file_type == "camera_file" or file_type == "default":
            # fbx have a particular export workflow, first step we must export the option
            fbxCmdOptions = []
            fbxCmdOptions.append('FBXExportAnimationOnly -v 0')  # Use this script to export only animation.
            fbxCmdOptions.append('FBXExportBakeComplexAnimation -v 1')  # This command is the script equivalent of the Bake animation option.
            # fbxCmdOptions.append('FBXExportBakeResampleAll -v 1')  # This command is the script version of the Resample Animation option in the FBX Exporter.
            fbxCmdOptions.append('FBXExportCacheFile -v 1')  # This command is the script version of the Geometry Cache file(s) option in the FBX Exporter.
            fbxCmdOptions.append('FBXExportCameras -v 1')  # Use this function to either include or exclude cameras in your FBX export.
            fbxCmdOptions.append('FBXExportConstraints -v 0')  # Causes all the constraints defined in the Maya scene to be either included or excluded from the exported FBX file.
            fbxCmdOptions.append('FBXExportEmbeddedTextures -v 0')  # Causes all the constraints defined in the Maya scene to be either included or excluded from the exported FBX file.
            fbxCmdOptions.append('FBXExportInAscii -v 1')  # Use this function to export as an ASCII file.
            fbxCmdOptions.append('FBXExportInstances -v 0')  # This is the script equivalent of the Preserve Instances option in the UI.
            fbxCmdOptions.append('FBXExportLights -v 0')  # Use this function to either exclude or include lights in the exported FBX file. See Lights for more information.
            fbxCmdOptions.append('FBXExportQuaternion -v quaternion')  # Use the quaternion interpolation script to select how to export your quaternion interpolations from the host application.
            fbxCmdOptions.append('FBXExportShapes -v 0')  # Use this function to either exclude or include shape deformations with your FBX file.
            # export with a specific FBX version
            fbxCmdOptions.append('FBXExportFileVersion {fbx_version}'.format(fbx_version=fbx_version))
            for fbxCmdOption in fbxCmdOptions:
                logging.info("Set Fbx Export Option: %s" % fbxCmdOption)
                mel.eval(fbxCmdOption)
            # second step, we launch the export command for exporting data
            fbxCmd = 'FBXExport -f "{path}" -s'.format(path=path)
            export_result = mel.eval(fbxCmd)

        if export_result == 'Success':
            return path
        else:
            return

    def _export_mxs(self, selection, path=None, animated=False, start=1, end=1, camera=None, file_type="mxs_static"):
        """
        export selection as mxs file.
        """

        # Select Selection
        try:
            cmds.select(selection, replace=True)
        except:
            logging.info("Can't Select: {s}".format(s=selection))
            return False

        # check path
        path = self.check_path(path=path, file_type=file_type, file_extension="mxs")

        # maxwell command inside maya
        # maxwell -exportMXS $file $anim $startFrame $endFrame $exportCam $camName;

        # resume before export
        logging.info("Export Selection - MXS - file_type: {file_type}\
            \n\t selection: {sel}\
            \n\t path: {path}".format(file_type=file_type, sel=selection, path=path))

        # build cmd
        export_result = None

        # define settings
        exp_animated = 0
        use_camera = 0
        if animated:
            exp_animated = 1

        if camera:
            use_camera = 1

        export_cmd = 'maxwell -exportMXS "{path}" {exp_animated} {start_frame} {end_frame} {use_camera} {camera}'.format(path=path, exp_animated=exp_animated, start_frame=start, end_frame=end, use_camera=use_camera, camera=camera)
        logging.info("Export Mxs Cmd: %s" % export_cmd)
        export_result = mel.eval(export_cmd)

        if not export_result or os.path.exists(path):
            return path
        else:
            return False

    def _export_vrscene(self, path=None, animated=False, start=1, end=1, file_type="vrscene"):
        """
        export selection as vrscene file.
        """

        for plugin in ['vrayformaya']:
            if plugin not in cmds.pluginInfo(query=True, listPlugins=True):
                try:
                    cmds.loadPlugin(plugin)
                    logger.info("pp - plugin successful loaded: %s" % plugin)
                except:
                    logger.warning("pp - can't load plugin: %s" % plugin)

        # check path
        path = self.check_path(path=path, file_type=file_type, file_extension="vrscene")

        settings = {
            "vraySettings.vrscene_on": {"orig": None, "new_value": 1, "type": "int"},
            "vraySettings.vrscene_render_on": {"orig": None, "new_value": 0, "type": "int"},

            "vraySettings.vrscene_filename": {"orig": None, "new_value": path, "type": "string"},
            "vraySettings.misc_separateFiles": {"orig": None, "new_value": 0, "type": "int"},
            "vraySettings.misc_eachFrameInFile": {"orig": None, "new_value": 0, "type": "int"},
            "vraySettings.misc_meshAsHex": {"orig": None, "new_value": 1, "type": "int"},
            "vraySettings.misc_transformAsHex": {"orig": None, "new_value": 1, "type": "int"},
            "vraySettings.misc_compressedVrscene": {"orig": None, "new_value": 1, "type": "int"},

            "vraySettings.vfbOn": {"orig": None, "new_value": 0, "type": "int"},

            "vraySettings.animType": {"orig": None, "new_value": animated, "type": "int"},
            "defaultRenderGlobals.startFrame": {"orig": None, "new_value": start, "type": "int"},
            "defaultRenderGlobals.endFrame": {"orig": None, "new_value": end, "type": "int"},
            "defaultRenderGlobals.byFrameStep": {"orig": None, "new_value": 1, "type": "int"},
            "vraySettings.runToAnimationStart": {"orig": None, "new_value": 1, "type": "int"},
        }

        # get current settings
        for k in settings.keys():
            settings[k]["orig"] = cmds.getAttr(k)

        # Apply export settings
        for k in settings.keys():
            if settings[k]["type"] == "string":
                cmds.setAttr(k, settings[k]["new_value"], type="string")
            else:
                cmds.setAttr(k, settings[k]["new_value"])

        # resume before export
        logging.info("Export Scene - vrscene - file_type: {file_type}\n\t path: {path}".format(file_type=file_type, path=path))

        # in mel help vrend
        export_cmd = 'vrend'
        export_result = mel.eval(export_cmd)

        if not export_result or os.path.exists(path):
            # restore settings
            for k in settings.keys():
                if settings[k]["type"] == "string":
                    if settings[k]["orig"]:
                        cmds.setAttr(k, settings[k]["orig"], type="string")
                else:
                    cmds.setAttr(k, settings[k]["orig"])
            return path
        else:
            return False
