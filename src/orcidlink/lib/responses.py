import json
from typing import Any, Dict, List, Mapping, Optional, Union
from urllib.parse import urlencode

from fastapi import Body, Header
from fastapi.responses import RedirectResponse
from pydantic import Field

# from orcidlink.lib.errors import ErrorCode2, ErrorResponse
from orcidlink.lib.type import ServiceBaseModel
from orcidlink.runtime import config

##
# Common http responses, implemented as response-generating functions.
#

# def json_rpc_error_response(error_code: int, message: str, data: Any = None):
#     # Rather informal for now. jsonrpc-fastapi does have a json-rpc
#     # error structure.
#     error_content = {
#         "jsonrpc": "2.0",

#     }
#     return JSONResponse(
#         status_code=200,
#         content=jsonable_encoder(response_content, exclude_unset=True),
#     )


# def error_response2(
#     # response_content: ErrorResponse[ServiceBaseModel],
#     response_content: Any,
#     status_code: int = 400,
# ) -> JSONResponse:
#     return JSONResponse(
#         status_code=status_code,
#         content=jsonable_encoder(response_content, exclude_unset=True),
#     )


# def error_response(
#     error: ErrorCode2,
#     message: str,
#     data: Optional[ServiceBaseModel] = None,
#     status_code: int = 400,
# ) -> JSONResponse:
#     response = ErrorResponse[ServiceBaseModel](
#         code=error.code,
#         title=error.title,
#         message=message,
#     )

#     if data is not None:
#         response.data = data

#     return JSONResponse(
#         status_code=status_code, content=jsonable_encoder(response, exclude_unset=True)
#     )


class ExceptionTraceback(ServiceBaseModel):
    filename: str = Field(...)
    line_number: Optional[int] = Field(
        default=None, validation_alias="line-number", serialization_alias="line-number"
    )
    name: str = Field(...)
    line: Optional[str] = Field(default=None)


class ExceptionData(ServiceBaseModel):
    exception: str = Field(...)
    traceback: List[ExceptionTraceback]


# def exception_error_response(
#     error: ErrorCode2,
#     exception: Exception,
#     status_code: int = 400,
# ) -> JSONResponse:
#     traceback = []
#     for tb in extract_tb(exception.__traceback__):
#         traceback.append(
#             ExceptionTraceback(
#                 filename=tb.filename, line_number=tb.lineno, name=tb.name, line=tb.line
#             )
#         )

#     data = ExceptionData(exception=str(exception), traceback=traceback)

#     response = ErrorResponse[Any](
#         code=error.code,
#         title=error.title or "Exception",
#         message=str(exception),
#         data=data,
#     )

#     return JSONResponse(
#         status_code=status_code, content=jsonable_encoder(response, exclude_unset=True)
#     )


# def ui_error_responsex(error: ErrorCode2, message: str) -> RedirectResponse:
#     error_params = urlencode(
#         {"code": error.code, "title": error.title, "message": message}
#     )
#     return RedirectResponse(
#         f"{config().ui_origin}?{error_params}#orcidlink/error", status_code=302
#     )


def ui_error_response(
    code: int, message: str, data: Optional[Any] = None
) -> RedirectResponse:
    raw_error = {"code": code, "message": message}

    # The data from an error may be arbitrary data - it means something to the
    # specific error
    if data is not None:
        raw_error["data"] = json.dumps(data)

    error_params = urlencode(raw_error)
    return RedirectResponse(
        f"{config().ui_origin}/orcidlink/error?{error_params}", status_code=302
    )


class UIError(Exception):
    def __init__(self, code: int, message: str, data: Optional[Any] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


#
# Specific canned error responses.
#


AUTHORIZATION_HEADER = Header(
    default=None,
    description="KBase auth token",
    min_length=32,
    max_length=32,
)

USERNAME_PARAM = Body(..., description="KBase username")

SESSION_ID_PARAM = Body(..., description="KBase linking session identifier")

PUT_CODE_PARAM = Body(..., description="ORCID Work activity record put code")

ResponseMapping = Mapping[Union[int, str], Dict[str, Any]]

AUTH_RESPONSES: ResponseMapping = {
    401: {
        "description": "KBase auth token absent or invalid",
        #   "model": ErrorResponse
    },
    # 403: {"description": "KBase auth token invalid", "model": ErrorResponse},
}

STD_RESPONSES: ResponseMapping = {
    422: {
        "description": "Input or output data does not comply with the API schema",
        # "model": ErrorResponse,
    }
}
