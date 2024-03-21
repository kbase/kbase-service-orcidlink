import os
from test.mocks.data import load_test_data
from test.mocks.env import MOCK_ORCID_API_PORT, TEST_ENV
from test.mocks.mock_contexts import (
    mock_orcid_api_service,
    mock_orcid_api_service_with_errors,
    no_stderr,
)
from unittest import mock

import pytest

from orcidlink.jsonrpc.errors import (
    ORCIDInsufficientAuthorizationError,
    ORCIDNotAuthorizedError,
    ORCIDNotFoundError,
    UpstreamError,
)
from orcidlink.lib.json_support import JSONObject
from orcidlink.lib.service_clients import orcid_api
from orcidlink.lib.service_clients.orcid_api_errors import (
    OAuthBearerError,
    ORCIDAPIError,
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


class FakeResponse:
    def __init__(self, status_code: int | None = None, text: str | None = None):
        self.status_code = status_code
        self.text = text


#
# ORCID API
#


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_ORCIDAPIClient_url():
    client = orcid_api.ORCIDAPIClient(url="url", access_token="access_token")
    url = client.url("foo")
    assert url == "url/foo"


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_ORCIDAPIClient_header():
    client = orcid_api.ORCIDAPIClient(url="url", access_token="access_token")
    header = client.header()
    assert header.get("accept") == "application/vnd.orcid+json"
    assert header.get("content-type") == "application/vnd.orcid+json"
    assert header.get("authorization") == "Bearer access_token"


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_ORCIDAPI_get_profile():
    with no_stderr():
        with mock_orcid_api_service(MOCK_ORCID_API_PORT) as [_, _, url, port]:
            orcid_id = "0000-0003-4997-3076"
            client = orcid_api.ORCIDAPIClient(url=url, access_token="access_token")
            profile = await client.get_profile(orcid_id)
            assert isinstance(profile, orcid_api.ORCIDProfile)
            assert profile.orcid_identifier.path == orcid_id


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_ORCIDAPI_get_profile_not_found():
    """
    If an ORCID profile is not found upstream, we expect a general purpose ServiceError
    with a status code of 404 and an error code of notFound
    """
    with no_stderr():
        with mock_orcid_api_service_with_errors(MOCK_ORCID_API_PORT) as [
            _,
            _,
            url,
            port,
        ]:
            # Just alter the final 6 to 7 so that it doesn't match any testing orcid
            # profiles.
            orcid_id = "0000-0003-4997-3077"
            with pytest.raises(ORCIDNotFoundError):
                client = orcid_api.ORCIDAPIClient(url=url, access_token="access_token")
                await client.get_profile(orcid_id)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_ORCIDAPI_get_profile_invalid_token():
    """
    If an ORCID profile is not found upstream, we expect a general purpose ServiceError
    with a status code of 404 and an error code of notFound
    """
    with no_stderr():
        with mock_orcid_api_service_with_errors(MOCK_ORCID_API_PORT) as [
            _,
            _,
            url,
            port,
        ]:
            # this orcid id triggers an "invalid_token" error from the mock ORCID api
            orcid_id = "trigger-invalid-token"
            with pytest.raises(ORCIDNotAuthorizedError):
                client = orcid_api.ORCIDAPIClient(url=url, access_token="access_token")
                await client.get_profile(orcid_id)


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# async def test_ORCIDAPI_get_profile_not_authorized():
#     with no_stderr():
#         with mock_orcid_api_service_with_errors(MOCK_ORCID_API_PORT) as [
#             _,
#             _,
#             url,
#             port,
#         ]:
#             # this orcid id triggers a similar error message from ORCID, but
#             orcid_id = "trigger-401"
#             with pytest.raises(ORCIDInsufficientAuthorizationError):
#                 client = orcid_api.ORCIDAPIClient(url=url, access_token="access_token")
#                 await client.get_profile(orcid_id)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_ORCIDAPI_get_profile_unauthorized():
    with no_stderr():
        with mock_orcid_api_service_with_errors(MOCK_ORCID_API_PORT) as [
            _,
            _,
            url,
            port,
        ]:
            # this orcid id triggers an "unauthorized" error, which means that the
            # token is valid, recognized, but does not provide access to the account
            # associated with the provided ORCID Id.
            # Note that ORCID replies with a "401", when this should be a "403".
            orcid_id = "trigger-unauthorized"
            with pytest.raises(ORCIDInsufficientAuthorizationError):
                client = orcid_api.ORCIDAPIClient(url=url, access_token="access_token")
                await client.get_profile(orcid_id)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_ORCIDAPI_get_profile_some_other_error():
    """
    An recognized error (in this case {"foo": "bar"}) will result in the
    somewhat generic "UpstreamError" with the data containing whatever
    JSON was returned as the error information.
    """
    with no_stderr():
        with mock_orcid_api_service_with_errors(MOCK_ORCID_API_PORT) as [
            _,
            _,
            url,
            port,
        ]:
            orcid_id = "trigger-error-some-other"
            with pytest.raises(UpstreamError) as err:
                client = orcid_api.ORCIDAPIClient(url=url, access_token="access_token")
                await client.get_profile(orcid_id)

            assert "upstream_error" in err.value.data


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_ORCIDAPI_get_profile_some_500_error():
    """
    Ensure we can handle a 500 error with a JSON response.

    One way to trigger a 500 error is to make a bad endpoint. E.g.
    https://api.sandbox.orcid.org/v3.0/1111-2222-3333-4444/recordx
    note the "x" at the end, triggers the error returned by the mock endpoing
    for this test.
    """
    with no_stderr():
        with mock_orcid_api_service_with_errors(MOCK_ORCID_API_PORT) as [
            _,
            _,
            url,
            port,
        ]:
            orcid_id = "trigger-500"
            with pytest.raises(UpstreamError):
                client = orcid_api.ORCIDAPIClient(url=url, access_token="access_token")
                await client.get_profile(orcid_id)


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# async def test_ORCIDAPI_get_profile_error_wrong_content_type():
#     with no_stderr():
#         with mock_orcid_api_service_with_errors(MOCK_ORCID_API_PORT) as [
#             _,
#             _,
#             url,
#             port,
#         ]:
#             orcid_id = "trigger-wrong-content-type"
#             with pytest.raises(UpstreamError):
#                 client = orcid_api.ORCIDAPIClient(url=url, access_token="access_token")
#                 await client.get_profile(orcid_id)


# TODO: revive
# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# async def test_ORCIDAPI_get_profile_other_error():
#     with no_stderr():
#         with mock_orcid_api_service_with_errors(MOCK_ORCID_API_PORT) as [
#             _,
#             _,
#             url,
#             port,
#         ]:
#             orcid_id = "trigger-415"
#             with pytest.raises():
#                 client = orcid_api.ORCIDAPIClient(url=url, access_token="access_token")
#                 await client.get_profile(orcid_id)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_ORCIDAPI_get_profile_no_content_type():
    """
    In which the ORCID API forgets to send a content-type header.
    """
    with no_stderr():
        with mock_orcid_api_service_with_errors(MOCK_ORCID_API_PORT) as [
            _,
            _,
            url,
            port,
        ]:
            orcid_id = "trigger-no-content-type"
            with pytest.raises(UpstreamError):
                client = orcid_api.ORCIDAPIClient(url=url, access_token="access_token")
                await client.get_profile(orcid_id)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_ORCIDAPI_get_profile_non_json_response():
    """
    In which the ORCID API forgets to send a content-type header.
    """
    with no_stderr():
        with mock_orcid_api_service_with_errors(MOCK_ORCID_API_PORT) as [
            _,
            _,
            url,
            port,
        ]:
            orcid_id = "trigger-not-json"
            with pytest.raises(UpstreamError):
                client = orcid_api.ORCIDAPIClient(url=url, access_token="access_token")
                await client.get_profile(orcid_id)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_ORCIDAPI_get_works():
    with no_stderr():
        with mock_orcid_api_service(MOCK_ORCID_API_PORT) as [_, _, url, port]:
            orcid_id = "0000-0003-4997-3076"
            client = orcid_api.ORCIDAPIClient(url=url, access_token="access_token")
            works = await client.get_works(orcid_id)
            assert isinstance(works, orcid_api.Works)
            assert works.group[0].work_summary[0].put_code == 1487805


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# async def test_ORCIDAPI_get_works_error():
#     """
#     TODO: What error?
#     """
#     with no_stderr():
#         with mock_orcid_api_service_with_errors(MOCK_ORCID_API_PORT) as [
#             _,
#             _,
#             url,
#             port,
#         ]:
#             orcid_id = "0000-0003-4997-3076"
#             client = orcid_api.ORCIDAPIClient(url=url, access_token="access_token")
#             with pytest.raises(UpstreamError):
#                 await client.get_works(orcid_id)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_get_work():
    """
    Tests normal case for get_work, which should return the requested fork activity
    record by orcid_id and put_code..
    """
    with no_stderr():
        with mock_orcid_api_service(MOCK_ORCID_API_PORT) as [_, _, url, port]:
            orcid_id = "0000-0003-4997-3076"
            put_code = 1526002
            client = orcid_api.ORCIDAPIClient(url=url, access_token="access_token")
            work = await client.get_work(orcid_id, put_code)
            assert isinstance(work, orcid_api.GetWorkResult)
            assert work.bulk[0].work.put_code == put_code


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_get_work_error():
    """
    Use a put code that is not implemented in the mock orcid, which
    """
    with no_stderr():
        with mock_orcid_api_service_with_errors(MOCK_ORCID_API_PORT) as [
            _,
            _,
            url,
            port,
        ]:
            orcid_id = "0000-0003-4997-3076"
            put_code = 1526002
            client = orcid_api.ORCIDAPIClient(url=url, access_token="access_token")
            with pytest.raises(ORCIDNotFoundError):
                await client.get_work(orcid_id, put_code)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_ORCIDAPI_save_work():
    with no_stderr():
        with mock_orcid_api_service(MOCK_ORCID_API_PORT) as [_, _, url, port]:
            orcid_id = "0000-0003-4997-3076"
            client = orcid_api.ORCIDAPIClient(url=url, access_token="access_token")
            # work_update: WorkUpdate(
            #     putCode="1487805",
            #     title="foo",
            #     journal="bar",
            #     date="2001/02/03",Ω
            #     workType="baz",
            #     url="some url",
            # )
            # TODO: external ids too!
            put_code = 1526002
            work_update = load_test_data(
                TEST_DATA_DIR, "orcid", f"work_{str(put_code)}"
            )["bulk"][0]["work"]
            # don't change anything for now
            result = await client.save_work(
                orcid_id, put_code, orcid_api.WorkUpdate.model_validate(work_update)
            )
            assert isinstance(result, orcid_api.Work)
            assert result.put_code == put_code


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_ORCIDAPI_save_work_error(fake_fs):
    #
    # We use the mock ORCID server which returns errors
    #
    with no_stderr():
        with mock_orcid_api_service_with_errors(MOCK_ORCID_API_PORT) as [
            _,
            _,
            url,
            port,
        ]:
            orcid_id = "0000-0003-4997-3076"
            #
            # The client we are testing will access the mock server above since we are
            # using the base_url it calculates, which uses IP 127.0.0.1 as specified in
            # the constructor, and a randomly generated port.
            #
            client = orcid_api.ORCIDAPIClient(url=url, access_token="access_token")
            with pytest.raises(UpstreamError):
                put_code = 1526002
                work_update = orcid_api.WorkUpdate.model_validate(
                    load_test_data(TEST_DATA_DIR, "orcid", f"work_{str(put_code)}")[
                        "bulk"
                    ][0]["work"]
                )
                # don't change anything for now
                await client.save_work(orcid_id, put_code, work_update)
            # assert ex.value.error.data["originalResponseJSON"]["response-code"] == 400

            # TODO: restore the error data
            # assert ex.value.error.code == ERRORS.upstream_orcid_error.code
            # assert ex.value.error.title == "Upstream ORCID Error"
            # assert ex.value.data is not None and ex.value.data.source == "save_work"
            # assert ex.value.data.status_code == 500
            # assert ex.value.error.response_code == 400
            # assert ex.value.error.data.status_code == 400


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# def test_make_upstream_error_401(fake_fs):
#     # A 401 from ORCID
#     error_content = {"error": "My Error", "error_description": "Should not see me"}
#     status_code = 401

#     result = exceptions.make_upstream_error(status_code, error_content, "foo")
#     assert isinstance(result, exceptions.UpstreamORCIDAPIError)
#     # assert result.status_code == 502
#     assert result.error.code == 1052
#     assert result.error.title == "Upstream ORCID Error"
#     assert result.data is not None and result.data.source == "foo"
#     assert (
#         isinstance(result.data.detail, dict)
#         and result.data.detail["error"] is not None
#         and result.data.detail["error"] == "My Error"
#     )
#     assert result.data.detail.get("error_description") is None
#     # assert "error_description" not in result.error.data.detail


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# def test_make_upstream_error_non_401(fake_fs):
#     with mock.patch.dict(os.environ, TEST_ENV, clear=True):
#         error_content = {
#             "response-code": 123,
#             "developer-message": "My Developer Message",
#             "user-message": "My User Message",
#             "error-code": 456,
#             "more-info": "My More Info",
#         }
#         status_code = 400

#         result = exceptions.make_upstream_error(status_code, error_content, "foo")
#         assert isinstance(result, exceptions.ServiceErrorY)
#         # assert result.status_code == 502
#         assert result.error.code == exceptions.ERRORS.upstream_orcid_error.code
#         assert result.error.title == "Upstream ORCID Error"
#         assert (
#             isinstance(result.data, exceptions.UpstreamErrorData)
#             and result.data.source == "foo"
#         )
#         # assert isinstance(result.data['detail'], dict) and result.data["detail"]["response-code"] == 123
#         # assert result.error.data.detail.error_description is None
#         # assert "error_description" not in result.error.data.detail


# def test_make_upstream_error_internal_server(fake_fs):
#     with mock.patch.dict(os.environ, TEST_ENV, clear=True):
#         error_content = {
#             "message-version": "123",
#             "orcid-profile": None,
#             "orcid-search-results": None,
#             "error-desc": {"value": "My error desc"},
#         }
#         status_code = 500

#         result = exceptions.make_upstream_error(status_code, error_content, "foo")
#         assert isinstance(result, exceptions.ServiceErrorY)
#         # assert result.status_code == 502
#         assert result.error.code == exceptions.ERRORS.upstream_orcid_error.code
#         assert result.error.title == "Upstream ORCID Error"
#         assert (
#             isinstance(result.data, exceptions.UpstreamErrorData)
#             and result.data.source == "foo"
#         )
# assert isinstance(result.data['detail'], dict) and result.data["detail"]["message-version"] == "123"
# assert result.error.data.detail.error_description is None
# assert "error_description" not in result.error.data.detail


def test_extract_error():
    """
    The extract_error function is a small function designed to analyze an error value
    returned by the ORCID API to determine which of the two known variants has
    been returned.
    """
    assert orcid_api.extract_error(None) is None

    #
    # This is the response for api endpoints if there is a problem with
    # authorization.
    #
    valid_api_error_object: JSONObject = {
        "error": "invalid_request",
        "error_description": "this is a foo error",
    }
    orcid_api_error = orcid_api.extract_error(valid_api_error_object)
    assert isinstance(orcid_api_error, OAuthBearerError)

    #
    # This is the normal form for an ORCID API Error
    #
    valid_api_response_error = {
        "response-code": 400,
        "developer-message": "There was an error connecting to ORCID.",
        "user-message": "There was an error connecting to ORCID.",
        "error-code": 9000,
        "more-info": "here is scant additional information",
    }
    api_response_error = orcid_api.extract_error(valid_api_response_error)
    assert isinstance(api_response_error, ORCIDAPIError)

    #
    # An unspecified error response is returned as plain JSON
    #
    unrecognized_error_object: JSONObject = {
        "something": "else",
    }
    other_orcid_api_error = orcid_api.extract_error(unrecognized_error_object)
    assert isinstance(other_orcid_api_error, dict)
    assert "something" in other_orcid_api_error
    assert other_orcid_api_error["something"] == "else"
