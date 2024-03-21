from enum import Enum
from typing import Optional

from pydantic import Field

from orcidlink.jsonrpc.errors import (
    JSONRPCError,
    ORCIDNotAuthorizedError,
    UpstreamError,
)

# from orcidlink.lib.service_clients.orcid_api import (
#     ORCIDAPIClientInvalidAccessTokenError, ORCIDAPIClientOtherError
# )
from orcidlink.lib.type import ServiceBaseModel

#
# The OAuth Bearer error has the same basic shape as the basic OAuth error,
# but the range of error codes (see the enum below) is different.
#
# These are the error codes that can be returned.
#
# See: https://www.rfc-editor.org/rfc/rfc6749#section-5.2
#
# invalid_request
#     The request is missing a required parameter, includes an
#     unsupported parameter value (other than grant type),
#     repeats a parameter, includes multiple credentials,
#     utilizes more than one mechanism for authenticating the
#     client, or is otherwise malformed.

# invalid_client
#     Client authentication failed (e.g., unknown client, no
#     client authentication included, or unsupported
#     authentication method).  The authorization server MAY
#     return an HTTP 401 (Unauthorized) status code to indicate
#     which HTTP authentication schemes are supported.  If the
#     client attempted to authenticate via the "Authorization"
#     request header field, the authorization server MUST
#     respond with an HTTP 401 (Unauthorized) status code and
#     include the "WWW-Authenticate" response header field
#     matching the authentication scheme used by the client.

# invalid_grant
#     The provided authorization grant (e.g., authorization
#     code, resource owner credentials) or refresh token is
#     invalid, expired, revoked, does not match the redirection
#     URI used in the authorization request, or was issued to
#     another client.

# unauthorized_client
#     The authenticated client is not authorized to use this
#     authorization grant type.

# unsupported_grant_type
#     The authorization grant type is not supported by the
#     authorization server.

# invalid_scope
#     The requested scope is invalid, unknown, malformed, or
#     exceeds the scope granted by the resource owner.


class OAUthAPIErrorType(str, Enum):
    invalid_request = "invalid_request"
    invalid_client = "invalid_client"
    invalid_grant = "invalid_grant"
    unauthorized_client = "unauthorized_client"
    unsuppported_grant_type = "unsupported_grant_type"
    invalid_scope = "invalid_scope"


class OAuthAPIError(ServiceBaseModel):
    """
    Although the name implies it is only for OAuth API errors, it may also be returned
    for authentication-related errors via the ORCID API.

    See https://datatracker.ietf.org/doc/html/rfc6749#page-45
    """

    error: OAUthAPIErrorType = Field(...)
    error_description: Optional[str] = Field(default=None)
    error_uri: Optional[str] = Field(default=None)


class ORCIDOAuthAPIErrorDetail(ServiceBaseModel):
    upstream_error: OAuthAPIError


def orcid_oauth_api_to_json_rpc_error(error: OAuthAPIError) -> JSONRPCError:
    """
    Converts an "interactive oauth" error to a JSON-RPC error to be returned
    by the request, or perhaps converted into a ui-error response.

    At present we do not create specific responses - such an error should be
    quite rare and would indicate some sort of systemwide error, so all we can
    really do is report it, which UpstreamError can do just fine.
    """
    error_detail = ORCIDOAuthAPIErrorDetail(upstream_error=error).model_dump()
    if error.error == OAUthAPIErrorType.invalid_request:
        raise UpstreamError(data=error_detail)
    elif error.error == OAUthAPIErrorType.invalid_client:
        raise UpstreamError(data=error_detail)
    elif error.error == OAUthAPIErrorType.invalid_grant:
        raise ORCIDNotAuthorizedError(data=error_detail)
    elif error.error == OAUthAPIErrorType.unauthorized_client:
        raise ORCIDNotAuthorizedError(data=error_detail)
    elif error.error == OAUthAPIErrorType.unsuppported_grant_type:
        raise UpstreamError(data=error_detail)
    else:
        # This last case is not possible, but pyright cannot determine
        # that we have exausted all the possible cases here, so we need
        # to tie this up with a catch-all (even though the construction)
        # of the error object would raise an error if the error code was
        # out of range.
        raise UpstreamError(data=error_detail)
