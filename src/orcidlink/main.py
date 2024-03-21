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
from typing import Any, AsyncGenerator, Generic, List, Optional, TypeVar

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import Body, FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi_jsonrpc import API, BaseError, Entrypoint, JsonRpcContext
from pydantic import Field
from starlette.responses import HTMLResponse

from orcidlink.jsonrpc.errors import (
    AuthorizationRequiredError,
    NotAuthorizedError,
    NotFoundError,
)
from orcidlink.jsonrpc.methods.delete_link import delete_link
from orcidlink.jsonrpc.methods.delete_own_link import delete_own_link
from orcidlink.jsonrpc.methods.error_info import ErrorInfoResult, error_info_method
from orcidlink.jsonrpc.methods.info import InfoResult, info_method
from orcidlink.jsonrpc.methods.is_linked import is_linked_method
from orcidlink.jsonrpc.methods.linking_sessions import (
    CreateLinkingSessionResult,
    create_linking_session,
    delete_linking_session,
    finish_linking_session,
    get_linking_session,
)
from orcidlink.jsonrpc.methods.manage import (
    FindLinksResult,
    GetLinkingSessionsResult,
    GetLinkResult,
    GetStatsResult,
    IsManagerResult,
    RefreshTokensResult,
    SearchQuery,
    delete_expired_linking_sessions,
    delete_linking_session_completed,
    delete_linking_session_initial,
    delete_linking_session_started,
    find_links,
    get_link,
    get_linking_sessions,
    get_stats,
    is_manager,
    refresh_tokens,
)
from orcidlink.jsonrpc.methods.other_link import other_link
from orcidlink.jsonrpc.methods.owner_link import owner_link
from orcidlink.jsonrpc.methods.profile import get_profile
from orcidlink.jsonrpc.methods.status import StatusResult, status_method
from orcidlink.jsonrpc.methods.works import (
    CreateWorkResult,
    GetWorkResult,
    SaveWorkResult,
    create_work,
    delete_work,
    get_work,
    get_works,
    save_work,
)
from orcidlink.jsonrpc.utils import ensure_account2, ensure_authorization2
from orcidlink.lib import logger
from orcidlink.lib.responses import (
    AUTHORIZATION_HEADER,
    PUT_CODE_PARAM,
    SESSION_ID_PARAM,
    USERNAME_PARAM,
    UIError,
    ui_error_response,
)
from orcidlink.lib.type import ServiceBaseModel
from orcidlink.model import (
    LinkingSessionCompletePublic,
    LinkRecordPublic,
    LinkRecordPublicNonOwner,
    NewWork,
    ORCIDProfile,
    ORCIDWorkGroup,
    WorkUpdate,
)
from orcidlink.routers import linking_sessions
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
    {"name": "jsonrpc", "description": "JSON-RPC 2.0 method"},
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


# logging.config.dictConfig(LOGGING_CONFIG)

# orcid_logger.info(ORCIDLogging("just a test", ORCIDRequestLogEntry(
#     request_id="foo",
#     request_at=123,
#     api='api here',
#     url='url here',
#     method='method here',
#     query_string='query_tring here',
#     data={"foo": "bar"}
# )))

logging.getLogger().info("Initializing main app")


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
    """
    Load the config here in order to trigger any configuration problems early in the
    application startup.
    """
    stats()
    logger.log_level(config_to_log_level(config().log_level))
    yield


# TODO: add fancy FastAPI configuration https://fastapi.tiangolo.com/tutorial/metadata/
# app = FastAPI(
#     docs_url=None,
#     redoc_url=None,
#     title="ORCID Link Service",
#     description=description,
#     terms_of_service="https://www.kbase.us/about/terms-and-conditions-v2/",
#     contact={
#         "name": "KBase, Lawrence Berkeley National Laboratory, DOE",
#         "url": "https://www.kbase.us",
#         "email": "engage@kbase.us",
#     },
#     license_info={
#         "name": "The MIT License",
#         "url": "https://github.com/kbase/kb_sdk/blob/develop/LICENSE.md",
#     },
#     openapi_tags=tags_metadata,
#     lifespan=lifespan,
# )

app = API(
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


COMMON_ERRORS: List[type[BaseError]] = [
    AuthorizationRequiredError,
    NotAuthorizedError,
    NotFoundError,
]
COMMON_ERRORS.extend(Entrypoint.default_errors)

# JSON-RPC middlewares


@asynccontextmanager
async def logging_middleware(ctx: JsonRpcContext):
    logger = logging.getLogger("api")
    logger.info(
        "jsonrpc request",
        extra={"type": "jsonrpc_request", "request": ctx.raw_request},  # type: ignore
    )
    try:
        yield
    finally:
        # logger.info('Response: %r', ctx.raw_response)
        logger.info(
            "jsonrpc response",
            extra={"type": "jsonrpc_response", "response": ctx.raw_response},  # type: ignore
        )


api_v1 = Entrypoint(
    "/api/v1", tags=["jsonrpc"], errors=COMMON_ERRORS, middlewares=[logging_middleware]
)


app.bind_entrypoint(api_v1)  # type: ignore

#
# JSON-RPC methods
#
# All method handlers should call a method implementation form another module.
#


@api_v1.method(name="status")  # type: ignore
def status() -> StatusResult:
    return status_method()


@api_v1.method(name="info")  # type: ignore
def info() -> InfoResult:
    return info_method()


@api_v1.method(name="error-info")  # type: ignore
def error_info(error_code: int) -> ErrorInfoResult:
    return error_info_method(error_code)


@api_v1.method(name="is-linked", errors=[AuthorizationRequiredError])  # type: ignore
async def is_linked(
    username: str = USERNAME_PARAM, authorization: str | None = AUTHORIZATION_HEADER
) -> bool:
    api_logger = logging.getLogger("api")
    api_logger.info(
        "Called /is-linked method",
        extra={
            "type": "api",
            "event": "call_started",
            "params": {"authorization": "REDACTED"},
            "path": "/is-linked",
        },
    )

    _, token_info = await ensure_authorization2(authorization)

    result = await is_linked_method(username, token_info.user)

    api_logger.info(
        "Successfully called /is_linked method",
        extra={
            "type": "api",
            "event": "call_success",
            "info": {"username": token_info.user},
            "path": "/is_linked",
        },
    )

    return result


@api_v1.method(name="owner-link", errors=[*COMMON_ERRORS])  # type: ignore
async def owner_link_handler(
    username: str = USERNAME_PARAM, authorization: str | None = AUTHORIZATION_HEADER
) -> LinkRecordPublic:
    """
    Returns the "public" ORCID Link for the calling user.

    Note that this is designed to be used by a user for their own link,
    as it reveals information about their link that is not necessarily
    appropriate for another user to access. The "public" record alread
    has ORCID tokens stripped out, leaving just link metadata, but that
    could be considered sensitive as well, or at least not needed by any
    other user. See "other-link" for an fetching the link for anyone.
    """
    _, token_info = await ensure_authorization2(authorization)

    result = await owner_link(username, token_info.user)

    return result


@api_v1.method(name="other-link", errors=[*COMMON_ERRORS])  # type: ignore
async def other_link_handler(
    username: str = USERNAME_PARAM, authorization: str | None = AUTHORIZATION_HEADER
) -> LinkRecordPublicNonOwner:
    """
    Returns the "public non-owner" version of the ORCID Link for the calling user.

    Note that this reduces down to almost just the ORCID Id, with most metadata
    including the tokens stripped out. This call may be used on behalf of any
    user in a context in which the user's orcid id is needed.
    """
    _, _ = await ensure_authorization2(authorization)

    result = await other_link(username)

    return result


@api_v1.method(name="delete-own-link", errors=[*COMMON_ERRORS])  # type: ignore
async def delete_own_link_handler(
    username: str = USERNAME_PARAM, authorization: str | None = AUTHORIZATION_HEADER
) -> None:
    _, token_info = await ensure_authorization2(authorization)

    await delete_own_link(username, token_info.user)


@api_v1.method(name="create-linking-session", errors=[*COMMON_ERRORS])  # type: ignore
async def create_linking_session_handler(
    username: str = USERNAME_PARAM, authorization: str | None = AUTHORIZATION_HEADER
) -> CreateLinkingSessionResult:
    _, token_info = await ensure_authorization2(authorization)

    result = await create_linking_session(username, token_info.user)

    return result


@api_v1.method(name="get-linking-session", errors=[*COMMON_ERRORS])  # type: ignore
async def get_linking_session_handler(
    session_id: str = SESSION_ID_PARAM, authorization: str = AUTHORIZATION_HEADER
) -> LinkingSessionCompletePublic:
    _, token_info = await ensure_authorization2(authorization)

    result = await get_linking_session(session_id, token_info.user)

    return result


@api_v1.method(name="delete-linking-session", errors=[*COMMON_ERRORS])  # type: ignore
async def delete_linking_session_handler(
    session_id: str = SESSION_ID_PARAM, authorization: str = AUTHORIZATION_HEADER
) -> None:
    _, token_info = await ensure_authorization2(authorization)

    result = await delete_linking_session(session_id, token_info.user)

    return result


@api_v1.method(name="finish-linking-session", errors=[*COMMON_ERRORS])  # type: ignore
async def finish_linking_session_handler(
    session_id: str = SESSION_ID_PARAM, authorization: str = AUTHORIZATION_HEADER
) -> None:
    _, token_info = await ensure_authorization2(authorization)

    result = await finish_linking_session(session_id, token_info.user)

    return result


@api_v1.method(name="get-orcid-profile", errors=[*COMMON_ERRORS])  # type: ignore
async def get_orcid_profile_handler(
    username: str = USERNAME_PARAM, authorization: str = AUTHORIZATION_HEADER
) -> ORCIDProfile:
    """
    Implements the "get-orcid-profile" method handler.

    See the method implementation for details.
    """
    _, token_info = await ensure_authorization2(authorization)

    return await get_profile(username, token_info.user)


#
# Management
#


@api_v1.method(name="is-manager", errors=[*COMMON_ERRORS])  # type: ignore
async def is_manager_handler(
    username: str, authorization: str = AUTHORIZATION_HEADER
) -> IsManagerResult:
    _, account_info = await ensure_account2(authorization)

    result = await is_manager(username, account_info)

    return result


@api_v1.method(name="find-links", errors=[*COMMON_ERRORS])  # type: ignore
async def find_links_handler(
    query: Optional[SearchQuery], authorization: str = AUTHORIZATION_HEADER
) -> FindLinksResult:
    _, account_info = await ensure_account2(authorization)

    if config().manager_role not in account_info.customroles:
        raise NotAuthorizedError("Not authorized for management operations")

    result = await find_links(query)

    return result


@api_v1.method(name="get-link", errors=[*COMMON_ERRORS])  # type: ignore
async def get_link_handler(
    username: str = USERNAME_PARAM, authorization: str = AUTHORIZATION_HEADER
) -> GetLinkResult:
    _, account_info = await ensure_account2(authorization)

    if config().manager_role not in account_info.customroles:
        raise NotAuthorizedError("Not authorized for management operations")

    link_record = await get_link(username)

    return link_record


@api_v1.method(name="get-linking-sessions", errors=[*COMMON_ERRORS])  # type: ignore
async def get_linking_sessions_handler(
    authorization: str = AUTHORIZATION_HEADER,
) -> GetLinkingSessionsResult:
    _, account_info = await ensure_account2(authorization)

    if config().manager_role not in account_info.customroles:
        raise NotAuthorizedError("Not authorized for management operations")

    result = await get_linking_sessions()

    return result


@api_v1.method(name="delete-expired-linking-sessions", errors=[*COMMON_ERRORS])  # type: ignore
async def delete_expired_linking_sessions_handler(
    authorization: str = AUTHORIZATION_HEADER,
) -> None:
    _, account_info = await ensure_account2(authorization)

    if config().manager_role not in account_info.customroles:
        raise NotAuthorizedError("Not authorized for management operations")

    await delete_expired_linking_sessions()


@api_v1.method(name="delete-linking-session-initial", errors=[*COMMON_ERRORS])  # type: ignore
async def delete_linking_session_initial_handler(
    session_id: str = SESSION_ID_PARAM, authorization: str = AUTHORIZATION_HEADER
) -> None:
    _, account_info = await ensure_account2(authorization)

    if config().manager_role not in account_info.customroles:
        raise NotAuthorizedError("Not authorized for management operations")

    await delete_linking_session_initial(session_id)


@api_v1.method(name="delete-linking-session-started", errors=[*COMMON_ERRORS])  # type: ignore
async def delete_linking_session_started_handler(
    session_id: str = SESSION_ID_PARAM, authorization: str = AUTHORIZATION_HEADER
) -> None:
    _, account_info = await ensure_account2(authorization)

    if config().manager_role not in account_info.customroles:
        raise NotAuthorizedError("Not authorized for management operations")

    await delete_linking_session_started(session_id)


@api_v1.method(name="delete-linking-session-completed", errors=[*COMMON_ERRORS])  # type: ignore
async def delete_linking_session_completed_handler(
    session_id: str = SESSION_ID_PARAM, authorization: str = AUTHORIZATION_HEADER
) -> None:
    _, account_info = await ensure_account2(authorization)

    if config().manager_role not in account_info.customroles:
        raise NotAuthorizedError("Not authorized for management operations")

    await delete_linking_session_completed(session_id)


@api_v1.method(name="delete-link", errors=[*COMMON_ERRORS])  # type: ignore
async def delete_link_handler(
    username: str = USERNAME_PARAM, authorization: str | None = AUTHORIZATION_HEADER
) -> None:
    _, account_info = await ensure_account2(authorization)

    await delete_link(username, account_info)


@api_v1.method(name="get-stats", errors=[*COMMON_ERRORS])  # type: ignore
async def get_stats_handler(
    authorization: str = AUTHORIZATION_HEADER,
) -> GetStatsResult:
    _, account_info = await ensure_account2(authorization)

    if config().manager_role not in account_info.customroles:
        raise NotAuthorizedError("Not authorized for management operations")

    result = await get_stats()
    return result


# TODO: I don't think this is used.
@api_v1.method(name="refresh-tokens", errors=[*COMMON_ERRORS])  # type: ignore
async def refresh_tokens_handler(
    username: str = USERNAME_PARAM, authorization: str = AUTHORIZATION_HEADER
) -> RefreshTokensResult:
    _, account_info = await ensure_account2(authorization)

    if config().manager_role not in account_info.customroles:
        raise NotAuthorizedError("Not authorized for management operations")

    result = await refresh_tokens(username)
    return result


#
# Works
#


@api_v1.method(name="get-orcid-works", errors=[*COMMON_ERRORS])  # type: ignore
async def get_orcid_works_handler(
    username: str = USERNAME_PARAM, authorization: str = AUTHORIZATION_HEADER
) -> List[ORCIDWorkGroup]:
    _, token_info = await ensure_authorization2(authorization)

    if username != token_info.user:
        raise NotAuthorizedError()

    result = await get_works(username)
    return result


@api_v1.method(name="get-orcid-work", errors=[*COMMON_ERRORS])  # type: ignore
async def get_orcid_work_handler(
    username: str = USERNAME_PARAM,
    put_code: int = PUT_CODE_PARAM,
    authorization: str = AUTHORIZATION_HEADER,
) -> GetWorkResult:
    _, token_info = await ensure_authorization2(authorization)

    if username != token_info.user:
        raise NotAuthorizedError()

    result = await get_work(username, put_code)
    return result


@api_v1.method(name="create-orcid-work", errors=[*COMMON_ERRORS])  # type: ignore
async def create_work_handler(
    username: str = USERNAME_PARAM,
    new_work: NewWork = Body(..., description="New work activity record"),
    authorization: str = AUTHORIZATION_HEADER,
) -> CreateWorkResult:
    _, token_info = await ensure_authorization2(authorization)

    if username != token_info.user:
        raise NotAuthorizedError()

    result = await create_work(username, new_work)
    return result


@api_v1.method(name="update-orcid-work", errors=[*COMMON_ERRORS])  # type: ignore
async def save_work_handler(
    username: str = USERNAME_PARAM,
    work_update: WorkUpdate = Body(..., description="A work activity update record"),
    authorization: str = AUTHORIZATION_HEADER,
) -> SaveWorkResult:
    _, token_info = await ensure_authorization2(authorization)

    if username != token_info.user:
        raise NotAuthorizedError()

    result = await save_work(username, work_update)
    return result


@api_v1.method(name="delete-orcid-work", errors=[*COMMON_ERRORS])  # type: ignore
async def delete_work_handler(
    username: str = USERNAME_PARAM,
    put_code: int = PUT_CODE_PARAM,
    authorization: str = AUTHORIZATION_HEADER,
) -> None:
    _, token_info = await ensure_authorization2(authorization)

    if username != token_info.user:
        raise NotAuthorizedError()

    result = await delete_work(username, put_code)
    return result


app.add_middleware(CorrelationIdMiddleware)


###############################################################################
# Routers
#
# All paths are included here as routers. Each router is defined in the "routers"
# directory.
###############################################################################
app.include_router(linking_sessions.router)

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
# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(
#     request: Request, exc: RequestValidationError
# ) -> JSONResponse:
#     logging.error(
#         "RequestValidationError: see validation_error_info for details",
#         extra={"type": "validation-error", "validation_error_info": exc.errors()},
#     )
#     detail = list(exc.errors())
#     data: ValidationError = ValidationError(detail=detail, body=exc.body)
#     return error_response(
#         errors.ERRORS.request_validation_error,
#         "This request does not comply with the schema for this endpoint",
#         data=data,
#         status_code=HTTP_422_UNPROCESSABLE_ENTITY,
#     )


@app.exception_handler(UIError)
async def ui_error_exception_handler(request: Request, exception: UIError):
    return ui_error_response(exception.code, exception.message, exception.data)


# @app.exception_handler(exceptions.ServiceErrorY)
# async def service_errory_exception_handler(
#     _: Request, exc: exceptions.ServiceErrorY
# ) -> JSONResponse:
#     logging.error(
#         f"ServiceErrorY: {str(exc)}",
#         extra={"type": "service-error", "details": exc.asdict()},
#     )
#     return exc.get_response()


# @app.exception_handler(AuthError)
# async def auth_error_exception_handler(
#     _: Request, exc: AuthError
# ) -> JSONResponse:
#     # logging.error(
#     #     f"ServiceErrorY: {str(exc)}",
#     #     extra={"type": "service-error", "details": exc.asdict()},
#     # )
#     error_content = exc.to_json_rpc_error()

#     content = jsonrpc_error_response(
#         error_content,

#     )

#     return JSONResponse(status_code=200, content=json_content)


#
# This catches good ol' internal server errors. These are primarily due to internal
# programming logic errors. The reason to catch them here is to override the default
# FastAPI error structure.
#
# @app.exception_handler(500)
# async def internal_server_error_handler(
#     request: Request, exc: Exception
# ) -> JSONResponse:
#     logging.error(
#         f"INTERNAL SERVER ERROR: {str(exc)}",
#         extra={"type": "internal-server-error", "exception": str(exc)},
#         exc_info=exc,
#     )
#     return exception_error_response(
#         errors.ERRORS.internal_server_error,
#         exc,
#         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#     )


class StarletteHTTPDetailData(ServiceBaseModel):
    detail: Any = Field(...)


class StarletteHTTPNotFoundData(StarletteHTTPDetailData):
    path: str = Field(...)


#
# Finally there are some other errors thrown by FastAPI / Starlette which need
# overriding to return a normalized JSON form. This should be all of them. See:
# https://fastapi.tiangolo.com/tutorial/handling-errors/
#
# @app.exception_handler(StarletteHTTPException)
# async def http_exception_handler(
#     request: Request, exc: StarletteHTTPException
# ) -> JSONResponse:
#     logging.error(f"StarletteHTTPException: {str(exc)}")
#     return JSONResponse(
#         status_code=exc.status_code,
#         content=json.dumps({

#         })
#         content=jsonable_encoder(response_content, exclude_unset=True),
#     )

# if exc.status_code == 404:
#     # Will be thrown by some non-api call, as those all
#     # use JSON-RPC on /api/v1, so 404 not possible.

#     return error_response2(
#         errors.ErrorResponse[StarletteHTTPNotFoundData](
#             code=errors.ERRORS.not_found.code,
#             title=errors.ERRORS.not_found.title,
#             message="The requested resource was not found",
#             data=StarletteHTTPNotFoundData(
#                 detail=exc.detail, path=request.url.path
#             ),
#         ),
#         status_code=HTTP_404_NOT_FOUND,
#     )

# return error_response2(
#     errors.ErrorResponse[StarletteHTTPDetailData](
#         code=errors.ERRORS.fastapi_error.code,
#         title=errors.ERRORS.fastapi_error.title,
#         message="Internal FastAPI Exception",
#         data=StarletteHTTPDetailData(detail=exc.detail),
#     ),
#     status_code=exc.status_code,
# )


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
