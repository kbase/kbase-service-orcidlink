from dataclasses import asdict, dataclass
from typing import Any, Optional

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette.responses import JSONResponse

from orcidlink.lib.json_file import JSONLikeObject


@dataclass
class ErrorCode:
    code: str
    title: str
    description: str
    status_code: int


REQUEST_PARAMETERS_INVALID = ErrorCode(
    code="requestParametersInvalid",
    title="Request Parameters Invalid",
    description="The request parameters (path, query, cooke) does not comply with the schema. "
    + "This indicates a mis-use of the API and should typically only be encountered "
    + "during development",
    status_code=422,
)

INVALID_TOKEN = ErrorCode(
    code="invalidToken",
    title="Invalid Token",
    description="Converted from an auth client exception, which in turn is in response to the auth "
    + "service reporting an invalid token",
    status_code=401,
)

TOKEN_REQUIRED_BUT_MISSING = ErrorCode(
    code="authorizationRequired",
    title="Authorization Required",
    description="The resource requires authorization, but not is present ",
    status_code=401,
)

ORCID_INVALID_TOKEN = ErrorCode(
    code="orcidInvalidToken",
    title="ORCID Invalid Token",
    description="""
Converted from an the ORCID API client exception, which in turn is in response to ORCID 
api reporting an invalid token. In all probability, this is due to the user having removed 
access for KBase.
""",
    status_code=401,
)

INTERNAL_SERVER_ERROR = ErrorCode(
    code="internalServerError",
    title="Internal Server Error",
    description="The good ol generalized internal server error, meaning that something unexpected "
    + "broke within the codebase and cannot be (or at least is not) handled any better "
    + "or more specifically.",
    status_code=500,
)

NOT_FOUND = ErrorCode(
    code="notFound",
    title="Not Found",
    description="The resource or some component of it could not be located. We define this ourselves "
    + "since we want to return ALL errors in our error structure.",
    status_code=404,
)

FASTAPI_ERROR = ErrorCode(
    code="fastapiError",
    title="FastAPI Error",
    description="Some other error raised by FastAPI. We let the raised error determine the status code.",
    status_code=500,
)

NOT_JSON = ErrorCode(
    code="badContentType",
    title="Received Incorrect Content Type",
    description="Expected application/json for a json response",
    status_code=502,
)

JSON_DECODE_ERROR = ErrorCode(
    code="jsonDecodeError",
    title="Error Decoding Response",
    description="An error was encountered parsing, or decoding, the JSON response string",
    status_code=502,
)

#
#
# XXX = ErrorCode(
#     id="",
#     description="",
#     status_code=123
# )


# errors = {
#     "requestParametersInvalid": {
#         "description": "The request parameters (path, query, cooke) does not comply with the schema. "
#                        + "This indicates a mis-use of the API and should typically only be encountered "
#                        + "during development",
#         "status_code": 422,
#     },
#     "invalidToken": {
#         "description": "Converted from an auth client exception, which in turn is in response to the auth "
#                        + "service reporting an invalid token",
#         "statusCode": 401,
#     },
#     "internalServerError": {
#         "description": "The good ol generalized internal server error, meaning that something unexpected "
#                        + "broke within the codebase and cannot be (or at least is not) handled any better "
#                        + "or more specifically.",
#         "statusCode": 500,
#     },
#     "notFound": {
#         "description": "The resource or some component of it could not be located. We define this ourselves "
#                        + "since we want to return ALL errors in our error structure.",
#         "statusCode": 404,
#     },
#     "fastapiError": {
#         "description": "Some other error raised by FastAPI. We let the raised error determine the status code.",
#         # TODO: is this a good idea? Perhaps we should always raise a 500 and document the original status
#         # code in the data?
#         "statusCode": None,
#     },
# }


class ServiceError(Exception):
    """
    An exception wrapper for an ErrorResponse and status_code.

    This is the exception to throw if you want to specify the
    specific error response.
    """

    error: Any
    status_code: int

    def __init__(self, error: Any, status_code: int):
        super().__init__(error.message)
        self.error = error
        self.status_code = status_code

    def get_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.status_code,
            content=jsonable_encoder(self.error, exclude_unset=True),
        )


class ServiceErrorXX(Exception):
    """
    An exception wrapper for an ErrorResponse and status_code.

    This is the exception to throw if you want to specify the
    specific error response.
    """

    error_code: ErrorCode

    def __init__(
        self, error_code: ErrorCode, message: str, data: JSONLikeObject | None = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.data = data

    def get_response(self) -> JSONResponse:
        content = asdict(self.error_code)
        # We always supply this data
        data = {
            "description": self.error_code.description,
            "status_code": self.error_code.status_code,
        }
        # Add more data ...
        if self.data is not None:
            data.update(self.data)

        content = {
            "message": self.message,
            "code": self.error_code.code,
            "data": data,
        }
        content["message"] = self.message
        return JSONResponse(status_code=self.error_code.status_code, content=content)


class ServiceErrorX(Exception):
    """
    An exception wrapper for an ErrorResponse and status_code.

    This is the exception to throw if you want to specify the
    specific error response.
    """

    code: str
    title: str
    description: str
    status_code: Optional[int]

    def __init__(
        self,
        code: str,
        title: str,
        message: str,
        data: Any = None,
        status_code: Optional[int] = None,
    ):
        super().__init__(message)
        self.code = code
        self.title = title
        self.message = message
        self.data = data
        self.status_code = status_code

    def get_response(self) -> JSONResponse:
        content = {"code": self.code, "title": self.title, "message": self.message}
        if self.data is not None:
            content["data"] = self.data
        return JSONResponse(status_code=self.status_code or 500, content=content)


# class ClientError(ServiceErrorX):
#     def __init__(self, status_code: int, message: str, data: Any = None):
#         super().__init__("clientError", "Client Error", message, data, status_code)


class AlreadyLinkedError(ServiceErrorX):
    def __init__(self, message: str, data: Any = None):
        super().__init__("alreadyLinked", "Already LInked", message, data, 400)


class AuthTokenRequiredError(ServiceErrorX):
    def __init__(self, message: str, data: Any = None):
        super().__init__("authTokenRequired", "Auth Token Required", message, data, 401)


class UnauthorizedError(ServiceErrorX):
    def __init__(self, message: str, data: Any = None):
        super().__init__("notAuthorized", "Not Authorized", message, data, 403)


class NotFoundError(ServiceErrorX):
    def __init__(self, message: str, data: Any = None):
        super().__init__("notFound", "Not Found", message, data, 404)


class InternalError(ServiceErrorX):
    def __init__(self, message: str, data: Any = None):
        super().__init__("internalError", "Internal Error", message, data, 500)


class UpstreamError(ServiceErrorX):
    def __init__(self, message: str, data: Any = None):
        super().__init__("upstreamError", "Upstream Error", message, data, 502)


# Standard JSON-RPC 2.0 errors

# See: https://www.jsonrpc.org/specification#error_object
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
SERVER_ERROR_MIN = -32000
SERVER_ERROR_MAX = -32099

# Our own errors.
# TODO
