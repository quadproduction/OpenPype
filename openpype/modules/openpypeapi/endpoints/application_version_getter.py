
from aiohttp.web_response import Response

from openpype.lib import ApplicationManager

from .utils import _RestApiEndpoint, get_application_dict, request_wrapper


class ApplicationVersionGetterEndpoint(_RestApiEndpoint):

    @request_wrapper
    async def get(self, application_name: str, application_version: str) -> Response:
        application_manager = ApplicationManager()
        application_prefix = f"{application_name}/{application_version}"
        app = application_manager.applications[application_prefix]
        return Response(
            status=200,
            body=self.resource.encode(get_application_dict(app)),
            content_type="application/json"
        )
