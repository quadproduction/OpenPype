def get_actions_by_name():
    from .action_plugin import discover_builder_plugins

    actions_by_name = {}
    for action in discover_builder_plugins():
        action_name = action.__name__
        if action_name in actions_by_name:
            raise KeyError(
                "Duplicated loader name {} !".format(action_name)
            )
        actions_by_name[action_name] = action
    return actions_by_name
