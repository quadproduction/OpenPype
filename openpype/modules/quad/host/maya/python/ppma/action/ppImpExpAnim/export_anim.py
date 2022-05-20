import maya.cmds as cmds
import maya.standalone as standalone
try:
    standalone.initialize(name='python')
except:
    pass
import random
import logging
import os
import sys
import time
import subprocess
import sgtk
import ppma.core.ppSceneManagement as ppSceneManagement
import ppma.core.ppScene as ppScene
import ppma.core.ppActions as ppActions
import ppUtils.ppNotifier as ppNotifier
import ppSgtkLibs.ppSgtkCmds as ppSgtkCmds
import ppRenderFarm.ppMuster as ppMuster
import ppUtils.ppSettings as ppSettings

from . import notifier
from . import exp_entity_exporter

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)

# default renderfarm settings
RENDERFARM_SETTINGS = {
    "linux2": {
        "priority": 10001,
        "pool": "Linux"
    },
}


class Exporter(ppSgtkCmds.Cmds):
    """docstring for Exporter"""
    def __init__(self, arg=None):
        super(Exporter, self).__init__(arg=arg)

        self.logger = logging.getLogger('ppma.action.ppImpExpAnim')
        self.logger.setLevel(logging.DEBUG)

        # retrieve sgtk instance
        self.init(arg=arg)

        # init var
        # get scene info
        self.scene = ppScene.Scene()
        # get actions
        self.actions = ppActions.Action()
        self.entities = []
        self.published_file_scene = None
        self.icons_dir = os.environ['PP_PIPE_ICONS']
        # export settings
        self.pre_roll = 30
        self.handles = 30
        # init command like mayapy and other
        self.mayapy_path = None
        # init references
        self.references = {}
        self.special_tags = ['dyn']

    def start(self, nodes=[], subprocess_mode="local", task_name=None):
        """
        This function is main function which launch the export animation
        """
        self.logger.info("Launch Export Animation")

        # get scene infos
        self._get_scene_info()

        if not nodes:
            nodes = self._get_nodes_for_export()

        # get pipeline info like namespace, entity type, asset name
        self._get_entities_info(nodeList=nodes)

        #  publish work scene
        if not task_name:
            # try to retrieve task from context.
            task_name = self.ctx.task['name']

        self._publish_work_scene(task_name=task_name)

        # build export list
        self._get_export_animation_per_entities(subprocess_mode=subprocess_mode)

        self._launch_export_animation_per_entities(export_anim_cmd_list=self.export_anim_cmd_list, subprocess_mode=subprocess_mode)

        return True

    def _get_scene_info(self):
        """Get Maya Scene Information needed by the ui"""
        self.scene.getAnimationSettings()

    def _get_mayapy_path(self):
        """
        retrieve the mayapy path from sgtk.

        """
        self.mayapy_path = "{0}/pp-launch-mayapy".format(os.environ["PP_PIPE_BIN_PATH"])
        return self.mayapy_path

    def _get_python_script_exporter(self):
        """
        This function retrieve the path to the python script
        which use by mayapy to export asset animation.
        """
        return "{0}/python/pp-launch-maya_export_animation.py".format(os.environ["PP_PIPE_BIN_PATH"])

    def _get_export_animation_per_entities(self, subprocess_mode="local"):
        """
        from self.entities build the export animation list. local or on renderfarm
        """
        self.logger.info("Build Export Animation List")
        self.export_anim_cmd_list = []
        # get mayapy path
        self._get_mayapy_path()
        for ent in self.entities:
            # init values
            project_path = self.tk.project_path
            # fucking windows
            project_path = project_path.replace('\\', '/')
            values = {
                'mayapy': self.mayapy_path,
                'project_path': project_path,
                'export': 'export',
                'subprocess_mode': subprocess_mode,
                'publishId': self.published_file_scene['id'],
                'name': ent.info['name'],
                'root_node': ent.info['rootNode'],
                'minTime': self.scene.minTime,
                'maxTime': self.scene.maxTime,
                'user': self.ctx.user['name']
            }
            # it could be possible some override added to the entity so we check and override some data
            if 'name' in ent.info['override'].keys():
                self.logger.info("Apply Override on name from: %s to %s" % (ent.info['name'], ent.info['override']['name']))
                values['name'] = ent.info['override']['name']
            # define arguments
            cmdArgs = []
            script_exporter = self._get_python_script_exporter()
            # build args
            argMapping = {
                '-p': values['project_path'],  # set project_path
                '-s': values['subprocess_mode'],  # set subprocess mode
                '-u': "'%s'" % values['user'],  # set user name
                '-f': values['publishId'],  # set published file to use
                '-e': values['name'],  # set entity name for publish
                '-r': "'%s'" % values['root_node'],  # set root node
                '-i': values['minTime'],
                '-o': values['maxTime']
            }
            for keyArg in sorted(argMapping):
                if sys.platform == 'linux2':
                    cmdArgs.append('%s %s' % (keyArg, argMapping[keyArg]))
                else:
                    cmdArgs.append('"%s %s"' % (keyArg, argMapping[keyArg]))
            # process local
            if subprocess_mode == 'local':
                # define cmd
                cmd = []
                # add mayapy
                if sys.platform == 'linux2':
                    cmd.append('%s' % values['mayapy'])
                    cmd.append('%s' % script_exporter)
                else:
                    cmd.append('"%s"' % values['mayapy'])
                    cmd.append('"%s"' % script_exporter)
                cmd.extend(cmdArgs)
                self.export_anim_cmd_list.append(cmd)
            if subprocess_mode == "renderfarm":
                # build args cmd line
                cmdArgsStr = " ".join(cmdArgs)
                values['published_file_name'] = self.published_file_scene["code"].split('.')[0]
                values['asset'] = ent.info['name']
                values['jobName'] = ppMuster.get_job_name(job_type="exp-anim", step=ent.info['name'], project_name=self.ctx.project['name'], entity=self.published_file_scene["code"].split('.')[0])
                values['project'] = "%s" % (self.ctx.project['name'])
                values['step'] = "%s" % (self.ctx.step['name'])
                values['priority'] = RENDERFARM_SETTINGS[sys.platform]['priority']
                values['pool'] = RENDERFARM_SETTINGS[sys.platform]['pool']
                values['scriptFile'] = script_exporter
                # fucking windows
                values['scriptFile'] = values['scriptFile'].replace('\\', '/')
                values['scriptsArgs'] = cmdArgsStr
                # on renderfarm mode we provide a dict to the export_anim_cmd_list
                self.export_anim_cmd_list.append(values)
        return self.export_anim_cmd_list

    def _get_entities_info(self, nodeList=[]):
        """
        """
        self.logger.info("Get Entities Info")
        for node in nodeList:
            # get pipeline info
            ent = ppSceneManagement.Entity()
            ent.getEntityInfo(node=node)
            self.entities.append(ent)

    def _get_nodes_for_export(self):
        """ retireves node available for export method 1"""
        # get node tagged for export
        nodes = ppSceneManagement.get_nodes_available_for_export()
        if not nodes:
            return False
        else:
            return nodes

    def _launch_export_animation_per_entities(self, export_anim_cmd_list=[], subprocess_mode="local"):
        """
        """
        if export_anim_cmd_list:
            self.export_anim_cmd_list = export_anim_cmd_list
        if not self.export_anim_cmd_list:
            self.logger.error('Please fill the arg export_anim_cmd_list')
            return False
        # case export local
        if subprocess_mode == "local":
            for cmd in self.export_anim_cmd_list:
                self.logger.info("Launching command: \n%s" % ' '.join(cmd))
                if sys.platform == "linux2":
                    # Launch the subprocess
                    if not cmds.about(batch=True):
                        # do user notification
                        obj = cmd[2].split(' ')[1]
                        topNode = cmd[8].split(' ')[1]
                        text = "Publish Name\t: {obj}\nTop Node\t: {topNode}".format(obj=obj, topNode=topNode)
                        ppNotifier.notify(title="Launch - Export Anim - {subprocess_mode}".format(subprocess_mode=subprocess_mode), text=text, time=10000)
                    # init xterm command
                    terminal_title = "Maya-Export-Animation-{shot}-{abc}".format(shot=self.ctx.entity["name"], abc=cmd[2].split(' ')[1])
                    # terminal color
                    terminal_color_list = [
                        "steelblue",
                        "aquamarine",
                        "LightGoldenrod",
                        "IndianRed",
                        "PaleVioletRed",
                        "MediumOrchid",
                        "NavajoWhite1",
                        "ivory1"
                    ]
                    unique_id = random.randint(0, len(terminal_color_list) - 1)
                    terminal_color = terminal_color_list[unique_id]
                    terminal_width_height = [200, 10]
                    cmd_xterm = [
                        "xterm",
                        "-hold",
                        "-bg",
                        "{terminal_color}".format(terminal_color=terminal_color),
                        "-geometry",
                        "{w}x{h}".format(w=terminal_width_height[0], h=terminal_width_height[1]),
                        "-T",
                        terminal_title,
                        "-e",
                        "bash",
                        "-c"
                    ]
                    # add cmd to xterm command
                    cmd_str = " ".join(cmd)
                    # cmd_str = cmd_str.replace("'", "\\'")
                    cmd_xterm.append('"{c}"'.format(c=cmd_str))
                    cmd_xterm.append('&')
                    self.logger.info(" ".join(cmd_xterm))
                    self.logger.info(cmd_str)
                    cmd_xterm_str = " ".join(cmd_xterm)
                    self.logger.info(" ".join(cmd_xterm))
                    try:
                        os.system(cmd_xterm_str)
                        # subprocess.call(cmd_xterm + [cmd_str])
                    except Exception, e:
                        print "Couldn't launch alembic export: %s" % str(e)
                        return False
                else:
                    try:
                        subprocess.Popen(' '.join(cmd))
                    except Exception, e:
                        print "Couldn't launch alembic export: %s" % str(e)
                        return False
                time.sleep(5)
            self.logger.info("Launch Export on %s - Done." % subprocess_mode)
            return True
        # case export on farm
        if subprocess_mode == "renderfarm":
            self.jobList = []
            # get tank context
            tk = sgtk.sgtk_from_path(cmds.file(q=True, sn=True))
            ctx = tk.context_from_path(cmds.file(q=True, sn=True))
            self.muster = ppMuster.MusterManager()
            asset_list = []
            for values in self.export_anim_cmd_list:
                self.logger.info("Launching Job on Renderfarm: %s" % values['jobName'])
                asset_list.append(values['asset'])
                # replace " by ' because system change command launch on muster:(
                values['scriptsArgs'] = values['scriptsArgs'].replace('"', "'")
                environment = 'TANK_CURRENT_PC={shotgun_path}/{project_name}'.format(
                    shotgun_path=os.environ['PP_SHOTGUN'],
                    project_name=values['project'])
                if os.environ.get("TANK_CURRENT_PC"):
                    environment = "TANK_CURRENT_PC={0}".format(os.environ.get("TANK_CURRENT_PC"))
                # get or create parent folder
                parent_folder_id = self._get_create_muster_parent_folder()
                try:
                    txt = "Launch Job: {j}\nPriority: {p}\n".format(j=values['jobName'], p=values['priority'])
                    ppNotifier.notify(title="Export Anim - Renderfarm", text=txt)
                    self.muster.send_mayapy(
                        job_name=values['jobName'],
                        script_file=values['scriptFile'],
                        script_args=values['scriptsArgs'],
                        project=values['project'],
                        department='pp-imp_exp_anim',
                        priority=values['priority'],
                        pools=[values['pool'], ],
                        dependency_jobs=None,
                        dependency_mode=-1,
                        parent_job_id=parent_folder_id,
                        environment=environment,
                        job_owner=sgtk.util.get_current_user(tk)['login']
                    )
                    self.jobList.append(values['jobName'])
                except Exception, e:
                    self.logger.error("Couldn't launch Muster job: %s" % str(e))
            # launch notification
            notifier.send_notification(tk=self.tk, user=ctx.user['name'], project_ctx=ctx.project, step_ctx=ctx.step, entity_ctx=ctx.entity, source_published_file_id=values['publishId'], source_published_file_name=values['published_file_name'], abc_published_file_id=None, entity_name=values['name'], mode="recap_export_on_farm", extra_values={"asset": asset_list}, logger=self.logger)
            self.logger.info("Launch Export on %s - Done." % subprocess_mode)
            for job in self.jobList:
                self.logger.info("\t job: %s" % (job))

    def _get_create_muster_parent_folder(self):
        """
        """
        parent_job_id = self.muster.get_job_id(ppSettings.MUSTER['folders']['actions_folders']['pp_export_anim'])
        if parent_job_id == -1:
            self.muster.create_muster_folders(ppSettings.MUSTER['folders']['actions_folders'])
            parent_job_id = self.muster.get_job_id(ppSettings.MUSTER['folders']['actions_folders']['pp_export_anim'])
        return parent_job_id

    def _publish_work_scene(self, task_name=None):
        """
        """
        self.logger.info("Publish Work Scene")
        # publiscene via ppAction module
        self.published_file_scene = self.actions.execute_action(action="publish_render_scene", params={'comment': 'Auto Published Scene Before Export Animation.'})
        return self.published_file_scene


def export_animation_entity(project_path, published_file_id, entity_name, root_node, in_frame, out_frame, subprocess_mode, user):
    """
    This function is called from the mayapy for export the entity (asset)
    """
    tk = None
    # define logger
    logger = logging.getLogger('ppma.action.ppImpExpAnim')
    logger.setLevel(logging.DEBUG)
    logger.info("Export Animation Entity: ")
    logger.info("\n- project_path %s \n- published_file_id %s \n- entity_name %s \n- root_node %s \n- in_frame %s \n- out_frame %s \n- user %s" % (project_path, published_file_id, entity_name, root_node, in_frame, out_frame, user))
    # get maya infop
    maya_version = cmds.about(q=True, version=True)
    logger.info("Maya Information :\n- version : {v}".format(v=maya_version))
    # get Exporter Class
    exporter = exp_entity_exporter.Entity_Exporter()
    exporter._load_plugins()
    # init sgtk
    if os.path.exists(project_path):
        tk = sgtk.sgtk_from_path(project_path)
        filters = [['id', 'is', int(published_file_id)]]
        fields_return = ['code', 'path', 'task', 'task.Task.step', 'project', 'entity']
        published_file = tk.shotgun.find_one('PublishedFile', filters, fields_return)
        logger.info("published_file Result: %s" % published_file)
        # check publishedFile exist
        if not published_file:
            logger.error("The Published File: %s not exist in Shotgun" % published_file_id)
            return False
        # get pat
        scene_path = published_file['path']['local_path']
        # set new scene
        cmds.file(new=True)
        # open scene
        logger.info("Open Scene: %s" % scene_path)
        try:
            cmds.file(scene_path, open=True, force=True, options="v=1", typ="mayaAscii")
        except RuntimeError, e:
            logger.error("RuntimeError - During Opening File %s \n----------------------------------------------------------------------" % scene_path)
            logger.error("Error Message : \n{e}\n----------------------------------------------------------------------".format(e=e))
            return False
        # get context
        # ctx = tk.context_from_path(scene_path)
        # export animation
        # set task name / sgtk can't retrieve task name from published file.
        res = exporter.export_animation_entity(
            entity_name=entity_name,
            root_node=root_node,
            in_frame=in_frame,
            out_frame=out_frame,
            task_name=published_file['task']['name'],
            subprocess_mode=subprocess_mode,
            user=user)
        logger.info("Export animation Result : {r}".format(r=res))

        # notify user
        if res and subprocess_mode == "renderfarm":
            try:
                r = notifier.send_notification(tk=tk, user=user, project_ctx=published_file['project'], step_ctx=published_file['task.Task.step'], entity_ctx=published_file['entity'], source_published_file_id=published_file_id, source_published_file_name=published_file['code'], abc_published_file_id=res['id'], entity_name=entity_name, mode="export_done_on_farm")
                return True
            except RuntimeError, e:
                logger.error("Can't Send Notification. Error {e}".format(e=e))
                return True

        elif res and subprocess_mode == "local":
            # print beautiful summary for end user.
            # init summary
            summary = "\n-----------------------\n"
            summary += " Export Animation : OK\n"
            summary += "\t Abc \t : {a}\n".format(a=res["code"])
            summary += "\t Scene \t : {a}\n".format(a=published_file['code'].split('.')[0])
            summary += "\t Shot \t : {a}\n".format(a=res["entity"]["name"])
            summary += "\t Project : {a}\n".format(a=res["project"]["name"])
            summary += "\t Task \t : {a}\n".format(a=res["task"]["name"])
            summary += "-----------------------\n"
            logger.info(summary)
            try:
                r = notifier.send_notification(tk=tk, user=user, project_ctx=published_file['project'], step_ctx=published_file['task.Task.step'], entity_ctx=published_file['entity'], source_published_file_id=published_file_id, source_published_file_name=published_file['code'], abc_published_file_id=res['id'], entity_name=entity_name, mode="export_done_on_local", logger=logger)
                return True
            except RuntimeError, e:
                logger.error("Can't Send Notification. Error {e}".format(e=e))
                return True
        else:
            logger.error("Error : {e}".format(e=res))
            # notify end user
            try:
                r = notifier.send_notification(tk=tk, user=user, project_ctx=published_file['project'], step_ctx=published_file['task.Task.step'], entity_ctx=published_file['entity'], source_published_file_id=published_file_id, source_published_file_name=published_file['code'], abc_published_file_id=res['id'], entity_name=entity_name, mode="export_error", error=res)
                return False
            except RuntimeError, e:
                logger.error("Can't Send Notification. Error {e}".format(e=e))
                return False
    else:
        logger.error("Project Path not exist: %s" % project_path)
        return False




