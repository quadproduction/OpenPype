import json
import datetime

from bson.objectid import ObjectId


from .endpoints import (
    APIStatusEndpoint,
    ApplicationGetterEndpoint,
    ApplicationVersionGetterEndpoint,
    ApplicationsGetterEndpoint,
    AssetGetterEndpoint,
    AssetsGetterEndpoint,
    ExtensionsGetterEndpoint,
    WorkfileContextGetterEndpoint,
    ProjectGetterEndpoint,
    ProjectsGetterEndpoint,
    RepresentationContextGetterEndpoint,
    RootlessPathEndpoint,
    TemplatesGetterEndpoint,
    VersionDependenciesGetterEndpoint,
    VersionGetterEndpoint,
    VersionsGetterEndpoint,
    WorkfileTemplateKeyGetterEndpoint,
)
from .endpoints.types import DependencyType


class OpenPypeAPIRestApiResource:
    def __init__(self, server_manager):
        self.server_manager = server_manager

        self.prefix = "/openpypeapi"

        self.endpoint_defs = (
            (
                "HEAD",
                "/api",
                APIStatusEndpoint(self)
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
            (
                "GET",
                "/applications/{application_name}/{application_version}",
                ApplicationVersionGetterEndpoint(self)
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
                "/extensions",
                ExtensionsGetterEndpoint(self)
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
                "/projects/{project_name}/rootless-path",
                RootlessPathEndpoint(self)
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
                "/versions/{version_number}/dependencies",
                VersionDependenciesGetterEndpoint(self)
            ),
            (
                "GET",
                "/workfile/context",
                WorkfileContextGetterEndpoint(self)
            ),
            (
                "GET",
                "/representation/context",
                RepresentationContextGetterEndpoint(self)
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
        elif isinstance(value, ObjectId):
            return str(value)
        elif isinstance(value, DependencyType):
            return value.name
        raise TypeError(value)

    @classmethod
    def encode(cls, data):
        return json.dumps(
            data,
            indent=4,
            default=cls.json_dump_handler
        ).encode("utf-8")
