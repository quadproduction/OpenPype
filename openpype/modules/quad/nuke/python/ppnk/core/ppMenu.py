#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import nuke
import logging
from tank_vendor import yaml
import ppnk  # do not remove. IT is used on must commands defined in ppMenu.yml


# loggger
# =======================================================================
format = '%(asctime)s %(levelname)s\t%(module)s.%(funcName)s | %(message)s'
logging.basicConfig(format=format)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def build_menu():
    """
    This function grab all yaml menu file and launch a build menu for each
    """
    menu_location = [
        {"env": "PP_PIPE_NUKE_COMMON_PATH", "suffix": "pp"},
        {"env": "PP_PIPE_NUKE_VERSION_PATH", "suffix": "ppV"},
        {"env": "PP_TD_NUKE_COMMON_PATH", "suffix": "td"},
        {"env": "PP_TD_NUKE_VERSION_PATH", "suffix": "tdV"},
        {"env": "PP_USER_NUKE_COMMON_PATH", "suffix": "us"},
        {"env": "PP_USER_NUKE_VERSION_PATH", "suffix": "usV"}
    ]
    for item in menu_location:
        yaml_path = os.path.join(os.environ.get(item.get("env")), 'ppMenu.yml')
        build_menu_from_yaml(yaml_path, item.get("suffix"))


def build_menu_from_yaml(path, suffix=''):

    if os.path.exists(path):

        with open(path, 'r') as menu_yaml_file:

            try:
                menus_list = yaml.load(menu_yaml_file.read())
            except Exception:
                logger.warning("Build Menu Failed for {0}".format(path))
                return

            if not menus_list:
                logger.info('Yaml file empty.')
                return

            for menu_dict in menus_list:
                menu_name = menu_dict.keys()[0]
                if suffix:
                    beauty_menu_name = "{0} [{1}]".format(menu_dict.keys()[0], suffix)
                else:
                    beauty_menu_name = menu_dict.keys()[0]
                menu_command_dict = menu_dict[menu_name]
                if 'separator' not in menu_name:
                    # hotkey
                    hotkey = str()
                    if 'hotkey' in menu_command_dict.keys():
                        hotkey = menu_command_dict['hotkey']
                    # icon
                    icon_path = str()
                    if 'icon' in menu_command_dict.keys():
                        icon_path = os.path.abspath(
                            os.path.join(
                                os.path.dirname(path),
                                'menu_icons',
                                menu_command_dict['icon']))
                    python_str = 'nuke.menu(\'Nuke\').addCommand("{command_name}", command=\'{command}\', shortcut="{hotkey}", icon="{icon_path}")'.format(
                        command_name=beauty_menu_name,
                        command=menu_command_dict['command'],
                        hotkey=hotkey,
                        icon_path=icon_path)
                    logger.debug(python_str)
                    exec(python_str)
                else:
                    parent_menu_name = '/'.join(menu_name.split('/')[0:-1])
                    menu = nuke.menu('Nuke').findItem(parent_menu_name)
                    menu.addSeparator()
