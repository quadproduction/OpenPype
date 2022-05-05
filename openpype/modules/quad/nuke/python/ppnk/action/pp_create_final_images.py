import re
import sys
import nuke
import logging
import argparse
import os
import pprint
from tank_vendor import yaml
import ppSgtkLibs.ppSgtkCmds as ppSgtkCmds
import ppSgtkLibs.ppSgtkPublisher as ppSgtkPublisher
import ppUtils.ppPath as ppPath
import ppSgtkLibs.ppProjectUtils as ppProjectUtils
import ppTools.pp_create_final_images as pp_create_final_images
import ppUtils.ppTemplateFile as ppTemplateFile
import PyOpenColorIO
import ppnk.core.ppActions as ppActions
import ppnk.core.ppTools as ppTools
from ppRenderFarm import ppMuster
from ppUtils import ppSettings
from ppSgtkLibs import ppTemplateUtils

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('pp_create_final_images')
logger.setLevel(logging.DEBUG)


class Finalizer(object):
    """docstring for Finalizer"""
    def __init__(self):
        super(Finalizer, self).__init__()
        self.sgCmds = None
        self.action = ppActions.Action()
        self.publisher = ppSgtkPublisher.BasePublish()

        # init
        self.published_file_id_script = None
        self.sg_published_file_script = None

        self.published_file_id_source = None
        self.sg_published_file_source = None

        self.published_file_id_grab = None
        self.sg_published_file_grab = None

        self.delivery_in = None
        self.delivery_out = None

        # ---
        # th new sg published file
        self.sg_published_file_script_new = None
        # the render job id from muster
        self.render_job_id = None
        # jobs department
        self.jobs_department = 'pp-final_image'

        # dedicated to store frame numbers data from project
        self.frame_numbers = {}
        self.slate_frame_number = 1000000000000000

        self.n = ppTemplateFile.get_nodes_for_file(file_name="io_main")

    def _init_cmds(self, arg=None):
        """
        This function launch the initialisation of ppSgtkCmds.

        :param arg: project_name or other thing describe in ppSgtkCmds.Cmds
        :type arg: str

        :returns: nothing but self.sgCmds is initialized
        :rtype: None
        """
        self.sgCmds = ppSgtkCmds.Cmds(arg)
        self.sgCmds.init(arg)

    def _get_delivery_spec(self):
        """
        This function retrieve the final delivery spec for the current shot context.
        and also retrieve the codec linked to, and store it into self.codec_spec
        :returns: self.delivery_spec the sg delivery spec
        :rtype: dict
        """

        # get context
        self._init_cmds()

        # get delivery spec
        filters = [
            ["sg_pp_type", "is", "final"],
            ["sg_status_list", "is", "act"]
        ]
        delivery_specs = self.sgCmds.get_entity_list(entityType="DeliverySpec", filters=filters)

        if not delivery_specs:
            raise RuntimeError("Delivery Spec Final and Active not exist for this project.")

        # acquire delivery spec
        self.delivery_spec = delivery_specs[0]

        # get codec spec
        self.codec_spec = self._get_codec_spec(codec_name=self.delivery_spec.get("sg_pp_codec").get("name"))

        return self.delivery_spec

    def _get_codec_spec(self, codec_name):
        """
        This function retrieve the codec spec by name linked to project.
        :params
        """
        # get delivery spec
        filters = [
            ["code", "is", codec_name]
        ]
        codec_specs = self.sgCmds.get_entity_list(entityType="CodecSpec", filters=filters)
        if not codec_specs:
            raise RuntimeError("Codec Spec '%s' seems not exit in Codec Spec List." % codec_name)

        self.codec_spec = codec_specs[0]

        return self.codec_spec

    def _open_published_file_id(self, published_file_id):
        """
        This function retrieve the path for the provided published file id
        and open it.
        :param published_file_id: published file id like 15
        :type published_file_id: int
        :returns: True or False
        :rtype: bool
        """
        # retrieve path from cmds
        p = self.sgCmds.get_one_published_file(id=published_file_id)
        self.published_file_id_script = published_file_id
        self.sg_published_file_script = p

        # open script via ppActions
        # define path and params
        path = ppPath.get_sg_path_from_current_platform(p.get('path'))
        params = {
            "sgpf": p  # sgpf is for shotgun published file like return by a find_one('PublishedFile', [], ['path'])
        }
        r = self.action._open_file(path=path, params=params)

        # get context
        self._init_cmds()

        return r

    def _get_frame_numbers(self):
        """
        This function retrieve the frame numbers declaration linked to current project.
        :returns: the dict which represent the frame_numbers settings
        :rtype: dict
        """
        # get context
        self._init_cmds()

        project_settings_manager = ppProjectUtils.Project_Settings(project_name=self.sgCmds.ctx.project.get("name"))
        self.frame_numbers = project_settings_manager.get_settings('frameNumbers')

        return self.frame_numbers

    def _get_sg_user(self, user_login):
        """
        """
        sg_users = self.sgCmds.get_entity_list(entityType="HumanUser", filters=[["login", "is", user_login]])
        if sg_users:
            self.sg_user = sg_users[0]
            return self.sg_user
        return None

    def _set_grab_source_reader(self, published_file_id):
        """
        This function retrieve the path for the provided published file id and
        - set the path
        - set the color space
        - set the format
        - set the frame range
        :param published_file_id: published file id like 15
        :type published_file_id: int
        :returns: True or False
        :rtype: bool
        """
        # get context
        self._init_cmds()

        node_name = self.n.get_node_name("final_metada_reader")

        # get sg published file
        # retrieve path from published file id
        self.sg_published_file_grab = self.sgCmds.get_one_published_file(id=published_file_id)
        self.published_file_id_grab = published_file_id

        if not self.sg_published_file_grab:
            raise RuntimeError("Can't retrieve the sg_published_file_source in shotgun. {published_file_id} not exist".format(published_file_id=published_file_id))

        self._set_reader(sg_published_file_id=self.sg_published_file_grab, node_name=node_name)

        return True

    def _set_color_transform(self):
        """
        This func retrieve lut and cdl for sthe current shot and apply it to params node.
        """
        #  get project settings from SG
        project_settings_manager = ppProjectUtils.Project_Settings(project_name=self.sgCmds.ctx.project.get("name"))
        project_settings = project_settings_manager.get_project_settings()
        # get ocio look name which includ lut and cdl
        ocio_io_look_name = project_settings['color_management_io_look_name']['value'].lower()
        # get lut and cdl from OCIO look
        lut_path = None
        cdl_path = None
        ocio_config = PyOpenColorIO.GetCurrentConfig()
        ocio_looks = ocio_config.getLooks()
        ocio_look = None
        # a. get the right look
        for look in ocio_looks:
            if look.getName() == ocio_io_look_name:
                ocio_look = look
                break
        # search the transform sources through the OCIO dir
        if ocio_look is not None:
            ocio_dir = os.path.dirname(os.environ['OCIO'])
            for transform in ocio_look.getTransform().getTransforms():
                if type(transform) == PyOpenColorIO.FileTransform:
                    src = transform.getSrc().replace('${PP_SHOT}', self.sgCmds.ctx.entity.get("name"))
                    for root, dirs, filenames in os.walk(ocio_dir):
                        for filename in filenames:
                            if filename == src:
                                transform_path = os.path.join(root, filename)
                                if 'lut' in transform_path:
                                    lut_path = transform_path
                                elif 'cdl' in transform_path:
                                    cdl_path = transform_path
        #  set param node
        param_node = nuke.toNode(self.n.get_node_name("params"))
        if lut_path:
            logger.info("Set Lut Path : %s" % lut_path)
            param_node.knob(self.n.get_attr_name("params", "lut")).setValue(lut_path)
        if cdl_path:
            logger.info("Set Lut Path : %s" % cdl_path)
            param_node.knob(self.n.get_attr_name("params", "cdl")).setValue(cdl_path)

    def _set_source_reader(self, published_file_id):
        """
        This function retrieve the path for the provided published file id and
        - set the path
        - set the color space
        - set the format
        - set the frame range
        :param published_file_id: published file id like 15
        :type published_file_id: int
        :returns: True or False
        :rtype: bool
        """
        # get context
        self._init_cmds()

        node_name = self.n.get_node_name("final_reader")

        # get sg published file
        # retrieve path from published file id
        self.sg_published_file_source = self.sgCmds.get_one_published_file(id=published_file_id)
        self.published_file_id_source = published_file_id

        if not self.sg_published_file_source:
            raise RuntimeError("Can't retrieve the sg_published_file_source in shotgun. {published_file_id} not exist".format(published_file_id=published_file_id))

        self._set_reader(sg_published_file_id=self.sg_published_file_source, node_name=node_name)

        return True

    def _set_reader(self, sg_published_file_id, node_name):
        """
        This function retrieve the path for the provided published file id and
        - set the path
        - set the color space
        - set the format
        - set the frame range
        :param published_file_id: published file id like 15
        :type published_file_id: int
        :param node_name: nuke reader node_name
        :type node_name: int
        :returns: True or False
        :rtype: bool
        """

        # get path for the current platform
        path = ppPath.get_sg_path_from_current_platform(sg_published_file_id.get('path'))

        # init params which use by action
        params = {
            "name": node_name
        }

        # get resolutions linked to plate > Shot
        resolutions = self.sgCmds._get_resolution_linked_to_shot(shot_name=self.sgCmds.ctx.entity.get('name'))
        if resolutions:
            # get format node_name, nuke call a resolution data a format
            for resolution in resolutions:
                if resolution.get("sg_pp_resolution_type") == "source":
                    params["format"] = ppTools.get_format(name=resolution.get("code"))

        # create or update reader
        # check if reader already exist
        n = None
        if not nuke.exists(node_name):
            raise RuntimeError("The Reader node : {node_name} not exist.".format(node_name=node_name))
        else:
            logger.info("update read node")
            # get node
            n = nuke.toNode(node_name)
            # setup reader data
            self.action._setup_read_img(node=n, path=path, params=params, sg_publish_data=sg_published_file_id)

        if not n:
            raise RuntimeError("Can't setup read node")

        # return
        return True

    def _set_reformat(self):
        """
        This func retrieve the final resolution for the current shot
        and apply it to the registred reformat
        """
        # get context
        self._init_cmds()

        # get params node for settings working resolution
        r = nuke.toNode(self.n.get_node_name("params"))

        # get resolutions linked to shot
        resolutions = self.sgCmds._get_resolution_linked_to_shot(shot_name=self.sgCmds.ctx.entity.get('name'))

        if not resolutions:
            raise RuntimeError("No resolutions found for this Shot. Can't reformat.")

        # get format node, nuke call a resolution data a format
        f = None
        for resolution in resolutions:
            if resolution.get("sg_pp_resolution_type") == "final":
                f = ppTools.get_format(name=resolution.get("code"))

        if not f:
            raise RuntimeError("No working resolution found for this Shot. Can't reformat.")

        # apply format to reformat node
        r.knob(self.n.get_attr_name("params", "final_format")).setValue(f)

        return True

    def _set_slate(self, slate_path):
        """
        This function set the slate provided into the final images.
        :param slate_path: str which represent the file path.
        :type slate_path: str
        :returns: true or false
        :rtype: bool
        """

        # slate is required
        # get slate frame number
        if not self.frame_numbers:
            self._get_frame_numbers()

        if not self.delivery_in:
            self._get_cut_info()

        self.slate_frame_number = self.delivery_in - 1

        # set frame bumber into nuke
        n = nuke.toNode(self.n.get_node_name("params"))
        if not n:
            raise RuntimeError("The params seems not exist.")
        n.knob(self.n.get_attr_name(node="params", attr="slate_frame_number")).setValue(self.slate_frame_number)

        # set slate active
        n.knob(self.n.get_attr_name(node="params", attr="add_slate_to_final")).setValue(1)

        # get slate node reader
        n = nuke.toNode(self.n.get_node_name("final_slate_reader"))
        if not n:
            raise RuntimeError("The final slate reader seems not exist.")

        # init params which use by action
        params = {
            "name": self.n.get_node_name("final_slate_reader")
        }

        # set path
        self.action._setup_read_img(node=n, path=slate_path, params=params)

        return True

    def _set_writer(self):
        """
        This func setup the writer node for the render.
        - from template retrieve the path
        - setup path
        - setup colorspace / define by user
        - setup file format and settings / define by user
        """
        # get context
        self._init_cmds()

        # check if writer exist
        if not nuke.exists(self.n.get_node_name("final_writer")):
            raise RuntimeError("The Writer node {writer_node}".format(writer_node=self.n.get_node_name("final_writer")))

        # get node
        w = nuke.toNode(self.n.get_node_name("final_writer"))

        # get delivery spec
        self._get_delivery_spec()

        path_source = ppPath.get_sg_path_from_current_platform(self.sg_published_file_source.get('path'))

        # ---
        # get template_name for the render node
        template_name = pp_create_final_images._SETTINGS.get("publish_render").get("render_template_name")

        # get template, template stored into self.publisher.template
        self.publisher._get_template_from_name(template_name=template_name, and_use_it=True)

        # fill template fields, we assume to be in Shot context
        # and we try to fill the specific template bases on the published source
        self.writer_fields = {
            "Sequence": "",  # there will be resolve later.
            "%s" % self.sgCmds.ctx.entity.get("type"): self.sgCmds.ctx.entity.get("name"),
            "Step": self.sg_published_file_source.get("task.Task.step").get("name"),
            "Task": self.sg_published_file_source.get("task").get("name"),
            "name": self.sg_published_file_source.get("name"),  # default name for publish
            "version": self.sg_published_file_source.get("version_number"),  # version is the same as source
            "file_ext": self.codec_spec.get("sg_pp_file_extension"),
            "width": w.width(),
            "height": w.height(),
            "PublishedType": pp_create_final_images._SETTINGS.get("publish_render").get("published_file_type_short_name")
        }

        if not self.writer_fields.get('Sequence') and self.sgCmds.ctx.entity.get("type") == 'Shot':
            self.writer_fields["Sequence"] = self.sgCmds.get_entity_list(entityType=self.sgCmds.ctx.entity.get("type"), filters=[['code', 'is', self.sgCmds.ctx.entity.get("name")]])[0].get('sg_sequence.Sequence.code')

        # override template keys SEQ, by the real padding.
        if self.sg_published_file_source:
            # get padding from self.sg_published_file_source

            # we assume padding is always between under the naming .%04d.
            m = re.search("\.%[0-9][0-9]d\.", path_source)

            if m:
                seq_padding = int(m.group(0).replace('.%', '').replace('d.', ''))
                # override SEQ
                self.publisher.template = ppTemplateUtils.set_template_sequence_padding(
                    self.publisher.template,
                    "SEQ",
                    seq_padding)
                self.writer_fields["SEQ"] = self.publisher.template.keys["SEQ"].default

        self.writer_path = self.publisher.template.apply_fields(self.writer_fields)

        logger.info("New Path for render is : %s" % self.writer_path)

        # ---
        # setup encoding params. the encoding is described by the Codec Spec in the field metadata.
        params = {}
        print self.codec_spec
        for attr in yaml.load(self.codec_spec.get("sg_pp_metadata")).get("nuke"):
            for attr_name in attr.keys():
                params[attr_name] = attr.get(attr_name)

        # ---
        # setup reader data
        self.action._setup_write_img(node=w, path=self.writer_path, params=params)

        # create output dir before render, you're so stupid nuke
        if not os.path.exists(os.path.dirname(self.writer_path)):
            os.makedirs(os.path.dirname(self.writer_path))

        return True

    def _publish_script(self):
        """
        This func publish the current script as new version.
        :returns: the shotgun published file dict
        :rtype: dict
        """

        # get context
        self._init_cmds()

        # init params
        params = {}
        params["project"] = self.sgCmds.ctx.project.get('name')
        params["entity_type"] = self.sgCmds.ctx.entity.get('type')
        params["entity_name"] = self.sgCmds.ctx.entity.get('name')
        params["step_name"] = self.sgCmds.ctx.step.get('name')
        params["task_name"] = self.sgCmds.ctx.task.get('name')
        params["task"] = self.sgCmds.ctx.task
        params["sg_additional_fields"] = {
            "tag_list": ["auto-publish"]
        }

        self.sg_published_file_script_new = self.action._primary_publish_file(params=params)
        # get a full detail sg published file
        self.sg_published_file_script_new = self.sgCmds.get_entity_list(entityType="PublishedFile", filters=[["id", "is", self.sg_published_file_script_new.get("id")]])[0]

        return self.sg_published_file_script_new

    def _get_cut_info(self):
        """
        """

        # get shot cut info
        filters = [['id', 'is', self.sgCmds.ctx.entity.get('id')]]
        sg_shot = self.sgCmds.get_entity_list("Shot", filters=filters)[0]

        # get start end frame
        delivery_head_handle = self.frame_numbers.get("frameNumbers_frameNumbers_delivery_head_handles").get("value")
        cut_in = sg_shot.get("sg_inframe")  # get cut in shot info
        cut_out = sg_shot.get("sg_outframe")  # get cut out shot info
        delivery_tail_handle = self.frame_numbers.get("frameNumbers_frameNumbers_delivery_tail_handles").get("value")

        self.delivery_in = cut_in - delivery_head_handle
        self.delivery_out = cut_out + delivery_tail_handle

    def _launch_render_job(self):
        """
        This func launch the render job on the renderfarm.
        :returns: the render job id
        :rtype: int
        """

        # get parent folder id
        muster_manager = ppMuster.MusterManager()
        parent_folder_id = muster_manager.get_job_id(job_name=pp_create_final_images.get_job_name(job_type="", published_file_id=self.published_file_id_source))

        # setup args
        script_file = ppPath.get_sg_path_from_current_platform(self.sg_published_file_script_new.get('path'))
        job_name = pp_create_final_images.get_job_name(job_type="render", published_file_id=self.published_file_id_source)

        # get cut info
        self._get_cut_info()

        start_frame = self.delivery_in
        end_frame = self.delivery_out
        by_frame = 1

        if self.slate_frame_number < start_frame:
            start_frame = self.slate_frame_number

        # create job
        self.render_job_id = muster_manager.send_nuke_render(
            job_name=job_name,
            script_file=script_file,
            start_frame=start_frame,
            end_frame=end_frame,
            by_frame=by_frame,
            #  render only this node
            script_args="-X %s" % self.n.get_node_name("final_writer"),
            project=self.sgCmds.ctx.project.get('name'),
            department=self.jobs_department,
            priority=pp_create_final_images.JOB_PRIORITY,
            pools=[ppSettings.MUSTER['pools']['nuke'], ],
            dependency_jobs=None,
            dependency_mode=-1,
            parent_job_id=parent_folder_id,
            pipe_version="None",
            environment="",
            packet_size=(end_frame - start_frame + 1),
            maximum_instances=1,
            job_owner=self.user_login)

        return self.render_job_id

    def _convert_dict_to_yaml_str(self, arg):
        """
        """
        arg_yaml = yaml.dump(arg, width=10000)
        # remove \n at the end
        arg_yaml = arg_yaml.replace('\n', '')
        # protect
        arg_yaml = '\\"%s\\"' % arg_yaml

        return arg_yaml

    def _launch_publish_job(self):
        """
        This func launch a publish job on the renderfarm.
        :returns: the shotgun published file dict
        :rtype: dict
        """

        muster_manager = ppMuster.MusterManager()
        # get parent folder id
        parent_folder_id = muster_manager.get_job_id(job_name=pp_create_final_images.get_job_name(job_type="", published_file_id=self.published_file_id_source))
        # compute jobs resources folder
        muster_resources_root_folder = ppMuster.compute_project_muster_resources_folder(
            self.sgCmds.tk.shotgun,
            self.sgCmds.ctx.project.get('name'))
        muster_manager.set_resources_root_folder(muster_resources_root_folder)
        job_resources_folder = muster_manager.get_job_resources_folder('publish_final_images')
        job_name = pp_create_final_images.get_job_name(job_type="publish", published_file_id=self.published_file_id_source)

        if not self.sg_user:
            self._get_sg_user()

        # define dependencies
        dependencies = [
            self.sg_published_file_script_new.get("id"),
            self.sg_published_file_source.get("id")
        ]
        if self.sg_published_file_grab:
            dependencies.append(self.sg_published_file_grab.get("id"))

        extra_template_fields_dict_file = ppMuster.encode_dict_in_file(
            {'SEQ': self.writer_fields.get("SEQ")},
            job_resources_folder,
            file_name='extra_template_fields')
        sg_user_short = {"type": self.sg_user.get("type"), "id": self.sg_user.get("id")}
        sg_user_dict_file = ppMuster.encode_dict_in_file(
            sg_user_short,
            job_resources_folder,
            file_name='user')
        sg_additional_fields_dict_file = ppMuster.encode_dict_in_file(
            {'version': self.sg_published_file_source.get("version")},
            job_resources_folder,
            file_name='sg_additional_fields')

        # setup publish command
        cmd = [
            "pp-launch-publish_file",
            "--project", self.sgCmds.ctx.project.get('name'),
            "--filePath", self.writer_path,
            "--fileType", pp_create_final_images._SETTINGS.get("publish_render").get("published_file_type_short_name"),
            "--linkType", self.sgCmds.ctx.entity.get("type"),
            "--linkName", self.writer_fields.get(self.sgCmds.ctx.entity.get("type")),
            "--publishName", self.sg_published_file_source.get("name"),
            "--stepName", self.writer_fields.get("Step"),
            "--taskName", self.writer_fields.get("Task"),
            "--version", str(self.writer_fields.get("version")),
            # "--comment",
            # "daily",
            # "audioFile",
            # "audioOffset",
            "--colorSpace", self.delivery_spec.get("sg_pp_color_space").get("name"),
            # "frameRate",
            # "sgMetaData",
            # "thumbnail",
            "--user", sg_user_dict_file,
            # "tags",
            "--copy_mode", pp_create_final_images._SETTINGS.get("publish_render").get("copy_mode"),
            "--set_status", self.sg_published_file_source.get("sg_status_list"),
            "--notify", str(False),
            "--extra_template_fields", extra_template_fields_dict_file,
            "--sg_additional_fields", sg_additional_fields_dict_file
        ]
        # add dependencies
        cmd.append("--dependencies")
        for dependency in dependencies:
            cmd.append(str(dependency))
        # stringify command
        logger.info(pprint.pformat(cmd))
        cmd_str = " ".join(cmd)

        # create job
        self.publish_job_id = muster_manager.sendShellCommands(
            [cmd_str, ],
            job_name=job_name,
            project=self.sgCmds.ctx.project.get('name'),
            department=self.jobs_department,
            priority=pp_create_final_images.JOB_PRIORITY,
            pools=[ppSettings.MUSTER['pools']['pp_process'], ],
            parent_job_id=parent_folder_id,
            dependency_jobs=[self.render_job_id],
            dependency_mode=ppMuster.DependMode.SUCCESS_REQUIRED,
            job_owner=self.user_login
        )

        return self.publish_job_id

    def start(self, published_file_id_script, published_file_id_source, actions, project_name=None, published_file_id_grab=None, slate_path=None, user_login=None):
        """
        """
        if not project_name:
            raise RuntimeError("Can't work without project name")

        #  init ppSgtkCmds into self.sgCmds
        self._init_cmds(arg=project_name)

        self.user_login = user_login
        self._get_sg_user(user_login=user_login)

        # open nuke scene
        r = self._open_published_file_id(published_file_id=published_file_id_script)
        if not r:
            raise RuntimeError("Can't Open File with Published File Id : {published_file_id_script}".format(published_file_id_script=published_file_id_script))

        # auto-set ocio context based on nuke sgtk current context
        ppTools.auto_set_context_ocio_node()

        # set color transform like lut and cdl
        self._set_color_transform()

        # get original grab for push metadata into final dpx
        if published_file_id_grab:
            self._set_grab_source_reader(published_file_id=published_file_id_grab)

        # setup reader, set path, format, color space, in and out range, ocio context
        self._set_source_reader(published_file_id=published_file_id_source)

        # apply final resolution
        self._set_reformat()

        # setup slate if required
        if slate_path:
            self._set_slate(slate_path=slate_path)

        # setup writer
        self._set_writer()

        # publish script
        self._publish_script()

        # launch a render job
        self._launch_render_job()

        # launch a publish job
        self._launch_publish_job()

        return True
