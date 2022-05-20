# -*- coding: utf-8 -*-

""" build menu in maya """

import logging
import os
from tank_vendor import yaml
import maya.cmds as cmds
import maya.mel as mel
import ppma


# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger('ppma.action.ppMenu')
logger.setLevel(logging.DEBUG)


class MenuBuilder(object):
    """ Build the Maya menu with all the studio tools entries.
    """
    def __init__(self):
        """ MenuBuilder constructor.
        """
        self.name = "fixstudio_maya_menu"
        self.label = "Fix|Studio"
        self.filename = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(ppma.__file__))),
            "ppMenu.yml",
        )
        logger.info("yaml description file: %s", self.filename)

    def _mk_root_menu(self):
        """ Create a root menu inside maya.
        """
        main_window = mel.eval("$tmpVar=$gMainWindow")

        cmds.menu(
            self.name,
            parent=main_window,
            tearOff=True,
            label=self.label,
            allowOptionBoxes=True,
        )

    def _mk_parent_menu(self, dirname):
        """ Create a parent menu.
        """
        parent = self.name

        for path in dirname.split('/'):
            if path:
                current = path.replace(' ', '')
                unique_name = "{0}_{1}".format(parent, current)

                if unique_name not in cmds.lsUI(menuItems=True):
                    r = cmds.menuItem(
                        unique_name,
                        parent=parent,
                        subMenu=True,
                        tearOff=True,
                        label=path,
                    )
                    if r:
                        parent = r.split('|')[-1]
                else:
                    parent = unique_name

        return parent

    def build_menu(self):
        """ Create the menu from the yaml file.
        """
        self._mk_root_menu()

        parent = self.name

        with open(self.filename, 'rb') as fd:
            data = yaml.load(fd)

        for entry in data:
            parent = self.name
            dirname = os.path.dirname(entry['path'])
            basename = os.path.basename(entry['path'])

            if dirname != "/":
                parent = self._mk_parent_menu(dirname)

            if basename and basename == "separator":
                cmds.menuItem(divider=True, parent=parent)
            elif basename:
                if entry['cmdType'] == "mel":
                    cmd = "maya.mel.eval('{0}')".format(entry['cmd'])
                else:
                    cmd = entry['cmd']

                cmds.menuItem(
                    label=basename,
                    command=cmd,
                    annotation=entry.get('comment', ""),
                    parent=parent,
                )


def build_menu():
    """ Maya menu builder entrypoint.
    """
    obj = MenuBuilder()
    obj.build_menu()
    logger.debug("Fixstudio menu loaded")
