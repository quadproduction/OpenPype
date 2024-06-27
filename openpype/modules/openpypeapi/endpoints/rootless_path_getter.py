
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from openpype.pipeline import Anatomy

from .utils import _RestApiEndpoint
from .utils import check_query_parameters


class RootlessPathEndpoint(_RestApiEndpoint):
    async def get(self, request: Request) -> Response:
        check_query_parameters(request, ("path",))
        
        project_name = request.match_info["project_name"]
        query_params = dict(request.query)
        _path = query_params["path"]
        anatomy = Anatomy(project_name)
        success, rootless_path = anatomy.find_root_template_from_path(_path)
        if not success:
            raise Exception(f"Given workfile path has unknown root for project {project_name}")
        
        return Response(
            status=200,
            body=self.resource.encode({"rootless_path": rootless_path}),
            content_type="application/json"
        )
