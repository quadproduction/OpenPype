import logging

from openpype.pipeline.plugin_discover import (
    discover,
    register_plugin,
    register_plugin_path,
    deregister_plugin,
    deregister_plugin_path
)


class BuilderAction(list):
    families = []
    representations = []
    extensions = {"*"}
    order = 0
    is_multiple_contexts_compatible = False
    enabled = True

    options = []

    log = logging.getLogger("BuilderAction")
    log.propagate = True

    def __init__(self, name, label, description, icon=None):
        self.name = name
        self.label = label
        self.description = description
        self.icon = icon

    def __repr__(self):
        return "<ActionPlugin name={}>".format(self.name)


def discover_builder_plugins():
    plugins = discover(BuilderAction)
    return plugins


def register_builder_action(plugin):
    register_plugin(BuilderAction, plugin)


def deregister_builder_action(plugin):
    deregister_plugin(BuilderAction, plugin)


def register_builder_action_path(path):
    register_plugin_path(BuilderAction, path)


def deregister_builder_action_path(path):
    deregister_plugin_path(BuilderAction, path)
