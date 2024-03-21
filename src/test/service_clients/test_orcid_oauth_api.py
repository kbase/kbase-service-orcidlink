import os
from test.mocks.env import MOCK_ORCID_OAUTH_PORT, TEST_ENV
from test.mocks.mock_contexts import mock_orcid_oauth_service, no_stderr
from unittest import mock

import pytest

from orcidlink.jsonrpc.errors import (
    ContentTypeError,
    JSONDecodeError,
    ORCIDNotAuthorizedError,
    UpstreamError,
)
from orcidlink.lib.json_support import json_path
from orcidlink.lib.service_clients import orcid_api
from orcidlink.lib.service_clients.orcid_oauth_api import (
    ORCIDOAuthAPIClient,
    orcid_oauth_api,
)

# Set up test data here; otherwise the ENV mocking interferes with the
# TEST_DATA_DIR env var which points to the location of test data!

TEST_DATA_DIR = os.environ["TEST_DATA_DIR"]


@pytest.fixture
def fake_fs(fs):
    data_dir = os.environ["TEST_DATA_DIR"]
    fs.add_real_directory(data_dir)
    yield fs


@pytest.fixture(scope="function")
def my_fs(fs):
    yield fs


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_orcid_api_url(fake_fs):
    value = orcid_api.orcid_api_url("path")
    assert isinstance(value, str)
    assert value == f"{TEST_ENV['ORCID_API_BASE_URL']}/path"


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_orcid_api():
    value = orcid_api.orcid_api("token")
    assert isinstance(value, orcid_api.ORCIDAPIClient)
    assert value.access_token == "token"


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_orcid_oauth():
    value = orcid_oauth_api()
    assert isinstance(value, ORCIDOAuthAPIClient)
    # assert isinstance(value.url, str)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_ORCIDOAuthClient_url():
    client = ORCIDOAuthAPIClient(url="url")
    url = client.url_path("foo")
    assert url == "url/foo"


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_ORCIDOAuthClient_header():
    client = ORCIDOAuthAPIClient(url="url")
    header = client.header()
    assert header.get("accept") == "application/json"
    assert header.get("content-type") == "application/x-www-form-urlencoded"


class FakeResponse:
    def __init__(self, status_code: int | None = None, text: str | None = None):
        self.status_code = status_code
        self.text = text


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# def test_ORCIDAuthClient_make_upstream_errorxx():
#     #
#     # Error response in expected form, with a JSON response including
#     # "error_description"
#     #

#     with pytest.raises(exceptions.ServiceErrorY) as exx:
#         raise exceptions.NotFoundError("ORCID User Profile Not Found")
#     # assert exx.value.status_code == 404
#     assert exx.value.error.code == ERRORS.not_found.code
#     assert exx.value.message == "ORCID User Profile Not Found"


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# def test_ORCIDAuthClient_make_upstream_error():
#     #
#     # Error response in expected form, with a JSON response including
#     # "error_description"
#     #
#     error_result = {"error_description": "bar"}
#     status_code = 123

#     with pytest.raises(exceptions.UpstreamORCIDAPIError) as ex:
#         raise exceptions.make_upstream_error(status_code, error_result, "source")

#     # assert ex.value.status_code == 502
#     assert ex.value.data is not None and ex.value.data.source == "source"
#     # TODO: more error properties
#     # assert ex.value.error.data["originalResponseJSON"]["error_description"] == "bar"
#     # assert "originalResponseText" not in ex.value.error.data

#     #
#     # Error response in expected form, with a JSON response without "error_description";
#     # Note that we don't make assumptions about any other field, and in this case, only
#     # in the case of a 401 or 403 status code, in order to remove private information.
#     #
#     error_result = {"foo": "bar"}
#     status_code = 123

#     with pytest.raises(exceptions.UpstreamORCIDAPIError) as ex:
#         raise exceptions.make_upstream_error(status_code, error_result, "source")

#     # assert ex.value.status_code == 502
#     assert ex.value.data is not None and ex.value.data.source == "source"
#     # TODO: more error properties
#     # assert "error_description" not in ex.value.error.data["originalResponseJSON"]
#     # assert ex.value.error.data["originalResponseJSON"]["foo"] == "bar"
#     # assert "originalResponseText" not in ex.value.error.data

#     #
#     # Error response in expected form, with a JSON response without "error_description";
#     # Note that we don't make assumptions about any other field, and in this case, only
#     # in the case of a 401 or 403 status code, in order to remove private information.
#     #
#     error_result = {"error_description": "bar", "foo": "foe"}
#     status_code = 401

#     with pytest.raises(exceptions.UpstreamORCIDAPIError) as ex:
#         raise exceptions.make_upstream_error(status_code, error_result, "source")

#     # assert ex.value.status_code == 502
#     assert ex.value.data is not None and ex.value.data.source == "source"
#     # TODO: more error properties
#     # assert "error_description" not in ex.value.error.data["originalResponseJSON"]
#     # assert ex.value.error.data["originalResponseJSON"]["foo"] == "foe"
#     # assert "originalResponseText" not in ex.value.error.data

#     #
#     # Finally, we need to be able to handle no-content responses from ORCID.
#     #
#     error_result = None
#     status_code = 401

#     with pytest.raises(exceptions.UpstreamORCIDAPIError) as ex:
#         raise exceptions.make_upstream_error(status_code, error_result, "source")

#     # assert ex.value.status_code == 502
#     assert ex.value.data is not None and ex.value.data.source == "source"
#     # TODO: more error properties
#     # assert "originalResponseJSON" not in ex.value.error.data
#     # assert ex.value.error.data["originalResponseText"] == "just text, folks"

#
# Revoke token
#


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_orcid_oauth_revoke_access_token_success():
    """
    The happy path
    """
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, _]:
            client = ORCIDOAuthAPIClient(url)
            response = await client.revoke_access_token("access_token")
            assert response is None


# This test doesn't make any sense -- the error is not thrown
@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_orcid_oauth_revoke_access_token_not_authorized_error():
    """
    A call to revoke an ORCID access token with a token which returns the
    "unauthorized_client" error.

    TODO: how to replicate
    """
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            client = ORCIDOAuthAPIClient(url)
            with pytest.raises(ORCIDNotAuthorizedError) as err:
                await client.revoke_access_token("error-unauthorized-client")
            assert err.value.CODE == ORCIDNotAuthorizedError.CODE
            found, error = json_path(err.value.data, ["upstream_error", "error"])
            assert found is True
            assert error == "unauthorized_client"


# This test doesn't make any sense -- the error is not thrown
@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_orcid_oauth_revoke_access_token_other_upstream_error():
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            client = ORCIDOAuthAPIClient(url)
            with pytest.raises(UpstreamError) as err:
                await client.revoke_access_token("error-invalid-scope")
            assert err.value.CODE == UpstreamError.CODE
            found, error = json_path(err.value.data, ["upstream_error", "error"])
            assert found is True
            assert error == "invalid_scope"


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_orcid_oauth_revoke_access_token_error_non_empty_response():
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            client = ORCIDOAuthAPIClient(url)
            with pytest.raises(UpstreamError):
                await client.revoke_access_token("non-empty-response")


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# async def test_orcid_oauth_revoke_access_token_error_no_content_type():
#     """
#     Although the normal response is empty and doesn't care about a content-type
#     being present or not, for an error condition it must have a content type
#     (and in the test below, it must be application/json)
#     """
#     with no_stderr():
#         with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
#             client = ORCIDOAuthAPIClient(url)
#             with pytest.raises(ContentTypeError):
#                 await client.revoke_access_token("error-response-no-content-type")


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_orcid_oauth_revoke_access_token_error_not_json():
    """
    Although the normal response is empty and doesn't care about a content-type
    being present or not, for an error condition it must be application/json.
    """
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            client = ORCIDOAuthAPIClient(url)
            with pytest.raises(JSONDecodeError):
                await client.revoke_access_token("error-response-not-json")


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_orcid_oauth_revoke_access_token_error_invalid_json():
    """
    Although the normal response is empty and doesn't care about a content-type
    being present or not, for an error condition it must be application/json.
    """
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            client = ORCIDOAuthAPIClient(url)
            with pytest.raises(UpstreamError) as err:
                await client.revoke_access_token("error-response-invalid-json")
            assert err.value.CODE == UpstreamError.CODE
            found, error = json_path(err.value.data, ["upstream_error", "foo"])
            assert found is True
            assert error == "bar"


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# async def test_orcid_oauth_revoke_access_token_no_content_type():
#     with no_stderr():
#         with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
#             client = ORCIDOAuthClient(url)
#             with pytest.raises(UIError) as ie:
#                 await client.revoke_access_token("no-content-type")
#             assert ie.value.code == ContentTypeError.CODE
#             # assert ie.value.message == "No content-type in response"


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# async def test_orcid_oauth_revoke_access_token_no_content_length():
#     with no_stderr():
#         with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
#             client = ORCIDOAuthInteractiveClient(url)
#             with pytest.raises(UIError) as ie:
#                 await client.revoke_access_token("no-content-length")
#             assert ie.value.code == UpstreamError.CODE


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# async def test_orcid_oauth_revoke_access_token_empty_content():
#     with no_stderr():
#         with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
#             code = "empty-content"
#             client = ORCIDOAuthInteractiveClient(url)
#             with pytest.raises(UIError) as uie:
#                 await client.revoke_access_token(code)
#             assert uie.value.code == UpstreamError.CODE


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# async def ttest_orcid_oauth_revoke_access_token_not_json_content():
#     with no_stderr():
#         with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
#             code = "not-json-content"
#             client = ORCIDOAuthInteractiveClient(url)
#             with pytest.raises(UIError) as err:
#                 await client.revoke_access_token(code)
#             assert err.value.code == JSONDecodeError.CODE
#             # assert ie.value.message == "Error decoding JSON response"


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# async def test_orcid_oauth_revoke_access_token_not_json_content_type():
#     with no_stderr():
#         with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
#             code = "not-json-content-type"
#             client = ORCIDOAuthInteractiveClient(url)
#             with pytest.raises(UIError) as uie:
#                 await client.revoke_access_token(code)
#             assert uie.value.code == ContentTypeError.CODE


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# async def test_orcid_oauth_revoke_access_token_error_incorrect_error_format():
#     with no_stderr():
#         with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
#             code = "error-incorrect-error-format"
#             client = ORCIDOAuthInteractiveClient(url=url)
#             with pytest.raises(UIError) as uie:
#                 await client.revoke_access_token(code)
#             assert uie.value.code == UpstreamError.CODE


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# async def test_orcid_oauth_revoke_access_token_error_correct_error_format():
#     with no_stderr():
#         with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
#             code = "error-correct-error-format"
#             client = ORCIDOAuthInteractiveClient(url=url)
#             with pytest.raises(UIError) as uie:
#                 await client.exchange_code_for_token(code)
#             assert uie.value.code == UpstreamError.CODE


#
# Refresh token
#


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_orcid_oauth_refresh_token():
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            client = ORCIDOAuthAPIClient(url)
            response = await client.refresh_token("refresh-token-foo")
            assert response is not None


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_orcid_oauth_refresh_token_error_unauthorized_client():
    """
    Tests the case in which the client autorization has failed; perhaps it the client id
    or secret are corrupted, or have been revoked.
    """
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            client = ORCIDOAuthAPIClient(url)
            with pytest.raises(ORCIDNotAuthorizedError):
                await client.refresh_token("refresh-token-unauthorized-client")


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_orcid_oauth_refresh_token_error_invalid_grant():
    """
    Tests the case in which the client autorization has failed; perhaps it the client id
    or secret are corrupted, or have been revoked.
    """
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            client = ORCIDOAuthAPIClient(url)
            with pytest.raises(ORCIDNotAuthorizedError):
                await client.refresh_token("refresh-token-invalid-grant")


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_orcid_oauth_refresh_token_error_other_error():
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            client = ORCIDOAuthAPIClient(url)
            with pytest.raises(UpstreamError) as err:
                await client.refresh_token("refresh-token-other-error")
            assert err.value.CODE == UpstreamError.CODE
            found, error = json_path(err.value.data, ["upstream_error", "error"])
            assert found is True
            assert error == "invalid_request"


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# async def test_orcid_oauth_refresh_token_error_no_content_length():
#     with no_stderr():
#         with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
#             client = ORCIDOAuthClient(url)
#             with pytest.raises(UpstreamError):
#                 await client.refresh_token("no-content-length")


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# async def test_orcid_oauth_refresh_token_error_no_content_length():
#     with no_stderr():
#         with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
#             client = ORCIDOAuthClient(url)
#             with pytest.raises(UpstreamError):
#                 await client.refresh_token("no-content-length")

#
# revoke_access_token
#


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_orcid_oauth_revoke_access_token_no_content_type():
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            client = ORCIDOAuthAPIClient(url)
            with pytest.raises(ContentTypeError):
                await client.refresh_token("no-content-type")


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# async def test_orcid_oauth_revoke_access_token_no_content_length():
#     with no_stderr():
#         with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
#             client = ORCIDOAuthClient(url)
#             with pytest.raises(UIError) as ie:
#                 await client.refresh_token("no-content-length")
#             assert ie.value.code == UpstreamError.CODE


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_orcid_oauth_revoke_access_token_empty_content():
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            client = ORCIDOAuthAPIClient(url)
            with pytest.raises(JSONDecodeError):
                await client.refresh_token("empty-content")


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_orcid_oauth_revoke_access_token_not_json_content():
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            client = ORCIDOAuthAPIClient(url)
            with pytest.raises(JSONDecodeError):
                await client.refresh_token("not-json-content")


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_orcid_oauth_revoke_access_token_not_json_content_type():
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            client = ORCIDOAuthAPIClient(url)
            with pytest.raises(ContentTypeError):
                await client.refresh_token("not-json-content-type")


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_orcid_oauth_revoke_access_token_invalid_error():
    """
    When a refresh token call is invoked, we may get back an error in an unexpected
    (incorrect!) format. It will be JSON, but just not the expected, standard, form.

    In this case, the error returned is {"foo": "bar"}, and is signaled by a non-200
    response code.
    """
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            client = ORCIDOAuthAPIClient(url)
            with pytest.raises(UpstreamError) as err:
                await client.refresh_token("invalid-error")

            assert err.value.CODE == UpstreamError.CODE
            found, error = json_path(err.value.data, ["upstream_error", "foo"])
            assert found is True
            assert error == "bar"


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# async def test_orcid_oauth_revoke_access_token_error_incorrect_error_format():
#     with no_stderr():
#         with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
#             code = "error-incorrect-error-format"
#             client = ORCIDOAuthClient(url=url)
#             with pytest.raises(UIError) as uie:
#                 await client.refresh_token(code)
#             assert uie.value.code == UpstreamError.CODE


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# async def test_orcid_oauth_revoke_access_token_error_correct_error_format():
#     with no_stderr():
#         with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
#             client = ORCIDOAuthClient(url=url)
#             with pytest.raises(UIError) as uie:
#                 await client.refresh_token("error-correct-error-format")
#             assert uie.value.code == UpstreamError.CODE


#
# Exchange code for token
#


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_exchange_code_for_token():
    """
    During the OAUTH 3-legged, interactive session, the ORCIDLink service needs to make
    a server-server call to exchange the oauth code for the orcid auth info, which
    includes the access_token.
    """
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            code = "foo"
            client = ORCIDOAuthAPIClient(url)
            response = await client.exchange_code_for_token(code)
            assert response.access_token == "access_token_for_foo"


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_exchange_code_for_token_empty_content():
    """
    If no content is returned, should get a JSON parsing error.

    Not sure why we are testing this; there are may cases of ill-formed responses that
    we could test...
    """
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            code = "empty-content"
            client = ORCIDOAuthAPIClient(url)
            with pytest.raises(JSONDecodeError) as err:
                await client.exchange_code_for_token(code)
            assert err.value.CODE == JSONDecodeError.CODE


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_exchange_code_for_token_not_json_content():
    """
    It is possible that even though the response says it is application/json, it is
    something else. We do catch that as a matter of course, and here we ensure that the
    expected Exception is thrown.
    """
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            code = "not-json-content"
            client = ORCIDOAuthAPIClient(url)
            with pytest.raises(JSONDecodeError) as err:
                await client.exchange_code_for_token(code)
            assert err.value.CODE == JSONDecodeError.CODE


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_exchange_code_for_token_not_json_content_type():
    """
    The response for the ORCID OAuth API must always be JSON - application/json. This
    test ensures that a non-complant response triggers the expected error.
    """
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            code = "not-json-content-type"
            client = ORCIDOAuthAPIClient(url)
            with pytest.raises(ContentTypeError) as uie:
                await client.exchange_code_for_token(code)
            assert uie.value.CODE == ContentTypeError.CODE


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_exchange_code_for_token_no_content_type():
    """
    Similar to the wrong content type, the lack of content type is also a detected error.
    """
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            code = "no-content-type"
            client = ORCIDOAuthAPIClient(url)
            with pytest.raises(ContentTypeError) as ie:
                await client.exchange_code_for_token(code)
            assert ie.value.CODE == ContentTypeError.CODE


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_exchange_code_for_token_error_incorrect_error_format():
    """
    We have exceeding confidence that the ORCID APIs will always return the
    expected error format. To handle that case, we have a catch-all which just returns
    the returned JSON as the data property.
    """
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            code = "error-incorrect-error-format"
            client = ORCIDOAuthAPIClient(url=url)
            with pytest.raises(UpstreamError) as err:
                await client.exchange_code_for_token(code)
            assert err.value.CODE == UpstreamError.CODE
            found, error = json_path(err.value.data, ["upstream_error", "foo"])
            assert found is True
            assert error == "bar"


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_exchange_code_for_token_error_correct_error_format():
    """
    Excercises one case of error, but the point of this is to demonstrate that a
    "normal" error is handled correctly, and propagates through the UpstreamError
    JSON-RPC error, which serves as an error wrapper.
    """
    with no_stderr():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT) as [_, _, url, port]:
            code = "error-correct-error-format"
            client = ORCIDOAuthAPIClient(url=url)
            with pytest.raises(UpstreamError) as err:
                await client.exchange_code_for_token(code)
            assert err.value.CODE == UpstreamError.CODE
            found, error = json_path(err.value.data, ["upstream_error", "error"])
            assert found is True
            assert error == "invalid_request"
