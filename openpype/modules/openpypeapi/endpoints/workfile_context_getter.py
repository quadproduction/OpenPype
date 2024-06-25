
from aiohttp.web_response import Response
from aiohttp.web_request import Request

from openpype.pipeline import Anatomy
from openpype.client.mongo import get_project_connection

from .types import WorkfileContext
from .utils import _RestApiEndpoint, check_query_parameters, request_wrapper


class WorkfileContextGetterEndpoint(_RestApiEndpoint):

    @request_wrapper
    async def get(self, request: Request) -> Response:
        check_query_parameters(request, ("workfile_path", "project_name"))

        query_params = dict(request.query)
        file_path = query_params["workfile_path"]
        project_name = query_params["project_name"]
        anatomy = Anatomy(project_name)
        
        success, rootless_path = anatomy.find_root_template_from_path(file_path)
        if not success:
            raise Exception(f"Given workfile path has unknown root for project {project_name}")

        project_coll = get_project_connection(project_name)
        workfile_doc = project_coll.find_one({
            "type": "workfile", "files": {"$in": [rootless_path]},
        })
        if workfile_doc is None:
            raise Exception("Given workfile path could not be found in {project_name} database")

        parent_id = workfile_doc["parent"]
        parent_doc = project_coll.find_one({"_id": parent_id })
        if parent_doc is None:
            raise Exception(f"Workfile parent could not be found in {project_name} database")
        
        workfile_dict = self.get_workfile_data(workfile_doc, parent_doc)

        deps = {
            "type": "workfile",
            "data": workfile_dict,
        }
        return Response(
            status=200,
            body=self.resource.encode(deps),
            content_type="application/json"
        )
        
    def get_workfile_data(self, workfile_doc, workfile_parent_doc) -> WorkfileContext:
        return {
            "asset_name": workfile_parent_doc["name"],
            "task_name": workfile_doc["task_name"],
        }
