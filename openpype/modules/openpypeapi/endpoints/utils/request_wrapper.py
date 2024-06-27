
import functools

from aiohttp.web_response import Response


def request_wrapper(func):
    """ Wrapper to catch any internal error to return an appropriated HTTP error response """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Response:
        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            return Response(
                status=422,
                reason=str(exc)
            )
    return wrapper
