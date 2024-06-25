
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from openpype.pipeline import Anatomy
from openpype.pipeline.workfile import get_workfile_with_version

from .types import Version
from .utils import _RestApiEndpoint
from .utils import (
    check_query_parameters,
    get_dir_path,
    get_extensions,
    get_file_template,
    get_workdir_data,
    request_wrapper,
)


class VersionGetterEndpoint(_RestApiEndpoint):

    @request_wrapper
    async def get(self, request: Request) -> Response:
        check_query_parameters(request, ("project_name", "asset_name", "task_name", "application_name"))
        
        version_number = int(request.match_info["version_number"])
        query_params = dict(request.query)
        application_name = query_params["application_name"]
        task_name = query_params["task_name"]
        project_name = query_params["project_name"]
        asset_name = query_params["asset_name"]
        project_anatomy = Anatomy(project_name)
        
        extensions = get_extensions(application_name)
        dir_path = get_dir_path(project_anatomy, asset_name, task_name, application_name)
        file_template = get_file_template(project_anatomy, application_name, task_name)
        workdir_data = get_workdir_data(project_name, asset_name, task_name)
        workfile_file_path, _ = get_workfile_with_version(dir_path, file_template, workdir_data, extensions, version=version_number, file_path=True)
        if workfile_file_path is None:
            return Response(
                status=422,
                reason="Failed to retrieve workfile path",
            )
        version_dict: Version = {
                "version_number": version_number,
                "path": workfile_file_path,
            }
        return Response(
            status=200,
            body=self.resource.encode(version_dict),
            content_type="application/json"
        )
