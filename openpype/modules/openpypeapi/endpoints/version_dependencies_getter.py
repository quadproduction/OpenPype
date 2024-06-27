
import json
import subprocess
from itertools import chain
from pathlib import Path
from typing import List
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from bson.objectid import ObjectId

from openpype.lib import ApplicationManager
from openpype.pipeline import Anatomy
from openpype.pipeline.workfile import get_workfile_with_version
from openpype.client import (
    get_asset_by_name, 
    get_subset_by_name, 
    get_version_by_name, 
    get_version_by_id, 
)
from openpype.client.mongo import get_project_connection

from .types import Dependency, DependencyType
from .utils import (
    _RestApiEndpoint,
    check_query_parameters,
    get_dir_path,
    get_extensions,
    get_file_template,
    get_workdir_data,
    request_wrapper,
)


JSON_IDENTIFIER = '"json_dependencies": true'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class VersionDependenciesGetterEndpoint(_RestApiEndpoint):

    @request_wrapper
    async def get(self, request: Request) -> Response:
        check_query_parameters(request, (
            "project_name", "asset_name", "task_name", "subset_name", "application_group_name", "script_path"))

        version_number = int(request.match_info["version_number"])
        query_params = dict(request.query)
        application_group_name = query_params["application_group_name"]
        task_name = query_params["task_name"]
        project_name = query_params["project_name"]
        asset_name = query_params["asset_name"]
        subset_name = query_params["subset_name"]
        script_path = query_params["script_path"]
        project_anatomy = Anatomy(project_name)

        # Get OP dependencies
        op_deps = self.get_openpype_dependencies(project_anatomy, asset_name, subset_name, version_number)

        # Get file dependencies
        file_deps = self.get_file_dependencies(project_anatomy, asset_name, task_name, version_number, application_group_name, script_path)

        deps = {}
        for dep in chain(op_deps, file_deps):
            if dep["path"] not in deps:
                deps[dep["path"]] = dep

        return Response(
            status=200,
            body=self.resource.encode(deps),
            content_type="application/json"
        )


    def get_openpype_dependencies(self, project_anatomy: Anatomy, asset_name: str, subset_name: str, version_number: int) -> List[Dependency]:
        """ 
        Get dependencies as tracked by OpenPype
        """
        project_name = project_anatomy.project_name
        asset_doc = get_asset_by_name(project_name, asset_name)
        if asset_doc is None:
            return []
        subset_doc = get_subset_by_name(project_name, subset_name, asset_doc["_id"])
        if subset_doc is None:
            return []
        version_doc = get_version_by_name(project_name, version_number, subset_doc["_id"])
        if version_doc is None or "inputLinks" not in version_doc["data"]:
            return []
        dependencies = version_doc["data"]["inputLinks"]

        res = []
        for dependency in dependencies:
            dep_version_doc = get_version_by_id(project_name, dependency["id"])
            project_coll = get_project_connection(project_name)
            dep_representation_doc = project_coll.find_one({
                "type": "representation", "parent": ObjectId(dep_version_doc["_id"]),
            })
            if dep_representation_doc is None:
                raise Exception("Failed to get representation for version")

            dep_version_path = dep_version_doc["data"]["source"]
            dep_version_path = project_anatomy.fill_root(dep_version_path)
            available_types = [dependency_type.name for dependency_type in DependencyType]
            if dependency["type"] not in available_types:
                raise Exception(f"Unkwnown dependency type '{dependency['type']}' from OpenPype")

            dependency_type = DependencyType[dependency["type"]]
            res.append(Dependency(
                project_name=project_name,
                asset_name=dep_representation_doc["context"]["asset"],
                subset_name=dep_representation_doc["context"]["subset"],
                version_number=dep_representation_doc["context"]["version"],
                task_name=dep_representation_doc["context"]["task"]["name"],
                path=dep_representation_doc["data"]["path"],
                dependency_type=dependency_type,
                source=dep_version_path,
            ))

        return res
        

    def get_file_dependencies(
            self, 
            project_anatomy: Anatomy, 
            asset_name: str, 
            task_name: str, 
            version_number: int, 
            application_group_name: str, 
            script_path: str
        ) -> List[Dependency]:
        """ 
        Get dependencies as actually contained in the scene
        """

        extensions = get_extensions(application_group_name)
        dir_path = get_dir_path(project_anatomy, asset_name, task_name, application_group_name)
        file_template = get_file_template(project_anatomy, application_group_name, task_name)
        workdir_data = get_workdir_data(project_anatomy.project_name, asset_name, task_name)
        workfile_file_path, _ = get_workfile_with_version(dir_path, file_template, workdir_data, extensions, version=version_number, file_path=True)

        if workfile_file_path is None:
            raise Exception("Failed to retrieve workfile path")
        
        if not Path(script_path).exists():
            raise FileNotFoundError(f"Script path {script_path} does not exist")

        # Launch given script on file path
        application_manager = ApplicationManager()
        application_code = next(app["name"] for app in project_anatomy._data["apps"] if app["name"].startswith(f"{application_group_name}/"))
        process = application_manager.launch_script(
            application_code,
            script_path,
            file_path=workfile_file_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            project_name=project_anatomy.project_name,
            asset_name=asset_name,
            task_name=task_name
        )

        # Parse process output for valid returned dependencies
        output_lines = process.stdout.readlines()
        for line in output_lines:
            if JSON_IDENTIFIER in line:
                json_obj = json.loads(line)

                # If process failed, create error response
                if json_obj["error"]:
                    print(f"{bcolors.FAIL}{json_obj['stack_string']}{bcolors.ENDC}")
                    raise Exception(f"Dependencies getter script from {application_code} "
                                    f"failed : {json_obj['message']}")

                assert "dependencies" in json_obj, "Failed to get valid dependencies object"
                dependencies = json_obj["dependencies"]
                return self.analyse_deps(project_anatomy, dependencies)

        raise Exception("Failed to get JSON with dependencies")


    def analyse_deps(self, project_anatomy: Anatomy, dependency_paths: List[str]) -> List[Dependency]:
        """
        Retrieve context info relative to given paths, and normalize response
        """
        res = []
        for dependency_path in dependency_paths:
            project_name = project_anatomy.project_name
            success, rootless_path = project_anatomy.find_root_template_from_path(dependency_path)

            project_coll = get_project_connection(project_name)
            representation_file_doc = project_coll.find_one({
                "type": "representation", "files": {"$elemMatch": {"path": rootless_path}},
            })
            if not success or representation_file_doc is None:

                dep = Dependency(
                    project_name=project_name,
                    asset_name=None,
                    subset_name=None,
                    version_number=None,
                    task_name=None,
                    path=dependency_path,
                    dependency_type=DependencyType.untracked,
                    source=None,
                )
                res.append(dep)
                continue
            
            version_id = representation_file_doc["parent"]
            version_doc = get_version_by_id(project_name, version_id)
            version_path = version_doc["data"]["source"]
            version_path = project_anatomy.fill_root(version_path)
            res.append(Dependency(
                project_name=project_name,
                asset_name=representation_file_doc["context"]["asset"],
                subset_name=representation_file_doc["context"]["subset"],
                version_number=representation_file_doc["context"]["version"],
                task_name=representation_file_doc["context"]["task"]["name"],
                path=representation_file_doc["data"]["path"],
                dependency_type=DependencyType.reference,
                source=version_path,
            ))
        return res
