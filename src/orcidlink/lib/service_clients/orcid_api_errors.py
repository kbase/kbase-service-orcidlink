# This is one form of error message returned by ORCID API
from enum import Enum
from typing import Optional

from pydantic import Field

from orcidlink.jsonrpc.errors import (
    JSONRPCError,
    ORCIDInsufficientAuthorizationError,
    ORCIDNotAuthorizedError,
    ORCIDNotFoundError,
    UpstreamError,
)
from orcidlink.lib.json_support import JSONObject
from orcidlink.lib.service_clients.orcid_api_error_codes import (
    ORCIDAPIErrorCategory,
    get_orcid_api_error,
)
from orcidlink.lib.type import ServiceBaseModel


class ORCIDAPIError(ServiceBaseModel):
    """
    One form of error response from the ORCID API.
    """

    response_code: int = Field(
        validation_alias="response-code", serialization_alias="response-code"
    )
    developer_message: str = Field(
        validation_alias="developer-message", serialization_alias="developer-message"
    )
    user_message: str = Field(
        validation_alias="user-message", serialization_alias="user-message"
    )
    error_code: int = Field(
        validation_alias="error-code", serialization_alias="error-code"
    )
    more_info: str = Field(
        validation_alias="more-info", serialization_alias="more-info"
    )


#
# The OAuth Bearer error has the same basic shape as the basic OAuth error,
# but the range of error codes (see the enum below) is different.
#
#  SEE https://www.rfc-editor.org/rfc/rfc6750
#
class OAUthBearerErrorType(str, Enum):
    # for bearer tokens
    invalid_request = "invalid_request"
    invalid_token = "invalid_token"
    insufficient_scope = "insufficient_scope"


class OAuthBearerError(ServiceBaseModel):
    """
    Although the name implies it is only for OAuth API errors, it may also be returned
    for authentication-related errors via the ORCID API.

    See https://datatracker.ietf.org/doc/html/rfc6749#page-45
    """

    error: OAUthBearerErrorType = Field(...)
    error_description: Optional[str] = Field(default=None)
    error_uri: Optional[str] = Field(default=None)


class ORCIDAPIOtherErrorDetail(ServiceBaseModel):
    upstream_error: JSONObject


class ORCIDOAuthBearerErrorDetail(ServiceBaseModel):
    upstream_error: OAuthBearerError


#
# The general OAuth error, as may be encountered during OAuth flow
#


class OAUthErrorEnum(str, Enum):
    invalid_request = "invalid_request"
    invalid_client = "invalid_client"
    invalid_grant = "invalid_grant"
    unauthorized_client = "unauthorized_client"
    unsupported_grant_type = "unsupported_grant_type"
    invalid_scope = "invalid_scope"


# class OAuthError(ServiceBaseModel):
#     """
#     Although the name implies it is only for OAuth API errors, it may also be returned
#     for authentication-related errors via the ORCID API.

#     See https://datatracker.ietf.org/doc/html/rfc6749#page-45
#     """

#     error: OAUthErrorEnum = Field(...)
#     error_description: Optional[str] = Field(default=None)
#     error_uri: Optional[str] = Field(default=None)


class ORCIDAPIErrorDetail(ServiceBaseModel):
    upstream_error: ORCIDAPIError


def orcid_api_error_to_json_rpc_error(api_error: ORCIDAPIError) -> JSONRPCError:
    error_code = get_orcid_api_error(api_error.error_code)
    error_detail = ORCIDAPIErrorDetail(upstream_error=api_error).model_dump
    if error_code is None:
        return UpstreamError(data=error_detail)
    elif error_code.category == ORCIDAPIErrorCategory.connection:
        return UpstreamError(data=error_detail)
    elif error_code.category == ORCIDAPIErrorCategory.bad_request:
        return UpstreamError(data=error_detail)
    elif error_code.category == ORCIDAPIErrorCategory.internal_error:
        return UpstreamError(data=error_detail)
    elif error_code.category == ORCIDAPIErrorCategory.not_authorized:
        return ORCIDNotAuthorizedError(data=error_detail)
    elif error_code.category == ORCIDAPIErrorCategory.insufficient_authorization:
        return ORCIDInsufficientAuthorizationError(data=error_detail)
    elif error_code.category == ORCIDAPIErrorCategory.not_found:
        return ORCIDNotFoundError(data=error_detail)
    elif error_code.category == ORCIDAPIErrorCategory.other_error:
        return UpstreamError(data=error_detail)
    else:
        return UpstreamError(data=error_detail)


def orcid_oauth_bearer_to_json_rpc_error(error: OAuthBearerError) -> JSONRPCError:
    error_detail = ORCIDOAuthBearerErrorDetail(upstream_error=error).model_dump()
    if error.error == OAUthBearerErrorType.invalid_token:
        # This indicates that either the token is actually malformed, or, in the
        # context of ORCID Link, that that the token has become invalid at
        # ORCID. The most likely cause being the user directly removing
        # authorization for KBase.
        raise ORCIDNotAuthorizedError(data=error_detail)
    elif error.error == OAUthBearerErrorType.invalid_request:
        raise UpstreamError(data=error_detail)
    elif error.error == OAUthBearerErrorType.insufficient_scope:
        raise ORCIDInsufficientAuthorizationError(data=error_detail)
    else:
        raise UpstreamError(data=error_detail)
