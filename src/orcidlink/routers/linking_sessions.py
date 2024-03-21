"""

Provides all support for creating an ORCID link.

This module implements an OAUTH flow and related services required to create an
ORCID Link and to fit into various front end usage scenarios.

"""

import json
import logging
from typing import Any
from urllib.parse import urlencode

from asgi_correlation_id import correlation_id
from fastapi import APIRouter, Cookie, Path, Query, responses
from fastapi_jsonrpc import InvalidParams
from pydantic import Field
from starlette.responses import RedirectResponse

# from orcidlink.lib import errors, exceptions
from orcidlink.jsonrpc.errors import (
    AlreadyLinkedError,
    AuthorizationRequiredError,
    JSONRPCError,
    NotAuthorizedError,
    UpstreamError,
)
from orcidlink.lib.auth import ensure_authorization_ui

# from orcidlink.lib.auth import ensure_authorization
from orcidlink.lib.responses import AUTH_RESPONSES, STD_RESPONSES, UIError
from orcidlink.lib.service_clients.orcid_api import AuthorizeParams
from orcidlink.lib.service_clients.orcid_oauth_api import orcid_oauth_api
from orcidlink.process import get_linking_session_initial, get_linking_session_started
from orcidlink.routers.interactive_route import InteractiveRoute
from orcidlink.runtime import config
from orcidlink.storage.storage_model import storage_model

router = APIRouter(prefix="/linking-sessions", route_class=InteractiveRoute)


#
# Commonly used fields
#
SESSION_ID_FIELD = Field(
    description="The linking session id",
    # It is a uuid, whose string representation is 36 characters.
    min_length=36,
    max_length=36,
)
SESSION_ID_PATH_ELEMENT = Path(
    description="The linking session id",
    # It is a uuid, whose string representation is 36 characters.
    min_length=36,
    max_length=36,
)
RETURN_LINK_QUERY = Query(
    default=None,
    description="A url to redirect to after the entire linking is complete; "
    + "not to be confused with the ORCID OAuth flow's redirect_url",
)
SKIP_PROMPT_QUERY = Query(
    default=None, description="Whether to prompt for confirmation of linking"
)

UI_OPTIONS_QUERY = Query(default="", description="Opaque string of ui options")

KBASE_SESSION_COOKIE = Cookie(
    default=None,
    description="KBase auth token taken from a cookie named 'kbase_session'",
)

KBASE_SESSION_BACKUP_COOKIE = Cookie(
    default=None,
    description="KBase auth token taken from a cookie named 'kbase_session_backup. "
    + "Required in the KBase production environment since the prod ui and services "
    + "operate on different hosts; the primary cookie, kbase_session, is host-based "
    "so cannot be read by a prod service.",
)

#
# Logging wrappers
#


def log_info(message: str, event: str, extra: dict[str, Any]) -> None:
    logger = logging.getLogger("interactiveapi")
    logger.info(
        message,
        extra={
            "type": "interactiveapi",
            "event": event,
            "correlation_id": correlation_id.get(),
            **extra,
        },
    )


def log_error(message: str, event: str, extra: dict[str, Any]) -> None:
    logger = logging.getLogger("orcidoauthapi")
    logger.error(
        message,
        extra={
            "type": "interactiveapi",
            "event": event,
            "correlation_id": correlation_id.get(),
            **extra,
        },
    )


#
# OAuth Interactive Endpoints
#

#
# The initial url for linking to an ORCID Account
# Note that this is an interactive url - that is the browser is directly invoking this
# endpoint.
# TODO: Errors should be redirects to the generic error handler in the ORCIDLink UI.
#


@router.get(
    "/{session_id}/oauth/start",
    response_class=RedirectResponse,
    status_code=302,
    responses={
        302: {
            "description": (
                "Redirect to ORCID if a valid linking session, back to KBase in "
                "the case of an error"
            )
        },
        **AUTH_RESPONSES,
        **STD_RESPONSES,
        # 404: {
        #     "description": (
        #         "Response when a linking session not found for the supplied
        # session id"
        #     ),
        #     "model": errors.ErrorResponse,
        # },
    },
    tags=["linking-sessions"],
)
async def start_linking_session(
    session_id: str = SESSION_ID_PATH_ELEMENT,
    return_link: str | None = RETURN_LINK_QUERY,
    skip_prompt: bool = SKIP_PROMPT_QUERY,
    ui_options: str = UI_OPTIONS_QUERY,
    kbase_session: str | None = KBASE_SESSION_COOKIE,
    kbase_session_backup: str | None = KBASE_SESSION_BACKUP_COOKIE,
) -> RedirectResponse:
    # TODO: should be no json responses here!
    """
    Start Linking Session

    This endpoint is designed to be used directly by the browser. It is the "start"
    of the ORCID OAuth flow. If the provided session id is found and the associated
    session record is still in the initial state, it will initiate the OAuth flow
    by redirecting the browser to an endpoint at ORCID.

    Starts a "linking session", an interactive OAuth flow the end result of which is an
    access_token stored at KBase for future use by the user.
    """

    log_info(
        "Starting start_linking_session",
        "start",
        {
            "params": {
                "session_id": session_id,
                "return_link": return_link,
                "skip_prompt": skip_prompt,
                "ui_options": ui_options,
                "kbase_session": "REDACTED" if kbase_session is not None else "n/a",
                "kbase_session_backup": (
                    "REDACTED" if kbase_session_backup is not None else "n/a"
                ),
            }
        },
    )

    if kbase_session is None:
        if kbase_session_backup is None:
            raise UIError(
                NotAuthorizedError.CODE,
                "Linking requires authorization",
            )
        else:
            authorization = kbase_session_backup
    else:
        authorization = kbase_session

    _, token_info = await ensure_authorization_ui(authorization)

    # We don't need the record, but we want to ensure it exists
    # and is owned by this user.
    try:
        await get_linking_session_initial(session_id, token_info.user)
    except JSONRPCError as je:
        raise UIError(je.CODE, je.MESSAGE)

    # TODO: enhance session record to record the status - so that we can prevent
    # starting a session twice!

    model = storage_model()
    await model.update_linking_session_to_started(
        session_id, return_link, skip_prompt, ui_options
    )

    # The redirect uri is back to ourselves ... this completes the interaction with
    # ORCID, after which we redirect back to whichever url the front end wants to
    # return to.
    # But how to determine the path back here if we are running as a dynamic service?
    # Eventually this will be a core service, but for now let us solve this interesting
    # problem.
    # I think we just need to assume we are running on the "most released"; I don't
    # think there is a way for a dynamic service to know where it is running...
    params = AuthorizeParams(
        client_id=config().orcid_client_id,
        response_type="code",
        scope=config().orcid_scopes,
        redirect_uri=f"{config().orcidlink_url}/linking-sessions/oauth/continue",
        prompt="login",
        state=json.dumps({"session_id": session_id}),
    )
    url = f"{config().orcid_oauth_base_url}/authorize?{urlencode(params.model_dump())}"

    log_info(
        "Successfully started linking session",
        "success",
        {"redirection_url": url, "orcidlink_url": config().orcidlink_url},
    )

    return responses.RedirectResponse(url, status_code=302)


#
# Redirection target for linking.
#
# The provided "code" is very short-lived and must be exchanged for the
# long-lived tokens without allowing the user to dawdle over it.
#
# Yet we do want the user to verify the linking with full account info first.
# Even using the forced logout during ORCID authentication, the ORCID interface
# does not identify the account after login. Since their user ids are cryptic,
#
# it would be possible on a multi-user computer to use the wrong ORCID Id.
# So what we do is save the response and issue our own temporary token.
# Upon submitting that token to /finish-link link is made.
#
@router.get(
    "/oauth/continue",
    status_code=302,
    response_class=RedirectResponse,
    responses={
        302: {
            "description": "Redirect to the continuation page; or error page",
        },
        **AUTH_RESPONSES,
        **STD_RESPONSES,
        401: {
            "description": "Linking requires authorization; same meaning as standard "
            + "auth 401, but caught and issued in a different manner"
        },
    },
    tags=["linking-sessions"],
)
async def linking_sessions_continue(
    kbase_session: str | None = KBASE_SESSION_COOKIE,
    kbase_session_backup: str | None = KBASE_SESSION_BACKUP_COOKIE,
    code: str | None = Query(
        default=None,
        description="For a success case, contains an OAuth exchange code parameter",
    ),
    state: str | None = Query(
        default=None,
        description="For a success case, contains an OAuth state parameter",
    ),
    error: str | None = Query(
        default=None, description="For an error case, contains an error code parameter"
    ),
) -> RedirectResponse:
    # TODO: should be no json responses here@
    """
    Continue Linking Session

    This endpoint implements the handoff from from the ORCID authorization step in
    the ORCID OAuth flow. That is, it
    serves as the redirection target after the user has successfully completed
    their interaction with ORCID, at which they may have logged in and provided
    their consent to issuing the linking token to KBase.

    Note that this is an interstitional endpoint, which does not have its own
    user interface. Rather, it redirects to kbase-ui when finished. If an error is
    encountered, it redirects to an error viewing endpoint in kbase-ui.
    """
    log_info(
        "Starting start_linking_session",
        "start",
        {
            "params": {
                "code": "REDACTED" if code is not None else "n/a",
                "state": state,
                "error": error,
                "kbase_session": "REDACTED" if kbase_session is not None else "n/a",
                "kbase_session_backup": (
                    "REDACTED" if kbase_session_backup is not None else "n/a"
                ),
            }
        },
    )

    # Note that this is the target for redirection from ORCID,
    # and we don't have an Authorization header. We don't
    # (necessarily) have an auth cookie.
    # So we use the state to get the session id.
    if kbase_session is None:
        if kbase_session_backup is None:
            raise UIError(
                AuthorizationRequiredError.CODE, "Linking requires authentication"
            )
        else:
            authorization = kbase_session_backup
    else:
        authorization = kbase_session

    authorization, token_info = await ensure_authorization_ui(authorization)

    #
    # TODO: MAJOR: ensure ui error responses are working; refactor
    #

    if error is not None:
        # return ui_error_response(errors.ERRORS.linking_session_error, error)
        raise UIError(
            UpstreamError.CODE,
            "Error returned by ORCID OAuth",
            data={"originalError": error},
        )

    if code is None:
        raise UIError(
            InvalidParams.CODE, "The 'code' query param is required but missing"
        )
        # return ui_error_response(
        #     errors.ERRORS.linking_session_continue_invalid_param,
        #     "The 'code' query param is required but missing",
        # )

    if state is None:
        raise UIError(
            InvalidParams.CODE, "The 'state' query param is required but missing"
        )
        # return ui_error_response(
        #     errors.ERRORS.linking_session_continue_invalid_param,
        #     "The 'state' query param is required but missing",
        # )

    unpacked_state = json.loads(state)

    if "session_id" not in unpacked_state:
        raise UIError(
            InvalidParams.CODE,
            "The 'session_id' was not provided in the 'state' query param",
        )
        # return ui_error_response(
        #     errors.ERRORS.linking_session_continue_invalid_param,
        #     "The 'session_id' was not provided in the 'state' query param",
        # )

    session_id = unpacked_state.get("session_id")

    try:
        session_record = await get_linking_session_started(session_id, token_info.user)
    except JSONRPCError as be:
        raise UIError(be.CODE, be.MESSAGE)

    #
    # Exchange the temporary token from ORCID for the authorized token.
    #
    # Note that the ORCID OAuth API will throw a JSONRPC Exception, because that
    # is how they are normall used, but in this case we are in an interactive
    # http request in which the browser follows the url, so we need to convert
    # this to a UI Error.
    #
    try:
        orcid_auth = await orcid_oauth_api().exchange_code_for_token(code)
    except JSONRPCError as err:
        raise UIError(err.CODE, err.MESSAGE)

    #
    # Note that it isn't until this point that we know the orcid id the user
    # wants to link. So here we can detect if the orcid id has already
    # been linked. If so, it is an error.
    #
    model = storage_model()

    existing_orcid_auth = await model.get_link_record_for_orcid_id(orcid_auth.orcid)

    if existing_orcid_auth is not None:
        # Remove the session - it is not valid to use.
        await model.delete_linking_session_started(session_id)

        # TODO: send the orcid in case the user wants to investigate?
        # return ui_error_response(
        #     errors.ERRORS.linking_session_already_linked_orcid,
        #     "The chosen ORCID account is already linked to another KBase account",
        # )
        raise UIError(
            AlreadyLinkedError.CODE,
            ("The chosen ORCID account is already linked to another " "KBase account"),
        )

    #
    # Now we store the response from ORCID in our session.
    # We still need the user to finalize the linking, now that it has succeeded
    # which is done in finalize-linking-session.
    #

    # Note that this is approximate, as it uses our time, not the
    # ORCID server time.

    await model.update_linking_session_to_finished(session_id, orcid_auth)

    #
    # Redirect back to the orcidlink interface, with some
    # options that support integration into workflows.
    #
    params: dict[str, str] = {}

    if session_record.return_link is not None:
        params["return_link"] = session_record.return_link

    params["skip_prompt"] = "true" if session_record.skip_prompt else "false"
    params["ui_options"] = session_record.ui_options

    url = f"{config().ui_origin}?{urlencode(params)}#orcidlink/continue/{session_id}"

    log_info(
        "Successfully continued linking session", "success", {"redirection_url": url}
    )

    return RedirectResponse(url, status_code=302)
