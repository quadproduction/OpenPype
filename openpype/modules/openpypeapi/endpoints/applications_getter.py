
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from collections import OrderedDict

from openpype.lib import ApplicationManager

from .utils import _RestApiEndpoint, get_application_dict, request_wrapper


class ApplicationsGetterEndpoint(_RestApiEndpoint):

    @request_wrapper
    async def get(self, request: Request) -> Response:
        application_manager = ApplicationManager()
        applications = OrderedDict(sorted({
            app_code: get_application_dict(app)
            for app_code, app in application_manager.applications.items()
        }.items(), key=lambda x: x[0]))
        return Response(
            status=200,
            body=self.resource.encode(applications),
            content_type="application/json"
        )
