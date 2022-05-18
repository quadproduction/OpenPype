# -*- coding: utf-8 -*-

"""
common classes and functions about node
"""

import logging
import os
import sys
import datetime
import sgtk
import webbrowser
import urllib
import pprint

import ppUtils.ppSettings as ppSettings
import ppUtils.ppNotifier as ppNotifier
from ppUtils import ppImgTools
from ppSgtkLibs import ppSgtkPublisher
import ppSgtkLibs.ppSgtkCmds as ppSgtkCmds
import ppSgtkLibs.ppSgtkUtils as ppSgtkUtils
import ppma.core.ppSceneManagement as ppSceneManagement
import ppma.core.ppIO as ppIO
import ppma.action.ppSanityCheck as ppSanityCheck
import ppma.core.ppScene as ppScene
import ppUtils.ppIcons
import ppma.core.ppUi as ppUi
from ppGui.ppUtils import Worker

import maya.cmds as cmds
import maya.mel as mel

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppActions')
logger.setLevel(logging.DEBUG)


class Action(object):
    """docstring for Action"""
    def __init__(self):
        super(Action, self).__init__()

        self.batch = cmds.about(batch=True)

        self.sceneTypeMapping = {
            "ma": "mayaAscii",
            "mb": "mayaBinary",
            "abc": "Alembic"
        }

        # path mapping
        self.system = sys.platform
        self.local_path_mapping = {
            "linux2": "local_path_linux",
            "win32": "local_path_windows",
            "mac": "local_path_mac"
        }

        # self.settings
        self.settings = {
            "handle": 30
        }

        # define icons path
        self.icons = ppUtils.ppIcons.Icons()

        self.sgCmds = ppSgtkCmds.Cmds()

        # init local var for export
        self.rootLocalFolder = "d:"
        if self.system == "linux2":
            self.rootLocalFolder = os.environ['HOME']
        try:
            self.rootLocalFolder = os.environ['PP_DATA_DIR']
        except:
            logger.warning("The Env Var 'PP_DATA_DIR' not exist")

        # Get Export Selection Command
        self.export_selection_cmd = ppIO.ExportSelection()

        # define publish template.
        self.publish_template_mapping = {
            'Asset': 'maya_asset_publish',
            'Shot': 'maya_shot_publish'
        }

        # check if the extension is good
        self.default_maya_file_extension = "ma"
        self.maya_file_extension_mapping = {
            'model': 'mb'
        }
        # publish copy mode
        self.copy_mode_settings = {
            "normal": "nothing",
            "in_progress": "nothing"
        }

        # init self.sg_publish
        self.sg_publish = None

    def get_actionDescription(self, action):
        """ """

        if "open_maya_scene" in action:
            return {
            "name": "open_maya_scene",
            "params": None,
            "icon": self.icons.get_icon_path(name='open'),
            "caption": "Open Maya Scene File",
            "description": "Open Maya Scene File"
        }
        if "jumpTo_shotgun" in action:
            return {
            "name": "jumpTo_shotgun",
            "params": None,
            "icon": self.icons.get_icon_path(name='web'),
            "caption": "",
            "description": "Jump to Shotgun."
        }
        if "jumpTo_filesystem" in action:
            return {
                "name": "jumpTo_filesystem",
                "params": None,
                "icon": self.icons.get_icon_path(name='server'),
                "caption": "",
                "description": "Jump to File System."
            }
        if "set_project" in action:
            return {
                "name": "set_project",
                "params": None,
                "icon": self.icons.get_icon_path(name='open'),
                "caption": "",
                "description": "Set Project."
            }
        if "publish_scene" in action:
            return {
                "name": "publish_scene",
                "params": None,
                "icon": self.icons.get_icon_path(name='publish'),
                "caption": "",
                "description": "Publish the current Scene.\n- With Sanity Check.\n Status : Approved"
            }
        if "publish_work_scene" in action:
            return {
                "name": "publish_work_scene",
                "params": None,
                "icon": self.icons.get_icon_path(name='save_up'),
                "caption": "",
                "description": "Publish the current Scene.\n- With Sanity Check.\n Status : Approved"
            }
        if "push_screenshot_to_thumbnail" in action:
            return {
                "name": "push_screenshot_to_thumbnail",
                "params": None,
                "icon": self.icons.get_icon_path(name='push_screenshot_to_thumbnail'),
                "caption": "",
                "description": "Push the current screenshot to thumbnail entity."
            }
        if "create_note" in action:
            return {
                "name": "create_note",
                "params": None,
                "icon": self.icons.get_icon_path(name='create_note'),
                "caption": "",
                "description": "Create Note based on Current Context."
            }
        if "create_asset" in action:
            return {
                "name": "create_asset",
                "params": None,
                "icon": self.icons.get_icon_path(name='create_asset'),
                "caption": "",
                "description": "Create Asset."
            }
        if "create_shot" in action:
            return {
                "name": "create_shot",
                "params": None,
                "icon": self.icons.get_icon_path(name='create_shot'),
                "caption": "",
                "description": "Create Shot."
            }
        if "create_timelog" in action:
            return {
                "name": "create_timelog",
                "params": None,
                "icon": self.icons.get_icon_path(name='create_timelog'),
                "caption": "",
                "description": "Create Timelog based on Current Context."
            }
        if "start_sgtk" in action:
            return {
                "name": "start_sgtk",
                "params": None,
                "icon": self.icons.get_icon_path(name='start_sgtk'),
                "caption": "",
                "description": "Start Shotgun Engine."
            }
        if "get_project_settings" in action:
            return {
                "name": "get_project_main_settings",
                "params": None,
                "icon": self.icons.get_icon_path(name='settings'),
                "caption": "",
                "description": "Get Project Settings like\n-framerate\n-unit\n-angle"
            }
        if "get_project_render_settings" in action:
            return {
                "name": "get_project_render_settings",
                "params": None,
                "icon": self.icons.get_icon_path(name='render_settings'),
                "caption": "",
                "description": "Get Project Render Settings like\n image size, file naming, etc.."
            }
        if "get_sound" in action:
            return {
                "name": "get_sound",
                "params": None,
                "icon": self.icons.get_icon_path(name='render_settings'),
                "caption": "",
                "description": "Get Project Render Settings like\n image size, file naming, etc.."
            }
        if "auto_get_sound" in action:
            return {
                "name": "auto_get_sound",
                "params": None,
                "icon": self.icons.get_icon_path(name='render_settings'),
                "caption": "",
                "description": "Get Project Render Settings like\n image size, file naming, etc.."
            }
        if "get_image_as_image_plane" in action:
            return {
                "name": "get_image_as_image_plane",
                "params": None,
                "icon": self.icons.get_icon_path(name='render_settings'),
                "caption": "",
                "description": "Get Project Render Settings like\n image size, file naming, etc.."
            }
        if "get_image_as_free_image_plane" in action:
            return {
                "name": "get_image_as_free_image_plane",
                "params": None,
                "icon": self.icons.get_icon_path(name='render_settings'),
                "caption": "",
                "description": "Get Project Render Settings like\n image size, file naming, etc.."
            }
        return None

    def execute_action(self, action, params=None):
        """ """
        logger.info("execute_action(action={action}, params={params})".format(action=action, params=params))
        r = None

        if "open_maya_scene" == action:
            # launch
            path = self.get_path(params["sgpf"])
            if path:
                r = self._open_maya_file(path=path, params=params)

        if "jumpTo_shotgun" == action:
            # launch web browser
            r = self._jumpTo_shotgun()

        if "jumpTo_filesystem" == action:
            # launch web browser
            r = self._jumpTo_filesystem()

        if "set_project" == action:
            # launch web browser
            path = self.get_path(params["sgpf"])
            if path:
                r = self._set_project(path, params=params)

        if "publish_scene" == action:
            # launch web browser
            r = self._publish_scene(params=params, pre_publish=True, copy_mode="nothing", set_status="apr", separate_process=True)

        if "publish_scene_unseparate" == action:
            # launch web browser
            r = self._publish_scene(params=params, pre_publish=True, copy_mode="nothing", set_status="apr", separate_process=False)

        if "publish_work_scene" == action:
            # launch web browser
            r = self._publish_scene(params=params, pre_publish=False, copy_mode="nothing", set_status="ip", separate_process=True)

        if "publish_work_scene_unseparate" == action:
            # launch web browser
            r = self._publish_scene(params=params, pre_publish=False, copy_mode="nothing", set_status="ip", separate_process=False)

        if "publish_playblast_scene" == action:
            # launch web browser
            r = self._publish_scene(params=params, pre_publish=False, copy_mode="nothing", set_status="ip", separate_process=False)

        if "publish_export_animation_scene" == action:
            # launch web browser
            r = self._publish_scene(params=params, pre_publish=False, copy_mode="nothing", set_status="apr", separate_process=False)

        if "publish_render_scene" == action:
            # launch web browser
            r = self._publish_scene(params=params, pre_publish=False, copy_mode="nothing", set_status="apr", separate_process=False)

        if "autocapture_screenshot" == action:
            action = "capture_viewport"

        if "capture_viewport" == action:
            # launch web browser
            r = self._capture_viewport(path=None, width=1280, height=720)

        if "capture_renderview" == action:
            # launch web browser
            r = self._capture_renderview()

        if "manual_capture_screenshot" == action:
            action = "capture_manual"

        if "capture_manual" == action:
            r = self._capture_manual()

        if "push_screenshot_to_thumbnail" == action:
            # launch web browser
            r = self._push_screenshot_to_thumbnail(path=params['path'], entityType=params['entityType'], entityId=params['entityId'])

        if "create_note" == action:
            # launch web browser based on context
            r = self._create_note()

        if "create_asset" == action:
            # launch web browser based on context
            r = self._create_asset()

        if "create_shot" == action:
            # launch web browser based on context
            r = self._create_shot()

        if "create_timelog" == action:
            # launch web browser based on context
            r = self._create_timelog()

        if "start_sgtk" == action:
            # launch web browser based on context
            r = self._start_sgtk()

        if "get_project_settings" == action:
            r = self._get_project_main_settings()

        if "get_project_render_settings" == action:
            r = self._get_project_render_settings()

        if "auto_get_sound" == action:
            r = self._auto_get_sound()

        if "get_image_as_image_plane" == action:
            r = self._get_image_as_image_plane()

        if "get_image_as_free_image_plane" == action:
            r = self._get_image_as_image_plane(free_image_plane=True)

        if "get_vrscene" == action:
            r = self._get_vrscene()
        return r

    def get_path(self, sgpf):
        """ """
        if 'path' in sgpf.keys():
            if self.local_path_mapping[self.system] in sgpf['path'].keys():
                return sgpf['path'][self.local_path_mapping[self.system]]
        else:
            return None

    def _jumpTo_shotgun(self):
        """ """
        url = sgtk.platform.current_engine().context.shotgun_url
        logger.debug("Launch Web Browser {url}".format(url=url))
        webbrowser.open(url="{url}".format(url=url))

    def _jumpTo_filesystem(self):
        """
        Jump from context to FS
        """
        # launch one window for each location on disk
        paths = sgtk.platform.current_engine().context.filesystem_locations
        for disk_location in paths:

            # get the setting
            system = sys.platform

            # run the app
            if system == "linux2":
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "win32":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)

            os.system(cmd)

    def _switch_from_publish_to_work(self, path):
        """
        this function switch maya from the publish path to the work path.
        """

        # we must switch to work scene to preserve published file
        # get template from path
        publish_template_path = self.sgCmds.tk.template_from_path(path)
        publish_fields = publish_template_path.get_fields(path)

        # get work scene path
        work_template_path = self.sgCmds.get_switchTemplate(path=path, template=None, replace=["publish", "work"])

        #  copy publish fields to work fields and enhance
        work_fields = publish_fields
        work_fields['iteration'] = 1
        work_fields['current_user_name'] = os.getlogin()

        # get the next iteration available for the work template path
        r = self.sgCmds.get_nextRevision(template=work_template_path, templateFields=work_fields, use_field='version')
        work_fields['iteration'] = r

        work_path = work_template_path.apply_fields(work_fields)

        # create dirs
        if not os.path.exists(os.path.dirname(work_path)):
            logger.info("Create File Structure on Disk")
            self.sgCmds.tk.create_filesystem_structure(entity_type=self.sgCmds.ctx.entity['type'], entity_id=self.sgCmds.ctx.entity['id'], engine ="tk-maya")

        # rename the scene
        self._rename_maya_scene(path=work_path)

        return True

    def _set_project(self, path, params=None):
        """

        """
        maya_project_template = None
        maya_project_template_settings = {
                                    "Asset": "asset_root",
                                    "Shot": "shot_root"
        }

        current_template_path = self.sgCmds.tk.template_from_path(path)
        fields = current_template_path.get_fields(path)

        for key in maya_project_template_settings.keys():
            if key in fields.keys():
                maya_project_template = maya_project_template_settings[key]

        template_path = self.sgCmds.tk.templates[maya_project_template]
        r = template_path.apply_fields(fields)

        if os.path.exists(r):
            cmds.workspace(r, openWorkspace=True)
            logging.info("Set Project Done =============> %s" % r)
            return True
        else:
            return False

    def _open_maya_file(self, path, params=None):
        """ """

        logging.info("Open Scene: %s" % path)

        # define default scene type
        sceneType = self.sceneTypeMapping["ma"]

        # get scene type from path
        ext = path.split('.')[len(path.split('.')) - 1]
        if ext in self.sceneTypeMapping.keys():
            sceneType = self.sceneTypeMapping[ext]

        cmds.file(path, open=True, force=True, options="v=0", typ=sceneType)

        mel.eval('addRecentFile("{path}", "{sceneType}")'.format(path=path, sceneType=sceneType))

        logging.info("Open Scene Done =============> %s" % path)

        #  set project
        self._set_project(path=path)

        if params:

            self.sgCmds.do_initTk(projectPath=path)

            logger.info("params: {p}".format(p=params))

            # self._switch_from_publish_to_work(path=path)
            self._versionUp_maya_scene(save=False)

            # Set New Context Post Open
            e = self.sgCmds.do_setNewContext(taskId=params["sgpf"]['task']['id'])

            # push shotgun published file to env
            ppSgtkUtils.push_to_env(published_file_id=params["sgpf"]["id"], context=self.sgCmds.ctx)

            if e:
                logger.debug("Context Change Done =============>")
            else:
                logger.debug("Context Change Failed >=============>")
                return

    def _rename_maya_scene(self, path, params=None):
        """ """
        if not path:
            return

        logger.debug("Maya Scene renammed to: {path}".format(path=path))
        cmds.file(rename=path)

    def _versionUp_maya_scene(self, save=True, publish=True, params=None):
        """
        versionUp maya scene is a publish scene without sanity check.
        the scene is published with the status "in progress".
        """

        # try to retrieve template from current path
        sn = cmds.file(q=True, sn=True)
        t = self.sgCmds.tk.template_from_path(sn)

        use_field = 'iteration'

        if t:
            f = t.get_fields(sn)
            if not "iteration" in f.keys():
                use_field = "version"

            r = self.sgCmds.get_nextRevision(path=sn, use_field=use_field)
            logger.debug("Next {use_field} available : {r}".format(use_field=use_field, r=r))
            f[use_field] = r

            newPath = t.apply_fields(f)

            logger.debug("Maya Scene renammed to: {path}".format(path=newPath))
            self._rename_maya_scene(path=newPath)

        else:
            logger.debug("Can't get a template path ")

    def get_extension(self, step):
        """
        retireve maya file extension based on step
        """
        if step in self.maya_file_extension_mapping.keys():
            return self.maya_file_extension_mapping[step]
        else:
            return self.default_maya_file_extension

    def get_publish_path(self):
        """
        retireve path for a params
        """

        # init
        self.publish_path = None
        self.publish_path_fields = {}

        # ------------------------
        # setup publish path
        # get template
        publish_template_name = self.publish_template_mapping[self.publishArgs['linkType']]
        self.publish_template = self.sgCmds.tk.templates[publish_template_name]

        # get path from template
        # maya_asset_publish assets/{sg_asset_type}/{Asset}/{Step}/publish/maya/scenes/{Asset}_{Step}_{name}_v{version}.{maya_ext}
        # maya_shot_publish sequences/{Sequence}/{Shot}/{Step}/publish/maya/scenes/{Shot}_{Step}_{name}_v{version}.ma
        self.publish_path_fields = {
                    "sg_asset_type": None,
                    "Sequence": None,
                    "Shot": self.publishArgs['linkName'],
                    "Asset": self.publishArgs['linkName'],
                    "Step": self.publishArgs['stepName'],
                    "Task": self.publishArgs['taskName'],
                    "name": self.publishArgs['publishName'],
                    "version": 1,
                    "maya_ext": self.get_extension(step=self.publishArgs['stepName'])
                }

        # Case Asset retrieve sg_asset_type
        if self.publishArgs['linkType'] == "Asset":
            logger.info("Get sg_asset_type : {name}, project id : {project}".format(name=self.publishArgs['linkName'], project=self.sgCmds.ctx.project["id"]))
            sgResult = self.sgCmds.tk.shotgun.find_one('Asset', [["code", "is", self.publishArgs['linkName']], ["project.Project.id", "is", self.sgCmds.ctx.project["id"]]], ['sg_asset_type'])
            
            if sgResult:
                self.publish_path_fields["sg_asset_type"] = sgResult["sg_asset_type"]
            else:
                logger.info("Can't Get sg_asset_type : {name}, project id : {project}".format(name=self.publishArgs['linkName'], project=self.sgCmds.ctx.project["id"]))

        # Case Shot retrieve Sequence
        elif self.publishArgs['linkType'] == "Shot":
            logger.info("Get Sequence : {name}, project id : {project}".format(name=self.publishArgs['linkName'], project=self.sgCmds.ctx.project["id"]))
            sgResult = self.sgCmds.tk.shotgun.find_one('Shot', [["code", "is", self.publishArgs['linkName']], ["project.Project.id", "is", self.sgCmds.ctx.project["id"]]], ['sg_sequence'])

            if sgResult:
                self.publish_path_fields["Sequence"] = sgResult["sg_sequence"]["name"]
            else:
                logger.info("Can't Get Sequence : {name}, project id : {project}".format(name=self.publishArgs['linkName'], project=self.sgCmds.ctx.project["id"]))

        else:
            logger.info("Link Type is : {linkType}".format(linkType=self.publishArgs['linkType']))

        # get next revision available
        next_revision_available = self.sgCmds.get_nextRevision(path=None, template=self.publish_template, templateFields=self.publish_path_fields, use_field='version')
        self.publish_path_fields["version"] = next_revision_available
        self.publish_path = self.publish_template.apply_fields(self.publish_path_fields)

        logger.info("publish_path : {publish_path}".format(publish_path=self.publish_path))

        return self.publish_path

    def get_task_id(self, entity_type, entity_name, task_name):
        """
        """
        request = [["content", "is", task_name], ["entity.{entity_type}.code".format(entity_type=entity_type), "is", entity_name], ["project.Project.id", "is", self.sgCmds.ctx.project["id"]]]
        task_id = self.sgCmds.tk.shotgun.find_one("Task", request)['id']

        return task_id

    def _publish_scene(self, params=None, pre_publish=True, copy_mode="nothing", set_status="apr", separate_process=True):
        """
        :param publish_mode: mode available "normal" the file is published the incrementation is done by the publisher. "in_progress" th incrementation is done by versioUp and the publish publish the current maya scene.)
        """
        logger.debug("_publish_scene(params={params})".format(params=params))
        # params exemple params={'comment': '', 'thumbnail': None, 'context': {'stepName': 'model', 'taskName': 'model', 'entityType': 'Asset', 'publishName': 'basic', 'entity': 'anOtherAsset'}}

        # get current app and context
        self.sgCmds.do_initTk()

        # build publish arg
        self.publishArgs = {
            'project': self.sgCmds.app_instance.sgtk.roots['primary'],
            'fileType': "maya_scene",
            'comment': "No comment",
            'thumbnail': None,
            'taskName': None,
            'version': None,
            'copy_mode': copy_mode
        }

        # ------------------------
        # set context
        if self.sgCmds.app_instance.context.entity:
            self.publishArgs['linkType'] = self.sgCmds.app_instance.context.entity['type']
        if self.sgCmds.app_instance.context.entity:
            self.publishArgs['linkName'] = self.sgCmds.app_instance.context.entity['name']
        if self.sgCmds.app_instance.context.step:
            self.publishArgs['stepName'] = self.sgCmds.app_instance.context.step['name']
        if self.sgCmds.app_instance.context.task:
            self.publishArgs['taskName'] = self.sgCmds.app_instance.context.task['name']

        if params:
            if "context" in params.keys():
                # set context
                self.publishArgs['linkType'] = params['context']['entityType']
                self.publishArgs['linkName'] = params['context']['entity']
                self.publishArgs['stepName'] = params['context']['stepName']
                self.publishArgs['taskName'] = params['context']['taskName']

        # ------------------------
        # get publish name from scene or params
        current_scene = cmds.file(q=True, sn=True)
        self.publishArgs['publishName'] = None
        if params:
            if "context" in params.keys():
                if "publishName" in params['context'].keys():
                    self.publishArgs['publishName'] = params['context']['publishName']
                else:
                    try:
                        f = self.sgCmds.get_fieldsFromPath(current_scene, fields=['name'])
                        self.publishArgs['publishName'] = f['name']
                    except:
                        pass

        #
        if not self.publishArgs['publishName']:
            try:
                f = self.sgCmds.get_fieldsFromPath(current_scene, fields=['name'])
                self.publishArgs['publishName'] = f['name']
            except:
                self.publishArgs['publishName'] = 'basic'

        # ------------------------
        # Do Pre-Prublish
        # Sanity check
        if pre_publish:
            sc = ppSanityCheck.sanity_check()
            if not sc.global_status:
                # so we have an issue
                # push message to user
                if not self.batch:
                    ppNotifier.notify(title="Sanity Check: Failed", text=sc.report, image=self.icons.get_icon_path(name='uncheck'), time=50000)

        # ------------------------
        # Scan Scene for dependencies
        self.publishArgs['dependencies'] = ppSceneManagement.scanScene()

        # Get current scene path
        current_scene = cmds.file(query=True, sn=True)
        self.publishArgs['filePath'] = current_scene

        # ------------------------
        # get publish_path, this func update self.publish_path with the good path
        # also update self.publish_path_fields wich contains all the fields for the template
        # the self.publish_template is also updated.
        self.publish_path = self.get_publish_path()
        # set version number
        self.publishArgs['version'] = self.publish_path_fields.get("version")

        # add sceneConfigurationScriptNode
        # ppScene.create_sceneConfigurationScriptNode()

        # save scene directly at the good place
        #res = cmds.file(localScene, force=True, options="v=1", type=self.sceneTypeMapping[snExtension], preserveReferences=True, exportUnloadedReferences=True, exportAll=True, uiConfiguration=True)
        self._rename_maya_scene(path=self.publish_path)
        res = cmds.file(save=True, force=True, options="v=1", type=self.sceneTypeMapping[self.get_extension(step=self.publishArgs['stepName'])], preserveReferences=True)

        

        # check publish_path exist
        if not os.path.exists(self.publish_path):
            return False

        # build publish arg
        self.publishArgs['filePath'] = self.publish_path

        # ------------------------
        # get thumbnail and comment
        if params:
            #  add thumbnail
            if 'thumbnail' in params.keys():
                if params['thumbnail']:
                    if os.path.exists(params['thumbnail']):
                        self.publishArgs['thumbnail'] = params['thumbnail']

            #  add comment
            if 'comment' in params.keys():
                if params['comment']:
                    self.publishArgs['comment'] = params['comment']

        # set publish file status
        self.publishArgs['set_status'] = set_status

        logger.debug("Do Publish: %s" % self.publishArgs['filePath'])
        logger.debug("Publish Args: %s" % pprint.pformat(self.publishArgs))

        # check all field required is ok
        all_fieldsRequired = True
        badFields = []
        for key in ['project', 'filePath', 'fileType', 'linkType', 'linkName', 'stepName', 'taskName', 'publishName']:
            if key not in self.publishArgs.keys():
                if not self.publishArgs[key]:
                    badFields.append(key)
            else:
                badFields.append(key)

        if not all_fieldsRequired:
            logger.error("Can't Publish empty fields:")
            for badf in badFields:
                logger.error("\t {f}".format(f=badf))
            return
        
        # launch publish in sg
        logger.debug("Launch Publish: separate_process={separate_process}".format(separate_process=separate_process))
        self._publish_in_sgtk(separate_process=separate_process)
        
        # # create folders
        if not separate_process and self.sg_publish:
            if self.sg_publish['version_number'] == 1:
                self.sgCmds.tk.create_filesystem_structure(entity_type=self.sg_publish['entity']['type'], entity_id=self.sg_publish['entity']['id'], engine="tk-maya")

        if os.path.exists(self.publish_path):

            logger.debug("Publish path exist @ {p}".format(p=self.publish_path))

            logger.debug("Version up Scene for preserving publish integrity.")
            # version up current published scene for preserving file without saving.
            self._versionUp_maya_scene(save=False, publish=False)

            # set context
            logger.debug("Get Task Id : entity_type=entity_type, entity_name=entity_name, task_name=task_name".format(entity_type=self.publishArgs["linkType"], entity_name=self.publishArgs["linkName"], task_name=self.publishArgs["taskName"]))
            task_id = self.get_task_id(entity_type=self.publishArgs["linkType"], entity_name=self.publishArgs["linkName"], task_name=self.publishArgs["taskName"])

            # set new context
            logger.debug("Set Context for Task Id {t}".format(t=task_id))
            self.sgCmds.do_setNewContext(taskId=task_id)

            if self.sg_publish:
                logger.info("Publish Id : {pid}".format(pid=self.sg_publish.get('id')))

                # push shotgun published file to env
                ppSgtkUtils.push_to_env(published_file_id=self.sg_publish.get("id"), context=self.sgCmds.ctx)
                
                return self.sg_publish

        else:
            logger.debug("Publish path not exist @ {p}".format(p=self.publish_path))
            return False

        return

    def _publish_mxs(self):
        """
        Publish Current Maya Scene to MXS File.
        """
        msg_title = "publish mxs"
        msg_message_type = "information"

        selection = cmds.ls(sl=True, long=True)
        if not selection:
            ppUi.message_dialog(title=msg_title, message="Sans selection je peux pas faire grand chose.", message_type=msg_message_type, button="Desole", cancel_button=None)
            return

        file_type = "mxs_static"  # like describe in SG Publioshed File Type and field short_name

        self._publish_in_other_format(export_name="mxs", file_type=file_type, selection=selection)

    def _publish_vrscene(self):
        """
        Publish Current Maya Scene to MXS File.
        """
        file_type = "vrscene"  # like describe in SG Publioshed File Type and field short_name
        self._publish_in_other_format(export_name="vrscene", file_type=file_type)

    def _publish_in_other_format(self, export_name="mxs", file_type="mxs_static", selection=None):
        """
        """
        msg_title = "publish {0}".format(export_name)
        msg_message_type = "information"

        separate_process = True

        # get current app and context
        self.sgCmds.do_initTk()

        # build publish arg
        self.publishArgs = {
            'project': self.sgCmds.app_instance.sgtk.roots['primary'],
            'fileType': file_type,
            'comment': "No comment",
            'thumbnail': None,
            'taskName': None,
            'version': None,
            'copy_mode': 'copy'
        }

        # ------------------------
        # set context
        if self.sgCmds.app_instance.context.entity:
            self.publishArgs['linkType'] = self.sgCmds.app_instance.context.entity['type']
        if self.sgCmds.app_instance.context.entity:
            self.publishArgs['linkName'] = self.sgCmds.app_instance.context.entity['name']
        if self.sgCmds.app_instance.context.step:
            self.publishArgs['stepName'] = self.sgCmds.app_instance.context.step['name']
        if self.sgCmds.app_instance.context.task:
            self.publishArgs['taskName'] = self.sgCmds.app_instance.context.task['name']

        # ------------------------
        # get publish name from scene or params
        current_scene = cmds.file(q=True, sn=True)
        self.publishArgs['publishName'] = 'basic'
        try:
            f = self.sgCmds.get_fieldsFromPath(current_scene, fields=['name'])
            self.publishArgs['publishName'] = f['name']
        except:
            pass

        # set publish file status
        self.publishArgs['set_status'] = "ip"

        # get data from published file in use
        published_file_env_data = ppSgtkUtils.get_from_env()
        if published_file_env_data:
            # get published file detail
            if "published_file_id" in published_file_env_data.keys():
                pf_detail = self.sgCmds.get_one_published_file(int(published_file_env_data.get("published_file_id")))
                if pf_detail:
                    self.publishArgs["version"] = pf_detail.get("version_number")
                    self.publishArgs['publishName'] = pf_detail.get("name")
                    self.publishArgs['set_status'] = pf_detail.get("sg_status_list")
                    self.publishArgs['dependencies'] = [int(published_file_env_data.get("published_file_id"))]

        # export
        if export_name == "mxs":
            self.publishArgs['filePath'] = self.export_selection_cmd._export_mxs(selection=selection, path=None, animated=False, start=1, end=1, camera=None, file_type=file_type)
        elif export_name == "vrscene":
            self.publishArgs['filePath'] = self.export_selection_cmd._export_vrscene(path=None, animated=False, start=1, end=1, file_type=file_type)

        logger.debug("Do Publish: %s" % self.publishArgs['filePath'])
        logger.debug("Publish Args: %s" % self.publishArgs)

        # check if all field required is ok
        all_fieldsRequired = True
        badFields = []
        for key in ['project', 'filePath', 'fileType', 'linkType', 'linkName', 'stepName', 'publishName']:
            if key not in self.publishArgs.keys():
                if not self.publishArgs[key]:
                    badFields.append(key)
            else:
                badFields.append(key)

        if not all_fieldsRequired:
            logger.error("Can't Publish empty fields:")
            for badf in badFields:
                logger.error("\t {f}".format(f=badf))

            ppUi.message_dialog(title=msg_title, message="Je ne peux pas creer de {export_name}.\nil manque {badFields}".format(export_name=export_name, badFields=badFields), message_type=msg_message_type, button="Desole", cancel_button=None)
            return
        
        # launch publish in sg
        logger.debug("Launch Publish: separate_process={separate_process}".format(separate_process=separate_process))
        self._publish_in_sgtk(separate_process=separate_process)

    def _publish_in_sgtk(self, separate_process=False):
        """
        this func get the var self.publishArgs and publish it in a separate process.
        """
        # init publish Args
        # TODO: find another way
        publishArgs = {
            "project": None,
            "filePath": None,
            "fileType": None,
            "linkType": None,
            "linkName": None,
            "publishName": None,
            "stepName": None,
            "taskName": None,
            "version": None,
            "comment": 'auto-publish',
            "daily": False,
            "dependencies": [],
            "audioFile": None,
            "audioOffset": 0,
            "colorSpace": None,
            "frameRate": None,
            "sgMetaData": {},
            "thumbnail": None,
            "user": {},
            "tags": [],
            "copy_mode": "copy",
            "set_status": "ip",
            "notify": True
        }

        # update publishArgs by self.publishArgs
        publishArgs.update(self.publishArgs)

        args = (
            publishArgs['project'],
            publishArgs['filePath'],
            publishArgs['fileType'],
            publishArgs['linkType'],
            publishArgs['linkName'],
            publishArgs['publishName'],
            publishArgs['stepName'])
        kwargs = {
            "taskName": publishArgs['taskName'],
            "version": publishArgs['version'],
            "comment": publishArgs['comment'],
            "daily": publishArgs['daily'],
            "dependencies": publishArgs['dependencies'],
            "audioFile": publishArgs['audioFile'],
            "audioOffset": publishArgs['audioOffset'],
            "colorSpace": publishArgs['colorSpace'],
            "frameRate": publishArgs['frameRate'],
            "sgMetaData": publishArgs['sgMetaData'],
            "thumbnail": publishArgs['thumbnail'],
            "user": publishArgs['user'],
            "tags": publishArgs['tags'],
            "copy_mode": publishArgs['copy_mode'],
            "set_status": publishArgs['set_status'],
            "notify": publishArgs['notify'],
        }
        
        # order argument for launch in separate process
        publishArgsList = [v for k, v in publishArgs.iteritems()]

        # -----
        # do publish in separate process
        self.sg_publish = None
        if separate_process:
            logger.info("separate_process : {s}".format(s=separate_process))
            try:
                self.bee = Worker(ppSgtkPublisher.publishFile, args, kwargs)
                self.bee.start()
            except Exception, e:
                logger.error("Couldn't publish file {p},\n publishArgs: {pa}\n error: {e}".format(p=publishArgs["filePath"], pa=publishArgsList, e=e))
        else:
            self.sg_publish = ppSgtkPublisher.publishFile(**publishArgs)

        return self.sg_publish

    def _capture_viewport(self, path=None, width=1280, height=720):
        """
        this func auto capture a screenshot based on the selected panel.
        """
        img_path = ppImgTools.getUniqueImgPath()

        # Import api modules
        import maya.OpenMaya as api
        import maya.OpenMayaUI as apiUI

        # Grab the last active 3d viewport
        view = apiUI.M3dView.active3dView()
        # Enable Alpha
        view.setColorMask(1, 1, 1, 1)

        # read the color buffer from the view, and save the MImage to disk
        image = api.MImage()

        view.readColorBuffer(image, True)
        image.resize(width, height, True)
        image.writeToFile(img_path, img_path.split('.')[len(img_path.split('.')) - 1])

        return img_path

    def _capture_renderview(self):
        """
        this capture the current render view image.
        """
        img_path = ppImgTools.getUniqueImgPath()

        import maya.app.general.createImageFormats as createImageFormats
        # set file format png for render view
        formatManager = createImageFormats.ImageFormats()
        formatManager.pushRenderGlobalsForDesc("PNG")

        # write image on disk
        editor = 'renderView'
        cmds.renderWindowEditor(editor, e=True, writeImage=img_path)

        formatManager.popRenderGlobals()

        return img_path


    def _capture_manual(self):
        """
        launch the application for take a screenshot manually
        """
        r = ppImgTools.screenCapture()

        return r

    def _push_screenshot_to_thumbnail(self, path=None, entityType=None, entityId=None):
        """
        this func push the thumbnail to the entity.
        """
        logger.debug("_push_screenshot_to_thumbnail(path={path}, entityType={entityType}, entityId={entityId})".format(path=path, entityType=entityType, entityId=entityId))

        sg = sgtk.api.shotgun.create_sg_connection()
        r = sg.upload_thumbnail(entityType, entityId, path)

        # push message to user
        if r and not self.batch:
            msg = "Successfully pushed to Thumbnail on\n- Entity {entityType} {entityId}".format(entityType=entityType, entityId=entityId)
            ppNotifier.notify(title="_push_screenshot_to_thumbnail", text=msg, image=path, time=10000)

        logger.debug(" _push_screenshot_to_thumbnail: result: {r}".format(r=r))

        return r

    def _create_note(self):
        """
        create note based on current context
        """

        # get current context
        self.sgCmds.do_initTk()

        # from context
        url_note = "{serverPath}/new/Note?".format(serverPath=ppSettings.SHOTGUN["serverPath"])

        if self.sgCmds.ctx:

            logger.info("_create_note: {c}".format(c=self.sgCmds.ctx))

            # add project
            if self.sgCmds.ctx.project:
                url_note += 'project={p}'.format(p=self.sgCmds.ctx.project['name'])
            # default
            url_note += '&defaults={'

            # add note_links like entity
            if self.sgCmds.ctx.entity:
                url_note += '%22note_links%22:[{{%22type%22:%22{t}%22,%22name%22:%22{n}%22}}],'.format(t=self.sgCmds.ctx.entity['type'], n=self.sgCmds.ctx.entity['name'])

            # add subject
            if self.sgCmds.ctx.entity:
                url_note += '%22subject%22:%22FYI%20on%20{n}%22,'.format(n=self.sgCmds.ctx.entity['name'])

            # add content
            url_note += '%22content%22:%22' + urllib.quote("J'ai un truc de ouf à te dire") + '%22,'

            # add note type
            url_note += '%22sg_note_type%22:%22Internal%22'

            # default bracket
            url_note += '}'

        else:
            logger.info("_create_note: no context found.")

        webbrowser.open(url=url_note, new=2, autoraise=False)

    def _create_asset(self):
        """
        create note based on current context
        """
        # from context
        url_note = "{serverPath}/new/Asset?".format(serverPath=ppSettings.SHOTGUN["serverPath"])

        # get current context
        self.sgCmds.do_initTk()

        if self.sgCmds.ctx:

            logger.info("_create_timelog: {c}".format(c=self.sgCmds.ctx))

            # add project
            if self.sgCmds.ctx.project:
                url_note += 'project={p}'.format(p=self.sgCmds.ctx.project['name'])
            # default
            url_note += '&defaults={'

            # define default value
            url_note += '%22code%22:%22myAssetName%22,'
            url_note += '%22sg_asset_type%22:%22Character%22,'
            url_note += '%22description%22:%22My%20Description%22'

            # default bracket
            url_note += '}'

        else:
            logger.info("_create_note: no context found.")

        webbrowser.open(url=url_note, new=2, autoraise=False)

    def _create_shot(self):
        """
        create shot
        """
        # from context
        url_note = "{serverPath}/new/Shot?".format(serverPath=ppSettings.SHOTGUN["serverPath"])

        # get current context
        self.sgCmds.do_initTk()

        if self.sgCmds.ctx:

            logger.info("_create_timelog: {c}".format(c=self.sgCmds.ctx))

            # add project
            if self.sgCmds.ctx.project:
                url_note += 'project={p}'.format(p=self.sgCmds.ctx.project['name'])
            # default
            url_note += '&defaults={'

            # define default value
            url_note += '%22code%22:%22000_0000%22,'
            url_note += '%22sg_shot_type%22:%22Shot%22,'
            url_note += '%22description%22:%22My%20Description%22'

            # default bracket
            url_note += '}'

        else:
            logger.info("_create_note: no context found.")

        webbrowser.open(url=url_note, new=2, autoraise=False)

    def _create_timelog(self):
        """ """

        # get current context
        self.sgCmds.do_initTk()

        # from context
        url_note = "{serverPath}/new/TimeLog?".format(serverPath=ppSettings.SHOTGUN["serverPath"])

        if self.sgCmds.ctx:

            logger.info("_create_timelog: {c}".format(c=self.sgCmds.ctx))
            # https://wizz.shotgunstudio.com/new/TimeLog?project=test_sgtk&defaults={%22user%22:{%22type%22:%22HumanUser%22,%22name%22:%22Marc%20Dubrois%22},%20%22date%22:%222015-07-20%22,%20%22duration%22:%224h%22}

            # add project
            if self.sgCmds.ctx.project:
                url_note += 'project={p}'.format(p=self.sgCmds.ctx.project['name'])
            # default
            url_note += '&defaults={'

            # add user
            if self.sgCmds.ctx.user:
                url_note += '%22user%22:{{%22type%22:%22HumanUser%22,%22name%22:%22{n}%22}},'.format(n=self.sgCmds.ctx.user['name'])

            # add description
            description = "J'ai travaillé très dur."
            if self.sgCmds.ctx.task and self.sgCmds.ctx.entity:
                url_note += '%22description%22:%22Travail%20sur%20{e}%20en%20{t}%22,'.format(e=self.sgCmds.ctx.entity['name'], t=self.sgCmds.ctx.task['name'])
            else:
                url_note += '%22description%22:%22{d}%22,'.format(d=urllib.quote(description))

            if self.sgCmds.ctx.task:
                url_note += '%22entity%22:{{%22type%22:%22Task%22,%22id%22:%22{i}%22}},'.format(i=self.sgCmds.ctx.task['id'])

            # pre fill duration
            url_note += '%22duration%22:%221%20days%22,'

            # add date
            url_note += '%22date%22:%22{d}%22'.format(d=datetime.date.today())

            # default bracket
            url_note += '}'

        else:
            logger.info("_create_note: no context found.")

        webbrowser.open(url=url_note, new=2, autoraise=False)

    def _start_sgtk(self):
        """ """
        logger.info("Try to start sgtk")

        scene_path = cmds.file(q=True, sn=True)
        project_path = None
        project_path_list = []

        # try to get project path.
        # usually our project path are /prod/project/project_name
        # try to split scene_path and retrieve this template
        scene_path_split = scene_path.split('/')
        if len(scene_path_split) >= 3:
            for i in range(0, 4):
                project_path_list.append(scene_path_split[i])
            project_path = "/".join(project_path_list)
        
        tk = None
        ctx = None

        if os.path.exists(scene_path) and project_path:
            # create instance and context from path
            tk = sgtk.sgtk_from_path(scene_path)
            ctx = tk.context_from_path(scene_path)
        else:
            logger.info("\tCan't get context from scene_path")

        if not ctx and project_path:
            # get ctx from project path
            # create instance and context from path
            tk = sgtk.sgtk_from_path(project_path)
            ctx = tk.context_from_path(project_path)
        else:
            logger.info("\tCan't get context from project_path")

        if not ctx:
            # get project from TANK_CURRENT_PC env var
            if 'TANK_CURRENT_PC' in os.environ.keys():
                if os.environ['TANK_CURRENT_PC']:
                    if os.path.exists(os.environ['TANK_CURRENT_PC']):
                        TANK_CURRENT_PC = os.environ['TANK_CURRENT_PC']
                        # usually TANK_CURRENT_PC path is like /prod/shotgun/{Project_Name}
                        # we do an awesome replace project instead of shotgun
                        project_path = TANK_CURRENT_PC.replace('shotgun', 'project')

            if project_path:
                # get ctx from project path
                # create instance and context from path
                tk = sgtk.sgtk_from_path(project_path)
                ctx = tk.context_from_path(project_path)
            else:
                logger.info("\tCan't get context from TANK_CURRENT_PC")

        if ctx:
            self.sgCmds.do_setNewContext(ctx=ctx)
        else:
            logger.info("Can't find a Context for ReStart engine.")

    def _get_project_main_settings(self):
        """ retrieve and set project settings"""

        sn = ppScene.Scene()
        sn.set_project_settings_to_maya()

    def _get_project_render_settings(self):
        """ """

        sn = ppScene.Scene()
        sn.set_project_render_settings_to_maya()

    def _auto_get_sound(self):
        """auto get sound from entity"""
        
        # get current app and context
        self.sgCmds.do_initTk()

        # retrieve publish file about sound
        r = self.sgCmds.get_publishedFile(entityType=self.sgCmds.ctx.entity['type'], entityName=self.sgCmds.ctx.entity['name'], publishedType=["Audio file"])

        if r:
            # keep the latest
            latest_r = r[len(r)-1]
            sound_path = self.get_path(latest_r)
            logger.info("Create reference for sound_path : {s}".format(s=sound_path))

            # create reference
            namespace = "sound_{n}".format(n=self.sgCmds.ctx.entity['name'])
            reference = cmds.file(
                sound_path,
                i=True,
                mergeNamespacesOnClash=False,
                options="o=0"
            )

            logger.info("reference {reference}".format(reference=reference))

            # retrieve audio node by remove all digit before letter
            # example we have 800_0001_edit_basic_v006.wav and audio node was _0001_edit_basic_v006
            audio_node_tmp = os.path.basename(sound_path).split('.')[0]
            audio_node = ""
            first_letter_found = False
            for l in audio_node_tmp:
                if not first_letter_found:
                    try:
                        int(l)
                    except:
                        first_letter_found = True

                if first_letter_found:
                    audio_node += l

            # check if audio node exist
            if not cmds.objExists(audio_node):
                logger.info("audio_node not found : {s}".format(s=audio_node))
                return

            # get first frame from sg
            # try to retrieve cut info from shotgun
            filters = [['code', 'is', self.sgCmds.ctx.entity['name']], ['project.Project.name', 'is', self.sgCmds.ctx.project['name']]]
            fieldsReturn = ['id', 'sg_inframe']
            order = [{'field_name': 'id', 'direction': 'desc'}]
            sgEntity = self.sgCmds.tk.shotgun.find_one(self.sgCmds.ctx.entity['type'], filters, fieldsReturn, order)

            # set offset
            audio_offset = 101
            if sgEntity:
                logger.info("Found Audio Offset from Sg")
                audio_offset = int(sgEntity["sg_inframe"])
            logger.info("Set Audio Offset : {audio_offset}".format(audio_offset=audio_offset))
            cmds.setAttr("{n}.offset".format(n=audio_node), audio_offset)

            # display wav
            logger.info("Set Audio Active in Timeslider")
            mel.eval("setSoundDisplay {audio_node} 1".format(audio_node=audio_node))

        else:
            logger.info("No sound found for {e} {n}".format(e=self.sgCmds.ctx.entity['type'], n=self.sgCmds.ctx.entity['name']))

    def _get_image_as_image_plane(self, name, image_path, first_frame=None, last_frame=None, free_image_plane=False):
        """
        """
        s = ppScene.Scene()
        s.get_animation_settings()

        # get selection
        sel = cmds.ls(sl=True, l=True)

        image_plane = None
        image_plane_shape = None

        # create image plane
        camera_shape = None
        if free_image_plane:
            logger.info("Create Free Image Plane : name={name}, fileName={image_path}".format(name=name, image_path=image_path))
            image_plane, image_plane_shape = cmds.imagePlane(name=name, fileName=image_path)
        else:
            if sel:
                shape = cmds.listRelatives(sel[0], type='camera')
                if shape:
                    camera_shape = shape[0]
                    logger.info("Create Image Plane : name={name}, fileName={image_path}, camera={camera_shape}".format(name=name, image_path=image_path, camera_shape=camera_shape))
                    image_plane, image_plane_shape = cmds.imagePlane(name=name, fileName=image_path, camera=camera_shape)
                else:
                    logger.info("The selected shape is not a camera")
                    return False
            else:
                logger.info("No selection found")
                return False
        
        # image sequence active
        if first_frame and last_frame and image_plane and image_plane_shape:

            # set animation
            cmds.setAttr("{image_plane_shape}.useFrameExtension".format(image_plane_shape=image_plane_shape), 1)

            # create anim_curve for driving image number.
            # define node name
            anim_curve = "{i}_anim".format(i=image_plane)

            # Store current tangent settings as origin for restore it later
            inTangentOrig = cmds.keyTangent(query=True, g=True, itt=True)[0]
            outTangentOrig = cmds.keyTangent(query=True, g=True, ott=True)[0]

            # Set tangent to linear
            cmds.keyTangent(g=True, itt='linear')
            cmds.keyTangent(g=True, ott='linear')

            # create a new timewarp node if needed
            anim_curve = cmds.createNode("animCurveTU", name=anim_curve)
            
            minTime = s.minTime
            maxTime = minTime + last_frame - first_frame
            cmds.setKeyframe(anim_curve, value=first_frame, time=(minTime, minTime))
            cmds.setKeyframe(anim_curve, value=last_frame, time=(maxTime, maxTime))

            # restore tangent settings
            cmds.keyTangent(g=True, itt=inTangentOrig)
            cmds.keyTangent(g=True, ott=outTangentOrig)

            # connect curve to image plane
            cmds.connectAttr("{anim_curve}.output".format(anim_curve=anim_curve), "{image_plane_shape}.frameExtension".format(image_plane_shape=image_plane_shape))

        # select image plane
        cmds.select(image_plane, replace=True)

    def _get_vrscene(self, name, path):
        """
        """
        for plugin in ['vrayformaya']:
            if plugin not in cmds.pluginInfo(query=True, listPlugins=True):
                try:
                    cmds.loadPlugin(plugin)
                    logger.info("pp - plugin successful loaded: %s" % plugin)
                except:
                    logger.warning("pp - can't load plugin: %s" % plugin)

        # 



def start_sgtk_engine():
    """
    start sgtk maya engine.
    in file_type sgtk was stupid.
    start engine from project_path
    """

    a = Action()
    a.execute_action(action="start_sgtk")


def execute_action(action):
    """
    """

    a = Action()
    a.execute_action(action=action)
