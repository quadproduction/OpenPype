import re
import nuke
import logging
import os
import pprint
from tank_vendor import yaml
import ppSgtkLibs.ppSgtkCmds as ppSgtkCmds
import ppSgtkLibs.ppSgtkPublisher as ppSgtkPublisher
import ppUtils.ppPath as ppPath
import ppTools.ppLinearize as ppLinearize
import ppUtils.ppTemplateFile as ppTemplateFile
import ppnk.core.ppActions as ppActions
import ppnk.core.ppTools as ppTools
from ppRenderFarm import ppMuster
from ppUtils import ppSettings
from ppSgtkLibs import ppTemplateUtils

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppLinearize')
logger.setLevel(logging.DEBUG)


class Linearizer(object):
    """docstring for Linearizer"""
    def __init__(self):
        super(Linearizer, self).__init__()
        self.sgCmds = None
        self.action = ppActions.Action()
        self.publisher = ppSgtkPublisher.BasePublish()

        # init
        self.published_file_id_script = None
        self.sg_published_file_script = None

        self.published_file_id_source = None
        self.sg_published_file_source = None

        self.user_login = None
        self.sg_user = None

        self.jobs_department = 'pp-linearize'

        # ---
        # th new sg published file
        self.sg_published_file_script_new = None
        # the render job id from muster
        self.render_job_id = None

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

    def _get_sg_user(self, user_login):
        """
        """
        sg_users = self.sgCmds.get_entity_list(entityType="HumanUser", filters=[["login", "is", user_login]])
        if sg_users:
            self.sg_user = sg_users[0]
            return self.sg_user
        return None

    def _set_source_reader(self, published_file_id_source):
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

        # retrieve path from published file id
        p = self.sgCmds.get_one_published_file(id=published_file_id_source)
        self.published_file_id_source = published_file_id_source
        self.sg_published_file_source = p

        if not p:
            raise RuntimeError("Can't retrieve the sg_published_file_source in shotgun. {published_file_id_source} not exist".format(published_file_id_source=published_file_id_source))

        # get path for the current platform
        path = ppPath.get_sg_path_from_current_platform(p.get('path'))

        # init params which use by action
        params = {
            "name": self.n.get_node_name("ingest_reader")
        }

        # get resolutions linked to plate > Shot
        resolutions = self.sgCmds._get_resolution_linked_to_shot(shot_name=self.sgCmds.ctx.entity.get('name'))
        if resolutions:
            # get format node, nuke call a resolution data a format
            for resolution in resolutions:
                if resolution.get("sg_pp_resolution_type") == "source":
                    params["format"] = ppTools.get_format(name=resolution.get("code"))

        # create or update reader
        # check if reader already exist
        n = None
        if not nuke.exists(self.n.get_node_name("ingest_reader")):
            raise RuntimeError("The Reader node : {node_name} not exist.".format(node_name=self.n.get_node_name("ingest_reader")))
        else:
            logger.info("update read node")
            # get node
            n = nuke.toNode(self.n.get_node_name("ingest_reader"))
            # setup reader data
            self.action._setup_read_img(node=n, path=path, params=params, sg_publish_data=p)

        if not n:
            raise RuntimeError("Can't setup read node")

        # return
        return True

    def _set_reformat(self):
        """
        This func retrieve the working resolution for the current shot
        and apply it to the registred reformat
        """
        # get context
        self._init_cmds()

        # get params node for settings working resolution
        r = nuke.toNode(self.n.get_node_name("params"))

        # set ingest use source resolution
        # in case source is declared as an element
        # we check the checkbox ingest_use_source_resolution
        ingest_use_source = False
        # Shot Type is Element
        if self.sg_published_file_source.get("entity.Shot.sg_shot_type") == "Element":
            ingest_use_source = True
        # Published File tagged Element
        elif "Element" in self.sg_published_file_source.get("tag_list"):
            ingest_use_source = True

        # in all case set ingest use source
        r.knob(self.n.get_attr_name("params", "ingest_use_source")).setValue(ingest_use_source)

        if not ingest_use_source:

            resolutions = self.sgCmds._get_resolution_linked_to_shot(shot_name=self.sgCmds.ctx.entity.get('name'))

            if not resolutions:
                raise RuntimeError("No resolutions found for this Shot. Can't reformat.")

            # get format node, nuke call a resolution data a format
            f = None
            for resolution in resolutions:
                if resolution.get("sg_pp_resolution_type") == "working":
                    f = ppTools.get_format(name=resolution.get("code"))

            if not f:
                raise RuntimeError("No working resolution found for this Shot. Can't reformat.")

            # apply format to reformat node
            r.knob(self.n.get_attr_name("params", "working_format")).setValue(f)

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

        # init params
        params = {}

        # ---
        # get path
        # get template_name for the render node
        template_name = ppLinearize.LINEAR_SETTINGS.get("publish_render").get("render_template_name")

        # get template, template stored into self.publisher.template
        self.publisher._get_template_from_name(template_name=template_name, and_use_it=True)

        # fill template fields, we assume to be in Shot context
        self.writer_fields = {
            "Sequence": "",
            "%s" % self.sgCmds.ctx.entity.get("type"): self.sgCmds.ctx.entity.get("name"),
            "Step": ppLinearize.LINEAR_SETTINGS.get("publish_render").get("step"),
            "Task": ppLinearize.LINEAR_SETTINGS.get("publish_render").get("task"),
            "graded_name": "raw",  # we don't actually knonwn how to stroe the graded status
            "name": self.sg_published_file_source.get("name"),  # default name for publish
            "file_ext": ppLinearize.LINEAR_SETTINGS.get("publish_render").get("file_ext")
        }

        if not self.writer_fields.get('Sequence') and self.sgCmds.ctx.entity.get("type") == 'Shot':
            self.writer_fields["Sequence"] = self.sgCmds.get_entity_list(entityType=self.sgCmds.ctx.entity.get("type"), filters=[['code', 'is', self.sgCmds.ctx.entity.get("name")]])[0].get('sg_sequence.Sequence.code')

        # override template keys SEQ, by the real padding.
        if self.sg_published_file_source:
            # get padding from self.sg_published_file_source
            path = ppPath.get_sg_path_from_current_platform(self.sg_published_file_source.get('path'))
            # we assume padding is always between under the naming .%04d.
            m = re.search("\.%[0-9][0-9]d\.", path)

            if m:
                seq_padding = int(m.group(0).replace('.%', '').replace('d.', ''))
                # override SEQ
                self.publisher.template = ppTemplateUtils.set_template_sequence_padding(
                    self.publisher.template,
                    "SEQ",
                    seq_padding)
                self.writer_fields["SEQ"] = self.publisher.template.keys["SEQ"].default

        next_version = self.publisher._get_next_version_available(template_name=template_name, fields=self.writer_fields, version_field_name="version", skip_keys=["SEQ"], skip_missing_optional_keys=False)

        self.writer_fields["version"] = next_version
        self.writer_path = self.publisher.template.apply_fields(self.writer_fields)

        logger.info("New Path for render is : %s" % self.writer_path)

        # ---
        # create or update reader
        # check if reader already exist
        w = None
        if not nuke.exists(self.n.get_node_name("ingest_writer")):
            raise RuntimeError("The Writer node {writer_node}".format(writer_node=self.n.get_node_name("ingest_writer")))
        else:
            logger.info("update write node")
            # get node
            w = nuke.toNode(self.n.get_node_name("ingest_writer"))
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

    def _launch_render_job(self):
        """
        This func launch the render job on the renderfarm.
        :returns: the render job id
        :rtype: int
        """

        # get parent folder id
        muster_manager = ppMuster.MusterManager()
        parent_folder_id = muster_manager.get_job_id(job_name=ppLinearize.get_job_name(job_type="", published_file_id=self.published_file_id_source))

        # setup args
        script_file = ppPath.get_sg_path_from_current_platform(self.sg_published_file_script_new.get('path'))
        job_name = ppLinearize.get_job_name(job_type="render", published_file_id=self.published_file_id_source)

        # get node
        n = nuke.toNode(self.n.get_node_name("ingest_reader"))
        start_frame = int(n.knob("first").getValue())
        end_frame = int(n.knob("last").getValue())
        by_frame = 1

        # create job
        self.render_job_id = muster_manager.send_nuke_render(
            job_name=job_name,
            script_file=script_file,
            start_frame=start_frame,
            end_frame=end_frame,
            by_frame=by_frame,
            #  render only this node
            script_args="-X %s" % self.n.get_node_name("ingest_writer"),
            project=self.sgCmds.ctx.project.get('name'),
            department=self.jobs_department,
            priority=ppLinearize.JOB_PRIORITY,
            pools=[ppSettings.MUSTER['pools']['nuke'], ],
            dependency_jobs=None,
            dependency_mode=-1,
            parent_job_id=parent_folder_id,
            pipe_version="None",
            packet_size=(end_frame - start_frame + 1),
            maximum_instances=0,
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

        # get parent folder id
        muster_manager = ppMuster.MusterManager()
        muster_resources_root_folder = ppMuster.compute_project_muster_resources_folder(
            self.sgCmds.tk.shotgun,
            self.sgCmds.ctx.project.get('name'))
        muster_manager.set_resources_root_folder(muster_resources_root_folder)
        job_resources_folder = muster_manager.get_job_resources_folder('linerarize__publish_file')
        parent_folder_id = muster_manager.get_job_id(job_name=ppLinearize.get_job_name(job_type="", published_file_id=self.published_file_id_source))

        job_name = ppLinearize.get_job_name(job_type="publish", published_file_id=self.published_file_id_source)

        if not self.sg_user:
            self._get_sg_user()

        extra_template_fields_dict_file = ppMuster.encode_dict_in_file(
            {'SEQ': self.writer_fields.get("SEQ")},
            job_resources_folder,
            file_name='extra_template_fields')
        sg_user_short = {"type": self.sg_user.get("type"), "id": self.sg_user.get("id")}
        sg_user_dict_file = ppMuster.encode_dict_in_file(
            sg_user_short,
            job_resources_folder,
            file_name='user')

        # setup publish command
        cmd = [
            "pp-launch-publish_file",
            "--project", self.sgCmds.ctx.project.get('name'),
            "--filePath", self.writer_path,
            "--fileType", ppLinearize.LINEAR_SETTINGS.get("publish_render").get("published_file_type"),
            "--linkType", self.sgCmds.ctx.entity.get("type"),
            "--linkName", self.writer_fields.get(self.sgCmds.ctx.entity.get("type")),
            "--publishName", self.sg_published_file_source.get("name"),
            "--stepName", self.writer_fields.get("Step"),
            "--taskName", self.writer_fields.get("Task"),
            "--version", str(self.writer_fields.get("version")),
            # "--comment",
            # "daily",
            "--dependencies", str(self.sg_published_file_script_new.get("id")), str(self.sg_published_file_source.get("id")),
            # "audioFile",
            # "audioOffset",
            "--colorSpace", ppLinearize.LINEAR_SETTINGS.get("publish_render").get("colorspace"),
            # "frameRate",
            # "sgMetaData",
            # "thumbnail",
            "--user", sg_user_dict_file,
            # "tags",
            "--copy_mode", ppLinearize.LINEAR_SETTINGS.get("publish_render").get("copy_mode"),
            "--set_status", ppLinearize.LINEAR_SETTINGS.get("publish_render").get("set_status"),
            "--notify", str(False),
            "--extra_template_fields", extra_template_fields_dict_file,
            # "sg_additional_fields",
        ]
        logger.info(pprint.pformat(cmd))
        cmd_str = " ".join(cmd)

        # create job
        self.publish_job_id = muster_manager.sendShellCommands(
            [cmd_str, ],
            job_name=job_name,
            project=self.sgCmds.ctx.project.get('name'),
            department=self.jobs_department,
            priority=ppLinearize.JOB_PRIORITY,
            pools=[ppSettings.MUSTER['pools']['pp_process'], ],
            parent_job_id=parent_folder_id,
            dependency_jobs=[self.render_job_id],
            dependency_mode=ppMuster.DependMode.SUCCESS_REQUIRED,
            job_owner=self.user_login
        )

        return self.publish_job_id

    def linearizer(self, published_file_id_script, published_file_id_source, actions, project_name, user_login):
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

        # setup reader, set path, format, color space, in and out range, ocio context
        self._set_source_reader(published_file_id_source=published_file_id_source)

        # setup reformat resolution
        self._set_reformat()

        # setup writer
        self._set_writer()

        # publish script
        self._publish_script()

        # launch a render job
        self._launch_render_job()

        # launch a publish job
        self._launch_publish_job()

        return True


def linearize_setup(published_file_id_script, published_file_id_source, actions, project_name, user_login):
    """
    Thi function launch the linearization setup script which
    - create a task if required
    - create copy a template nuke script if required
    - open the shot script
    - setup the reader (path, color_space, in, out)
    - setup the reformat
    - setup the writer
    """

    lin = Linearizer()
    lin.linearizer(published_file_id_script=published_file_id_script, published_file_id_source=published_file_id_source, actions=actions, project_name=project_name, user_login=user_login)
