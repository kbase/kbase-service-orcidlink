"""
The main service entrypoint

The main module provides the sole entrypoint for the FastAPI application. It defines the
top level "app", and most interaction with the FastAPI app itself, such as exception
handling overrides, application metadata for documentation, incorporation of all routers
supporting all endpoints, and a sole endpoint implementing the online api documentation
at "/docs".

All endpoints other than the /docs are implement as "routers". All routers are
implemented in individual modules within the "routers" directory. Each router should be
associated with a top level path element, other than "root", which implements top level
endpoints (other than /docs). Routers include: link, linking-sessions, works, orcid, and
root.

"""
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Generic, List, TypeVar

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from pydantic import Field
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import HTMLResponse, JSONResponse

from orcidlink.lib import errors, exceptions, logger
from orcidlink.lib.responses import (
    error_response,
    error_response2,
    exception_error_response,
)
from orcidlink.lib.type import ServiceBaseModel
from orcidlink.routers import link, linking_sessions, manage, root
from orcidlink.routers.orcid import profile, works
from orcidlink.runtime import config, stats

###############################################################################
# FastAPI application setup
#
# Set up FastAPI top level app with associated metadata for documentation purposes.
#
###############################################################################

description = """\
The *ORCID Link Service* provides an API to enable the linking of a KBase
 user account to an ORCID account. This "link" consists of a [Link
 Record](#user-content-header_type_linkrecord) which contains a KBase username, ORCID
 id, ORCID access token, and a few other fields. This link record allows KBase to create
 tools and services which utilize the ORCID api to view or modify certain aspects of a
 users ORCID profile.

Once connected, *ORCID Link* enables certain integrations, including:

- syncing your KBase profile from your ORCID profile
- creating and managing KBase public Narratives within your ORCID profile\
"""

tags_metadata = [
    {"name": "misc", "description": "Miscellaneous operations"},
    {
        "name": "link",
        "description": "Access to and control over stored ORCID Links",
    },
    {
        "name": "linking-sessions",
        "description": """\
OAuth integration and internal support for creating ORCID Links.

The common path element is `/linking-sessions`.

Some of the endpoints are "browser interactive", meaning that the links are followed
directly by the browser, rather than being used within Javascript code.\
""",
    },
    {"name": "orcid", "description": "Direct access to ORCID via ORCID Link"},
    {
        "name": "works",
        "description": "Add, remove, update 'works' records for a user's ORCID Account",
    },
]


def config_to_log_level(log_level: str) -> int:
    """
    Translate a log level string to a Python log level value.
    """
    if log_level == "DEBUG":
        return logging.DEBUG
    elif log_level == "INFO":
        return logging.INFO
    elif log_level == "WARNING":
        return logging.WARNING
    elif log_level == "ERROR":
        return logging.ERROR
    elif log_level == "CRITICAL":
        return logging.CRITICAL
    else:
        raise ValueError(f'Invalid log_level config setting "{log_level}"')


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    #
    # Load the config here in order to trigger any configuration problems early in the
    # application startup.
    #
    stats()
    logger.log_level(config_to_log_level(config().log_level))

    yield


# TODO: add fancy FastAPI configuration https://fastapi.tiangolo.com/tutorial/metadata/
app = FastAPI(
    docs_url=None,
    redoc_url=None,
    title="ORCID Link Service",
    description=description,
    terms_of_service="https://www.kbase.us/about/terms-and-conditions-v2/",
    contact={
        "name": "KBase, Lawrence Berkeley National Laboratory, DOE",
        "url": "https://www.kbase.us",
        "email": "engage@kbase.us",
    },
    license_info={
        "name": "The MIT License",
        "url": "https://github.com/kbase/kb_sdk/blob/develop/LICENSE.md",
    },
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

###############################################################################
# Routers
#
# All paths are included here as routers. Each router is defined in the "routers"
# directory.
###############################################################################
app.include_router(root.router)
# app.include_router(rpc.router)
app.include_router(link.router)
app.include_router(linking_sessions.router)
app.include_router(profile.router)
app.include_router(works.router)
app.include_router(manage.router)

###############################################################################
#
# Exception handlers
#
#
###############################################################################

T = TypeVar("T", bound=ServiceBaseModel)


class WrappedError(ServiceBaseModel, Generic[T]):
    detail: T = Field(...)


class ValidationError(ServiceBaseModel):
    detail: List[Any] = Field(...)
    body: Any = Field(...)


#
# Custom exception handlers.
# Exceptions caught by FastAPI result in a variety of error responses, using
# a specific JSON format. However, we want to return all errors using our
# error format, which mimics JSON-RPC 2.0 and is compatible with the way
# our JSON-RPC 1.1 APIs operate (though not wrapped in an array).
#


# Have this return JSON in our "standard", or at least uniform, format. We don't want
# users of this api to need to accept FastAPI/Starlette error format. These errors are
# returned when the API is misused; they should not occur in production. Note that
# response validation errors are caught by FastAPI and converted to Internal Server
# errors. https://fastapi.tiangolo.com/tutorial/handling-errors/
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logging.error(f"RequestValidationError: {str(exc)}")
    detail = list(exc.errors())
    data: ValidationError = ValidationError(detail=detail, body=exc.body)
    return error_response(
        errors.ERRORS.request_validation_error,
        "This request does not comply with the schema for this endpoint",
        data=data,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


@app.exception_handler(exceptions.ServiceErrorY)
async def service_errory_exception_handler(
    _: Request, exc: exceptions.ServiceErrorY
) -> JSONResponse:
    logging.error(f"ServiceErrorY: {str(exc)}")
    return exc.get_response()


#
# This catches good ol' internal server errors. These are primarily due to internal
# programming logic errors. The reason to catch them here is to override the default
# FastAPI error structure.
#
@app.exception_handler(500)
async def internal_server_error_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logging.error(f"INTERNAL SERVER ERROR: {str(exc)}")
    return exception_error_response(
        errors.ERRORS.internal_server_error,
        exc,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


class StarletteHTTPDetailData(ServiceBaseModel):
    detail: Any = Field(...)


class StarletteHTTPNotFoundData(StarletteHTTPDetailData):
    path: str = Field(...)


#
# Finally there are some other errors thrown by FastAPI / Starlette which need
# overriding to return a normalized JSON form. This should be all of them. See:
# https://fastapi.tiangolo.com/tutorial/handling-errors/
#
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    logging.error(f"StarletteHTTPException: {str(exc)}")
    if exc.status_code == 404:
        return error_response2(
            errors.ErrorResponse[StarletteHTTPNotFoundData](
                code=errors.ERRORS.not_found.code,
                title=errors.ERRORS.not_found.title,
                message="The requested resource was not found",
                data=StarletteHTTPNotFoundData(
                    detail=exc.detail, path=request.url.path
                ),
            ),
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return error_response2(
        errors.ErrorResponse[StarletteHTTPDetailData](
            code=errors.ERRORS.fastapi_error.code,
            title=errors.ERRORS.fastapi_error.title,
            message="Internal FastAPI Exception",
            data=StarletteHTTPDetailData(detail=exc.detail),
        ),
        status_code=exc.status_code,
    )


###############################################################################
#
# API
#
###############################################################################


@app.get(
    "/docs",
    response_class=HTMLResponse,
    include_in_schema=True,
    tags=["misc"],
    responses={
        200: {
            "description": "Successfully returned the api docs",
        },
        404: {"description": "Not Found"},
    },
)
async def docs(req: Request) -> HTMLResponse:
    """
    Get API Documentation

    Provides a web interface to the auto-generated API docs.
    """
    if app.openapi_url is None:
        # FastAPI is obstinate - I initially wanted to handle this case
        # with a "redirect error" to kbase-ui, but even though I returned
        # 302, it resulted in a 404 in tests! I don't know about real life.
        # So lets just make this a 404, which is reasonable in any case.
        # return error_response_not_found("The 'openapi_url' is 'None'")
        return HTMLResponse(
            content="<h1>Not Found</h1><p>Sorry, the openapi url is not defined</p>",
            status_code=404,
        )

    openapi_url = config().orcidlink_url + app.openapi_url
    return get_swagger_ui_html(
        openapi_url=openapi_url,
        title="API",
    )
