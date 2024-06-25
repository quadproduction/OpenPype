
from aiohttp.web_response import Response

from typing import Dict, List

from openpype.modules import ModulesManager, IHostAddon

from .utils import _RestApiEndpoint, request_wrapper


class ExtensionsGetterEndpoint(_RestApiEndpoint):

    @request_wrapper
    async def get(self) -> Response:
        module_manager = ModulesManager()
        available_extensions: Dict[str, List[str]] = {}
        for module in module_manager.modules:
            if isinstance(module, IHostAddon):
                module_extensions = module.get_workfile_extensions()
                available_extensions[module.host_name] = module_extensions

        return Response(
            status=200,
            body=self.resource.encode({"extensions": available_extensions}),
            content_type="application/json"
        )
