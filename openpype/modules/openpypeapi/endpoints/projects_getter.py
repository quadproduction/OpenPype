
from aiohttp.web_response import Response

from openpype.client import get_projects

from .types import ProjectSummarized
from .utils import _RestApiEndpoint, request_wrapper


class ProjectsGetterEndpoint(_RestApiEndpoint):

    @request_wrapper
    async def get(self) -> Response:
        project_docs = list(get_projects())
        projects = []
        for project_doc in project_docs:
            project_dict: ProjectSummarized = {
                "id": project_doc["_id"],
                "name": project_doc["name"],
                "applications": [app["name"] for app in project_doc["config"]["apps"]]
            }
            projects.append(project_dict)
        return Response(
            status=200,
            body=self.resource.encode(projects),
            content_type="application/json"
        )
