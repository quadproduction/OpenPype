# -*- coding: utf-8 -*-
"""
common classes and functions about node
"""

import logging
import os
import sys
import sgtk
import pprint
from tank_vendor import yaml
import ppUtils.ppPath as ppPath
from ppSgtkLibs import ppSgtkPublisher
import ppSgtkLibs.ppSgtkCmds as ppSgtkCmds
import ppSgtkLibs.ppSgtkUtils as ppSgtkUtils
import ppUtils.ppIcons

from . import ppTools
import ppUtils.ppFileSequence as ppFileSequence

import nuke

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppActions')
logger.setLevel(logging.INFO)

NUKE_PUBLISHED_FILE_TYPE_NAME = "nuke_script"


class Action(object):
    """docstring for Action"""

    def __init__(self):
        super(Action, self).__init__()

        # define icons path
        self.icons = ppUtils.ppIcons.Icons()
        self.sgCmds = ppSgtkCmds.Cmds()

        # init local var for export
        self.rootLocalFolder = "d:"
        if sys.platform == "linux2":
            self.rootLocalFolder = os.environ.get('HOME')
            if not self.rootLocalFolder:
                self.rootLocalFolder = '/tmp'
        try:
            self.rootLocalFolder = os.environ['PP_DATA_DIR']
        except:
            logger.warning("The Env Var 'PP_DATA_DIR' not exist")

        # publish copy mode
        self.copy_mode_settings = {
            "normal": "nothing",
            "in_progress": "nothing"
        }

        # init self.sg_publish
        self.sg_publish = None

    def get_actionDescription(self, action):
        """ """

        if "open_file" in action:
            return {
                "name": "open_file",
                "params": None,
                "icon": self.icons.get_icon_path(name='open'),
                "caption": "Open File",
                "description": "Open File"
            }
        return None

    def execute_action(self, action, params=None):
        """ """
        logger.info("execute_action(action={action}, params={params})".format(action=action, params=params))
        r = None

        if "open_file" == action:
            # launch
            path = ppPath.get_sg_path_from_current_platform(sg_published_file_path=params["sgpf"])
            if path:
                r = self._open_file(path=path, params=params)

        if "publish_file" == action:
            r = self._publish_scene(params=params, pre_publish=True, copy_mode="nothing", set_status="apr", separate_process=True)

        if "create_OCIODisplay" == action:
            r = self._create_OCIODisplay()

        return r

    def _open_file(self, path, params=None):
        """ """

        logger.info("Open File : %s" % path)

        # open file
        nuke.scriptOpen(path)

        # set context
        if params:

            self.sgCmds.do_initTk(projectPath=path)

            logger.debug("params: {p}".format(p=params))

            # Set New Context Post Open
            e = self.sgCmds.do_setNewContext(taskId=params["sgpf"]['task']['id'], engine_name="tk-nuke")

            # push shotgun published file to env
            ppSgtkUtils.push_to_env(published_file_id=params["sgpf"]["id"], context=self.sgCmds.ctx)

            if e:
                logger.debug("Context Change Done =============>")
            else:
                logger.debug("Context Change Failed >=============>")
                return False

        return True

    def _create_read_img(self, path, params={}, sg_publish_data={}):
        """
        this func create a read node.
        :param str path: the file path for yhe reader.
        :param dict params: this arg is dedicated to custom your node. the dict represent a key value like "name": "tutu"
        :param dict sg_publish_data: shotgun published file data like > {'version_number': 9, 'code': 'ABC_0001_queen_scan_raw_source_v009.%04d.dpx', 'description': 'No comment', 'published_file_type.PublishedFileType.code': 'Scan', 'created_at': datetime.datetime(2016, 5, 12, 17, 40, 23, tzinfo=<tank_vendor.shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x2b172a0f3cd0>), 'published_file_type': {'type': 'PublishedFileType', 'id': 27, 'name': 'Scan'}, 'created_by': {'type': 'HumanUser', 'id': 40, 'name': 'Marc Dubrois'}, 'entity': {'type': 'Shot', 'id': 27583, 'name': 'ABC_0001'}, 'project': {'type': 'Project', 'id': 991, 'name': 'DEV_VFX_16_991'}, 'image': 'https://sg-media-usor-01.s3.amazonaws.com/131d05f9e5705cb2e17eba8b55ea3b861ad7c4d3/3ad2159d8c257fb17341f810dd0c46fdbf95def7/tmp9HPedf_t.jpg?AWSAccessKeyId=AKIAIFHY52V77FIVWKLQ&Expires=1469441399&Signature=T%2FH6iWj%2BcfSwwffL69aghldCROg%3D', 'task': {'type': 'Task', 'id': 50863, 'name': 'raw'}, 'sg_status_list': 'ip', 'sg_pp_meta_data': '{end: 1140, start: 977}', 'task.Task.step': {'type': 'Step', 'id': 17, 'name': 'scan'}, 'sg_pp_color_space': {'type': 'CustomNonProjectEntity17', 'id': 103, 'name': 'lg10'}, 'path': {'local_path_windows': 'c:\\prod\\project\\DEV_VFX_16_991\\sequences\\ABC\\ABC_0001\\scan\\images\\ABC_0001_queen_scan_raw_source_v009\\ABC_0001_queen_scan_raw_source_v009.%04d.dpx', 'name': 'ABC_0001_queen_scan_raw_source_v009.%04d.dpx', 'local_path_linux': '/prod/project/DEV_VFX_16_991/sequences/ABC/ABC_0001/scan/images/ABC_0001_queen_scan_raw_source_v009/ABC_0001_queen_scan_raw_source_v009.%04d.dpx', 'url': 'file:///prod/project/DEV_VFX_16_991/sequences/ABC/ABC_0001/scan/images/ABC_0001_queen_scan_raw_source_v009/ABC_0001_queen_scan_raw_source_v009.%04d.dpx', 'local_storage': {'type': 'LocalStorage', 'id': 11, 'name': 'primary'}, 'local_path': '/prod/project/DEV_VFX_16_991/sequences/ABC/ABC_0001/scan/images/ABC_0001_queen_scan_raw_source_v009/ABC_0001_queen_scan_raw_source_v009.%04d.dpx', 'content_type': 'image/dpx', 'local_path_mac': '/prod/project/DEV_VFX_16_991/sequences/ABC/ABC_0001/scan/images/ABC_0001_queen_scan_raw_source_v009/ABC_0001_queen_scan_raw_source_v009.%04d.dpx', 'type': 'Attachment', 'id': 241080, 'link_type': 'local'}, 'type': 'PublishedFile', 'id': 106281, 'name': 'queen'}
        :return: the func return a nuke node.
        :rtype: Node
        """

        logger.info("Create Reader : %s" % path)

        # open file
        n = nuke.createNode("Read", inpanel=False)

        if not n:
            return None

        # setup node
        self._setup_read_img(node=n, node_name=None, path=path, params=params, sg_publish_data=sg_publish_data)

        return n

    def _setup_read_img(self, node=None, node_name=None, path=None, params={}, sg_publish_data={}):
        """
        This function setup a write with the provided data.
        :param node: the node instance
        :type node: Node
        :param node_name: the node name in string
        :type node_name: str
        :param path: the path like nuke love, please use %04d
        :type path: str
        :param params: a dict which represent the field : value mapping
        :type params: dict
        :param sg_publish_data: the sg publish data like shotgun love.
        :type sg_publish_data: dict
        :returns: True or False
        :rtype: bool
        """

        if not node and not node_name:
            raise RuntimeError("Can't do anything without node or node_name")

        # get node
        n = node
        if not node and node_name:
            n = nuke.toNode(node_name)

        # add path to params
        params['file'] = path

        # push sg_publish_data to params without override
        if sg_publish_data:
            # get data from meta data field
            if sg_publish_data.get("sg_pp_meta_data"):
                sg_pp_meta_data = yaml.load(sg_publish_data.get("sg_pp_meta_data"))

                # get start
                if "first" not in params and "origfirst" not in params:
                    if "start" in sg_pp_meta_data.keys():
                        # set params
                        params["first"] = int(sg_pp_meta_data.get("start"))
                        params["origfirst"] = int(sg_pp_meta_data.get("start"))
                # get end
                if "last" not in params and "origlast" not in params:
                    if "end" in sg_pp_meta_data.keys():
                        # set params
                        params["last"] = int(sg_pp_meta_data.get("end"))
                        params["origlast"] = int(sg_pp_meta_data.get("end"))

                # get color space
                if "colorspace" not in params:
                    if sg_publish_data.get("sg_pp_color_space"):
                        params["colorspace"] = sg_publish_data.get("sg_pp_color_space").get("name")

        # check name not already exist in script
        if "name" in params:
            # and before check if it's not our name
            if params.get("name") == n.name():
                # remove name, it already have the good_name
                del params["name"]
            else:
                good_name = ppTools.get_next_name_available(name=params.get("name"))
                params["name"] = good_name
        else:
            # setup default name if required
            # get name from path
            name = ppTools.get_name_from_path(path)
            # check name
            good_name = ppTools.get_next_name_available(name=name)
            params["name"] = good_name

        # setup node based on params
        for key in sorted(params.keys()):
            # set value
            logger.debug("Set {key} : {value}".format(key=key, value=params.get(key)))
            try:
                n.knob(key).setValue(params.get(key))
            except Exception, e:
                logger.error("Set {key} : {value}".format(key=key, value=params.get(key)))
                logger.error("Error : {e}".format(e=e))

        # set width, height pixelAspect, until we pipe resolution
        if "width" not in params.keys() and "format" not in params.keys():
            f = ppTools.get_format(width=n.width(), height=n.height(), pixelAspect=n.pixelAspect())
            n.knob("format").setValue(f)

        # set ocio
        if sg_publish_data:
            ppTools.set_ocio_context_to_node(node=n, sg_publish_data=sg_publish_data)

        return True

    def _create_write_img(self, path, params={}):
        """
        this func create a read node.
        :param str path: the file path for yhe reader.
        :param dict params: this arg is dedicated to custom your node. the dict represent a key value like "name": "tutu"
        :param dict sg_publish_data: shotgun published file data like > {'version_number': 9, 'code': 'ABC_0001_queen_scan_raw_source_v009.%04d.dpx', 'description': 'No comment', 'published_file_type.PublishedFileType.code': 'Scan', 'created_at': datetime.datetime(2016, 5, 12, 17, 40, 23, tzinfo=<tank_vendor.shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x2b172a0f3cd0>), 'published_file_type': {'type': 'PublishedFileType', 'id': 27, 'name': 'Scan'}, 'created_by': {'type': 'HumanUser', 'id': 40, 'name': 'Marc Dubrois'}, 'entity': {'type': 'Shot', 'id': 27583, 'name': 'ABC_0001'}, 'project': {'type': 'Project', 'id': 991, 'name': 'DEV_VFX_16_991'}, 'image': 'https://sg-media-usor-01.s3.amazonaws.com/131d05f9e5705cb2e17eba8b55ea3b861ad7c4d3/3ad2159d8c257fb17341f810dd0c46fdbf95def7/tmp9HPedf_t.jpg?AWSAccessKeyId=AKIAIFHY52V77FIVWKLQ&Expires=1469441399&Signature=T%2FH6iWj%2BcfSwwffL69aghldCROg%3D', 'task': {'type': 'Task', 'id': 50863, 'name': 'raw'}, 'sg_status_list': 'ip', 'sg_pp_meta_data': '{end: 1140, start: 977}', 'task.Task.step': {'type': 'Step', 'id': 17, 'name': 'scan'}, 'sg_pp_color_space': {'type': 'CustomNonProjectEntity17', 'id': 103, 'name': 'lg10'}, 'path': {'local_path_windows': 'c:\\prod\\project\\DEV_VFX_16_991\\sequences\\ABC\\ABC_0001\\scan\\images\\ABC_0001_queen_scan_raw_source_v009\\ABC_0001_queen_scan_raw_source_v009.%04d.dpx', 'name': 'ABC_0001_queen_scan_raw_source_v009.%04d.dpx', 'local_path_linux': '/prod/project/DEV_VFX_16_991/sequences/ABC/ABC_0001/scan/images/ABC_0001_queen_scan_raw_source_v009/ABC_0001_queen_scan_raw_source_v009.%04d.dpx', 'url': 'file:///prod/project/DEV_VFX_16_991/sequences/ABC/ABC_0001/scan/images/ABC_0001_queen_scan_raw_source_v009/ABC_0001_queen_scan_raw_source_v009.%04d.dpx', 'local_storage': {'type': 'LocalStorage', 'id': 11, 'name': 'primary'}, 'local_path': '/prod/project/DEV_VFX_16_991/sequences/ABC/ABC_0001/scan/images/ABC_0001_queen_scan_raw_source_v009/ABC_0001_queen_scan_raw_source_v009.%04d.dpx', 'content_type': 'image/dpx', 'local_path_mac': '/prod/project/DEV_VFX_16_991/sequences/ABC/ABC_0001/scan/images/ABC_0001_queen_scan_raw_source_v009/ABC_0001_queen_scan_raw_source_v009.%04d.dpx', 'type': 'Attachment', 'id': 241080, 'link_type': 'local'}, 'type': 'PublishedFile', 'id': 106281, 'name': 'queen'}
        :return: the func return a nuke node.
        :rtype: Node
        """

        logger.info("Create Reader : %s" % path)

        # open file
        n = nuke.createNode("Write", inpanel=False)

        if not n:
            return None

        # setup node
        self._setup_write_img(node=n, node_name=None, path=path, params=params)

        return n

    def _setup_write_img(self, node=None, node_name=None, path=None, params={}):
        """
        """
        if not node and not node_name:
            raise RuntimeError("Can't do anything without node or node_name")

        # get node
        n = node
        if not node and node_name:
            n = nuke.toNode(node_name)

        # set path before apply params
        if path:
            n.knob("file").setValue(path)

        # set file_type based on file extension
        n.knob("file_type").setValue(path.split('.')[len(path.split('.')) - 1])

        # setup node based on params
        logger.debug("Set Param on Node : {node_name}".format(node_name=n.name()))
        for key in sorted(params.keys()):
            # set value
            value = params.get(key)
            logger.info("Try to set '{key}'' : '{value}'".format(key=key, value=value))
            if n.knob(key):
                n.knob(key).setValue(value)
            else:
                logger.warning("\t Can't set on Attr : '{key}'' : '{value}'".format(key=key, value=value))

        return True

    def _publish_file(self, params=None, set_status="apr", secondary_publish_tasks=[]):
        """
        :param publish_mode: mode available "normal" the file is published the incrementation is done by the publisher.
        "in_progress" th incrementation is done by versioUp and the publish publish the current maya scene.)
        """

        # _primary_pre_publish_file

        # _secondary_pre_publish_file

        # _primary_publish_file

        # _secondary_publish_file
        pass

    def _primary_pre_publish_file(self, params=None):
        """
        this func do some sanity check to be sure we publish without problem
        """
        return []

    def _secondary_pre_publish_file(self, params=None):
        """
        this func do some sanity check to be sure we do secondary(post)
        publish without problem
        """
        return []

    def _primary_publish_file(self, params=None):
        """
        That's the main publish it publish your nuke script.
        """
        # get current nuke script
        script_path = nuke.root().name().replace("/", os.path.sep)
        if script_path == "Root":
            script_path = ""
        script_path = os.path.abspath(script_path)

        # scan scene dependencies
        dependency_paths = ppTools.get_dependencies()  # temporary method not at the good place

        # recover publish data
        if not params.get('project'):
            params["project"] = self.sgCmds.ctx.project.get('name')
        if not params.get('entity_type'):
            params["entity_type"] = self.sgCmds.ctx.entity.get('type')
        if not params.get('entity_name'):
            params["entity_name"] = self.sgCmds.ctx.entity.get('name')
        if not params.get('step_name'):
            params["step_name"] = self.sgCmds.ctx.step.get('name')
        if not params.get('task_name'):
            params["task_name"] = self.sgCmds.ctx.task.get('name')
        if not params.get('task'):
            params["task"] = self.sgCmds.ctx.task

        # get new path
        bp = ppSgtkPublisher.BasePublish()
        bp.init(params.get('project'))

        # get template to use based on published file type (nuke_script) and entity_type (asset or shot)
        logger.debug("get template from published file type")
        bp._get_template_from_published_file_type_name(published_file_type_name=NUKE_PUBLISHED_FILE_TYPE_NAME, entity_type=params.get('entity_type'))

        # get publish_name from current script if not provided by params
        if not params.get('publish_name'):
            params["publish_name"] = bp.template.get_fields(script_path)['name']

        # publish template for "nuke_asset_publish" "assets/{sg_asset_type}/{Asset}/{Step}/publish/nuke/{Shot}_{Step}_{name}.v{version}.nk"
        # publish template for "nuke_shot_publish" "sequences/{Sequence}/{Shot}/{Step}/publish/nuke/{Shot}_{Step}_{name}.v{version}.nk"
        # set field like Sequence and sg_asset_type
        if not params.get('sg_asset_type') and params.get('entity_type') == 'Asset':
            params["sg_asset_type"] = self.sgCmds.get_entity_list(entityType=params.get('entity_type'), filters=[['code', 'is', params.get('entity_name')]])[0].get('sg_asset_type')

        if not params.get('Sequence') and params.get('entity_type') == 'Shot':
            params["Sequence"] = self.sgCmds.get_entity_list(entityType=params.get('entity_type'), filters=[['code', 'is', params.get('entity_name')]])[0].get('sg_sequence.Sequence.code')

        # remap field like template like
        re_mapping = {
            "Shot": "entity_name",
            "Asset": "entity_name",
            "Step": "step_name",
            "Task": "task_name",
            "name": "publish_name"
        }
        for k in re_mapping:
            if k not in params.keys():
                params[k] = params.get(re_mapping.get(k))

        # get next version available
        logger.debug("params : %s" % pprint.pformat(params))
        params["version"] = bp._get_next_version_available(template_name=bp.template_name, fields=params, version_field_name="version", skip_keys=[], skip_missing_optional_keys=False)

        # get publish_path
        publish_path = bp.template.apply_fields(params)

        logger.info("Publish Path determined : %s" % publish_path)
        nuke.scriptSaveAs(filename=publish_path)

        # get required field for publish in shotgun
        bp.tk = self.sgCmds.tk

        # set ctx
        if params.get('ctx'):
            bp.ctx = params.get('ctx')
        if params.get('task'):
            bp.task = params.get('task')
        if params.get('sg_additional_fields'):
            bp.sg_additional_fields = params.get('sg_additional_fields')
        if not params.get('user'):
            params["user"] = sgtk.util.get_current_user(self.sgCmds.tk)

        if not params.get('ctx'):
            if not params.get('task'):
                # get task
                params['task'] = bp._get_sg_task(task_name=params.get('task_name'), entity_type=params.get('entity_type'), entity_name=params.get('entity_name'), set_as_task=True)
                bp.task = params.get('task')
            # get context from task
            params['ctx'] = bp.tk.context_from_entity(entity_type="Task", entity_id=params.get('task').get('id'))
            bp.ctx = params.get('ctx')

        # set publish_file_path
        bp.publish_file_path = publish_path

        # set publish name
        bp.publish_name = params.get('name')

        # set version
        bp.version = params.get('version')

        # set comment
        bp.comment = params.get('comment')

        # set thumbnail path
        bp.thumbnail_path = params.get('thumbnail_path')

        # set dependencies
        bp._set_dependencies(dependencies=dependency_paths)

        # set published file type
        if not bp.sg_published_file_type:
            bp._get_sg_published_file_type(published_file_type_name=NUKE_PUBLISHED_FILE_TYPE_NAME)

        # set user
        bp.user = params.get('user')

        # register in shotgun
        r = bp._publish_in_shotgun(post_publish=[])
        return r

    def _secondary_publish_file(self, params=None):
        """
        That's the secondary publish.
        Post your primary publish it execute some action like publish your renders.
        """
        logger.debug("params : {p}".format(p=params))
        # params = {
        #   "primary_publish_path": None,
        #   "comment": None,
        #   "thumbnail_path": None,
        #   "use_script_version": True
        #   "tasks": [
        #       {
        #           "type": "publish_write_node",
        #           "node": "ShotgunWrite1",
        #       }
        #   ]
        # }
        # define use_script_version
        if "use_script_version" not in params.keys():
            params["use_script_version"] = True

        # retrieve published data about primary_publish_path
        path_cache = params.get("primary_publish_path").replace("/prod/project/", "")
        primary_published_file = self.sgCmds.get_entity_list(entityType="PublishedFile", filters=[["path_cache", "is", path_cache]])
        print primary_published_file
        if not primary_published_file:
            raise RuntimeError("Can't retrieve primary publish file with path : {p}".format(p=path_cache))
        else:
            primary_published_file = primary_published_file[0]

        # for each task
        for task in params.get("tasks"):

            # setup command
            self._publish_write_node(node_name=task.get("node"), primary_published_file=primary_published_file, params=params, use_script_version=params.get("use_script_version"))

        # get selected render

        # publish render version up + x, based on publish script version. + add tag create_qt_vfx

        return []

    def _publish_write_node(self, node_name, primary_published_file, params, use_script_version=True):
        """
        That's the secondary publish. Post your primary publish it execute some action like publish your renders.
        """
        write_node = nuke.toNode(node_name)

        # get node type
        write_node_type = write_node.Class()

        # init base publish
        bp = ppSgtkPublisher.BasePublish()
        bp.init(primary_published_file.get("id"))

        # case ShotgunWrite node
        if write_node_type == "WriteTank":
            # try to recover write_node_app to interact easily with node.
            write_node_app = self.sgCmds.app_instance.apps.get("tk-nuke-writenode")

            # get file_path
            render_path = write_node_app.get_node_render_path(write_node)
            render_template = write_node_app.get_node_render_template(write_node)
            publish_template = write_node_app.get_node_publish_template(write_node)
            render_path_fields = render_template.get_fields(render_path)

            # retrieve profile. whith profile we could retrieve the published file type to use for publish
            profile_name = write_node_app.get_node_profile_name()  # profile name is like Mono EXR, 16bit

            # get profile detail
            profile_detail = {}
            for s in write_node_app.settings.get("write_nodes"):
                if s.get("name") == profile_name:
                    profile_detail = s

            # override version number if required
            if use_script_version:
                # retrieve publish version from primary_published_file
                render_path_fields["version"] = primary_published_file.get("version_number")

            # ---
            # move file from source to destination
            # source_file_path
            source_file_path = render_path.replace("%V", write_node.knob("views").value())  # replace %V by view name
            # destination path
            destination_file_path = render_template.apply_fields(render_path_fields)
            destination_file_path_without_V = destination_file_path.replace("%V", write_node.knob("views").value())  # replace %V by view name

            logger.info("setup transfert_file_sequence")
            logger.info("source_file_path : {f}".format(f=source_file_path))
            logger.info("destination_file_path : {f}".format(f=destination_file_path_without_V))

            ppFileSequence.transfert_file_sequence(source_file_path=source_file_path, destination_file_path=destination_file_path_without_V, transfert_mode="move", symlink=False)

            # TODO
            # setup publish
            # set ctx
            bp.task = bp.ctx.task
            if params.get('sg_additional_fields'):
                bp.sg_additional_fields = params.get('sg_additional_fields')
            
            if not params.get('user'):
                params["user"] = sgtk.util.get_current_user(bp.tk)

            # set publish_file_path
            bp.publish_file_path = destination_file_path

            # set publish name
            bp.publish_name = render_path_fields.get('name')

            # set version
            bp.version = render_path_fields.get('version')

            # set comment
            bp.comment = params.get('comment')

            # set thumbnail path
            bp._create_thumbnail(destination_file_path)
            bp.thumbnail_path = params.get('comment')

            # set dependencies
            bp._set_dependencies(dependencies=[destination_file_path])

            # get image data like width height
            bp._get_image_data_from_file_path(file_path=destination_file_path)
            bp._update_sg_metadata_based_on_image_data()

            # set published file type
            if not bp.sg_published_file_type:
                bp._get_sg_published_file_type(code=profile_detail.get("tank_type"))

            # register in shotgun
            bp._publish_in_shotgun(post_publish=[])
        return []

    def _create_camera_reader(self, camera_file):
        """Creates a camera node to read a camera file
        :param camera_file: path to the camera file to import
        :type camera_file: str
        :returns: the camera node
        :rtype: node
        """
        node = nuke.createNode('Camera2', inpanel=False)
        node.knob('read_from_file').setValue(True)
        node.knob('file').setValue(camera_file)
        node.knob('fbx_node_name').setValue('ppCam')
        return node

    def _create_OCIODisplay(self):
        """Creates a camera node to read a camera file
        :param camera_file: path to the camera file to import
        :type camera_file: str
        :returns: the camera node
        :rtype: node
        """
        node = nuke.createNode('OCIODisplay', inpanel=False)
        ppTools.auto_set_context_ocio_node(node_type=[], sel=[node])
        return node


def execute_action(action):
    """
    """
    a = Action()
    a.execute_action(action=action)
