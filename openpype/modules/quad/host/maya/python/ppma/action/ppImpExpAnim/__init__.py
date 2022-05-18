import logging
import time
import maya.cmds as cmds
from . import import_anim
from . import export_anim
# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppma.action.ppImpExpAnim')
logger.setLevel(logging.DEBUG)


# ---
# import section
def import_animation_from_current_scene():
    start_time = time.clock()
    i = import_anim.Importer()
    i.start()
    end_time = time.clock()
    length = end_time - start_time
    logger.info("import animation time : %s s" % length)


def import_animation_from_selection():
    """
    """
    # get selection
    sel = cmds.ls(sl=True, long=True)
    logger.info("Selection: %s" % sel)
    start_time = time.clock()
    i = import_anim.Importer()
    i.start(nodes=sel)
    end_time = time.clock()
    length = end_time - start_time
    logger.info("import animation time : %s s" % length)


# ---
# export section
def export_animation_from_current_scene(subprocess_mode="local"):
    """
    This function is used from maya by artist to launch export for all the scene
    """
    #
    e = export_anim.Exporter()
    e.start(nodes=[], subprocess_mode=subprocess_mode)


def export_animation_from_selection(subprocess_mode="local"):
    """
    This function is used from maya by artist to launch export for a selection
    """
    #
    nodes = cmds.ls(sl=True)
    if nodes:
        e = export_anim.Exporter()
        e.start(nodes=nodes, subprocess_mode=subprocess_mode)
    else:
        logger.info("Please Select something")
        return False
