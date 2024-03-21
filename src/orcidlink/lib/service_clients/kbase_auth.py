"""
A basic KBase auth client for the Python server.

The SDK version has been modified to integrate with this codebase, such as
using httpx, pydantic models.
"""

import json
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import Field

from orcidlink.jsonrpc import errors
from orcidlink.lib.responses import UIError
from orcidlink.lib.type import ServiceBaseModel

#
# Auth Exceptions
#
# Note that these should be caught by an adapter layer which will translate the
# errors into either JSON-RPC 2.0 error responses or UI error redirects.
#


class AuthError(Exception):
    message: str
    data: Optional[Any]

    def __init__(self, message: str, data: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.data = data


class AuthorizationRequiredAuthError(AuthError):
    pass


class ContentTypeAuthError(AuthError):
    pass


class JSONDecodeAuthError(AuthError):
    pass


class OtherAuthError(AuthError):
    pass


#
# Types in support of the auth api.
#


class TokenInfo(ServiceBaseModel):
    type: str = Field(...)
    id: str = Field(...)
    expires: int = Field(...)
    created: int = Field(...)
    name: str | None = Field(...)
    user: str = Field(...)
    custom: Dict[str, str] = Field(...)
    cachefor: int = Field(...)


class Identity(ServiceBaseModel):
    id: str = Field(...)
    provider: str = Field(...)
    provusername: str = Field(...)


class Role(ServiceBaseModel):
    id: str = Field(...)
    desc: str = Field(...)


class PolicyAgreement(ServiceBaseModel):
    id: str = Field(...)
    agreedon: int = Field(...)


class AccountInfo(ServiceBaseModel):
    user: str = Field(...)
    display: str = Field(...)
    email: str = Field(...)
    created: int = Field(...)
    lastlogin: int = Field(...)
    local: bool = Field(...)
    roles: List[Role] = Field(...)
    customroles: List[str] = Field(...)
    idents: List[Identity] = Field(...)
    policyids: List[PolicyAgreement]


class KBaseAuth(object):
    """
    A basic KBase auth client which only implements methods utilized by this service.

    Note that this is not a caching client. The primary task of auth in the service
    is to validate a token, and to obtain the username and roles for the user who owns
    the token.
    """

    def __init__(
        self,
        url: str,
        timeout: int,
    ):
        """
        Constructor
        """
        self.url = url
        self.timeout = timeout

    async def _get(self, path: str, authorization: str) -> Any:
        """
        General purpose "GET request" request and response implementation for the auth
        service V2 api.

        It can handle any endpoint which uses the GET request method, as it is
        agnostic about the structure of the response.

        It raises several errors, under the following conditions:

        - ContentTypeError - if the wrong content type (not application/json)
          is returned (raised by aiohttp)
        - JSONDecodeError - if the response does not parse correctly as
          JSON (raised by aiohttp)
        - AuthorizationRequiredAuthError - if the error returned by the
          auth service is 10020 (invalid token),
        - OtherAuthError - for any other error reported by the auth service
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.url}/api/V2/{path}"
                async with session.get(
                    url, headers={"authorization": authorization}, timeout=self.timeout
                ) as response:
                    json_result = await response.json()

        except aiohttp.ContentTypeError as cte:
            # Raised if it is not application/json
            # data = exceptions.ContentTypeErrorData()
            # if cte.headers is not None:
            #     data.originalContentType = cte.headers["content-type"]
            error_data: Dict[str, Any] = {}
            if cte.headers is not None:
                error_data["originalContentType"] = cte.headers["content-type"]

            raise ContentTypeAuthError("Wrong content type", error_data) from cte

        except json.JSONDecodeError as jde:
            raise JSONDecodeAuthError(
                "Error decoding JSON response", {"decodeErrorMessage": str(jde)}
            ) from jde

        except aiohttp.ClientConnectionError:
            # TODO: should be own bespoke error?
            raise OtherAuthError("Error connecting to auth service")

        if not response.ok:
            # We don't care about the HTTP response code, just the appcode in the
            # response data.
            appcode = json_result["error"]["appcode"]
            json_result["error"]["message"]
            if appcode == 10020:
                raise AuthorizationRequiredAuthError("Authorization Required")
            else:
                raise OtherAuthError("Error authenticating with auth service")

        return json_result

    async def get_token_info(self, token: str) -> TokenInfo:
        """
        Fetches token information from the auth service and returns it in a
        Pydantic class matching the original structure.

        Other than errors thrown by _get, it may throw a ValidationError if the data
        returned from the auth service is not compliant with the TokenInfo type
        """
        json_result = await self._get("token", token)

        return TokenInfo.model_validate(json_result)

    async def get_me(self, token: str) -> AccountInfo:
        """
        Fetches user account information from the auth service and returns it in a
        Pydantic class matching the original structure.

        Other than errors thrown by _get, it may throw a ValidationError if the data
        returned from the auth service is not compliant with the AccountINfo type
        """
        if token == "":
            raise AuthorizationRequiredAuthError("Token may not be empty")

        json_result = await self._get("me", token)

        # TODO: we need this model validation to trigger a ui error.
        # though, to be fair, this would be an internal error, not something the user
        # can do anything about.
        return AccountInfo.model_validate(json_result)


def auth_error_to_jsonrpc_error(error: AuthError) -> errors.JSONRPCError:
    """
    An adapter for an AuthError, as defined in this module, to a JSONPRCError.

    Designed to be used in JSONRPC methods to so that auth errors may propagate
    naturally in that context.
    """
    if isinstance(error, AuthorizationRequiredAuthError):
        return errors.AuthorizationRequiredError(error.message)
    elif isinstance(error, ContentTypeAuthError):
        return errors.ContentTypeError(error.message)
    elif isinstance(error, JSONDecodeAuthError):
        return errors.JSONDecodeError(error.message)
    elif isinstance(error, OtherAuthError):
        return errors.UpstreamError(error.message)
    else:
        return errors.UpstreamError(error.message)


def auth_error_to_ui_error(error: AuthError) -> UIError:
    """
    An adapter for an AuthError, as defined in this module, to a UIError.

    Designed to be used in JSONRPC methods to so that auth errors may propagate
    naturally in that context.

    Note that the auth error -> jsonrpc error transformation is applied first, as the
    same code and message are sent as ui errors.
    """
    json_rpc_error = auth_error_to_jsonrpc_error(error)
    # Weird that the BaseError from jsonrpc-fastapi has code as optional;
    # imo it should be required, as the spec requires it
    return UIError(
        code=json_rpc_error.CODE or 0, message=error.message, data=error.data
    )
