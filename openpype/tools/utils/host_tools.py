"""Single access point to all tools usable in hosts.

It is possible to create `HostToolsHelper` in host implementation or
use singleton approach with global functions (using helper anyway).
"""
import os

import pyblish.api

from openpype import AYON_SERVER_ENABLED
from openpype.host import IWorkfileHost, ILoadHost
from openpype.lib import Logger
from openpype.settings import get_project_settings
from openpype.pipeline import (
    registered_host,
    get_current_host_name,
    get_current_asset_name,
    get_current_project_name
)

from .lib import qt_app_context


class HostToolsHelper:
    """Create and cache tool windows in memory.

    Almost all methods expect parent widget but the parent is used only on
    first tool creation.

    Class may also contain tools that are available only for one or few hosts.
    """

    def __init__(self, parent=None):
        self._log = None
        # Global parent for all tools (may and may not be set)
        self._parent = parent

        # Prepare attributes for all tools
        self._workfiles_tool = None
        self._loader_tool = None
        self._creator_tool = None
        self._publisher_tool = None
        self._subset_manager_tool = None
        self._scene_inventory_tool = None
        self._library_loader_tool = None
        self._experimental_tools_dialog = None

    @property
    def log(self):
        if self._log is None:
            self._log = Logger.get_logger(self.__class__.__name__)
        return self._log

    def _init_ayon_workfiles_tool(self, parent):
        from openpype.tools.ayon_workfiles.widgets import WorkfilesToolWindow

        workfiles_window = WorkfilesToolWindow(parent=parent)
        self._workfiles_tool = workfiles_window

    def _init_openpype_workfiles_tool(self, parent):
        from openpype.tools.workfiles.app import Window

        # Host validation
        host = registered_host()
        IWorkfileHost.validate_workfile_methods(host)

        workfiles_window = Window(parent=parent)
        self._workfiles_tool = workfiles_window

    def get_workfiles_tool(self, parent, on_top=None):
        """Create, cache and return workfiles tool window."""
        if self._workfiles_tool is None:
            if AYON_SERVER_ENABLED:
                self._init_ayon_workfiles_tool(parent)
            else:
                self._init_openpype_workfiles_tool(parent)

        self._workfiles_tool.ensure_visible(on_top=on_top)
        return self._workfiles_tool

    def show_workfiles(
        self, parent=None, use_context=None, save=None, on_top=None
    ):
        """Workfiles tool for changing context and saving workfiles."""

        with qt_app_context():
            workfiles_tool = self.get_workfiles_tool(parent)
            workfiles_tool.ensure_visible(use_context, save, on_top)

    def get_loader_tool(self, parent, on_top=None):
        """Create, cache and return loader tool window."""
        if self._loader_tool is None:
            from openpype.tools.loader import LoaderWindow

            host = registered_host()
            ILoadHost.validate_load_methods(host)

            loader_window = LoaderWindow(
                parent=parent or self._parent,
                on_top=on_top
            )
            self._loader_tool = loader_window
        return self._loader_tool

    def show_loader(self, parent=None, use_context=None, on_top=None):
        """Loader tool for loading representations."""
        with qt_app_context():
            loader_tool = self.get_loader_tool(parent, on_top)

            loader_tool.show()
            loader_tool.raise_()
            loader_tool.activateWindow()
            loader_tool.showNormal()

            if use_context is None:
                use_context = False

            if use_context:
                context = {"asset": get_current_asset_name()}
                loader_tool.set_context(context, refresh=True)
            else:
                loader_tool.refresh()

    def get_creator_tool(self, parent, on_top=None):
        """Create, cache and return creator tool window."""
        if self._creator_tool is None:
            from openpype.tools.creator import CreatorWindow

            creator_window = CreatorWindow(
                parent=parent or self._parent,
                on_top=on_top
            )
            self._creator_tool = creator_window

        return self._creator_tool

    def show_creator(self, parent=None, on_top=None):
        """Show tool to create new instantes for publishing."""
        with qt_app_context():
            creator_tool = self.get_creator_tool(parent, on_top)
            creator_tool.refresh()
            creator_tool.show()

            # Pull window to the front.
            creator_tool.raise_()
            creator_tool.activateWindow()

    def get_subset_manager_tool(self, parent, on_top=None):
        """Create, cache and return subset manager tool window."""
        if self._subset_manager_tool is None:
            from openpype.tools.subsetmanager import SubsetManagerWindow

            subset_manager_window = SubsetManagerWindow(
                parent=parent or self._parent,
                on_top=on_top
            )
            self._subset_manager_tool = subset_manager_window

        return self._subset_manager_tool

    def show_subset_manager(self, parent=None, on_top=None):
        """Show tool display/remove existing created instances."""
        with qt_app_context():
            subset_manager_tool = self.get_subset_manager_tool(parent, on_top)
            subset_manager_tool.show()

            # Pull window to the front.
            subset_manager_tool.raise_()
            subset_manager_tool.activateWindow()

    def get_scene_inventory_tool(self, parent, on_top=None):
        """Create, cache and return scene inventory tool window."""
        if self._scene_inventory_tool is None:
            from openpype.tools.sceneinventory import SceneInventoryWindow

            host = registered_host()
            ILoadHost.validate_load_methods(host)

            scene_inventory_window = SceneInventoryWindow(
                parent=parent or self._parent,
                on_top=on_top
            )
            self._scene_inventory_tool = scene_inventory_window

        return self._scene_inventory_tool

    def show_scene_inventory(self, parent=None, on_top=None):
        """Show tool maintain loaded containers."""
        with qt_app_context():
            scene_inventory_tool = self.get_scene_inventory_tool(parent, on_top)
            scene_inventory_tool.show()
            scene_inventory_tool.refresh()

            # Pull window to the front.
            scene_inventory_tool.raise_()
            scene_inventory_tool.activateWindow()
            scene_inventory_tool.showNormal()

    def get_library_loader_tool(self, parent, on_top=None):
        """Create, cache and return library loader tool window."""
        if self._library_loader_tool is None:
            from openpype.tools.libraryloader import LibraryLoaderWindow

            library_window = LibraryLoaderWindow(
                parent=parent or self._parent,
                on_top=on_top
            )
            self._library_loader_tool = library_window

        return self._library_loader_tool

    def show_library_loader(self, parent=None, on_top=None):
        """Loader tool for loading representations from library project."""
        with qt_app_context():
            library_loader_tool = self.get_library_loader_tool(parent, on_top)
            library_loader_tool.show()
            library_loader_tool.raise_()
            library_loader_tool.activateWindow()
            library_loader_tool.showNormal()
            library_loader_tool.refresh()

    def show_publish(self, parent=None, on_top=None):
        """Try showing the most desirable publish GUI

        This function cycles through the currently registered
        graphical user interfaces, if any, and presents it to
        the user.
        """

        #TODO: propagate on_top setting

        pyblish_show = self._discover_pyblish_gui()
        return pyblish_show(parent)

    def _discover_pyblish_gui(self):
        """Return the most desirable of the currently registered GUIs"""
        # Prefer last registered
        guis = list(reversed(pyblish.api.registered_guis()))
        for gui in guis:
            try:
                gui = __import__(gui).show
            except (ImportError, AttributeError):
                continue
            else:
                return gui

        raise ImportError("No Pyblish GUI found")

    def get_experimental_tools_dialog(self, parent=None, on_top=None):
        """Dialog of experimental tools.

        For some hosts it is not easy to modify menu of tools. For
        those cases was added experimental tools dialog which is Qt based
        and can dynamically filled by experimental tools so
        host need only single "Experimental tools" button to see them.

        Dialog can be also empty with a message that there are not available
        experimental tools.
        """
        if self._experimental_tools_dialog is None:
            from openpype.tools.experimental_tools import (
                ExperimentalToolsDialog
            )

            self._experimental_tools_dialog = ExperimentalToolsDialog(
                parent=parent,
                on_top=on_top
            )
        return self._experimental_tools_dialog

    def show_experimental_tools_dialog(self, parent=None, on_top=None):
        """Show dialog with experimental tools."""
        with qt_app_context():
            dialog = self.get_experimental_tools_dialog(parent, on_top)

            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
            dialog.showNormal()

    def get_publisher_tool(self, parent=None, controller=None, on_top=None):
        """Create, cache and return publisher window."""

        if self._publisher_tool is None:
            from openpype.tools.publisher.window import PublisherWindow

            host = registered_host()
            ILoadHost.validate_load_methods(host)

            publisher_window = PublisherWindow(
                controller=controller, parent=parent or self._parent,
                on_top=on_top
            )
            self._publisher_tool = publisher_window

        return self._publisher_tool

    def show_publisher_tool(self, parent=None, controller=None, tab=None, on_top=None):
        with qt_app_context():
            window = self.get_publisher_tool(parent, controller, on_top)
            if tab:
                window.set_current_tab(tab)
            window.make_sure_is_visible()

    def get_tool_by_name(self, tool_name, parent=None, *args, **kwargs):
        """Show tool by it's name.

        This is helper for
        """

        self.set_windows_custom_settings(kwargs)

        if tool_name == "workfiles":
            return self.get_workfiles_tool(parent, *args, **kwargs)

        elif tool_name == "loader":
            return self.get_loader_tool(parent, *args, **kwargs)

        elif tool_name == "libraryloader":
            return self.get_library_loader_tool(parent, *args, **kwargs)

        elif tool_name == "creator":
            return self.get_creator_tool(parent, *args, **kwargs)

        elif tool_name == "subsetmanager":
            return self.get_subset_manager_tool(parent, *args, **kwargs)

        elif tool_name == "sceneinventory":
            return self.get_scene_inventory_tool(parent, *args, **kwargs)

        elif tool_name == "publish":
            self.log.info("Can't return publish tool window.")

        # "new" publisher
        elif tool_name == "publisher":
            return self.get_publisher_tool(parent, *args, **kwargs)

        elif tool_name == "experimental_tools":
            return self.get_experimental_tools_dialog(parent, *args, **kwargs)

        else:
            self.log.warning(
                "Can't show unknown tool name: \"{}\"".format(tool_name)
            )

    def show_tool_by_name(self, tool_name, parent=None, *args, **kwargs):
        """Show tool by it's name.

        This is helper for
        """

        self.set_windows_custom_settings(kwargs)

        if tool_name == "workfiles":
            self.show_workfiles(parent, *args, **kwargs)

        elif tool_name == "loader":
            self.show_loader(parent, *args, **kwargs)

        elif tool_name == "libraryloader":
            self.show_library_loader(parent, *args, **kwargs)

        elif tool_name == "creator":
            self.show_creator(parent, *args, **kwargs)

        elif tool_name == "subsetmanager":
            self.show_subset_manager(parent, *args, **kwargs)

        elif tool_name == "sceneinventory":
            self.show_scene_inventory(parent, *args, **kwargs)

        elif tool_name == "publish":
            self.show_publish(parent, *args, **kwargs)

        elif tool_name == "publisher":
            self.show_publisher_tool(parent, *args, **kwargs)

        elif tool_name == "experimental_tools":
            self.show_experimental_tools_dialog(parent, *args, **kwargs)

        else:
            self.log.warning(
                "Can't show unknown tool name: \"{}\"".format(tool_name)
            )

    def set_windows_custom_settings(self, kwargs):
        settings = get_project_settings(get_current_project_name())
        custom_windows_settings = settings.get('fix_custom_settings', []).get('general', []).get('windows_on_top', None)
        if not custom_windows_settings:
            self.log.warning("Can't retrieve custom windows settings. Default OpenPype's values will be applied.")
            return

        current_host_name = get_current_host_name()
        on_top_setting = self._get_host_on_top_settings(current_host_name, custom_windows_settings)
        if on_top_setting is None:
            self.log.info(f"Can not retrieve `on_top` value for host {current_host_name}. Default value will be applied.")
            on_top_setting = custom_windows_settings.get('default', None)

        kwargs['on_top'] = on_top_setting
        self.log.info(f"Windows property named `on_top` overriden with value ({on_top_setting}).")

    def _get_host_on_top_settings(self, current_host_name, custom_windows_settings):
        for on_top_set in custom_windows_settings.get('per_hosts', []):
            if current_host_name in on_top_set.get('hosts', []):
                return on_top_set.get('on_top', None)

        return None


class _SingletonPoint:
    """Singleton access to host tools.

    Some hosts don't have ability to create 'HostToolsHelper' object anc can
    only register function callbacks. For those cases is created this singleton
    point where 'HostToolsHelper' is created "in shared memory".
    """
    helper = None

    @classmethod
    def _create_helper(cls):
        if cls.helper is None:
            cls.helper = HostToolsHelper()

    @classmethod
    def show_tool_by_name(cls, tool_name, parent=None, *args, **kwargs):
        cls._create_helper()
        cls.helper.show_tool_by_name(tool_name, parent, *args, **kwargs)

    @classmethod
    def get_tool_by_name(cls, tool_name, parent=None, *args, **kwargs):
        cls._create_helper()
        return cls.helper.get_tool_by_name(tool_name, parent, *args, **kwargs)


# Function callbacks using singleton access point
def get_tool_by_name(tool_name, parent=None, *args, **kwargs):
    return _SingletonPoint.get_tool_by_name(tool_name, parent, *args, **kwargs)


def show_tool_by_name(tool_name, parent=None, *args, **kwargs):
    _SingletonPoint.show_tool_by_name(tool_name, parent, *args, **kwargs)


def show_workfiles(*args, **kwargs):
    _SingletonPoint.show_tool_by_name(
        "workfiles", *args, **kwargs
    )


def show_loader(parent=None, use_context=None):
    _SingletonPoint.show_tool_by_name(
        "loader", parent, use_context=use_context
    )


def show_library_loader(parent=None):
    _SingletonPoint.show_tool_by_name("libraryloader", parent)


def show_creator(parent=None):
    _SingletonPoint.show_tool_by_name("creator", parent)


def show_subset_manager(parent=None):
    _SingletonPoint.show_tool_by_name("subsetmanager", parent)


def show_scene_inventory(parent=None):
    _SingletonPoint.show_tool_by_name("sceneinventory", parent)


def show_publish(parent=None):
    _SingletonPoint.show_tool_by_name("publish", parent)


def show_publisher(parent=None, **kwargs):
    _SingletonPoint.show_tool_by_name("publisher", parent, **kwargs)


def show_experimental_tools_dialog(parent=None):
    _SingletonPoint.show_tool_by_name("experimental_tools", parent)


def get_pyblish_icon():
    pyblish_dir = os.path.abspath(os.path.dirname(pyblish.api.__file__))
    icon_path = os.path.join(pyblish_dir, "icons", "logo-32x32.svg")
    if os.path.exists(icon_path):
        return icon_path
    return None
