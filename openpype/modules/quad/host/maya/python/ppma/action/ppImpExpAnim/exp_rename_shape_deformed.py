import maya.cmds as cmds
import logging
import re
import ppma.core.ppNode as ppNode


def rename_shape_deformed(shape_filter='*', logger=None):
    '''
    @summary: rename all shape deformed to original name to preserve shading assignment
    '''
    # init logger
    if not logger:
        format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
        logging.basicConfig(format=format)
        logger = logging.getLogger('ppma.action.ppImpExpAnim')
        logger.setLevel(logging.DEBUG)
    shape_deform_pattern = "Deformed"
    logger.info("-\n---> Rename Shape Deformed :\n- Filter : '{0}'\n- Pattern : {1}".format(shape_filter, shape_deform_pattern))
    objectList = []
    for objectType in ["mesh", "nurbsCurve"]:
        r = cmds.ls(shape_filter, type=objectType, long=True, recursive=True)
        objectList.extend(r)
    shape_deformed_list = []
    for obj in objectList:
        if re.search(shape_deform_pattern, obj):
            shape_deformed_list.append(obj)
    # list shape deformed
    if not shape_deformed_list:
        logger.info("No Shape Found")
    else:
        logger.info("==> %s shape found" % len(shape_deformed_list))
        # for each shape get parent
        for shape_deformed in shape_deformed_list:
            # check it's not an intermediate shape
            if not cmds.getAttr("%s.intermediateObject" % shape_deformed):
                logger.info("\t Rename : {s}".format(s=shape_deformed))
                # before do this we must check if the shapes come from a reference. we mus import it before the rename
                if cmds.referenceQuery(shape_deformed, isNodeReferenced=True):
                    _import_reference_from_this_node(shape_deformed)
                parent_transform = cmds.listRelatives(shape_deformed, parent=True, fullPath=True)
                intermediate_shape = cmds.getAttr("%s.intermediateObject" % shape_deformed)
                if parent_transform and not intermediate_shape:
                    parent_transform = parent_transform[0]
                    # from parent get original shape
                    children_shape = cmds.listRelatives(parent_transform, children=True, shapes=True, fullPath=True)
                    original_shape = None
                    if children_shape:
                        if not children_shape[0] == shape_deformed:
                            original_shape = children_shape[0]
                    #  check if we have all names we needed
                    if shape_deformed and parent_transform and original_shape:
                        # build new_name List
                        name_list = {
                            "shape_deformed": {"old_name": shape_deformed, "new_name": original_shape},
                            "original_shape": {"old_name": original_shape, "new_name": "%sOriginal" % original_shape}
                        }
                        #  rename original shape to *shapeOrignal
                        orig_shape_renamed = name_list["original_shape"]["new_name"].split('|')[len(name_list["original_shape"]["new_name"].split('|')) - 1]
                        # check if node locked
                        if cmds.lockNode(name_list["original_shape"]["old_name"], query=True, lock=True)[0]:
                            logger.info("Unlock Node : {n}".format(n=name_list["original_shape"]["old_name"]))
                            # try to unlock
                            cmds.lockNode(name_list["original_shape"]["old_name"], lock=False)
                        else:
                            logger.info("Node already Unlocked : {n}".format(n=name_list["original_shape"]["old_name"]))
                        # in any case try to import reference, fuck subtility
                        _import_reference_from_this_node(name_list["original_shape"]["old_name"])
                        locked = cmds.lockNode(name_list["original_shape"]["old_name"], query=True, lock=True)[0]
                        is_a_reference = cmds.referenceQuery(shape_deformed, isNodeReferenced=True)
                        logger.info("Node Summary : {n}\n- locked : {l}\n- isReference : {r}".format(n=name_list["original_shape"]["old_name"], l=locked, r=is_a_reference))
                        logger.info("Rename ShapeOrig \n %s \n To  > %s" % (name_list["original_shape"]["old_name"], orig_shape_renamed))
                        result_orig_shape = cmds.rename(name_list["original_shape"]["old_name"], orig_shape_renamed)
                        logger.info("Rename ShapeOrig \n %s \n To  > %s \n Name Post Rename = %s" % (name_list["original_shape"]["old_name"], orig_shape_renamed, result_orig_shape))
                        shape_deformed_renamed = name_list["shape_deformed"]["new_name"].split('|')[len(name_list["shape_deformed"]["new_name"].split('|')) - 1]
                        result_shape_deformed = cmds.rename(name_list["shape_deformed"]["old_name"], shape_deformed_renamed)
                        logger.info("Rename shape_deformed \n %s \n To  > %s \n Name Post Rename = %s" % (name_list["shape_deformed"]["old_name"], shape_deformed_renamed, result_shape_deformed))
                    else:
                        logger.debug("Problem: shape_deformed: %s // parent_transform: %s // original_shape % s" % (shape_deformed, parent_transform, original_shape))
            else:
                logger.debug("Couldn't find parent to shape: %s" % shape_deformed)

        logger.info("Rename Done")
        return True


def _import_reference_from_this_node(node):
    """
    import from reference if the node is a reference
    """
    # before do this we must check if the shapes comme from a reference. we must import it before renaming
    # is a referenced node?
    return ppNode.importReferenceFromNode(node=node)
