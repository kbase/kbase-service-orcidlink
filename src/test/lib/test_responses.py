import os
from test.mocks.env import TEST_ENV
from unittest import mock
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.responses import RedirectResponse

from orcidlink.lib.responses import ui_error_response


@pytest.fixture
def fake_fs(fs):
    data_dir = os.environ["TEST_DATA_DIR"]
    fs.add_real_directory(data_dir)
    yield fs


# def test_error_response():
#     class TestData(ServiceBaseModel):
#         some: str

#     value = error_response(
#         ERRORS.impossible_error,
#         "message",
#         data=TestData(some="data"),
#         status_code=123,
#     )
#     assert isinstance(value, JSONResponse)
#     assert value.status_code == 123
#     # The JSONResponse structure is not in scope for this project; it is simply provided
#     # to fastapi which utilizes it for the response
#     assert value.body is not None


# def test_exception_error_response():
#     try:
#         raise Exception("I am exceptional")
#     except Exception as ex:
#         value = exception_error_response(ERRORS.impossible_error, ex, status_code=123)
#         assert isinstance(value, JSONResponse)
#         assert value.status_code == 123
#         # The JSONResponse structure is not in scope for this project; it is simply
#         # provided to fastapi which utilizes it for the response.
#         #
#         # Still, the whole point of testing this is to assure ourselves that the
#         # response is as we expect, so ... here we go.
#         assert value.body is not None
#         data = json.loads(value.body)
#         assert data["code"] == ERRORS.impossible_error.code
#         assert data["title"] == ERRORS.impossible_error.title
#         assert data["message"] == "I am exceptional"
#         assert isinstance(data["data"]["traceback"], list)


# def test_exception_error_response_no_data():
#     try:
#         raise Exception("I am exceptional")
#     except Exception as ex:
#         value = exception_error_response(ERRORS.impossible_error, ex, status_code=123)
#         assert isinstance(value, JSONResponse)
#         assert value.status_code == 123
#         # The JSONResponse structure is not in scope for this project; it is simply
#         # provided to fastapi which utilizes it for the response.
#         #
#         # Still, the whole point of testing this is to assure ourselves that the
#         # response is as we expect, so ... here we go.
#         assert value.body is not None
#         data = json.loads(value.body)
#         assert data["code"] == ERRORS.impossible_error.code
#         assert data["title"] == ERRORS.impossible_error.title
#         assert data["message"] == "I am exceptional"
#         assert data["data"]["exception"] == "I am exceptional"
#         assert isinstance(data["data"]["traceback"], list)


def as_str(something: str | bytes) -> str:
    if isinstance(something, str):
        return something
    else:
        return str(something, encoding="utf-8")


def test_ui_error_response(fake_fs):
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        value = ui_error_response(123, "message")
        assert isinstance(value, RedirectResponse)
        assert value.status_code == 302
        assert "location" in value.headers
        location_value = value.headers.get("location")
        assert location_value is not None
        url = urlparse(location_value)
        assert url.scheme == "http"
        assert url.hostname == "127.0.0.1"
        assert url.path == "/orcidlink/error"
        # assert url.query
        # annoyingly, may be string or bytes, so coerce, primarily to make
        # typing happy.
        query_string = as_str(url.query)
        query = parse_qs(query_string)  # type: ignore
        assert "code" in query
        assert query["code"] == [str(123)]
