
from aiohttp.web_response import Response
from aiohttp.web_request import Request

from openpype.client import get_asset_by_name

from .utils import _RestApiEndpoint, check_query_parameters, request_wrapper


class AssetGetterEndpoint(_RestApiEndpoint):

    @request_wrapper
    async def get(self, request: Request) -> Response:
        check_query_parameters(request, ("project_name", ))
        
        query_params = dict(request.query)
        project_name = query_params["project_name"]
        asset_name = request.match_info["asset_name"]

        asset = get_asset_by_name(project_name, asset_name)
        if asset is None:
            raise Exception(f"Unknown asset named `{asset_name}` in project {project_name}")
            
        return Response(
            status=200,
            body=self.resource.encode(asset),
            content_type="application/json"
        )
