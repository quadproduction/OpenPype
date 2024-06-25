
from aiohttp.web_response import Response

from openpype.client import get_project

from .utils import _RestApiEndpoint, request_wrapper


class ProjectGetterEndpoint(_RestApiEndpoint):
    
    @request_wrapper
    async def get(self, project_name: str) -> Response:
        project_doc = get_project(project_name=project_name)
        if project_doc:
            return Response(
                status=200,
                body=self.resource.encode(project_doc),
                content_type="application/json"
            )
        return Response(
            status=404,
            reason="Project name {} not found".format(project_name)
        )
