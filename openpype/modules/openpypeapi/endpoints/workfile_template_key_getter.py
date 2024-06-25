
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from openpype.pipeline.workfile import get_workfile_template_key

from .utils import _RestApiEndpoint, check_query_parameters, request_wrapper


class WorkfileTemplateKeyGetterEndpoint(_RestApiEndpoint):

    @request_wrapper
    async def get(self, request: Request) -> Response:
        check_query_parameters(request, ("task_type", "application_name"))

        query_params = dict(request.query)

        workfile_template_key: str = get_workfile_template_key(
            task_type=query_params["task_type"],
            host_name=query_params["application_name"],
            project_name=request.match_info["project_name"]
        )
        return Response(
            status=200,
            body=self.resource.encode(workfile_template_key),
            content_type="application/json"
        )

