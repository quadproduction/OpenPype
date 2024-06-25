
from aiohttp.web_request import Request


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

