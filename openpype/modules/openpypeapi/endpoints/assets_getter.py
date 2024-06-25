
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from typing import List

from openpype.client import get_assets

from .types import AssetSummarized
from .utils import _RestApiEndpoint, check_query_parameters, request_wrapper


class AssetsGetterEndpoint(_RestApiEndpoint):

    @request_wrapper
    async def get(self, request: Request) -> Response:
        
        check_query_parameters(request, ("project_name", ))

        query_params = dict(request.query)
        project_name = query_params["project_name"]
        assets: List[AssetSummarized] = [
            {
                "id": asset["_id"],
                "name": asset["name"],
                "entity_type": asset["data"]["entityType"] if "entityType" in asset["data"] else None,
                "ftrack_id": asset["data"]["ftrackId"] if "ftrackId" in asset["data"] else None,
                "hierarchy": "/".join(asset["data"]["parents"]),
            } for asset in get_assets(project_name=project_name)
        ]
        return Response(
                status=200,
                body=self.resource.encode(assets),
                content_type="application/json"
            )
