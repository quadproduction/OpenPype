import logging

log = logging.getLogger(__name__)


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


def action_with_repre_context(
    Action, repre_context, namespace=None, name=None, options=None, **kwargs
):
    # Fallback to subset when name is None
    if name is None:
        name = repre_context["subset"]["name"]

    log.info(f"Running {Action.__name__} on {repre_context['asset']['name']}")  # noqa

    action = Action(repre_context)
    return action.process(repre_context)
