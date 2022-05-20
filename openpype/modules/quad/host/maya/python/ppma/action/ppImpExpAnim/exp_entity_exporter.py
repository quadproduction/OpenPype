import maya.cmds as cmds
import maya.mel as mel
import logging
import os
import sys
import platform
import sgtk
import ppma.core.ppSceneManagement as ppSceneManagement
import ppma.core.ppScene as ppScene
import ppma.core.ppActions as ppActions
import ppma.core.ppPlugins as ppPlugins
import ppma.core.ppNode as ppNode
import ppUtils.ppNotifier as ppNotifier

from ppSgtkLibs import ppSgtkPublisher
from . import exp_rename_shape_deformed
# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format, level=logging.DEBUG)

# define local folder
ROOT_FOLDER = "d:"
if sys.platform == "linux2":
    ROOT_FOLDER = os.environ['HOME']
try:
    ROOT_FOLDER = os.environ['PP_DATA_DIR']
except:
    pass
LOCAL_FOLDER = "%s/pp/tmpExportAnimation" % ROOT_FOLDER


class Entity_Exporter(object):
    """docstring for Entity_Exporter"""
    def __init__(self, ):
        super(Entity_Exporter, self).__init__()
        # self.arg = arg
        self.logger = logging.getLogger('ppma.action.ppImpExpAnim')
        self.logger.setLevel(logging.DEBUG)

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

    def _setup_maya_for_export(self):
        """
        """
        # houdini engine set asynchronous mode set to false
        try:
            self.logger.info("houdini engine set asynchronous mode set to false")
            mel.eval("houdiniEnginePreferences_toggleAsynchronousMode false")
        except:
            pass

    def _force_execute_scriptNode(self):
        """
        sometimes we use script node for force the loading of a specific reference file.
        in batch we must force excute the script node before export the abc.
        """
        # we get from ppNode.Reference the pattern name for ours script node
        r = ppNode.Reference()
        cAttr = ppNode.CustomAttr()
        pattern = "%s_%s" % (cAttr.prefix, r.scriptNodeAttrReferenceNode)
        self.logger.info("Force Execute Script Node match pattern: %s" % pattern)
        # list script node.
        sns = cmds.ls("%s*" % pattern, type="script")
        if sns:
            for sn in sns:
                self.logger.info("\t executeBefore %s" % sn)
                cmds.scriptNode(sn, executeBefore=True)

    def _bake_joints(self, min_frame, max_frame):
        """
        """
        # bake joint
        self.logger.info("do bake joint")
        joints = cmds.ls(type='joint')
        if joints:
            # Publish the file
            try:
                res = cmds.bakeResults(joints, simulation=True, time=(min_frame, max_frame), sampleBy=1, disableImplicitControl=True, preserveOutsideKeys=True, sparseAnimCurveBake=False, removeBakedAttributeFromLayer=False, bakeOnOverrideLayer=False, minimizeRotation=True, controlPoints=False, shape=True)
            except Exception, e:
                self.logger.error("Couldn't bake joints %s" % (joints))
                self.logger.error("%s" % str(e))
                return False
            return res
        else:
            return True

    def _bake_constraint(self, min_frame, max_frame):
        """
        """
        # bake joint
        self.logger.info("do bake constraint")
        # init bake list
        bl = []
        # list all constraint in the scene.
        constraints = cmds.ls(type='constraint')
        # for each constraint get the conenction list.
        for c in constraints:
            # get connections
            nodes = cmds.listConnections(c, source=False, destination=True, plugs=False)
            if nodes:
                for n in nodes:
                    if n not in bl:
                        bl.append(n)
        if bl:
            res = cmds.bakeResults(bl, simulation=True, time=(min_frame, max_frame), sampleBy=1, disableImplicitControl=True, preserveOutsideKeys=True, sparseAnimCurveBake=False, removeBakedAttributeFromLayer=False, bakeOnOverrideLayer=False, minimizeRotation=True, controlPoints=False, shape=True)
            # delete by constraints
            cmds.delete(bl, constraints=True)
            return res
        else:
            return True

    def _load_plugins(self):
        """
        _load_plugins required
        """
        # Load plugins fbxmaya
        pluginList = ["AbcImport", "AbcExport"]
        res = ppPlugins.loadPlugins(pluginNameList=pluginList)
        for pluginName in pluginList:
            if not res[pluginName]['loaded']:
                self.logger.error("Can't Load plugins %s" % pluginName)
                return False
        return True

    def _get_scene_info(self):
        """Get Maya Scene Information needed by the ui"""
        self.scene.getAnimationSettings()

    def _get_extra_attrs(self, root_node):
        """
        """
        # init result
        extraAttrs = []
        # get root_node and children
        ns = cmds.listRelatives(root_node, allDescendents=True, fullPath=True)
        ns.append(root_node)
        for n in ns:
            # get extra attr
            attrs = cmds.listAttr(n, userDefined=True)
            if attrs:
                for attr in attrs:
                    if attr not in extraAttrs:
                        extraAttrs.append(attr)
        return extraAttrs

    def export_animation_entity(self, entity_name=None, root_node=None, in_frame=None, out_frame=None, task_name=None, rename_shape_deformed=True, bakeJoint=True, bakeConstraint=False, force_dgDirty_by_frame=False, subprocess_mode="local", user=None):
        """
        """
        self.logger.info("export_animation_entity(entity_name={entity_name}, root_node={root_node}, in_frame={in_frame}, out_frame={out_frame}, task_name={task_name}, rename_shape_deformed={rename_shape_deformed}, bakeJoint={bakeJoint}, bakeConstraint={bakeConstraint}, force_dgDirty_by_frame={force_dgDirty_by_frame}, subprocess_mode={subprocess_mode}, user={user})".format(entity_name=entity_name, root_node=root_node, in_frame=in_frame, out_frame=out_frame, task_name=task_name, rename_shape_deformed=rename_shape_deformed, bakeJoint=bakeJoint, bakeConstraint=bakeConstraint, force_dgDirty_by_frame=force_dgDirty_by_frame, subprocess_mode=subprocess_mode, user=user))
        self.logger.info("====>> Maya Information : installedVersion={installedVersion}".format(installedVersion=cmds.about(installedVersion=True)))
        # notify end user
        if subprocess_mode == "local":
            text = "Asset: {entity_name} - {root_node}\nFrame: {in_frame} - {out_frame}\n".format(entity_name=entity_name, root_node=root_node, in_frame=in_frame, out_frame=out_frame)
            image = "{icons_dir}/modernuiicons/dark/appbar.timer.png".format(icons_dir=self.icons_dir)
            ppNotifier.notify(title="Start - Export Anim - {subprocess_mode}".format(subprocess_mode=subprocess_mode), text=text, image=image, time=10000)
        #  reformat float value
        in_frame = float(in_frame)
        out_frame = float(out_frame)
        # load Plugins
        self.logger.info("Load Plugins")
        self._load_plugins()
        # setup maya before export
        self._setup_maya_for_export()
        current_scene = cmds.file(query=True, sn=True)
        # init app from
        self.logger.info("Get Sgtk Instance from Current Scene : {current_scene}".format(current_scene=current_scene))
        tk = sgtk.sgtk_from_path(current_scene)
        ctx = tk.context_from_path(current_scene)
        self.logger.debug("Ctx found : {ctx}".format(ctx=ctx))
        self.logger.debug("\tCtx project : {ctx}".format(ctx=ctx.project))
        self.logger.debug("\tCtx entity : {ctx}".format(ctx=ctx.entity))
        self.logger.debug("\tCtx step : {ctx}".format(ctx=ctx.step))
        self.logger.debug("\tCtx task : {ctx}".format(ctx=ctx.task))
        self.logger.debug("\tCtx user : {ctx}".format(ctx=ctx.user))
        # force synchronize local cache before export. # ticket #836
        synced_folders = tk.synchronize_filesystem_structure(full_sync=False)
        self.logger.info("{synced_folders} Synced Folders".format(synced_folders=len(synced_folders)))
        ctx = tk.context_from_path(current_scene)
        # get scene infos
        self._get_scene_info()
        # force reload remapping
        self._force_execute_scriptNode()
        # create local directory
        scene_folder = os.path.basename(current_scene)
        scene_folder = scene_folder.split('.')[0]
        local_export_folder = "%s/%s" % (LOCAL_FOLDER, scene_folder)
        # Create the export directory
        if not os.path.exists(local_export_folder):
            self.logger.info("Create local directory: %s" % local_export_folder)
            try:
                os.makedirs(local_export_folder)
            except RuntimeError, e:
                self.logger.error("Can't create directory: %s" % local_export_folder)
                self.logger.error("Error: %s" % e)
        # get info from node
        self.logger.info("Get info from node='{node}')".format(node=root_node))
        ent = ppSceneManagement.Entity()
        ent.getEntityInfo(node=root_node)
        # we try to get the parent entity info, to protect again the case where the model provide from an other entity.
        # prod case hotspot. the serveuse get the model from womanC
        parent_of_root_node = None
        entParent = ppSceneManagement.Entity()
        if cmds.listRelatives(root_node, parent=True):
            parent_of_root_node = cmds.listRelatives(root_node, parent=True)[0]
            self.logger.info("Get Parent Entity Info of Node : '{n}'".format(n=parent_of_root_node))
            entParent.getEntityInfo(node=parent_of_root_node)
        # kill children we don't want to store it
        entParent.info["children"] = []
        # get extra attr on node
        extraAttrs = self._get_extra_attrs(root_node=root_node)
        if rename_shape_deformed:
            self.logger.info("Rename Shape Deformed Active")
            shape_filter = "*"
            if ent.info['providedBy'] == 'reference':
                # check if node is a reference and import if needed
                # self._import_reference_from_this_node(node=root_node)
                shape_filter = "%s:*" % ent.info['namespace']
                self.logger.info("Set shape_filter to : {shape_filter} based on namespace.".format(shape_filter=shape_filter))
                exp_rename_shape_deformed.rename_shape_deformed(shape_filter=shape_filter, logger=self.logger)
                # double rename in case the ShapeDeformed is not include into the namespace model ticket 1119
                if entParent.info['namespace']:
                    shape_filter = "%s:*" % entParent.info['namespace']
                    self.logger.debug("set shape_filter to : {shape_filter} based on parent namespace.".format(shape_filter=shape_filter))
                    exp_rename_shape_deformed.rename_shape_deformed(shape_filter=shape_filter, logger=self.logger)
            else:
                # rename shape deformed
                exp_rename_shape_deformed.rename_shape_deformed(shape_filter=shape_filter, logger=self.logger)
        # Export the ABC file
        abc_file_path = "%s/%s_%s.abc" % (local_export_folder, ctx.entity['name'], entity_name)
        min_frame = in_frame - self.handles
        max_frame = out_frame + self.handles
        # create script node force eval dgdirty per frame to protect again cycle check.
        if force_dgDirty_by_frame:
            ppSceneManagement.do_createScriptNodeForceDgDirtyByFrame()
        # set current frame to 1 for force eval first frame
        cmds.currentTime(1)
        # do bake joint before
        if bakeJoint:
            self._bake_joints(min_frame=min_frame, max_frame=max_frame)
        # do bake constraint before
        if bakeConstraint:
            self._bake_constraint(min_frame=min_frame, max_frame=max_frame)
        self.logger.info("Export Abc entity_name %s, root_node %s, in_frame %s, out_frame %s, handles %s, pre_roll %s, abcFile %s" % (entity_name, root_node, in_frame, out_frame, self.handles, self.pre_roll, abc_file_path))
        exportCmd = ['AbcExport -preRollStartFrame %s' % self.pre_roll]
        exportCmd.append('-j')
        exportCmd.append('"-fr %s %s ' % (min_frame, max_frame))
        # add extraAttr
        if extraAttrs:
            for attr in extraAttrs:
                exportCmd.append('-attr %s' % attr)
        exportCmd.append('-uvWrite')
        exportCmd.append('-wholeFrameGeo')
        exportCmd.append('-worldSpace')
        exportCmd.append('-stripNamespaces')
        exportCmd.append('-writeVisibility')
        # exportCmd.append('-eulerFilter')
        # add pre frame callback python
        cmd_pre_frame_python = 'import ppma.action.ppImpExpAnim.exp_entity_exporter;ppma.action.ppImpExpAnim.exp_entity_exporter.abc_per_frame_callback()'
        exportCmd.append('-pythonPerFrameCallback \\"%s\\"' % cmd_pre_frame_python)
        exportCmd.append('-root %s' % root_node)
        exportCmd.append('-file %s"' % abc_file_path)
        self.logger.info("Export Abc Command : %s" % ' '.join(exportCmd))
        export_result = mel.eval(' '.join(exportCmd))
        if not export_result and os.path.exists(abc_file_path):
            export_result = True
        # do publish
        if export_result:
            meta_data = {
                "handles": self.handles,
                "pre_roll": self.pre_roll,
                "strippedNamespace": ent.info['namespace'],
                "min_frame": min_frame,
                "max_frame": max_frame,
                "unit": self.scene.unit,
                "fps": self.scene.fps,
                "entityInfo": ent.info,
                "entityParentInfo": entParent.info,
                "abcType": "animated",
                "abcCreator": "maya",
                "abcExportCmd": ' '.join(exportCmd)
            }
            # build thumbnail path
            thumbnailPath = "%s/publishedFileType/pft_alembic.png" % self.icons_dir
            # get sg user
            if user:
                # get info from shotgun
                sgUser = tk.shotgun.find_one('HumanUser', [['name', 'is', user]], ['id', 'type'])
                if sgUser:
                    user = sgUser
            # build publish arg
            comment_scene = "abc / animated / exported from %s / created by maya." % ctx.entity['name']
            if subprocess_mode == "renderfarm":
                comment_scene += " / on renderfarm by %s." % platform.node()
            # sanity check for publish name
            publish_name = entity_name
            if '_' in publish_name:
                publish_split = publish_name.split('_')
                for i in range(1, len(publish_split)):
                    publish_split[i] = publish_split[i].title()
                publish_name = ''.join(publish_split)
            publishArgs = {
                'project': tk.project_path,
                'filePath': abc_file_path,
                'fileType': "alembic",
                'linkType': ctx.entity['type'],
                'linkName': ctx.entity['name'],
                'publishName': publish_name,
                'stepName': ctx.step['name'],
                'taskName': task_name,
                'comment': comment_scene,
                'dependencies': [],
                'sgMetaData': meta_data,
                'thumbnail': thumbnailPath,
                'user': user,
                'tags': ["auto-publish"]
            }
            # extra dependencies
            fileDependencies = [current_scene]
            # add model to file dependency
            if ent.info:
                if 'providedBy' in ent.info.keys():
                    if ent.info['providedBy'] == 'reference':
                        fileDependencies.append(ent.info['filename'])
            # add rig to file dependency
            if entParent.info:
                if 'providedBy' in entParent.info.keys():
                    if entParent.info['providedBy'] == 'reference':
                        fileDependencies.append(entParent.info['filename'])
            for filename in fileDependencies:
                #  get published id from reference
                #  preformat path for request
                tkFile = sgtk.sgtk_from_path(filename)
                ctxFile = tkFile.context_from_path(filename)
                # split by project name
                self.logger.info("Project Name: '%s'" % ctxFile.project['name'])
                pathRequest = filename.split(ctxFile.project['name'])[1]
                pathRequest = '%s%s' % (ctxFile.project['name'], pathRequest)
                filters = [['path_cache', 'is', pathRequest]]
                fields_return = ['id']
                published_file = tkFile.shotgun.find_one('PublishedFile', filters, fields_return)
                if published_file:
                    publishArgs['dependencies'].append(published_file['id'])
            self.logger.info("Do Publish: %s" % abc_file_path)
            self.logger.info("Publish Args: %s" % publishArgs)
            # do publish scene
            self.sgPublishedAbc = ppSgtkPublisher.publishFile(
                project=publishArgs['project'],
                filePath=publishArgs['filePath'],
                fileType=publishArgs['fileType'],
                linkType=publishArgs['linkType'],
                linkName=publishArgs['linkName'],
                publishName=publishArgs['publishName'],
                stepName=publishArgs['stepName'],
                taskName=publishArgs['taskName'],
                comment=publishArgs['comment'],
                dependencies=publishArgs['dependencies'],
                sgMetaData=publishArgs['sgMetaData'],
                thumbnail=publishArgs['thumbnail'],
                user=publishArgs['user'],
                tags=publishArgs['tags'])
            self.logger.info("Published Result %s" % (self.sgPublishedAbc))
            # delete tmp directory
            self.logger.info("Remove Tmp Abc File: %s" % abc_file_path)
            os.remove(abc_file_path)
            if self.sgPublishedAbc:
                # notify user
                self.logger.info("==================================")
                self.logger.info("Export Animation Publish: OK")
                self.logger.info("publishName %s, version %s" % (self.sgPublishedAbc['name'], self.sgPublishedAbc['version_number']))
                # notify end user
                if subprocess_mode == "local":
                    text = "Alembic Published:\n{abcName} - v{abcVersion}\n\nAsset: {entity_name} - {root_node}\nFrame: {in_frame} - {out_frame}".format(shot=publishArgs['linkName'], abcName=self.sgPublishedAbc['name'], abcVersion=self.sgPublishedAbc['version_number'], entity_name=entity_name, root_node=root_node, in_frame=in_frame, out_frame=out_frame)
                    image = "{icons_dir}/modernuiicons/dark/appbar.check.png".format(icons_dir=self.icons_dir)
                    ppNotifier.notify(title="Done - Export Anim - {shot}".format(shot=publishArgs['linkName']), text=text, image=image, time=10000)

                return self.sgPublishedAbc

            # notify end user
            else:
                if subprocess_mode == "local":
                    text = "Can't Publish Alembic file."
                    image = "{icons_dir}/modernuiicons/dark/appbar.timer.stop.png".format(icons_dir=self.icons_dir)
                    ppNotifier.notify(title="Problem - Export Anim - {subprocess_mode}".format(subprocess_mode=subprocess_mode), text=text, image=image, time=10000)

                return None

        else:
            self.logger.error("No Abc exist at %s" % abc_file_path)

            return None


def abc_per_frame_callback():
    """
    this func is evaluate each frame when exporting alembic cache.
    """
    # dgdirty -a
    print("Apply dgdirty -a | Frame {0}".format(cmds.currentTime(query=True)))
    cmds.dgdirty(allPlugs=True)
    return True
