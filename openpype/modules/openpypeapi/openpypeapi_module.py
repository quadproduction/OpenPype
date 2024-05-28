
from openpype.modules import OpenPypeModule


class OpenPypeAPIModule(OpenPypeModule):
    name = "openpypeapi"


    def initialize(self, modules_settings):
        # This module is always enabled
        self.enabled = True
        self.rest_api_ref = None

    # Webserver module implementation
    def webserver_initialization(self, server_manager):
        """Add routes for webserver."""
        from .rest_api import OpenPypeAPIRestApiResource
        self.rest_api_ref = OpenPypeAPIRestApiResource(server_manager)
