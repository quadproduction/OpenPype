# -*- coding: utf-8 -*-

"""
common classes and functions about node
"""

import maya.cmds as cmds
import maya.mel as mel
import fnmatch, logging, os, re
from tank_vendor import yaml
import sgtk

# loggger
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('core.ppNode')
logger.setLevel(logging.INFO)

class Node(object):
    """docstring for Node"""
    def __init__(self):

        self.nodes =  {}
        self.nodeType = None
        self.settings = {
            "file": {
                "nodeType": "file",
                "getAttr": [
                    "fileTextureName"
                ]
            }
        }

    def do_setNodeType(self, nodeType):
        """ """
        if not nodeType in self.settings.keys():
            return False

        self.nodeType = nodeType
        return True

    def get_nodeInfo(self, node):
        """ """
        r = {}

        for attr in self.settings[self.nodeType]["getAttr"]:
            r[attr] = cmds.getAttr("{node}.{attr}".format(node=node, attr=attr))

        return r

    def do_setAttr(self, node, attr, value):
        """ """
        # get attribute type
        attrType = cmds.getAttr("{node}.{attr}".format(node=node, attr=attr), type=True)

        if attrType == "string":
            cmds.setAttr("{node}.{attr}".format(node=node, attr=attr), value, type="string")
        else:
            logger.warning("attribute type unsupported. {attrType}".format(attrType=attrType))


    def get_nodes(self):
        """ retrieve nodes """

        self.nodes = {}
        r = cmds.ls(type=self.nodeType)

        for n in r:

            self.nodes[n] = self.get_nodeInfo(node=n)

        return self.nodes


class VRayMesh(Node):
    """docstring for ClassName"""
    def __init__(self):
        super(VRayMesh, self).__init__()

        self.nodeType = "VRayMesh"
        self.nodes = {}

        self.node_name = None
        self.filename = None
        self.geometry_representation = None  # 0 Place Holder, 1 Boudning Box, 2 Preview, 3 Maya Mesh, 4 GPU Mesh
        self.cache_geometry = True
        self.pp_name = None
        self.is_node_referenced = None
        self.ref_node = None

    def get_vraymesh_in_scene(self):
        """
        """
        self.nodes = {}
        vraymesh_nodes = cmds.ls(long=True, type="VRayMesh")
        for vraymesh_node in vraymesh_nodes:
            n = VRayMesh()
            n.get_data_from_node(vraymesh_node)
            self.nodes[vraymesh_node] = n
        return self.nodes

    def get_data_from_node(self, node=None):
        """
        """
        self.node_name = node
        self.filename = cmds.getAttr("{0}.fileName2".format(self.node_name))
        self.geometry_representation = cmds.getAttr("{0}.geomType".format(self.node_name))
        self.cache_geometry = cmds.getAttr("{0}.cacheGeometry".format(self.node_name))
        self.is_node_referenced = cmds.referenceQuery(self.node_name, isNodeReferenced=True)
        # get namespace and reference info
        if self.is_node_referenced:
            # get ref_node linked to node
            self.ref_node = cmds.referenceQuery(self.node_name, referenceNode=True, topReference=True)
        try:
            self.pp_name = cmds.getAttr("{0}.pp_name".format(self.node_name))
        except:
            pass


class VRayVolumeGrid(Node):
    """docstring for ClassName"""
    def __init__(self):
        super(VRayVolumeGrid, self).__init__()

        self.nodeType = "VRayVolumeGrid"

class Camera(object):
    """docstring for Camera"""
    def __init__(self):
        #list cameraShape and transform
        self.cameras = {}

        self.shortTransform = None
        self.shortShape = None
        self.transform = None
        self.shape = None

        self.imagePlane = None


    def getCameras(self, filter=None):
        """ get Camera in the scene
        @param filter (string) do filtering on result. available filter: noFpst (front, persp, side, top)
        """
        self.cameras = {}
        camsShape = cmds.ls(type="camera", long=True)
        for camera in camsShape:

            # get transform
            p = cmds.listRelatives(camera, parent=True, type="transform", fullPath=True)

            if p:
                # do filtering
                # filter noFpst
                if filter == "noFpst":
                    goodCam = True
                    for pattern in ["*front*", "*persp*", "*side*", "*top*", "*left*", "*bottom*", "*FACIAL*"]:
                        if fnmatch.fnmatch(p[0], pattern):
                            goodCam = False

                    if goodCam:
                        self.cameras[p[0]] = {
                                                    "shape":camera,
                                                    "shortShape":camera.split('|')[len(camera.split('|'))-1],
                                                    "shortName":p[0].split('|')[len(p[0].split('|'))-1],
                                                    "name":p[0]
                                                }
                else:
                    self.cameras[p[0]] = {
                                                    "shape":camera,
                                                    "shortShape":camera.split('|')[len(camera.split('|'))-1],
                                                    "shortName":p[0].split('|')[len(p[0].split('|'))-1],
                                                    "name":p[0]
                                                }

        return self.cameras

    def getDataFromSelectedCamera(self):
        """
        """
        # Get Selected Camera
        sel = cmds.ls(sl=True, l=True)
        self.getDataFromCamera(node=sel[0])


    def getDataFromCamera(self, node=None):
        """
        """
        if not node:
            logger.error("please fill arg node.")
            return False

        #  check node
        #  is transform
        if cmds.nodeType(node) == "transform":
            self.transform  = node
            #  retrieve camerashape
            if self.transform:
                # get children and looking for node type camera
                children = cmds.listRelatives(self.transform, shapes=True, type="camera", children=True, fullPath=True)
                if children:
                    self.shape = children[0]

        # case it's the camera shape
        if cmds.nodeType(node) == "camera":
            self.shape  = node
            #  retrieve camerashape
            if self.shape:
                # get parent and looking for node type camera
                parent = cmds.listRelatives(self.shape, type="transform", parent=True, fullPath=True)
                if parent:
                    self.transform = parent[0]

        # set short name
        if self.transform:
            self.shortTransform = self.transform.split('|')[len(self.transform.split('|'))-1]
        if self.shape:
            self.shortShape = self.shape.split('|')[len(self.shape.split('|'))-1]

        #
        self.getImagePlane()

        return True


    def getImagePlane(self):
        """
        retrieve this associated image plane.
        """
        if self.shape:
            # maya change imagePlane since maya 2014 2cases:(
            if int(cmds.about(version=True).split(' ')[0]) == 2012:
                try:
                    self.imagePlane = cmds.listConnections("%s.imagePlane" % self.shape)[0]
                    logger.info("Image Plane: %s" % self.imagePlane)
                except:
                    logger.warning("!! WARNING !! No Image Plane Found.")
            else:
                #try:
                rawConnections  = cmds.listConnections("%s.imagePlane" % self.shape)
                if rawConnections:
                    if cmds.nodeType(rawConnections[0]) == "transform":
                        self.imagePlane = cmds.listRelatives("%s" % rawConnections[0])[0]
                        logger.info("Image Plane: %s" % self.imagePlane)


            if self.imagePlane:
                return self.imagePlane
            else:
                return False

        return False

    def getActiveCamera(self):
        """
        retireve usefull animation from camera, like min start anim and max end anim.
        """

        # retrieve connected animCurve to translate rotate scale, focal
        pass


class Sound(object):
    """docstring for Camera"""
    def __init__(self):
        """
        init functions

        self.sounds follow the schema
        {
            "soundNode":{
                            "path":path,
                            "offset":offset,
                            "activeInTimeSlider":False
            }

        }
        """
        #list sound
        self.sounds = {}

        #
        self.gPlayBackSlider = mel.eval('$tmpVar=$gPlayBackSlider')
        self.activeSound = self.soundIsActive()

    def soundIsActive(self):
        """ check if a sound is active in the timeslider"""
        self.activeSound = cmds.timeControl(self.gPlayBackSlider, query=True, sound=True)
        return self.activeSound

    def getSounds(self, activeInTimeSlider=False):
        """ get sound in the scene
        :param activeInTimeSlider: (string) return only the active sound in the timeslider
        """

        soundNodes = []
        # only sound node in timeslider
        if activeInTimeSlider:
            # check if a sound active
            if self.soundIsActive():
                soundNodes = [self.activeSound]

        # else get all node
        else:
            soundNodes = cmds.ls(type="audio")

        # if sound node previously found get some other data
        if soundNodes:
            for soundNode in soundNodes:

                # init sound in dict
                self.sounds[soundNode] = {}
                self.sounds[soundNode]['activeInTimeSlider'] = False

                # get sound offset
                self.sounds[soundNode]['offset'] = cmds.getAttr("%s.offset" % soundNode)

                #  get path
                self.sounds[soundNode]['path'] = cmds.getAttr("%s.filename" % soundNode)

                # check if activeInTimeSlider True
                if activeInTimeSlider:
                    self.sounds[soundNode]['activeInTimeSlider'] = True
                else:
                    if soundNode == self.activeSound:
                        self.sounds[soundNode]['activeInTimeSlider'] = True

            return self.sounds

        else:
            logger.info("No Sound found in this scene")
            return None


class Reference():

    def __init__(self, tk=None):

        self.referencesNode = {}
        self.refNodeDefaultValue = {
            "filename":None,
            "pipelineStep":None,
            "currentRevision":None,
            "latestRevision":None,
            "upToDate":False,
            "revisionAvailable":{},
            "fileExtension":None,
            "referenceType":None,
            "isLoaded":None
        }
        self.refNode = None
        self.rootNode = None
        self.subRefNodes = []
        self.isLoaded = None
        self.filename = None
        self.fileExtension = None

        self.referenceTypeMapping = {
            "ma": "mayaAscii",
            "mb": "mayaBinary",
            "abc": "Alembic"
        }
        self.scriptNodeAttrReferenceNode = "referenceNode"

        #  init var shotgun context
        self.tk = None
        if tk:
            self.tk = tk
        self.ctx = None
        # init fields template
        self.fields = None

    def init_tk(self):
        """

        """
        if not self.tk:
            self.app_instance = sgtk.platform.current_engine()

            if self.app_instance:
                self.tk = self.app_instance.sgtk
                self.ctx = self.app_instance.context

        if not self.tk:
            sn = cmds.file(query=True, sn=True)
            if sn:
                self.tk = sgtk.sgtk_from_path(sn)

        return self.tk

    def getReferenceNodeInScene(self, getContext=False, get_template=False, onlyTopNode=True):
        """
        retrieve reference info from a given node
        :param getContext: True or False, get the shotgun toolkit context.
        """
        # get reference node
        refNodes = cmds.ls(references=True)

        if not self.tk:
            self.init_tk()

        for refNode in refNodes:

            ref = Reference()
            ref.tk = self.tk

            if onlyTopNode:

                # check if ref node come from a referenced node
                if not cmds.referenceQuery(refNode, isNodeReferenced=True):

                    ref.getReferenceDetail(refNode=refNode, getContext=getContext, get_template=get_template)

            else:
                ref.getReferenceDetail(refNode=refNode, getContext=getContext, get_template=get_template)

            if ref.filename:
                self.referencesNode[refNode] = ref

        return self.referencesNode

    def getReferenceInfoFromObjectNode(self, node, getContext=False):
        """
        retrieve reference info from a given node
        :param node: (str) ndoe name
        """
        # get reference node
        refNode = cmds.referenceQuery(node, referenceNode=True)
        if refNode:
            self.getReferenceDetail(refNode=refNode, getContext=getContext)

        return self

    def getReferenceDetail(self, refNode=None, filename=None, getContext=False, get_template=False):

        logger.debug("Get Reference Detail Node: %s" % refNode)

        # init var
        self.refNode = refNode
        self.filename = filename
        self.fileExtension = None
        self.namespace = None

        # get filename
        if not self.filename:
            self.filename = self.getFilename(refNode=refNode)

        if self.filename:

            # check if reference is loaded
            self.getIsLoadedStatus(refNode=refNode)

            # get file extension
            self.getFileExtension(filename=self.filename)

            if self.isLoaded and refNode:

                # get root node
                self.getRootNode(refNode=refNode)

                # Get Namespace
                self.getNamespace(refNode=refNode)

                if getContext:
                    self.getContext(filename=self.filename)

                if get_template:
                    self.fields = self.get_template(filename=self.filename)
            else:
                logger.info("Reference filename :\n- is not loaded\nor\n- the reference node is equal to '{0}'".format(refNode))

        else:
            logger.debug("Filename not found for reference node: %s" % refNode)
            return False

        return self

    def getRootNode(self, refNode):
        """
        retrieve the root node from reference node
        """
        logger.info("Reference Query Node : {0}".format(refNode))
        nodes = sorted(cmds.referenceQuery(refNode, nodes=True))

        for node in nodes:
            if fnmatch.fnmatch(node, "*root"):
                self.rootNode = node
                return self.rootNode

        return None

    def getReferenceNode(self, node):
        """
        """
        refNode = cmds.referenceQuery(node, referenceNode=True)
        if refNode:
            self.refNode = refNode
            return refNode

    def getNamespace(self, refNode):
        self.refNode = refNode
        try:
            self.namespace = cmds.referenceQuery(refNode, namespace=True)
        except:
            self.namespace = None

        return self.namespace

    def getLinks(self, refNode):
        self.refNode = refNode
        self.links = []
        cAttr = CustomAttr()
        if not cmds.objExists("%s.%s_%s" % (refNode, cAttr.prefix, 'links')):
            cAttr.createAttr(node=refNode, attr='links')
        else:
            cmds.objExists("%s.%s_%s" % (refNode, cAttr.prefix, 'links'))

    def getIsLoadedStatus(self, refNode):
        self.refNode = refNode
        self.isLoaded = cmds.referenceQuery(refNode, isLoaded=True)

        return self.isLoaded

    def getFilename(self, refNode):
        logger.debug("getFilename(refNode={refNode})".format(refNode=refNode))
        try:
            self.filename = cmds.referenceQuery(refNode, filename=True, unresolvedName=False, withoutCopyNumber=True)
            return self.filename
        except:
            self.filename = None
            return self.filename

    def getReferenceNodeFromFilename(self, filename):
        try:
            self.refNode = cmds.referenceQuery(filename, referenceNode=True)
            return self.refNode
        except:
            self.refNode = None
            return self.refNode

    def getFileExtension(self, filename):
        self.filename = filename
        self.fileExtension = os.path.basename(self.filename.split('.')[len(self.filename.split('.'))-1])

        return self.fileExtension

    def get_template(self, filename):
        """
        """
        if not self.tk:
            logger.debug("sgtk instance not exist init it with the path: {filename})".format(filename=filename))
            self.tk = sgtk.sgtk_from_path(filename)

        if self.tk:
            logger.debug("get template from filename {filename})".format(filename=filename))
            self.template = self.tk.template_from_path(filename)
            logger.debug("template found {template})".format(template=self.template))

            if self.template:
                self.fields = self.template.get_fields(filename)
            return self.fields

        return {}

    def getContext(self, filename, get_ctx=True, get_template=True):
        """
        """
        logger.debug("getContext(filename={filename})".format(filename=filename))

        if not self.tk:
            logger.debug("sgtk instance not exist init it with the path: {filename})".format(filename=filename))
            self.tk = sgtk.sgtk_from_path(filename)

        if self.tk:
            logger.debug("sgtk instance exist: {sgtkInst}".format(sgtkInst=self.tk))

            logger.debug("get context filename {filename})".format(filename=filename))

            if get_ctx:
                self.ctx = self.tk.context_from_path(filename)
                logger.debug("context found {ctx})".format(ctx=self.ctx))

                # fucking cache synchronization
                if self.ctx.__str__() == "Empty Context":
                    logger.debug("==> fucking cache synchronization <==")
                    self.tk.synchronize_filesystem_structure()
                    self.ctx = self.tk.context_from_path(filename)
                    logger.debug("context found {ctx})".format(ctx=self.ctx))

            if get_template:
                self.fields = self.get_template(filename=filename)
        else:
            logger.debug("can't find and initialize an sgtk instance from filename: {filename}".format(filename=filename))

            self.ctx = None
            self.template = None
            self.fields = None

        return self.ctx

    def getSubReferenceNode(self, refNode):
        """
        retrieve reference under this reference node
        """
        self.subRefNodes = []
        rs = cmds.ls(type='reference')
        for rn in rs:
            try:
                parentRefNode = cmds.referenceQuery(rn, referenceNode=True, parent=True)
                if refNode == parentRefNode:
                    self.subRefNodes.append(rn)
            except:
                pass

        return self.subRefNodes


    def get_referenceNodeUnlinkedToFile(self):
        """ this function retireve the refernece unlink to a file and delete it.
        """
        r = {}

        # get reference node
        refNodes = cmds.ls(type='reference')

        for refNode in refNodes:
            ref = Reference()
            ref.getReferenceDetail(refNode=refNode, getContext=False)

            if not ref.filename:
                r[refNode] = ref

        return r

    def do_cleanReferenceNode(self):
        """ this function retireve the refernece unlink to a file and delete it.
        """
        rns = self.get_referenceNodeUnlinkedToFile()

        for key in rns.keys():

            # test if the node is locked
            if cmds.lockNode(key, query=True, lock=True):
                # unlock node
                cmds.lockNode(key, lock=False)

            # try to delete node
            try:
                cmds.delete(key)
                logger.info("delete reference node unlink to file: '%s'" % key)
            except:
                logger.info("Can't delete the reference node: '%s'" % key)

        return

    def do_importReference(self, node=None):
        """
        """
        # check if it's top level reference node
        # check if reference node and path exist
        refNode = None
        if node:
            if cmds.referenceQuery(node, isNodeReferenced=True):
                # get reference node
                refNode = cmds.referenceQuery(node, referenceNode=True, topReference=True)

        if refNode:
            # get reference node
            refNode = cmds.referenceQuery(refNode, referenceNode=True, topReference=True)

            # import it
            try:
                cmds.file(referenceNode=refNode, importReference=True)
                logger.info("import Reference Node: %s" % refNode)
            except:
                logger.error("can't import Reference Node: %s" % refNode)
                return False
        else:
            logger.info("is not a referenced node")
            return True

        if cmds.referenceQuery(node, isNodeReferenced=True):
            return self.do_importReference(node=node)
        else:
            return True

    def do_ReplaceReference(self, refNode=None, path=None, forceRemapping=False, forceReload=False):

        # check if reference node and path exist
        if cmds.objExists(refNode) and os.path.exists(path):

            # check if filename is already setted
            rFilename = self.getFilename(refNode)
            if rFilename != path or forceReload:

                # get extension and find type
                referenceType = None
                if path.split('.')[len(path.split('.'))-1] in self.referenceTypeMapping.keys():
                    referenceType = self.referenceTypeMapping[path.split('.')[len(path.split('.'))-1]]

                if not referenceType:
                    cmds.file(path, loadReference=refNode)
                else:
                    cmds.file(path, loadReference=refNode, type=referenceType)
            else:
                logger.info("Reference Node already use this file {rFilename}, we skip the reload.".format(rFilename=rFilename))

            # check if it's really need?
            # we only need form remapping when the reference node is under another reference node.
            # so if the top level reference node is the same as the provided reference node do not forceRemapping
            if not refNode == cmds.referenceQuery(refNode, referenceNode=True, topReference=True):

                logger.info("Create a Force Remmaping Node.")

                # scriptNode
                scriptNode = None

                # list all scriptNode with attribute

                # check if refNode already have a script node linked to
                cAttr = CustomAttr()
                scriptNodeList = cmds.ls("*.%s_%s" % (cAttr.prefix, self.scriptNodeAttrReferenceNode))

                for sNAttr in scriptNodeList:

                    # check if attr == referenceNode
                    sNVal = cmds.getAttr(sNAttr)
                    if sNVal == refNode:
                        scriptNode = sNAttr.split('.')[0]

                if not scriptNode:
                    # create ScriptNode
                    scriptNode = cmds.createNode('script', name="%s_%s" % (cAttr.prefix, self.scriptNodeAttrReferenceNode))
                    # create links attr
                    cAttr.createAttr(node=scriptNode, attr=self.scriptNodeAttrReferenceNode)

                # do update
                if scriptNode:

                    referencePath = path.replace('\\', '/')
                    syntax = 'file -loadReference \"%s\" -type \"%s\" -options \"v=0\" \"%s\";' % (refNode, referenceType, referencePath)
                    #syntax = 'cmds.file("%s", loadReference="%s", type="%s", options="v=0")' % (path.replace('\\', '/'), refNode, referenceType)

                    cmds.scriptNode(scriptNode, edit=True, scriptType=1, beforeScript=syntax, sourceType="mel")

                    if cmds.objExists("%s.%s_%s" % (scriptNode, cAttr.prefix, self.scriptNodeAttrReferenceNode)):

                        cmds.setAttr("%s.%s_%s" % (scriptNode, cAttr.prefix, self.scriptNodeAttrReferenceNode), refNode, type="string")

        return True


    def do_UnloadReference(self, refNode=None):

        # check if reference node and path exist
        if cmds.objExists(refNode):
            #
            cmds.file(unloadReference=refNode)

    def do_createReference(self, namespace, filename):
        """
        """
        filename = cmds.file(filename, namespace=namespace, reference=True)
        if filename:
            self.filename = filename
            #  get reference node
            refNode = self.getReferenceNodeFromFilename(filename=self.filename)
            return refNode
        else:
            return False


    def do_LoadReference(self, refNode=None):

        # check if reference node and path exist
        if cmds.objExists(refNode):
            #
            cmds.file(loadReference=refNode)


def importReferenceFromNode(node):
    """
    """
    ref = Reference()
    return ref.do_importReference(node=node)

def getMinMaxAnimation(self, node):
    """
    retrieve the min and max animation
    """

    # get keyable attributes

    # for each attributes check if is connected to animCurve

        # get first and last keyframe



    # return dict

    pass



class Config(object):
    """
    Node to set configuration
    """

    def __init__(self, nodeName):
        """
        Initialize the class attributes

        :param nodeName: Config node name
        :type nodeName: str
        """

        self.prefixName = 'pp'
        self.name = nodeName
        self.type = 'objectSet'
        self.extraAttrs = {}
        self.node = None



    def createNode(self):
        """
        Create the config node with its attributes if exist
        """

        if not self.getNode():

            # Create the node
            self.node = cmds.createNode(self.type, name=self.name)

            # Add the attributes
            for k in self.extraAttrs.keys():
                self.addAttr(k, self.extraAttrs[k])

        else:
            logger.warning("Config node %s already exists" % self.name)



    def getNode(self):
        """
        Get the config node

        @return (str)
        The node name
        """
        self.node = None
        if cmds.objExists(self.name):
            self.node = self.name
        return self.node



    def addAttr(self, attrName, attrValue):
        """
        Add an attribute to the config node

        :param attrName: Attribute name
        :type attrName: str
        :param attrValue: Attribute value
        :type attrValue: dict
        """

        # Make sure attribute name starts with pp_
        if not re.search('^%s_' % self.prefixName, attrName):
            attrName = '%s_%s' % (self.prefixName, attrName)

        if not self.getAttr(attrName):

            # Make sure attribute name starts with pp_
            if not re.search('^%s_' % self.prefixName, attrName):
                attrName = '%s_%s' % (self.prefixName, attrName)

            if self.node:

                # Create an empty attribute and set it value
                cmds.addAttr(self.node, longName=attrName, dataType="string")
                self.setAttr(attrName, attrValue)

            else:
                logging.critical("Couldn't add attribute %s: config node %s doesn't exist" % (attrName, self.name))

        else:
            logger.warning("Attribute %s already exists for config node %s" % (attrName, self.name))



    def getAttr(self, attrName):
        """
        Get the attribute value

        :param attrName: Attribute name
        :type attrName: str
        :returns: None if the attribute doesn't exist, it value otherwise
        :rtype: dict
        """

        attrValue = None

        # Make sure attribute name starts with pp_
        if not re.search('^%s_' % self.prefixName, attrName):
            attrName = '%s_%s' % (self.prefixName, attrName)

        if self.node:
            if cmds.objExists('%s.%s' % (self.node, attrName)):
                ymlData = cmds.getAttr('%s.%s' % (self.node, attrName))
                return yaml.load(ymlData)
        else:
            logger.warning("Couldn't get attribute %s: config node %s doesn't exist" % self.name)



    def setAttr(self, attrName, attrValue):
        """
        Set an attribute value

        :param attrName: Attribute name
        :type attrName: str
        :param attrValue: Attribute value
        :type attrValue: dict
        """

        # Make sure attribute name starts with pp_
        if not re.search('^%s_' % self.prefixName, attrName):
            attrName = '%s_%s' % (self.prefixName, attrName)

        ymlData = yaml.dump(attrValue, default_flow_style=True)
        cmds.setAttr('%s.%s' % (self.node, attrName), ymlData, type="string")


class Timewarp(object):
    """
    Node to set timewarp in a scene
    """

    def __init__(self):
        """
        Initialize the class attributes

        :param nodeName: Config node name
        :type nodeName: str
        """

        self.prefixName = 'pp'
        self.shortName = "shotTimewarp"
        self.name = "%s_%s" % (self.prefixName, self.shortName)
        self.type = 'animCurveTT'
        self.extraAttrs = {}
        self.node = None

    def createNode(self):
        """
        Create the config node with its attributes if exist
        """

        if not self.getNode():

            # Create the node
            self.node = cmds.createNode(self.type, name=self.name)
            return self.node
            # Add the attributes
            # for k in self.extraAttrs.keys():
            #   self.addAttr(k, self.extraAttrs[k])

        else:
            logger.warning("%s node already exists" % self.name)
            return



    def getNode(self):
        """
        Get the config node
        :returns: the node name
        :rtype: str
        """
        self.node = None
        if cmds.objExists(self.name):
            self.node = self.name
        return self.node

    def addAttr(self, attrName, attrValue):
        """
        Add an attribute to the config node

        :param attrName: Attribute name
        :type attrName: str
        :param attrValue: Attribute value
        :type attrValue: dict
        """

        # Make sure attribute name starts with pp_
        if not re.search('^%s_' % self.prefixName, attrName):
            attrName = '%s_%s' % (self.prefixName, attrName)

        if not self.getAttr(attrName):

            # Make sure attribute name starts with pp_
            if not re.search('^%s_' % self.prefixName, attrName):
                attrName = '%s_%s' % (self.prefixName, attrName)

            if self.node:

                # Create an empty attribute and set it value
                cmds.addAttr(self.node, longName=attrName, dataType="string")
                self.setAttr(attrName, attrValue)

            else:
                logging.critical("Couldn't add attribute %s: config node %s doesn't exist" % (attrName, self.name))

        else:
            logger.warning("Attribute %s already exists for config node %s" % (attrName, self.name))



    def getAttr(self, attrName):
        """
        Get the attribute value

        :param attrName: Attribute name
        :type attrName: str
        :returns: None if the attribute doesn't exist, it value otherwise
        :rtype: dict
        """

        attrValue = None

        # Make sure attribute name starts with pp_
        if not re.search('^%s_' % self.prefixName, attrName):
            attrName = '%s_%s' % (self.prefixName, attrName)

        if self.node:
            if cmds.objExists('%s.%s' % (self.node, attrName)):
                ymlData = cmds.getAttr('%s.%s' % (self.node, attrName))
                return yaml.load(ymlData)
        else:
            logger.warning("Couldn't get attribute %s: config node %s doesn't exist" % self.name)



    def setAttr(self, attrName, attrValue):
        """
        Set an attribute value

        :param attrName: Attribute name
        :type attrName: str
        :param attrValue: Attribute value
        :type attrValue: dict
        """

        # Make sure attribute name starts with pp_
        if not re.search('^%s_' % self.prefixName, attrName):
            attrName = '%s_%s' % (self.prefixName, attrName)

        ymlData = yaml.dump(attrValue, default_flow_style=True)
        cmds.setAttr('%s.%s' % (self.node, attrName), ymlData, type="string")

class CustomAttr(object):
    """docstring for CustomAttr"""
    def __init__(self):

        self.node = None

        self.prefix = "pp"
        self.ovrPrefix = "ovr"
        self.defautlAttr = {
                                'links':{'type':'message'},
                                'name':{'type':'string'},
                                'entityName':{'type':'string'},
                                'entityType':{'type':'string'},
                                'entitySubType':{'type':'string'},
                                'referenceNode':{'type':'string'}
                            }

    def get_attribute_name(self, attr, ovr=False):
        """
        """

        # check if attr already exist
        attrFinal = "%s_%s" % (self.prefix, attr)
        if ovr:
            attrFinal = "%s_%s_%s" % (self.prefix, self.ovrPrefix, attr)

        return attrFinal

    def createAttr(self, node, attr, ovr=False):
        """
        Adds an attribute to the node

        :param node: (str) node list
        :param attr: (str) attr name
        """

        # check if attr already exist
        attrFinal = self.get_attribute_name(attr=attr, ovr=ovr)

        if not cmds.objExists("%s.%s" % (node, attrFinal)):

            # check if node locked
            if cmds.lockNode(node, lock=True, query=True):
                cmds.lockNode(node, lock=False)

            if attr in self.defautlAttr.keys():
                
                # create attr
                if self.defautlAttr[attr]['type'] == 'message':
                    resAddAttr = cmds.addAttr(node, ln=attrFinal, at="message")

                if self.defautlAttr[attr]['type'] == 'string_list':
                    resAddAttr = cmds.addAttr(node, ln=attrFinal, dt="string")

                if self.defautlAttr[attr]['type'] == 'string':
                    resAddAttr = cmds.addAttr(node, ln=attrFinal, dt="string")

                return True
            else:
                logger.error("attr %s not in the default list self.defautlAttr" % attr)
                return False

        else:
            return False

def get_vraymesh_in_scene():
    """
    """
    v = VRayMesh()
    return v.get_vraymesh_in_scene()

def getReferenceNodeInScene(getContext=False, tk=None):
    """
    retrieve reference Node available in the scene.
    output dict.
    """

    ref = Reference(tk=tk)
    return ref.getReferenceNodeInScene(getContext=getContext, onlyTopNode=False)

def do_replaceMySelectedReferencedNodeByMyFile(filename, forceRemapping=False):
    """
    """

    sels = cmds.ls(sl=True, l=True)

    if sels:
        do_replaceReferencedNodeByMyFile(node=sels[0], filename=filename, forceRemapping=forceRemapping)


def do_replaceReferencedNodeByMyFile(node, filename, forceRemapping=False):
    """
    """
    r = Reference()
    refNode = r.getReferenceNode(node=node)

    if refNode:
        result = r.do_ReplaceReference(refNode=refNode, path=filename, forceRemapping=forceRemapping)
        if not result:
            return False

    return False


def create_group(path=None):
    """ this function create a group structure from a path definition like root|groupA|groupB. then return the group node."""
    logger.info("create_group : {path}".format(path=path))
    if not cmds.objExists(path):

        # create
        splittedGroup = path.split('|')

        currentParent = None
        for item in splittedGroup:

            if not cmds.objExists(item):
                item = cmds.group(name=item, empty=True)
                if item and currentParent:
                    cmds.parent(item, currentParent)

            # update parent
            if not currentParent:
                currentParent = item
            else:
                currentParent += "|%s" % item


def delete_locked_node(nodes=[], selection=False):
    """
    """
    if not nodes:
        nodes = cmds.ls(sl=True, l=True)

    logging.info("Selection: {nodes}".format(nodes=nodes))

    for n in nodes:

        # if camera remove attr startup camera
        ns = [n]
        children = cmds.listRelatives(n, children=True)
        if children:
            ns.extend(children)

        for sub_n in ns:
            if cmds.objExists(sub_n):
                logging.info("unlock node: {node}".format(node=sub_n))
                cmds.lockNode(sub_n, lock=False)

                if cmds.nodeType(sub_n) == "camera":
                    cmds.camera(sub_n, edit=True, startupCamera=False)
                cmds.delete(sub_n)
