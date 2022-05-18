# -*- coding: utf-8 -*-

"""
common classes and functions about entities like asset, assetInstance, shot, sequence, representation
"""

import maya.cmds as cmds
from tank_vendor import yaml
import os
import logging
import sys
import fnmatch
import shutil
import ppma.core.ppNode as ppNode
import sgtk
import time

import ppma.action.ppPublishCamera as ppPublishCamera

# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppma.core.ppSceneManagement')
logger.setLevel(logging.DEBUG)


class Tag(object):
    """ """

    def __init__(self):
        """
        """
        self.tagPrefix = "pp"
        self.tagSuffix = "tags"
        self.tagAttr = "%s_%s" % (self.tagPrefix, self.tagSuffix)

        self.initTagsInScene()

        self.defaultTag = {
                            'active_camera': {
                                        'autotag': True
                                        },
                            'camera': {
                                        'autotag': True
                                        },
                            'exportAnim': {
                                        'autotag': True
                                        }
                            }

    def initTagsInScene(self):
        """
        """
        self.tagsInScene = {
                    'byNode': {},
                    'byTag': {}
                    }

    def getDefaultTags(self):
        """
        """
        return self.defaultTag

    def getTags(self):
        """
        list tags in scene.
        """

        # get tag Attr name
        nodeList = cmds.ls("*.%s" % self.tagAttr, recursive=True)

        for nodeAttr in nodeList:

            node = nodeAttr.split('.')[0]

            # get value
            values = cmds.getAttr(nodeAttr)
            tags = []
            if values:
                # split value
                tags = values.split(',')

            # store byNode result
            self.tagsInScene['byNode'][node] = tags

            # store byTag
            for tag in tags:

                if tag in self.tagsInScene['byTag'].keys():
                    self.tagsInScene['byTag'][tag].append(node)
                else:
                    self.tagsInScene['byTag'][tag] = [node]

        return self.tagsInScene


    def createTagAttr(self, nodeList=[]):
        """
        this function add an attribute to the node.
        :param nodeList: (list) node list
        """
        result = {}
        for node in nodeList:

            # check if attr already exist
            if not cmds.objExists('%s.%s' % (node,self.tagAttr)):
                # create attr
                resAddAttr  = cmds.addAttr(node, ln=self.tagAttr, dt="string")
                result[node] = resAddAttr
            else:
                result[node] = resAddAttr

        return result

    def getTag(self, node):
        """
        return the tag associated to the node.
        :param node: (str) node name
        """
        if cmds.objExists('%s.%s' % (node, self.tagAttr)):
            values = cmds.getAttr('%s.%s' % (node, self.tagAttr))
            if values:
                return values.split(',')
        return []
    def isTaggedBy(self, tagName, node):
        """ """
        if self.isTagged(node=node):

            # get atg
            tags = self.getTag(node=node)
            if tagName in tags:
                return True
            else:
                return False
        else:
            return False

    def isTagged(self, node=None):
        """
        check if the node is tagged.
        """
        if cmds.objExists('%s.%s' % (node, self.tagAttr)):
            return True
        else:
            return False

    def addTag(self, nodeList=[], tagList=[]):
        """
        add a tag to the node list
        :param nodeList: (list)
        :param tagList: (list)
        """
        for node in nodeList:
            # check if tagged
            if not self.isTagged(node=node):
                # create tag attr
                self.createTagAttr(nodeList=[node])

            # get tags list
            tags = self.getTag(node=node)

            for tag in tagList:
                if not tag in tags:
                    # add tag
                    tags.append(tag)
            # add tags to node
            cmds.setAttr('%s.%s' % (node, self.tagAttr), ','.join(tags), type='string')

        return True

    def removeTag(self, nodeList=[], tagList=[]):
        """
        remove a tag to the node list
        :param nodeList: (list)
        :param tagList: (list)
        """
        for node in nodeList:
            # check if tagged
            if self.isTagged(node=node):
                tags = self.getTag(node=node)

                for tag in tagList:
                    if tag in tags:
                        # remove tag
                        tags.remove(tag)

                # add tags to node
                cmds.setAttr('%s.%s' % (node, self.tagAttr), ','.join(tags), type='string')

    def getAutoTagAvailable(self):
        """
        retrieve the available tag for autoTag
        """

        autotagList = []
        for item in self.defaultTag.keys():
            if self.defaultTag[item]['autotag']:
                autotagList.append(item)

        return autotagList

    def autoTag(self, which='exportAnim'):
        """
        autoTag node
        """

        # check if autotag supported for this tag
        if which in self.getAutoTagAvailable():

            # do autotag
            if which == 'exportAnim':

                # get all nodes wich follow the pattern *model:root
                nodes = cmds.ls('*model:root', recursive=True)

                if nodes:
                    # add tag exportAnim
                    self.addTag(nodeList=nodes, tagList=['exportAnim'])

        #

    def getNodeByTag(self, tag):
        """
        retriev node linked to tag.
        :param tag: tag name, somthing like exportAnim.
        """
        self.initTagsInScene()
        self.getTags()

        if not tag in self.tagsInScene['byTag'].keys():
            logger.error("No node tagged: exportAnim, please add this tag to a node and retry.")
            return []
        else:
            return self.tagsInScene['byTag'][tag]


    def exportTagsAsYaml(self):
        """
        this func export tags as a yaml string, it could be usefull for copy paste tags from one scene to another.
        """

        self.getTags()

        ymlData = yaml.dump(self.tagsInScene, default_flow_style=True)
        return ymlData

    def importTagsFromYaml(self, yamlData):
        """
        """
        pass


# multiproc

def worker(procnum, return_dict):

    print("%s represent" % procnum)
    return_dict[procnum] = procnum




class Entity(object):
    """docstring for Pipeline"""
    def __init__(self, tk=None):

        self.node = None
        self.reference = ppNode.Reference()

        # init shotgun var
        self.sgtk = None
        self.ctx = None

        self.sgtkTemplate = None
        # tag
        self.tag = Tag()

        self.currentTk = None
        self.currentCtx = None

        # get custom attr class
        self.cAttr = ppNode.CustomAttr()
        # get publish camera class
        self.pCam = ppPublishCamera.Publish()

        # recap info
        self.info = {
                        "project":None,
                        "projectPath":None,
                        "name":None,
                        "entityName":None,
                        "entityType":None,
                        "entitySubType":None,
                        "representation":None,
                        "step":None,
                        "rootNode":None,
                        "namespace":None,
                        "version":None,
                        "isLatest":None,
                        "tags":None,
                        "filename":None,
                        "publishName":None,
                        "referenceNode":None,
                        "providedBy":None, # reference, maya, gpucache
                        "override":{},
                        "children":[]
        }

        self.ovrAttrList = ['name', 'entityName', 'entityType', 'entitySubType']

        self.getCurrentCtx()

    def getCurrentCtx(self):
        """
        """
        # Get Current Scene
        sn = cmds.file(q=True, sn=True)
        if sn:
            self.currentTk = sgtk.sgtk_from_path(sn)
            self.currentCtx = self.currentTk.context_from_path(sn)

    def getMayaOverrides(self, node=None):
        """
        in special case we want to be able to override entityName or something like this. so we check if an attr pp_ovr_entityName exist
        """

        for attr in self.ovrAttrList:
            if cmds.objExists('%s.%s_%s_%s' % (node, self.cAttr.prefix, self.cAttr.ovrPrefix, attr)):
                self.info['override'][attr] = cmds.getAttr('%s.%s_%s_%s' % (node, self.cAttr.prefix, self.cAttr.ovrPrefix, attr))
            # else:
            #   logger.debug("attribute not exist %s.%s_%s_%s" % (node, self.cAttr.prefix, self.cAttr.ovrPrefix, attr))

    def getMayaNodeInfo(self, node=None):
        """
        get info from maya node
        """
        logger.debug("getMayaNodeInfo(node={node})".format(node=node))

        # try to retrieve namespace
        if ':' in node:
            if len(node.split(':')) > 2:
                latestNodeName = node.split(':')[len(node.split(':'))-1]
                self.info['namespace'] = ":%s:" % node[:-len(latestNodeName)]
        else:
            self.info['namespace'] = ":"

        # get name
        self.info['name'] = node
        self.info['step'] = 'current'
        self.info['entityName'] = 'current'
        self.info['entitySubType'] = 'current'
        if self.currentCtx:
            self.info['entityType'] = self.currentCtx.entity['type']
        else:
            self.info['entityType'] = 'current'

        # providedBY
        self.info["representation"] = "maya"
        self.info["providedBy"] = "maya"

        # if ppCam it's a camera
        if fnmatch.fnmatch(node, "*%s*" % self.pCam.defaultPublishName['camera']):
            self.info['entitySubType'] = "Camera"

    def getEntities(self, multiproc=False):
        """
        retrieve entities in the scene.
        """

        # First, get potentially available nodes list.
        nodesRaw = []
        # # get entites by name *root
        # nRaw = cmds.ls("*root", recursive=True)
        # if nRaw:
        #   nodesRaw.extend(nRaw)

        # get cameras
        #nRaw = cmds.ls("*%s" % (self.pCam.defaultPublishName['camera']), recursive=True)
        cam = ppNode.Camera()
        nRaw = sorted(cam.getCameras(filter='noFpst').keys())
        if nRaw:
            nodesRaw.extend(nRaw)

        # # get entities by tags
        # tag = Tag()
        # tag.getTags()

        # for node in sorted(tag.tagsInScene['byNode'].keys()):
        #   # check if node already in nodesRaw
        #   if not node in nodesRaw:
        #       nodesRaw.append(node)


        refs = cmds.ls(type='reference')
        for r in refs:
            fi = None
            try:
                fi = cmds.referenceQuery(r, filename=True, unresolvedName=False, withoutCopyNumber=True)
            except:
                pass
            if fi:
                pr = cmds.referenceQuery(r, referenceNode=True, topReference=True)
                if not pr in nodesRaw:
                    nodesRaw.append(pr)


        # check nodesRaw and build result into nodes
        nodes = []
        if not multiproc:
            for node in nodesRaw:

                # init ent
                e = Entity()
                res = e.getEntityInfo(node=node)
                if res:
                    nodes.append(e)
        else:
            logger.info("MultiProc")

            from multiprocessing import Process, Manager

            manager = Manager()
            return_dict = manager.dict()

            jobs = []

            for i in range(5):
                p = Process(target=worker, args=(i, return_dict))
                jobs.append(p)
                p.start()

            for proc in jobs:
                proc.join()

            print(return_dict)

        return nodes

    def getEntityInfo(self, node):
        """
        retrieve information about pipeline
        :param node: (str) node name
        """

        if not cmds.objExists(node):
            logger.error("Node : {n} not exist".format(n=node))
            return False

        # check if it's a transform node or a reference node
        if cmds.nodeType(node) == 'transform':
            self.info["rootNode"] = node

        if cmds.nodeType(node) == 'reference':
            self.info["referenceNode"] = node

            # get nodes
            ns = cmds.referenceQuery(node, nodes=True)
            if ns:
                if len(ns) == 1:
                    if cmds.nodeType(ns[0]) == 'audio':
                        self.info["rootNode"] = ns[0]
                else:
                    for n in ns:
                        # we assume root node is the top node
                        if fnmatch.fnmatch(n, "*root"):
                            self.info["rootNode"] = n

        if not self.info["rootNode"]:
            return False
        else:
            logger.debug("Get Entity Info: %s" % self.info["rootNode"])

            #  check if it's a reference
            if cmds.referenceQuery(self.info["rootNode"], isNodeReferenced=True):
                self.getReferenceInfo(node=self.info["rootNode"])

            # get Tags
            self.getTags(node=self.info["rootNode"])

            # get overrides / we could specify
            self.getMayaOverrides(node=self.info["rootNode"])

            if not self.info['providedBy'] == 'reference':
                # no reference so we try to to retrieve a lot of infos
                self.getMayaNodeInfo(node=self.info["rootNode"])

            # get sgtk info
            if self.info['filename']:
                #self.getSgtkInfo(filename=self.info['filename'])
                pass

            # check if it's a camera
            if self.info["rootNode"]:
                camNode = False
                if cmds.nodeType(self.info["rootNode"]) == "camera":
                    camNode = True

                if cmds.nodeType(self.info["rootNode"]) == "transform":
                    children = cmds.listRelatives(self.info["rootNode"], shapes=True, type="camera", children=True, fullPath=True)
                    if children:
                        if cmds.nodeType(children[0]) == "camera":
                            camNode = True

                if camNode:
                    self.info['entitySubType'] = "Camera"

        return self.info

    def getReferenceInfo(self, node=None):
        """
        """
        logger.debug("getReferenceInfo(self, node={node})".format(node=node))

        self.reference.getReferenceNode(node=node)

        if self.reference.refNode:
            self.reference.getFilename(refNode=self.reference.refNode)

            self.reference.getIsLoadedStatus(refNode=self.reference.refNode)

            self.reference.getNamespace(refNode=self.reference.refNode)

            self.reference.getContext(filename=self.reference.filename)

            # get children
            subRefNodes = self.reference.getSubReferenceNode(refNode=self.reference.refNode)
            if subRefNodes:
                for subRefNode in subRefNodes:
                    e = Entity()
                    e.getEntityInfo(node=subRefNode)
                    if e.reference.isLoaded:
                        self.info["children"].append(e)

        # check if we get a filename
        if self.reference.filename:
            self.info["filename"] = self.reference.filename
            self.info["namespace"] = self.reference.namespace

            # reformat name
            if self.reference.namespace:
                self.info["name"] = self.reference.namespace.replace(':', '')
                self.info["name"] = self.info["name"].replace('_', '')
            else:
                self.info["name"] = node

            self.info["referenceNode"] = self.reference.refNode
            self.info["representation"] = "maya"
            self.info["providedBy"] = "reference"

        if self.reference.ctx:

            # get context
            self.info["project"]= self.reference.ctx.project['name']
            self.info["projectPath"] = self.reference.tk.roots['primary']

            # special case alembic published file
            if self.info["filename"].split('.')[len(self.info["filename"].split('.'))-1] == 'abc':
                # we need to get the real entity name. we retriev this information from shotgun published file in the metadata field.
                # we reconstruct the path for the request
                pathRequest = self.info["filename"].split(self.reference.ctx.project['name'])[1]
                pathRequest = '%s%s' % (self.reference.ctx.project['name'], pathRequest)
                filters = [['path_cache', 'is', pathRequest]]
                fieldsReturn = ['id', 'sg_pp_meta_data']
                sgPublishFile = self.reference.tk.shotgun.find_one('PublishedFile', filters, fieldsReturn)

                logger.debug(sgPublishFile)

                if sgPublishFile:
                    # now we must have a published file and the metadata.
                    # get yaml data from sg_pp_meta_data
                    metadata = yaml.load(sgPublishFile['sg_pp_meta_data'])
                    if 'entityInfo' in metadata.keys():
                        if 'entityName' in metadata['entityInfo'].keys():
                            self.info['entityName'] = metadata['entityInfo']['entityName']
                        if 'entityType' in metadata['entityInfo'].keys():
                            self.info['entityType'] = metadata['entityInfo']['entityType']
                        if 'entitySubType' in metadata['entityInfo'].keys():
                            self.info['entitySubType'] = metadata['entityInfo']['entitySubType']
                        if 'step' in metadata['entityInfo'].keys():
                            self.info['step'] = metadata['entityInfo']['step']

                        logger.debug(self.info)

            else:
                self.info["entityName"] = self.reference.ctx.entity['name']
                self.info["entityType"] = self.reference.ctx.entity['type']

            if self.reference.ctx.step:
                self.info["step"] = self.reference.ctx.step['name']

            # get template path
            if self.reference.fields:
                if 'version' in self.reference.fields.keys():
                    self.info['version'] = self.reference.fields['version']
                if 'name' in self.reference.fields.keys():
                    self.info['publishName'] = self.reference.fields['name']
                if 'sg_asset_type' in  self.reference.fields.keys():
                    self.info['entitySubType'] = self.reference.fields['sg_asset_type']

            # special case camera
            if not self.info["step"] and (self.info['publishName'] == "camtrack" or self.info['publishName'] == "cambaked"):
                self.info["step"] = "rig"
                self.info['entitySubType'] = "Camera"

    def getTags(self, node=None):
        """
        """
        tags = self.tag.getTag(node=node)
        self.info['tags'] = tags

    #TODO check if it's a really unused method and remove it
    def getSgtkInfo(self, filename=None, extra=False):
        """
        obsolete method
        """
        # sgtk info from filename
        if self.info["filename"]:

            #  get sgtk info
            self.sgtk = sgtk.sgtk_from_path(self.info["filename"])

            if self.sgtk:
                self.ctx = self.sgtk.context_from_path(self.info["filename"])

            #
            logger.debug("node: %s / filename: %s" % (self.node, filename))

            # get context
            if self.ctx:
                self.info["project"]= self.ctx.project['name']
                self.info["projectPath"] = self.sgtk.roots['primary']
                self.info["entityName"] = self.ctx.entity['name']
                self.info["entityType"] = self.ctx.entity['type']

                if self.ctx.step:
                    self.info["step"] = self.ctx.step['name']

            # get template path
            if self.sgtk:
                template_path = self.sgtk.template_from_path(self.info["filename"])
                templateResult = template_path.get_fields(self.info["filename"])

                if 'version' in templateResult.keys():
                    self.info['version'] = templateResult['version']
                if 'name' in templateResult.keys():
                    self.info['publishName'] = templateResult['name']
                if 'sg_asset_type' in  templateResult.keys():
                    self.info['entitySubType'] = templateResult['sg_asset_type']

            # special case camera
            if not self.info["step"] and (self.info['publishName'] == "camtrack" or self.info['publishName'] == "cambaked"):
                self.info["step"] = "rig"
                self.info['entitySubType'] = "Camera"

            return True

        else:
            # can't decode
            logger.error("No filename in self.info['filename']. Please Fill it")
            return False

    def get_preferred_scene(self):
        """
        return the a dict which contain a mapping between shot step and asset step for auto create reference during import animation.
        """
        preferredGetSettings = {
                                    'cfx': {'StepName': 'rigCfx', 'PublishName': 'basic'},
                                    'sfx': {'StepName': 'surface', 'PublishName': 'basic'},
                                    'light': {'StepName': 'surface', 'PublishName': 'basic'}

        }
        return preferredGetSettings

    def createReference(self, namespace, filename):
        """
        """
        r = ppNode.Reference()
        return r.do_createReference(namespace=namespace, filename=filename)

    def createEntity(self, projectPath=None, entityName=None, entityType=None, step=None, publishName=None, instanceNumber=None, revision=None, mode='reference'):
        """
        """
        logger.info("Create Entity : projectPath={projectPath}, entityName={entityName}, entityType={entityType}, step={step}, publishName={publishName}, instanceNumber={instanceNumber}, revision={revision}, mode={mode}".format(projectPath=projectPath, entityName=entityName, entityType=entityType, step=step, publishName=publishName, instanceNumber=instanceNumber, revision=revision, mode=mode))
        #  get sgtk
        engine = sgtk.platform.current_engine()
        currentStep = engine.context.step['name']

        # get project
        projectName = os.path.basename(projectPath)

        #  get prefered scene
        preferredGetSettings = self.get_preferred_scene()

        # sgPublishFile
        sgPublishFile = None

        # Case entityType: Asset
        if entityType == 'Asset':

            # get published files available
            filters = []
            # set entityName
            filters.append(['entity.Asset.code', 'is', entityName])
            # set project
            filters.append(['project.Project.name', 'is', projectName])
            # set published file Maya Scene
            filters.append(['published_file_type.PublishedFileType.id', 'is', 3])
            # only active file
            filters.append(['sg_status_list', 'is_not', 'omt'])

            # get step
            if not step:
                # auto determine step from current engine.
                if currentStep in preferredGetSettings.keys():
                    step = preferredGetSettings[currentStep]['StepName']

            # only active file
            if step:
                # get step from Shotgun
                sgStep = engine.shotgun.find_one('Step', [['code', 'is', step], ['entity_type', 'is', entityType]], [])
                filters.append(['task.Task.step', 'is', sgStep])

            # get publishName
            if not publishName:
                # auto determine publishName from current engine.
                logger.info("retrieve publishName from preferredGetSettings")
                if currentStep in preferredGetSettings.keys():
                    publishName = preferredGetSettings[currentStep]['PublishName']

            if publishName:
                filters.append(['name', 'is', publishName])

            fieldsReturn = ['id', 'name', 'task', 'path', 'project']
            order = [{'field_name': 'id', 'direction': 'desc'}]

            if projectName and entityName and step and publishName:
                sgPublishFile = engine.shotgun.find_one('PublishedFile', filters, fieldsReturn, order)

            else:
                logger.error("please fill all arg - projectName:%s entityName:%s step:%s publishName:%s" % (projectName, entityName, step, publishName))

            #
            if sgPublishFile:
                logger.info(sgPublishFile)

                # build namespace
                if not instanceNumber:
                    instanceNumber = 1

                # get path
                system = sys.platform
                snPath = sgPublishFile['path']['local_path_windows']
                if system == "darwin":
                    snPath = sgPublishFile['path']['local_path_mac']
                if system == "linux2":
                    snPath = sgPublishFile['path']['local_path_linux']

                # create reference
                namespace = "%s%03d" % (entityName, instanceNumber)
                refNode = self.createReference(namespace=namespace, filename=snPath)

                return refNode

            else:
                logger.error("no published file found for this filter: %s" % filters)
                return False

        #

    def do_AddMayaAttrOverride(self, node):
        """
        """
        ovr = True
        for attr in self.ovrAttrList:
            self.cAttr.createAttr(node=node, attr=attr, ovr=ovr)

        # pre-fill maya attributes
        # self.ovrAttrList = ['name', 'entityName', 'entityType', 'entitySubType']
        # set name
        short_node = node.replace('grp_', '')
        short_node = short_node.replace('_grp', '')
        default_prefill = {
                            "name": short_node,
                            "entityName": short_node,
                            "entityType": "Asset",
                            "entitySubType": "Prop"
        }
        for attr in self.ovrAttrList:

            if attr in default_prefill:

                value = default_prefill[attr]

                # get final attr on node
                final_attr = self.cAttr.get_attribute_name(attr=attr, ovr=ovr)

                # set attr
                cmds.setAttr("{n}.{a}".format(n=node, a=final_attr), value, type="string")


class Scene_Structure(object):
    """docstring for rootStructure"""
    def __init__(self):

        # define scene structure for each step
        self.scene_structure = {
                                # default step
                                'default': {
                                                'group': [
                                                            'root',
                                                            'root|grp_model',
                                                            'root|grp_wip'
                                                ]
                                },

                                # model step
                                'model': {
                                                'group': [
                                                            'root',
                                                            'root|grp_model',
                                                            'root|grp_blendShape',
                                                            'root|grp_wip'
                                                ],
                                                'layer': [
                                                            {'name': 'model', 'color': None},
                                                            {'name': 'high', 'color': 31},
                                                ]
                                },
                                # rig step
                                'rig': {
                                                'group': [
                                                            'root',
                                                            'root|grp_reference_model',
                                                            'root|grp_rig',
                                                            'root|grp_rig|grp_ctrl',
                                                            'root|grp_wip'
                                                ],
                                                'layer': [
                                                            {'name': 'ctrl', 'color': None},
                                                ]
                                },
                                # shading step
                                'shading': {
                                                'group': [
                                                            'root',
                                                            'root|grp_reference_model',
                                                            'root|grp_shading',
                                                            'root|grp_wip'
                                                ]
                                },
                                # turntable
                                'turntable': {
                                                'group': [
                                                            'root',
                                                            'root|grp_size_reference',
                                                            'root|grp_reference_asset',
                                                            'root|grp_turntable_camera',
                                                            'root|grp_cyclo'
                                                ]
                                },
                                # previz
                                'previz': {
                                                'group': [
                                                            'root',
                                                            'root|grp_cameras',
                                                            'root|grp_lights',
                                                            'root|grp_wip',
                                                ]
                                },
                                # lighting
                                'lighting': {
                                                'group': [
                                                            'root',
                                                            'root|grp_cameras',
                                                            'root|grp_wip',
                                                ]
                                },
                            }

    def get_structure(self, step="default"):
        """ retrieve the scene sctructure defined"""
        logger.info("get_structure : {step}".format(step=step))
        if not step in self.scene_structure.keys():
            return self.scene_structure['default']

        else:
            return self.scene_structure[step]

    def create_structure(self, step="default"):
        """ retrieve the scene sctructure defined"""

        nodes_path = self.get_structure(step=step)
        for node_path in nodes_path:
            ppNode.create_group(node_path)


class Remap(object):
    """docstring for Remap"""
    def __init__(self):
        """ """
        pass

    def do_remap(self, search, replace, fileTexture=True, copyFileTexture=False, reference=True):
        """ """

        if fileTexture:
            # get files
            fs = ppNode.File()
            fs.get_nodes()

            for n in sorted(fs.nodes.keys()):
                for attr in sorted(fs.nodes[n].keys()):

                    vCorrected = fs.nodes[n][attr].replace(search, replace)
                    logger.info("orig path: {path}".format(path=fs.nodes[n][attr]))
                    logger.info(">new path: {path}".format(path=vCorrected))

                    if copyFileTexture and not os.path.exists(vCorrected):
                        if not os.path.exists(os.path.dirname(vCorrected)):
                            logger.info("\t create dir: {rep}".format(rep=os.path.dirname(vCorrected)))
                            os.makedirs(os.path.dirname(vCorrected))

                        if os.path.exists(fs.nodes[n][attr]):
                            logger.info("\t copy file: {path}".format(path=vCorrected))
                            shutil.copy(fs.nodes[n][attr], vCorrected)

                    fs.do_setAttr(node=n, attr=attr, value=vCorrected)

        if reference:
            #
            pass

def autoTag(tagName):
    """
    """
    tg = Tag()
    tg.autoTag(which=tagName)

def add_tag(tag_name, node_list=[]):
    """
    add tag on node list
    :param tagName:
    :param nodeList:
    """
    tag = Tag()
    res = tag.addTag(nodeList=node_list, tagList=[tag_name])
    return res

def addTag(tagName, nodeList=[]):
    """
    deprecated use add_tag
    """
    return add_tag(tag_name=tagName, node_list=nodeList)

def getTag(node):
    """
    get tag on provided node
    :param node: node name
    :type node: str
    :returns: a tag list
    :rtype: list
    """
    tag = Tag()
    res = tag.getTag(node=node)
    return res

def removeTag(tagName, nodeList=[]):
    """
    add tag on node list
    :param tagName:
    :param nodeList:
    """
    tag = Tag()
    res = tag.removeTag(nodeList=nodeList, tagList=[tagName])
    return res

def objectIsTaggedBy(tagName, node=None):
    """
    add tag on node list
    :param tagName:
    :param nodeList:
    """
    tag = Tag()
    res = tag.isTaggedBy(tagName=tagName, node=node)
    return res


def getObjectTaggedWith(tagName):
    """
    retireve tagged object by the tag
    """
    tag = Tag()
    res = tag.getNodeByTag(tag=tagName)

    return res


def get_nodes_available_for_export(method="name"):
    """
    :param method: name or tag
    """

    # init result
    nodes = []

    # first method name
    # get references based on name model
    looking_for_name = "model"
    r = ppNode.Reference()
    rs = r.getReferenceNodeInScene(get_template=True, onlyTopNode=False)
    
    # add ref to item
    for item in rs:
        # escape non model reference
        if looking_for_name in rs[item].filename and rs[item].isLoaded and "Step" in rs[item].fields.keys():
            node = "{n}:root".format(n=rs[item].namespace)
            # check tag do_not_export is present
            if "do_not_export" not in getTag(node=node):
                nodes.append(node)
            else:
                logger.info("Node {0} skipped because tag 'do_not_export' detected.".format(node))

    # second method tag exportAnim
    looking_for_tag = "exportAnim"
    # get node tagged for export
    tag = Tag()
    tag.getTags()

    tmp_nodes = tag.tagsInScene['byTag'].get(looking_for_tag)

    if tmp_nodes:
        for tmp_node in tmp_nodes:
            # tag method return node whithout colon as first character, we add it if necessary
            if ":" not in tmp_node[0]:
                # add it
                tmp_node = ":%s" % tmp_node

            # check if node not already in list
            if tmp_node not in nodes:
                nodes.append(tmp_node)

    return sorted(nodes)


def do_AddMayaAttrOverrideSelection():
    """
    for each selected object add an override attr on node
    """
    sel = cmds.ls(sl=True)
    for n in sel:
        # add override
        do_AddMayaAttrOverride(node=n)

    # add tag export anim
    addTag(tagName="exportAnim", nodeList=sel)


def do_AddMayaAttrOverride(node):
    """
    add override attr on node
    """
    e = Entity()
    e.do_AddMayaAttrOverride(node=node)


def do_forceDgDirtyByFrame():
    """
    """
    logger.info("dgdirty all")
    cmds.dgdirty(allPlugs=True)


def do_createScriptNodeForceDgDirtyByFrame():
    """
    current = cmds.currentTime(query=True)
    logger.info("previousFrame")
    """
    nodeName = 'forceDgDirtyByFrame'
    cAttr = ppNode.CustomAttr()
    finalName = "%s_%s" % (cAttr.prefix, nodeName)

    if not cmds.objExists(finalName):
        logger.info("create scriptnode: %s" % finalName)
        finalName = cmds.createNode('script', name=finalName)

    if cmds.objExists(finalName):
        # create scriptNode force eval
        syntax = 'import ppma.core.ppSceneManagement as ppSceneManagement;ppSceneManagement.do_forceDgDirtyByFrame()'
        logger.error("edit scriptnode: %s / syntax: %s" % (finalName, syntax))
        res = cmds.scriptNode(finalName, edit=True, scriptType=7, beforeScript=syntax, sourceType="python")

        return finalName

    else:
        logger.error("can't edit scriptnode: %s" % finalName)
        return None


def getEntities(multiproc=False):
    """
    get entitites in the scene
    """
    startTime = time.clock()

    e = Entity()
    res = e.getEntities(multiproc=multiproc)

    stopTime = time.clock()
    logger.info("get entities time elapsed: %s" % (stopTime - startTime))
    return res


def _retrieve_workspace_definition(directory):
    """
    """
    w = "{d}/workspace.mel".format(d=directory)
    if os.path.exists(w):
        return directory
    else:
        new_d = os.path.dirname(directory)
        if new_d == directory:
            return None
        else:
            return _retrieve_workspace_definition(directory=new_d)


def get_absolute_path(node, path):
    """
    """
    # if node is come from a refernece
    if cmds.referenceQuery(node, isNodeReferenced=True):
        # retrieve workspace.mel
        scene_path = cmds.referenceQuery(node, filename=True, unresolvedName=False, withoutCopyNumber=True)
        workspace_path = _retrieve_workspace_definition(os.path.dirname(scene_path))
        if not workspace_path:
            return
        absolute_path = "{w}/{path}".format(w=workspace_path, path=path)
        return absolute_path
    else:
        # else try to find path via workspace
        for w in cmds.workspace(listFullWorkspaces=True):
            absolute_path = "{w}/{path}".format(w=w, path=path)
            if os.path.exists(absolute_path):
                return absolute_path
    return


def get_dependencies():
    """
    """
    # init result
    dependencies = {
        "reference": {"full": [], "first": []},
        "file_texture": {"full": [], "first": []},
        "gpu_cache": {"full": [], "first": []},
        "mxs": {"full": [], "first": []},
        "mxm": {"full": [], "first": []},
        "open_vdb": {"full": [], "first": []},
    }
    # ---
    # Reference
    ref_nodes = cmds.ls(references=True)
    for ref_node in ref_nodes:
        if not fnmatch.fnmatch(ref_node, "*sharedReferenceNode*"):
            # get the path:
            ref_path = cmds.referenceQuery(ref_node, filename=True, unresolvedName=False, withoutCopyNumber=True)
            # make it platform dependent
            ref_path = ref_path.replace("/", os.path.sep)
            if ref_path:
                if ref_path not in dependencies["reference"]["full"]:
                    dependencies["reference"]["full"].append(ref_path)
                if ":" not in ref_node:
                    if ref_path not in dependencies["reference"]["first"]:
                        dependencies["reference"]["first"].append(ref_path)
    # ---
    # Gpu Cache
    for file_node in cmds.ls(long=True, type="gpuCache"):
        path = cmds.getAttr("%s.cacheFileName" % file_node).replace("/", os.path.sep)
        if path:
            if path[0] != "/":
                path = get_absolute_path(file_node, path)
            if path not in dependencies["gpu_cache"]["full"]:
                dependencies["gpu_cache"]["full"].append(path)
            if ":" not in file_node:
                if path not in dependencies["gpu_cache"]["first"]:
                    dependencies["gpu_cache"]["first"].append(path)
    # ---
    # File Texture
    for file_node in cmds.ls(long=True, type="file"):
        path = cmds.getAttr("%s.fileTextureName" % file_node).replace("/", os.path.sep)
        if path:
            if path[0] != "/":
                path = get_absolute_path(file_node, path)
            if path not in dependencies["file_texture"]["full"]:
                dependencies["file_texture"]["full"].append(path)
            if ":" not in file_node:
                if path not in dependencies["file_texture"]["first"]:
                    dependencies["file_texture"]["first"].append(path)
    # ---
    # Mxs
    for file_node in cmds.ls(long=True, type="maxwellReferencedMXS"):
        path = cmds.getAttr("%s.file" % file_node).replace("/", os.path.sep)
        if path:
            if path[0] != "/":
                path = get_absolute_path(file_node, path)
            if path not in dependencies["mxs"]["full"]:
                dependencies["mxs"]["full"].append(path)
            if ":" not in file_node:
                if path not in dependencies["gpu_cache"]["first"]:
                    dependencies["mxs"]["first"].append(path)

    # ---
    # Mxm
    for file_node in cmds.ls(long=True, type="maxwellRefMaterial"):
        path = cmds.getAttr("%s.mxmFile" % file_node).replace("/", os.path.sep)
        if path:
            if path[0] != "/":
                path = get_absolute_path(file_node, path)
            if path not in dependencies["mxm"]["full"]:
                dependencies["mxm"]["full"].append(path)
            if ":" not in file_node:
                if path not in dependencies["mxm"]["first"]:
                    dependencies["mxm"]["first"].append(path)

    return dependencies


def scanScene():
    """
    Scan Scene for retrieve dependency path.
    """
    currentSn = cmds.file(query=True, sn=True)
    tk = None
    try:
        tk = sgtk.sgtk_from_path(currentSn)
    except:
        return []
    dependency_paths = []
    ref_paths = get_dependencies().get("reference").get("first")
    for ref_path in ref_paths:
        # see if there is a template that is valid for this path:
        for template in tk.templates.values():
            if template.validate(ref_path):
                dependency_paths.append(ref_path)
                break

    return dependency_paths


def reloadPPReferenceNode():
    """ this func reload all pp_referenceNode in the scene."""

    ppNodes = cmds.ls("pp_referenceNode*")

    for n in ppNodes:

        logger.info("Reload pp_referenceNode: {ppNode}".format(ppNode=n))
        cmds.scriptNode(n, executeBefore=True)


def get_scene_structure(step="default"):
    """

    """
    sn = Scene_Structure()
    sn.get_structure(step=step)


def create_scene_structure(step="default"):
    """

    """
    sn = Scene_Structure()
    sn.create_structure(step=step)
