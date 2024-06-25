

from aiohttp.web_request import Request
from aiohttp.web_response import Response
from typing import List

from openpype.pipeline import Anatomy
from openpype.pipeline.workfile import get_workfiles

from .utils import _RestApiEndpoint
from .utils import (
    check_query_parameters,
    get_dir_path,
    get_extensions,
    get_file_template,
    get_workdir_data,
    request_wrapper,
)


class VersionsGetterEndpoint(_RestApiEndpoint):

    @request_wrapper
    async def get(self, request: Request) -> Response:
        check_query_parameters(request, ("project_name", "task_name", "application_name"))

        query_params = dict(request.query)
        project_name = query_params["project_name"]
        application_name = query_params["application_name"]
        task_name = query_params["task_name"]
        asset_name = request.match_info["asset_name"]

        project_anatomy = Anatomy(project_name)
        extensions = get_extensions(application_name)
        dir_path = get_dir_path(project_anatomy, asset_name, task_name, application_name)
        file_template = get_file_template(project_anatomy, application_name, task_name)
        workdir_data = get_workdir_data(project_name, asset_name, task_name)
        workfile_file_paths: List[str] = get_workfiles(dir_path, file_template, workdir_data, extensions, file_path=True)

        return Response(
            status=200,
            body=self.resource.encode(workfile_file_paths),
            content_type="application/json"
        )
