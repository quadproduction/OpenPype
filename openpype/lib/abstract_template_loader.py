import os
from abc import ABCMeta, abstractmethod

import traceback

import six

from openpype.settings import get_project_settings
from openpype.lib import Anatomy, get_linked_assets, get_loaders_by_name
from openpype.api import PypeLogger as Logger
from openpype.pipeline import legacy_io, load

from functools import reduce

from openpype.lib.build_template_exceptions import (
    TemplateAlreadyImported,
    TemplateLoadingFailed,
    TemplateProfileNotFound,
    TemplateNotFound
)

import logging

log = logging.getLogger(__name__)


def update_representations(entities, entity):
    if entity['context']['subset'] not in entities:
        entities[entity['context']['subset']] = entity
    else:
        current = entities[entity['context']['subset']]
        incomming = entity
        entities[entity['context']['subset']] = max(
            current, incomming,
            key=lambda entity: entity["context"].get("version", -1))

    return entities


def parse_loader_args(loader_args):
    if not loader_args:
        return dict()
    try:
        parsed_args = eval(loader_args)
        if not isinstance(parsed_args, dict):
            return dict()
        else:
            return parsed_args
    except Exception as err:
        print(
            "Error while parsing loader arguments '{}'.\n{}: {}\n\n"
            "Continuing with default arguments. . .".format(
                loader_args,
                err.__class__.__name__,
                err))
        return dict()


@six.add_metaclass(ABCMeta)
class AbstractTemplateLoader:
    """
    Abstraction of Template Loader.
    Properties:
        template_path : property to get current template path
    Methods:
        import_template : Abstract Method. Used to load template,
            depending on current host
        get_template_nodes : Abstract Method. Used to query nodes acting
            as placeholders. Depending on current host
    """

    def __init__(self, placeholder_class):

        self.loaders_by_name = get_loaders_by_name()
        self.current_asset = legacy_io.Session["AVALON_ASSET"]
        self.project_name = legacy_io.Session["AVALON_PROJECT"]
        self.host_name = legacy_io.Session["AVALON_APP"]
        self.task_name = legacy_io.Session["AVALON_TASK"]
        self.placeholder_class = placeholder_class
        self.current_asset_docs = legacy_io.find_one({
            "type": "asset",
            "name": self.current_asset
        })
        self.task_type = (
            self.current_asset_docs
            .get("data", {})
            .get("tasks", {})
            .get(self.task_name, {})
            .get("type")
        )

        self.log = Logger().get_logger("BUILD TEMPLATE")

        self.log.info(
            "BUILDING ASSET FROM TEMPLATE :\n"
            "Starting templated build for {asset} in {project}\n\n"
            "Asset : {asset}\n"
            "Task : {task_name} ({task_type})\n"
            "Host : {host}\n"
            "Project : {project}\n".format(
                asset=self.current_asset,
                host=self.host_name,
                project=self.project_name,
                task_name=self.task_name,
                task_type=self.task_type
            ))
        # Skip if there is no loader
        if not self.loaders_by_name:
            self.log.warning(
                "There is no registered loaders. No assets will be loaded")
            return

    def template_already_imported(self, err_msg):
        """In case template was already loaded.
        Raise the error as a default action.
        Override this method in your template loader implementation
        to manage this case."""
        self.log.error("{}: {}".format(
            err_msg.__class__.__name__,
            err_msg))
        raise TemplateAlreadyImported(err_msg)

    def template_loading_failed(self, err_msg):
        """In case template loading failed
        Raise the error as a default action.
        Override this method in your template loader implementation
        to manage this case.
        """
        self.log.error("{}: {}".format(
            err_msg.__class__.__name__,
            err_msg))
        raise TemplateLoadingFailed(err_msg)

    @property
    def template_path(self):
        """
        Property returning template path. Avoiding setter.
        Getting template path from open pype settings based on current avalon
        session and solving the path variables if needed.
        Returns:
            str: Solved template path
        Raises:
            TemplateProfileNotFound: No profile found from settings for
                current avalon session
            KeyError: Could not solve path because a key does not exists
                in avalon context
            TemplateNotFound: Solved path does not exists on current filesystem
        """
        project_name = self.project_name
        host_name = self.host_name
        task_name = self.task_name
        task_type = self.task_type

        anatomy = Anatomy(project_name)
        project_settings = get_project_settings(project_name)

        build_info = project_settings[host_name]['templated_workfile_build']
        profiles = build_info['profiles']

        for prf in profiles:
            if prf['task_types'] and task_type not in prf['task_types']:
                continue
            if prf['tasks'] and task_name not in prf['tasks']:
                continue
            path = prf['path']
            break
        else:  # IF no template were found (no break happened)
            raise TemplateProfileNotFound(
                "No matching profile found for task '{}' of type '{}' "
                "with host '{}'".format(task_name, task_type, host_name)
            )
        if path is None:
            raise TemplateLoadingFailed(
                "Template path is not set.\n"
                "Path need to be set in {}\\Template Workfile Build "
                "Settings\\Profiles".format(host_name.title()))
        try:
            solved_path = None
            while True:
                solved_path = anatomy.path_remapper(path)
                if solved_path is None:
                    solved_path = path
                if solved_path == path:
                    break
                path = solved_path
        except KeyError as missing_key:
            raise KeyError(
                "Could not solve key '{}' in template path '{}'".format(
                    missing_key, path))
        finally:
            solved_path = os.path.normpath(solved_path)

        if not os.path.exists(solved_path):
            raise TemplateNotFound(
                "Template found in openPype settings for task '{}' with host "
                "'{}' does not exists. (Not found : {})".format(
                    task_name, host_name, solved_path))

        self.log.info("Found template at : '{}'".format(solved_path))

        return solved_path

    def populate_template(self, ignored_ids=None):
        """
        Use template placeholders to load assets and parent them in hierarchy
        Arguments :
            ignored_ids :
        Returns:
            None
        """
        loaders_by_name = self.loaders_by_name
        current_asset = self.current_asset
        linked_assets = [asset['name'] for asset
                         in get_linked_assets(self.current_asset_docs)]

        ignored_ids = ignored_ids or []
        placeholders = self.get_placeholders()
        self.log.debug("Placeholders found in template: {}".format(
            [placeholder.data['node'] for placeholder in placeholders]
        ))
        for placeholder in placeholders:
            self.log.debug("Start to processing placeholder {}".format(
                placeholder.data['node']
            ))
            placeholder_representations = self.get_placeholder_representations(
                placeholder,
                current_asset,
                linked_assets
            )

            if not placeholder_representations:
                self.log.info(
                    "There's no representation for this placeholder: "
                    "{}".format(placeholder.data['node'])
                )
                continue

            for representation in placeholder_representations:
                self.preload(placeholder, loaders_by_name, representation)

                if self.load_data_is_incorrect(
                        placeholder,
                        representation,
                        ignored_ids):
                    continue

                self.log.info(
                    "Loading {}_{} with loader {}\n"
                    "Loader arguments used : {}".format(
                        representation['context']['asset'],
                        representation['context']['subset'],
                        placeholder.loader,
                        placeholder.data['loader_args']))

                try:
                    container = self.load(
                        placeholder, loaders_by_name, representation)
                except Exception:
                    self.load_failed(placeholder, representation)
                else:
                    self.load_succeed(placeholder, container)
                finally:
                    self.postload(placeholder)

    def get_placeholder_representations(
            self, placeholder, current_asset, linked_assets):
        placeholder_db_filters = placeholder.convert_to_db_filters(
            current_asset,
            linked_assets)
        # get representation by assets
        for db_filter in placeholder_db_filters:
            placeholder_representations = list(legacy_io.find(db_filter))
            for representation in reduce(update_representations,
                                         placeholder_representations,
                                         dict()).values():
                yield representation

    def load_data_is_incorrect(
            self, placeholder, last_representation, ignored_ids):
        if not last_representation:
            self.log.warning(placeholder.err_message())
            return True
        if (str(last_representation['_id']) in ignored_ids):
            print("Ignoring : ", last_representation['_id'])
            return True
        return False

    def preload(self, placeholder, loaders_by_name, last_representation):
        pass

    def load(self, placeholder, loaders_by_name, last_representation):
        repre = load.get_representation_context(last_representation)
        return load.load_with_repre_context(
            loaders_by_name[placeholder.loader],
            repre,
            options=parse_loader_args(placeholder.data['loader_args']))

    def load_succeed(self, placeholder, container):
        placeholder.parent_in_hierarchy(container)

    def load_failed(self, placeholder, last_representation):
        self.log.warning("Got error trying to load {}:{} with {}\n\n"
                         "{}".format(last_representation['context']['asset'],
                                     last_representation['context']['subset'],
                                     placeholder.loader,
                                     traceback.format_exc()))

    def postload(self, placeholder):
        placeholder.clean()

    def update_missing_containers(self):
        loaded_containers_ids = self.get_loaded_containers_by_id()
        self.populate_template(ignored_ids=loaded_containers_ids)

    def get_placeholders(self):
        placeholder_class = self.placeholder_class
        placeholders = map(placeholder_class, self.get_template_nodes())
        valid_placeholders = filter(placeholder_class.is_valid, placeholders)
        sorted_placeholders = sorted(valid_placeholders,
                                     key=placeholder_class.order)
        return sorted_placeholders

    @abstractmethod
    def get_loaded_containers_by_id(self):
        """
        Collect already loaded containers for updating scene
        Return:
            dict (string, node): A dictionnary id as key
            and containers as value
        """
        pass

    @abstractmethod
    def import_template(self, template_path):
        """
        Import template in current host
        Args:
            template_path (str): fullpath to current task and
                host's template file
        Return:
            None
        """
        pass

    @abstractmethod
    def get_template_nodes(self):
        """
        Returning a list of nodes acting as host placeholders for
        templating. The data representation is by user.
        AbstractLoadTemplate (and LoadTemplate) won't directly manipulate nodes
        Args :
            None
        Returns:
            list(AnyNode): Solved template path
        """
        pass


@six.add_metaclass(ABCMeta)
class AbstractPlaceholder:
    """Abstraction of placeholders logic
    Properties:
        attributes: A list of mandatory attribute to decribe placeholder
            and assets to load.
        optional_attributes: A list of optional attribute to decribe
            placeholder and assets to load
        loader: Name of linked loader to use while loading assets
        is_context: Is placeholder linked
            to context asset (or to linked assets)
    Methods:
        is_repres_valid:
        loader:
        order:
        is_valid:
        get_data:
        parent_in_hierachy:
    """

    attributes = {'builder_type', 'family', 'representation',
                  'order', 'loader', 'loader_args'}
    optional_attributes = {}

    def __init__(self, node):
        self.get_data(node)

    def order(self):
        """Get placeholder order.
        Order is used to sort them by priority
        Priority is lowset first, highest last
        (ex:
            1: First to load
            100: Last to load)
        Returns:
            Int: Order priority
        """
        return self.data.get('order')

    @property
    def loader(self):
        """Return placeholder loader type
        Returns:
            string: Loader name
        """
        return self.data.get('loader')

    @property
    def is_context(self):
        """Return placeholder type
        context_asset: For loading current asset
        linked_asset: For loading linked assets
        Returns:
            bool: true if placeholder is a context placeholder
        """
        return self.data.get('builder_type') == 'context_asset'

    def is_valid(self):
        """Test validity of placeholder
        i.e.: every attributes exists in placeholder data
        Returns:
            Bool: True if every attributes are a key of data
        """
        if set(self.attributes).issubset(self.data.keys()):
            print("Valid placeholder : {}".format(self.data["node"]))
            return True
        print("Placeholder is not valid : {}".format(self.data["node"]))
        return False

    @abstractmethod
    def parent_in_hierarchy(self, containers):
        """Place container in correct hierarchy
        given by placeholder
        Args:
            containers (String): Container name returned back by
                placeholder's loader.
        """
        pass

    @abstractmethod
    def clean(self):
        """Clean placeholder from hierarchy after loading assets.
        """
        pass

    @abstractmethod
    def convert_to_db_filters(self, current_asset, linked_asset):
        """map current placeholder data as a db filter
        args:
            current_asset (String): Name of current asset in context
            linked asset (list[String]) : Names of assets linked to
                current asset in context
        Returns:
            dict: a dictionnary describing a filter to look for asset in
                a database
        """
        pass

    @abstractmethod
    def get_data(self, node):
        """
        Collect placeholders information.
        Args:
            node (AnyNode): A unique node decided by Placeholder implementation
        """
        pass
