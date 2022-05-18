# -*- coding: utf-8 -*-

"""
common classes and functions about node
"""
import maya.cmds as cmds
import maya.mel as mel
import fnmatch
import logging
import os
import re
import ppUtils.ppFileSequence as ppFileSequence
# import ppma.core.ppTools as ppTools

# loggger
#=======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('core.ppNode')
logger.setLevel(logging.INFO)


class Node(object):
    """docstring for Node"""

    def __init__(self):
        self.node = None
        self.nodeShape = None

    def create_controller(self, node, shape_type="locator", constraint_node_to_controller=True, parent_node_to_controller=False):
        """
        this function create a controller with different shape.
        """

        self.node = None
        
        # create controller
        if shape_type == "locator":
            self.node = cmds.spaceLocator(name="{node}_ctrl".format(node=node))[0]

        if not self.node:
            return
        # snap to
        ppTools.snap(source=node, destination=self.node, snap_method="snap_transform")
        
        # freeze transform
        cmds.makeIdentity(self.node, apply=True, translate=True, rotate=True, scale=True)

        if constraint_node_to_controller:
            # constraint node by self.node
            ppTools.snap(source=self.node, destination=node, snap_method="constraint_t_r_s")

        if parent_node_to_controller:
            cmds.parent(node, self.node)

        return self.node

    def createGpuCache(self, name=None, filepath=None):
        """ this create a open vdb reader via maxwelle """

        # define default name
        defaultName = "gpuCache_ReaderShape1"

        # check name
        if not name:
            self.nodeShape = defaultName
        else:
            self.nodeShape = "gpuCache_{name}".format(name=name)
            if not "Shape" in self.nodeShape:
                self.nodeShape = "{name}Shape".format(name=self.nodeShape)

        # create node
        self.nodeShape = cmds.createNode("gpuCache", name=self.nodeShape)

        # set filepath
        cmds.setAttr("{nodeShape}.cacheFileName".format(nodeShape=self.nodeShape), filepath, type="string")

        return self.nodeShape

    def createOpenVdbReader(self, name=None, filepath=None, method="maxwell"):
        """ this create a open vdb reader via maxwelle """

        # define default name
        defaultName = "openVDB_ReaderShape1"

        # check name
        if not name:
            self.nodeShape = defaultName
        else:
            self.nodeShape = "openVDB_{name}".format(name=name)
            if not "Shape" in self.nodeShape:
                self.nodeShape = "{name}Shape".format(name=self.nodeShape)

        # check filepath
        # if % in filepath remap it
        if "%" in filepath:

            # get seq_info from file
            seq = ppFileSequence.get_pyseq_info(filepath)
            filepath = filepath % seq.start()

        # check wich method we use
        if method == "maxwell":

            # create node
            self.nodeShape = cmds.createNode("maxwellVolumetricObject", name=self.nodeShape)

            # set filepath available
            cmds.setAttr("{nodeShape}.useConstantDensity".format(nodeShape=self.nodeShape), 3)

            # set filepath
            cmds.setAttr("{nodeShape}.file".format(nodeShape=self.nodeShape), filepath, type="string")

            # create and assign default shader
            materialNode = cmds.shadingNode("maxwellLayeredMaterial", asShader=True)

            # rename shader
            materialNode = cmds.rename(materialNode, "{nodeShape}_mtl".format(nodeShape=self.nodeShape))

            # select node and assign shader to him
            cmds.select(self.nodeShape, replace=True)
            cmds.hyperShade(assign=materialNode)

            return self.nodeShape

    def create_mxs_reference(self, name=None, filepath=None):
        """
        this func create a maxwellReferencedMXS node.
        """
        prefix = "mxsRef"

        # define default name
        defaultName = "%s_ReaderShape001" % prefix

        # check name
        if not name:
            self.nodeShape = defaultName
        else:
            self.nodeShape = "mxs_{name}".format(name=name)
            if "Shape" not in self.nodeShape:
                self.nodeShape = "{name}Shape".format(name=self.nodeShape)

        # create node
        self.nodeShape = cmds.createNode("maxwellReferencedMXS", name=self.nodeShape)

        # set filepath
        cmds.setAttr("{nodeShape}.file".format(nodeShape=self.nodeShape), filepath, type="string")

        # connect time to maxwellReferencedMXS.time
        cmds.connectAttr("time1.outTime", "{node_shape}.time".format(node_shape=self.nodeShape), force=True)

        # define animated or not
        animated_value = 0
        if len(os.path.basename(filepath).split('.')) > 2:
            animated_value = 1

        cmds.setAttr("{node_shape}.animated".format(node_shape=self.nodeShape), animated_value)

        return self.nodeShape

    def create_vrscene(self, name=None, filepath=None):
        """
        this func create a maxwellReferencedMXS node.
        """
        # create mesh node
        mesh_transform_name = "vrscene_{0}".format(name)
        mesh_shape_name = "{0}Shape".format(mesh_transform_name)
        mesh_vrscene_name = "{0}vrscene".format(mesh_transform_name)

        mesh_transform_name = cmds.createNode("transform", name=mesh_transform_name)
        mesh_shape_name = cmds.createNode("mesh", name=mesh_shape_name, parent=mesh_transform_name)
        mesh_vrscene_name = cmds.createNode("VRayScene", name=mesh_vrscene_name, parent=mesh_transform_name)

        # connect mesh description
        cmds.connectAttr("{0}.outMesh".format(mesh_vrscene_name), "{0}.inMesh".format(mesh_shape_name))

        # set filepath
        cmds.setAttr("{0}.FilePath".format(mesh_vrscene_name), filepath, type="string")
        # set flipAxis
        cmds.setAttr("{0}.FlipAxis".format(mesh_vrscene_name), 0)
        # connect time
        if not cmds.isConnected("time1.outTime", "{0}.inputTime".format(mesh_vrscene_name)):
            cmds.connectAttr("time1.outTime", "{0}.inputTime".format(mesh_vrscene_name))
        # add shading group to mesh
        cmds.select(mesh_shape_name, replace=True)
        cmds.hyperShade(assign="initialShadingGroup")

        cmds.select(mesh_transform_name, replace=True)

        return mesh_transform_name
