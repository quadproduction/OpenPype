
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from .utils import _RestApiEndpoint, request_wrapper


class APIStatusEndpoint(_RestApiEndpoint):

    @request_wrapper
    async def head(self, request: Request):
        return Response()
