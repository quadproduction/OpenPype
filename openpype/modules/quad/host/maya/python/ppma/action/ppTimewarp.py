# -*- coding: utf-8 -*-

"""
timewarp manage the time in a shot
"""

import maya.cmds as cmds
import logging
import fnmatch
import pprint
import ppma.core.ppNode as ppNode
import ppTools.ppTimewarp as ppTimewarp


# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppma.action.ppTimewarp')
logger.setLevel(logging.INFO)


class Timewarp():

    def __init__(self):

        # timewarp node
        self.node = None

        # store shot name and project name
        self.entity = None
        self.project = None

        # timeawarp data inside
        self.data = None

        # retireve main class Timewarp from ppTools
        self.main_timewarp = ppTimewarp.Timewarp()

    def initTk(self):
        """
        """
        self.main_timewarp.cmds.do_initTk()
        self.tk = self.main_timewarp.cmds.tk
        self.ctx = self.main_timewarp.cmds.ctx

        self.entity = self.ctx.entity['name']
        self.project = self.ctx.project['name']

    def get_and_apply_timewarp_on_selection(self, killPreviousNode=False):
        """
        """
        #  get selection
        res = self.get_selection()
        self.get_and_apply_timewarp_on_nodes(nodes=res, killPreviousNode=killPreviousNode)

    def get_and_apply_timewarp_on_nodes(self, nodes=[], killPreviousNode=None):
        """
        """

        # get current shot
        self.initTk()

        # get timewarp curves
        if not self.get_timewarp_curve():
            logger.info("Can't get timewarp curve, please fill shotgun or publish a timewarp file.")
            return False

        # so we apply the timewarp curve on nodes
        self.apply_timewarp_on_nodes(nodes=nodes, killPreviousNode=killPreviousNode)

    def get_selection(self):
        """
        from the current selection. isolate each node.
        """
        # Get Selection
        selTmp = cmds.ls(selection=True)

        # Select Hierarchy
        # cmds.select(selTmp, replace=True, hierarchy=True)
        cmds.select(selTmp, replace=True, hierarchy=False)
        selTmp = cmds.ls(selection=True)
        self.selection = []

        # Looking for imagePlane if camera
        for obj in selTmp:
            if cmds.nodeType(obj) == "camera":
                self.selection.append(obj)

                # case maya 2012
                if int(cmds.about(version=True).split(' ')[0]) == 2012:
                    tmpNodes = cmds.listConnections("%s.imagePlane" % obj, source=True, destination=False)
                    if tmpNodes:
                        for tmpNode in tmpNodes:
                            if cmds.nodeType(tmpNode) == "imagePlane":
                                self.selection.append(tmpNode)
                else:
                    # case maya 2014
                    rawConnections = cmds.listConnections("%s.imagePlane" % obj)
                    if rawConnections:
                        if cmds.nodeType(rawConnections[0]) == "transform":
                            tmpNode = cmds.listRelatives("%s" % rawConnections[0])[0]
                            if cmds.nodeType(tmpNode) == "imagePlane":
                                self.selection.append(tmpNode)

            if cmds.nodeType(obj) == "transform":
                self.selection.append(obj)

        return self.selection

    def get_timewarp_curve(self):
        """
        We check if we could retrieve timewarp info from a published file or hard coded path or from shotgun.
        """
        if not self.entity and not self.project:
            logger.error("can't get shot or/and project name.")
            return
        # init result
        self.data = None

        # get common class timewarp
        self.main_timewarp.retrieve_timewarp_info(shot_name=self.entity, project_name=self.project)

        # check result
        if "timewarp_values" in self.main_timewarp.data.keys():
            if len(self.main_timewarp.data["timewarp_values"].keys()) > 0:
                self.data = self.main_timewarp.data

        return self.data

    def apply_timewarp_on_nodes(self, nodes=[], killPreviousNode=False, start_frame=None):
        """
        apply timewarp curve on nodes.
        :param nodes:
        :param killPreviousNode:
        """
        if not nodes:
            logger.warning("No nodes to apply.")
        # get start frame
        if not start_frame:
            timewarp_values = self.main_timewarp.get_shot_cut_info_from_sg(shot_name=self.entity, project_name=self.project)
            start_frame = float(min(timewarp_values.keys()))
            # start_frame = self.main_timewarp.settings["start_working_time"]
        logger.info("Timewarp Values :")
        logger.info("Start Frame : {0}".format(start_frame))
        logger.info(pprint.pformat(self.data["timewarp_values"]))
        # create maya timewarp node
        twNode = ppNode.Timewarp()
        self.node = twNode.getNode()
        # Store current tangent settings as origin for restore it later
        inTangentOrig = "auto"
        outTangentOrig = "auto"
        if int(cmds.about(apiVersion=True)) < 201653:
            inTangentOrig = cmds.keyTangent(query=True, g=True, itt=True)[0]
            outTangentOrig = cmds.keyTangent(query=True, g=True, ott=True)[0]
        # Set tangent to linear
        cmds.keyTangent(g=True, itt='spline')
        cmds.keyTangent(g=True, ott='spline')
        logger.info("Apply TimeWarp on: %s" % self.selection)
        # if timewarp node exist and killPreviousNode True / delete node
        if self.node and killPreviousNode:
            # delete previous node
            cmds.delete(twNode.node)
            self.node = None
        # create a new timewarp node if needed
        if not self.node:
            # create a new timewarp node
            self.node = twNode.createNode()
        # add attr path
        twNode.addAttr(attrName="pp_timewarp_path", attrValue=self.main_timewarp.tw_path)
        # get first frame from key
        first_frame = float(min(self.data["timewarp_values"].keys()))
        # calc difference between first_frame and start_working_time aka start_frame
        diff_start_frame = start_frame - first_frame
        # Set TimeWarp Value
        first_frame_offset = float(min(self.data["timewarp_values"].keys())) + diff_start_frame
        last_frame_offset = float(max(self.data["timewarp_values"].keys())) + diff_start_frame
        for frame_origin in sorted(self.data["timewarp_values"].keys()):
            frame_offsetted = float(frame_origin) + diff_start_frame
            frame_target = float(self.data["timewarp_values"][frame_origin])
            logger.info("\t Set KeyFrame {node}, time:{t}, value:{v}".format(node=self.node, t=frame_offsetted, v=frame_target))
            cmds.setKeyframe(self.node, value=frame_target, time=(frame_offsetted, frame_offsetted))

        # set tangent to spline for the first and last key before set pre and post infinity.
        cmds.keyTangent(self.node, inTangentType='spline', outTangentType='spline', time=(first_frame_offset, first_frame_offset))
        cmds.keyTangent(self.node, inTangentType='spline', outTangentType='spline', time=(last_frame_offset, last_frame_offset))
        # set pre and post infinity to linear.
        cmds.selectKey(clear=True)
        logger.info("Set Timewarp Pre and Post infinity to Linear\n - Time Range ({0} - {1})".format(first_frame_offset, last_frame_offset))
        cmds.selectKey(self.node, time=(first_frame_offset, last_frame_offset))
        cmds.setInfinity(preInfinite='linear', postInfinite='linear')
        # cmds.selectKey(clear=True)

        # Connect each anim curve from nodes to our timewarp node
        # init the anilm curve list
        self.anim_curve_list = []

        # Get Anim Curve from Selection
        for item in nodes:
            # Get Keyable Attr
            attrs = cmds.listAttr(item, keyable=True)
            if attrs:
                # Get Connection
                for attr in attrs:
                    connections = cmds.listConnections("%s.%s" % (item, attr), destination=False, source=True)
                    if connections:
                        for con in connections:
                            if fnmatch.fnmatch(cmds.nodeType(con), "animCurve*"):
                                self.anim_curve_list.append(con)

        # Make the Connection between animcurve and timewarp.
        if len(self.anim_curve_list) > 0:
            for animCurve in self.anim_curve_list:
                master = "%s.output" % (self.node)
                slave = "%s.input" % (animCurve)
                logger.info("Connect: %s > %s" % (master, slave))
                if not cmds.isConnected(master, slave):
                    cmds.connectAttr(master, slave, force=True)
        else:
            logger.info("No Anim Curve to TimeWarp")

        #=======================================================================
        # SET EXTRA DATA on TimeWarp
        #=======================================================================
        # logger.info("Add Extra Attr")

        # jour      = "%s" % datetime.datetime.today()

        # user      = "Guest"
        # try:
        #   user    = os.environ["PIPE_USER"]
        # except:
        #   user    = "Guest"

        # extraAttrDico = {"createdAt":jour, "createdBy":user, "timeWarpMode":self.timeWarpMode}

        # for attr in extraAttrDico.keys():

        #   if not cmds.objExists("%s.%s" % (self.node,attr)):
        #       resAddAttr  = cmds.addAttr(self.node, ln=attr, dt="string")

        #   if cmds.objExists("%s.%s" % (self.node,attr)):
        #       resAddAttr  = cmds.setAttr("%s.%s" % (self.node,attr), extraAttrDico[attr], type="string")

        # restore tangent settings
        cmds.keyTangent(g=True, itt=inTangentOrig)
        cmds.keyTangent(g=True, ott=outTangentOrig)

        # set attr

        return True

    def publish_timewarp_curve(self, node=None):
        """
        publish the anim curve node as a timewarp file.
        """

        self.initTk()

        if not node:
            # get selection
            sel = cmds.ls(sl=True, l=True)
            if not sel:
                logger.error("Can't publish timewarp curve, nothing node=None and nothing selected:(")
                return
            else:
                node = sel[0]

        # check if it's an animCurve type
        if not fnmatch.fnmatch(cmds.nodeType(node), "animCurve*"):
            logger.error("Can't publish a node different than an animCurve.")
        else:
            # duplicate node
            tmp_node = "{node}_tmp".format(node=node)
            tmp_node = cmds.duplicate(node, name=tmp_node, returnRootsOnly=False)[0]

            # bake anim curve
            self.bake_curve_node(node=tmp_node)

            # get frame mapping
            key_mapping = self.get_keyframe_list(node=tmp_node)

            # publish this data
            self.main_timewarp.ingest_timewarp_from_dict(data=key_mapping, encoding_type="maya", shot_name=self.entity, project_name=self.project, cut_name=None, update_shotgun=True, fps=25.0)

    def bake_curve_node(self, node):
        """
        bake curve, set one key by frame.
        """
        # bake node
        # get first and last key
        number_of_keys = cmds.keyframe(node, query=True, keyframeCount=True)
        first_frame = cmds.keyframe(node, query=True, index=(0, 0), timeChange=True)[0]
        last_frame = cmds.keyframe(node, query=True, index=(number_of_keys-1, number_of_keys-1), timeChange=True)[0]
        # bake tmp_node
        cmds.bakeResults(node, time=(first_frame, last_frame), simulation=True, sampleBy=1)

        return True

    def get_keyframe_list(self, node):
        """
        get a dict which represent the mapping key: frame
        """
        # get first and last key
        number_of_keys = cmds.keyframe(node, query=True, keyframeCount=True)
        key_mapping = {}

        for index in range(0, number_of_keys):

            frame = cmds.keyframe(node, query=True, index=(index, index), timeChange=True)[0]
            value = cmds.keyframe(node, query=True, index=(index, index), valueChange=True)[0]

            key_mapping[frame] = value

        return key_mapping


def create_timewarp_on_selection(killPreviousNode=False):
    """
    """
    tw = Timewarp()
    tw.get_and_apply_timewarp_on_selection(killPreviousNode=killPreviousNode)


def publish_selected_timewarp():
    """
    """
    tw = Timewarp()
    tw.publish_timewarp_curve()
