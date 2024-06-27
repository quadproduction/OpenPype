
from openpype_modules.webserver.base_routes import RestApiEndpoint


class _RestApiEndpoint(RestApiEndpoint):
    def __init__(self, resource):
        self.resource = resource
        super(_RestApiEndpoint, self).__init__()
