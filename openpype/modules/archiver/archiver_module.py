import os

from openpype.modules import OpenPypeModule, ITrayService


class ArchiverModule(OpenPypeModule, ITrayService):
    name = "archiver"
    label = "Archiver"


    def initialize(self, modules_settings):
        # This module is always enabled
        self.enabled = True

        # Tray attributes
        self.rest_api_obj = None


    def tray_init(self):
        return

    def tray_start(self, *_a, **_kw):
        return

    def tray_exit(self, *_a, **_kw):
        return

    # Webserver module implementation
    def webserver_initialization(self, server_manager):
        """Add routes for webserver."""
        if self.tray_initialized:
            from .rest_api import ArchiverRestApiResource
            self.rest_api_obj = ArchiverRestApiResource(server_manager)
