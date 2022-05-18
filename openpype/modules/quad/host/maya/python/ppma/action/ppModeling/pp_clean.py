import maya.cmds as cmds
import logging

format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppma.action.ppModeling.pp_clean')
logger.setLevel(logging.INFO)


def auto_rename_shape():
    """
    """
    m_l = []
    r = cmds.ls(sl=True, l=True)
    for item in r:
        s = cmds.listRelatives(item, children=True, noIntermediate=True, shapes=True, fullPath=True)
        if s:
            m_l.append(s[0])
    if not m_l:
        m_l = cmds.ls(type="mesh", l=True)

    m_l_failed = []

    for m in m_l:
        # get parent transform
        r = cmds.listRelatives(m, parent=True, type="transform")
        if r:
            s = r[0]
            i = 0
            rm_number = 0
            for i in range(0, len(s)):
                last_s = s[len(s) - 1 - i]
                logger.debug("\t" + last_s)
                if last_s.isdigit():
                    rm_number = i + 1
                else:
                    break
            r_string = s
            if rm_number:
                r_string = s[:-rm_number]
            r_number = r[0].replace(r_string, "")
            m_new_name = "{0}Shape{1}".format(r_string, r_number)
            logger.info("Parent {parent} - Rename {m} > {m_new_name}".format(parent=s, m=m, m_new_name=m_new_name))
            try:
                cmds.rename(m, m_new_name)
            except:
                m_l_failed.append(m)
    for m in m_l_failed:
        logger.error("Failed to rename : {0}".format(m))
    if m_l_failed:
        return False
    return True
