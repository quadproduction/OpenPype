import json
import datetime
from collections import OrderedDict

from bson.objectid import ObjectId

from aiohttp.web_response import Response
from aiohttp.web_request import Request

from openpype.client import (
    get_project,
    get_projects,
    get_assets,
    get_asset_by_name,
)

from openpype.pipeline.workfile import (
    get_workfile_template_key,
    get_workfile_with_version,
    get_workfiles,
)

from openpype.modules import ModulesManager
from openpype.lib import ApplicationManager
from openpype.lib.applications import Application
from openpype.pipeline import Anatomy
from openpype_modules.webserver.base_routes import RestApiEndpoint


class _RestApiEndpoint(RestApiEndpoint):
    def __init__(self, resource):
        self.resource = resource
        super(_RestApiEndpoint, self).__init__()


def get_extensions(host_name: str):
    """
    Get all extensions for host with given name.

    Returns:
        List[str]: Extensions used for workfiles with dot.
    """
    module_manager = ModulesManager()
    host_module = module_manager.get_host_module(host_name)
    extensions = host_module.get_workfile_extensions()
    return extensions

def get_workdir_data(project_name: str, asset_name: str, task_name: str):
    """
    Get a dictionary holding data for given task.
    This dictionary is used internally by openpype to fill templates
    with actual data.

    Returns:
        Dict[str, Any]: Dictionary holding task data
    """
    asset = get_asset_by_name(project_name, asset_name)
    workdir_data = {
        'project': {'name': project_name},
        'hierarchy': "/".join(asset["data"]["parents"]),
        'asset': asset["name"],
        'task': {'name': task_name},
    }
    return workdir_data

def get_dir_path(
        project_anatomy: Anatomy, asset_name: str, task_name: str, host_name: str
    ) -> str:
    """
    Get path to directory on the file system
    """
    workfile_template_key = get_workfile_template_key(
        task_type=task_name,
        host_name=host_name,
        project_name=project_anatomy.project_name
    )
    workdir_data = get_workdir_data(project_anatomy.project_name, asset_name, task_name)
    dir_template = project_anatomy.templates_obj[workfile_template_key]["folder"]
    dir_path = dir_template.format_strict(workdir_data)
    return dir_path

def get_file_template(project_anatomy: Anatomy, host_name: str, task_name: str) -> str:
    """
    Get template for file name (as defined in project settings)
    """
    workfile_template_key = get_workfile_template_key(
        task_type=task_name,
        host_name=host_name,
        project_name=project_anatomy.project_name
    )
    file_template = project_anatomy.templates[workfile_template_key]["file"]
    return file_template

def get_application_dict(application: Application):
    """
    Get dictionary from given application instance

    Returns:
        Dict[str, Any]: Dictionary holding application info
    """
    return {
        "full_name": application.full_name, 
        "full_label": application.full_label,
        "executable_paths": [app_exec.executable_path for app_exec in application.executables],
        "label": application.label,
        "name": application.name,
        }

def check_query_parameters(request: Request, needed_query_parameters):
    """
    Args:
        request (Request): Incoming request
        needed_query_parameters (Tuple[str]): Parameters
    Raises:
        Exception: If given parameters are not found in request query
    """
    query_params = dict(request.query)
    for needed_query_parameter in needed_query_parameters:
        if needed_query_parameter not in query_params:
            raise Exception(f"Missing query parameter `{needed_query_parameter}`")



class ProjectsGetterEndpoint(_RestApiEndpoint):
    async def get(self) -> Response:
        project_docs = list(get_projects())
        projects = []
        for project_doc in project_docs:
            projects.append({
                "id": project_doc["_id"],
                "name": project_doc["name"],
            })
        return Response(
            status=200,
            body=self.resource.encode(projects),
            content_type="application/json"
        )


class ProjectGetterEndpoint(_RestApiEndpoint):
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

class AssetsGetterEndpoint(_RestApiEndpoint):
    async def get(self, request: Request) -> Response:
        try:
            check_query_parameters(request, ("project_name", ))
        except Exception as exc:
            return Response(
                status=422,
                reason=str(exc)
            )
        query_params = dict(request.query)
        project_name = query_params["project_name"]
        assets = [
            {
                "id": asset["_id"],
                "name": asset["name"],
                "entity_type": asset["data"]["entityType"] if "entityType" in asset["data"] else None,
                "ftrack_id": asset["data"]["ftrackId"] if "ftrackId" in asset["data"] else None,
                "hierarchy": "/".join(asset["data"]["parents"]),
            }
            for asset in get_assets(project_name=project_name)
        ]
        return Response(
                status=200,
                body=self.resource.encode(assets),
                content_type="application/json"
            )

class VersionGetterEndpoint(_RestApiEndpoint):
    async def get(self, request: Request) -> Response:
        try:
            check_query_parameters(request, ("project_name", "asset_name", "task_name", "host_name"))
        except Exception as exc:
            return Response(
                status=422,
                reason=str(exc)
            )
        version_number = int(request.match_info["version_number"])
        query_params = dict(request.query)
        host_name = query_params["host_name"]
        task_name = query_params["task_name"]
        project_name = query_params["project_name"]
        asset_name = query_params["asset_name"]
        project_anatomy = Anatomy(project_name)

        dir_path = get_dir_path(project_anatomy, asset_name, task_name, host_name)
        file_template = get_file_template(project_anatomy, host_name, task_name)
        extensions = get_extensions(host_name)
        workdir_data = get_workdir_data(project_name, asset_name, task_name)

        workfile_file_path, _ = get_workfile_with_version(dir_path, file_template, workdir_data, extensions, version=version_number, file_path=True)
        if workfile_file_path is None:
            return Response(
                status=422,
                reason=f"Couldn't find working file for given parameters",
            )

        return Response(
            status=200,
            body=self.resource.encode({
                "version_number": version_number,
                "path": workfile_file_path
            }),
            content_type="application/json"
        )


class VersionsGetterEndpoint(_RestApiEndpoint):
    async def get(self, request: Request) -> Response:
        try:
            check_query_parameters(request, ("project_name", "task_name", "host_name"))
        except Exception as exc:
            return Response(
                status=422,
                reason=str(exc)
            )
        query_params = dict(request.query)
        project_name = query_params["project_name"]
        host_name = query_params["host_name"]
        task_name = query_params["task_name"]
        project_anatomy = Anatomy(project_name)
        asset_name = request.match_info["asset_name"]

        dir_path = get_dir_path(project_anatomy, asset_name, task_name, host_name)
        file_template = get_file_template(project_anatomy, host_name, task_name)
        extensions = get_extensions(host_name)
        workdir_data = get_workdir_data(project_name, asset_name, task_name)

        workfile_file_paths = get_workfiles(dir_path, file_template, workdir_data, extensions, file_path=True)

        return Response(
            status=200,
            body=self.resource.encode(workfile_file_paths),
            content_type="application/json"
        )


class TemplatesGetterEndpoint(_RestApiEndpoint):
    async def get(self, project_name) -> Response:
        project_doc = get_project(project_name=project_name)
        templates = project_doc["config"]["templates"]
        return Response(
            status=200,
            body=self.resource.encode(templates),
            content_type="application/json"
        )


class WorkfileTemplateKeyGetterEndpoint(_RestApiEndpoint):
    async def get(self, request: Request) -> Response:
        try:
            check_query_parameters(request, ("task_type", "host_name"))
        except Exception as exc:
            return Response(
                status=422,
                reason=str(exc)
            )
        query_params = dict(request.query)

        workfile_template_key = get_workfile_template_key(
            task_type=query_params["task_type"],
            host_name=query_params["host_name"],
            project_name=request.match_info["project_name"]
        )
        return Response(
            status=200,
            body=self.resource.encode(workfile_template_key),
            content_type="application/json"
        )


class ApplicationsGetterEndpoint(_RestApiEndpoint):
    async def get(self, request: Request) -> Response:
        application_manager = ApplicationManager()
        applications = OrderedDict(sorted({
            app_code: get_application_dict(app) 
            for app_code, app in application_manager.applications.items() 
        }.items(), key=lambda x: x[0]))
        return Response(
            status=200,
            body=self.resource.encode(applications),
            content_type="application/json"
        )


class ApplicationGetterEndpoint(_RestApiEndpoint):
    async def get(self, application_name: str) -> Response:
        application_manager = ApplicationManager()
        application_prefix = f"{application_name}/"
        applications = OrderedDict(sorted({
            app_code: get_application_dict(app) 
            for app_code, app in application_manager.applications.items() 
            if app_code.startswith(application_prefix)
        }.items(), key=lambda x: x[0]))
        return Response(
            status=200,
            body=self.resource.encode(applications),
            content_type="application/json"
        )


class AssetGetterEndpoint(_RestApiEndpoint):
    async def get(self, request: Request) -> Response:
        try:
            check_query_parameters(request, ("project_name", ))
        except Exception as exc:
            return Response(
                status=422,
                reason=str(exc)
            )
        query_params = dict(request.query)
        project_name = query_params["project_name"]
        asset_name = request.match_info["asset_name"]

        asset = get_asset_by_name(project_name, asset_name)
        if asset is None:
            return Response(
                status=422,
                reason=f"Unknown asset named `{asset_name}` in project {project_name}",
            )
        return Response(
            status=200,
            body=self.resource.encode(asset),
            content_type="application/json"
        )

class APIStatusEndpoint(_RestApiEndpoint):
    async def head(self, request: Request):
        return Response()


class ArchiverRestApiResource:
    def __init__(self, server_manager):
        self.server_manager = server_manager

        self.prefix = "/archiver"

        self.endpoint_defs = (
            (
                "HEAD",
                "/api",
                APIStatusEndpoint(self)
            ),
            (
                "GET",
                "/projects",
                ProjectsGetterEndpoint(self)
            ),
            (
                "GET",
                "/projects/{project_name}",
                ProjectGetterEndpoint(self)
            ),
            (
                "GET",
                "/projects/{project_name}/templates",
                TemplatesGetterEndpoint(self)
            ),
            (
                "GET",
                "/projects/{project_name}/workfile-template-key",
                WorkfileTemplateKeyGetterEndpoint(self)
            ),
            (
                "GET",
                "/assets",
                AssetsGetterEndpoint(self)
            ),
            (
                "GET",
                "/assets/{asset_name}",
                AssetGetterEndpoint(self)
            ),
            (
                "GET",
                "/assets/{asset_name}/versions",
                VersionsGetterEndpoint(self)
            ),
            (
                "GET",
                "/versions/{version_number}/path",
                VersionGetterEndpoint(self)
            ),
            (
                "GET",
                "/applications",
                ApplicationsGetterEndpoint(self)
            ),
            (
                "GET",
                "/applications/{application_name}",
                ApplicationGetterEndpoint(self)
            ),
        )

        self.register()

    def register(self):
        for methods, url, endpoint in self.endpoint_defs:
            final_url = self.prefix + url
            self.server_manager.add_route(
                methods, final_url, endpoint.dispatch
            )

    @staticmethod
    def json_dump_handler(value):
        if isinstance(value, datetime.datetime):
            return value.isoformat()
        if isinstance(value, ObjectId):
            return str(value)
        raise TypeError(value)

    @classmethod
    def encode(cls, data):
        return json.dumps(
            data,
            indent=4,
            default=cls.json_dump_handler
        ).encode("utf-8")
