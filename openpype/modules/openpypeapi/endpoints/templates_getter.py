
from aiohttp.web_response import Response

from openpype.client import get_project

from .utils import _RestApiEndpoint, request_wrapper


class TemplatesGetterEndpoint(_RestApiEndpoint):

    @request_wrapper
    async def get(self, project_name) -> Response:
        project_doc = get_project(project_name=project_name)
        templates = project_doc["config"]["templates"]
        return Response(
            status=200,
            body=self.resource.encode(templates),
            content_type="application/json"
        )
