import logging

from openpype.pipeline.plugin_discover import (
    discover,
    register_plugin,
    register_plugin_path,
    deregister_plugin,
    deregister_plugin_path
)


class ActionPlugin(list):
    families = []
    representations = []
    extensions = {"*"}
    order = 0
    is_multiple_contexts_compatible = False
    enabled = True

    options = []

    log = logging.getLogger("SubsetLoader")
    log.propagate = True

    def __init__(self, name, label, description, icon=None):
        self.name = name
        self.label = label
        self.description = description
        self.icon = icon

    def __repr__(self):
        return "<ActionPlugin name={}>".format(self.name)


def discover_action_plugins(project_name=None):
    from openpype.lib import Logger

    log = Logger.get_logger("ActionDiscover")
    plugins = discover(ActionPlugin)
    for plugin in plugins:
        log.info("PLUGIN: {}".format(plugin))
    return plugins


def register_action_plugin(plugin):
    register_plugin(ActionPlugin, plugin)


def deregister_action_plugin(plugin):
    deregister_plugin(ActionPlugin, plugin)


def register_action_plugin_path(path):
    register_plugin_path(ActionPlugin, path)


def deregister_action_plugin_path(path):
    deregister_plugin_path(ActionPlugin, path)
