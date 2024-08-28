import os
import re
from enum import Enum
from pathlib import Path

from openpype.modules import OpenPypeModule


class RestAPIMethod(Enum):
    UNDEFINED = "NULL"
    GET = "GET"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class RestAPIRoute:
    _regex_validate_route = r"[A-Za-z-/]+"

    def __init__(self, method, path, handler):
        # Ensure arguments validity
        if not isinstance(method, RestAPIMethod):
            raise TypeError("RestAPIRoute: 'method' argument need to be of type RestAPIRoute")
        if not isinstance(path, (str, Path)):
            raise TypeError("RestAPIRoute: 'path' argument need to be of type str or pathlib.Path")
        if not re.fullmatch(RestAPIRoute._regex_validate_route, path):
            raise ValueError("RestAPIRoute: 'path' argument can only contains non accentuated letters, "
                             "dashes '-' and slashes '/'")
        if isinstance(path, Path):
            # Convert to a string since the server manager take string paths
            path = str(path)
        if not callable(handler):
            raise TypeError("RestAPIRoute: 'handler' argument need to be a valid callable object")

        self.method = method
        self.path = path
        self.handler = handler


class RestAPIModule(OpenPypeModule):
    name = "rest_api"

    _request_prefix = "api"

    def __init__(self, manager, settings):
        self._server_manager = None
        self._module_settings = None
        self._available_routes: [RestAPIRoute] = []

        super().__init__(manager, settings)

    def _retrieve_routes(self):
        dir_path = Path(os.path.abspath(os.path.dirname(__file__)))
        for child_path in dir_path.iterdir():


    def initialize(self, modules_settings):
        self._module_settings = modules_settings

        self._retrieve_routes()

    def webserver_initialization(self, server_manager):
        """Register routes"""
        self._server_manager = server_manager

        route: RestAPIRoute
        for route in self._available_routes:
            self._server_manager.add_route(
                method=route.method,
                path=route.path,
                handler=route.handler
            )
