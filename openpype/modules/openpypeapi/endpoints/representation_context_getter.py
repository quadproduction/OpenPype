
from aiohttp.web_response import Response
from aiohttp.web_request import Request

from openpype.pipeline import Anatomy
from openpype.client.mongo import get_project_connection

from .types import RepresentationContext
from .utils import _RestApiEndpoint, check_query_parameters, request_wrapper


class RepresentationContextGetterEndpoint(_RestApiEndpoint):

    @request_wrapper
    async def get(self, request: Request) -> Response:
        check_query_parameters(request, ("representation_path", "project_name"))

        query_params = dict(request.query)
        file_path = query_params["representation_path"]
        project_name = query_params["project_name"]
        anatomy = Anatomy(project_name)
        
        success, rootless_path = anatomy.find_root_template_from_path(file_path)
        if not success:
            raise Exception(f"Given representation path has unknown root for project {project_name}")

        project_coll = get_project_connection(project_name)
        representation_file_doc = project_coll.find_one({
            "type": "representation", "files": {"$elemMatch": {"path": rootless_path}},
        })
        if representation_file_doc is None:
            raise Exception(f"Given path could not be found in {project_name} database")
        
        parent_id = representation_file_doc["parent"]
        parent_representation_doc = project_coll.find_one({ "_id": parent_id })
        if parent_representation_doc is None:
            raise Exception(f"Could not find representation parent in {project_name} database")
        
        representation_dict = self.get_representation_data(representation_file_doc, parent_representation_doc)
        json_response = {
            "type": "representation",
            "data": representation_dict,
        }
        return Response(
            status=200,
            body=self.resource.encode(json_response),
            content_type="application/json"
        )
    
    
    def get_representation_data(self, representation_doc, parent_representation_doc) -> RepresentationContext:
        return {
            "project_name": representation_doc["context"]["project"]["name"],
            "asset_name": representation_doc["context"]["asset"],
            "task_name": representation_doc["context"]["task"]["name"],
            "version_number": representation_doc["context"]["version"],
            "source": parent_representation_doc["data"]["source"],
        }
