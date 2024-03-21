from typing import Callable

from fastapi import APIRouter, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute

from orcidlink.lib.responses import UIError


class InteractiveRoute(APIRoute):
    """
    This is a custom route, whose sole purpose is to support isolated
    exception handling for OAuth endpoints that flow through the browser -
    what I've termed "interactive" routes.
    """

    def get_route_handler(self) -> Callable:  # type: ignore
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            # app = request.app
            try:
                return await original_route_handler(request)
            except RequestValidationError as rve:
                raise UIError(-30602, "Parameter error") from rve
            except UIError as ue:
                raise ue
            except Exception as ex:
                raise UIError(-32603, "Internal error") from ex

        return custom_route_handler


router = APIRouter(prefix="/services", route_class=InteractiveRoute)
