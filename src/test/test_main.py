import contextlib
import json
import logging
import os
from test.mocks.data import load_data_file, load_data_json
from test.mocks.env import (
    MOCK_KBASE_SERVICES_PORT,
    MOCK_ORCID_API_PORT,
    MOCK_ORCID_OAUTH_PORT,
    TEST_ENV,
)
from test.mocks.mock_contexts import (
    mock_auth_service,
    mock_orcid_api_service,
    mock_orcid_api_service_with_errors,
    mock_orcid_oauth_service,
    mock_orcid_oauth_service2,
    no_stderr,
)
from test.mocks.testing_utils import (
    add_linking_session_completed,
    add_linking_session_initial,
    add_linking_session_started,
    assert_json_rpc_error,
    assert_json_rpc_result,
    assert_json_rpc_result_ignore_result,
    clear_database,
    create_link,
    generate_kbase_token,
    get_link,
    get_linking_session_initial,
    rpc_call,
)
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from orcidlink.jsonrpc.errors import (
    NotAuthorizedError,
    NotFoundError,
    ORCIDNotFoundError,
    UpstreamError,
)
from orcidlink.lib.logger import log_event
from orcidlink.lib.utils import posix_time_millis
from orcidlink.main import app, config_to_log_level
from orcidlink.model import (
    LinkingSessionComplete,
    LinkingSessionInitial,
    LinkingSessionStarted,
    LinkRecord,
    LinkRecordPublic,
    LinkRecordPublicNonOwner,
)

TEST_DATA_DIR = os.environ["TEST_DATA_DIR"]


client = TestClient(app, raise_server_exceptions=False)

kbase_yaml = load_data_file(TEST_DATA_DIR, "kbase1.yml")

INVALID_TOKEN = generate_kbase_token("invalid_token")
EMPTY_TOKEN = ""
# NO_TOKEN = generate_kbase_token("no_token")
BAD_JSON = generate_kbase_token("bad_json")
TEXT_JSON = generate_kbase_token("text_json")
CAUSES_INTERNAL_ERROR = generate_kbase_token("something_bad")

service_description_toml = load_data_file(TEST_DATA_DIR, "service_description1.toml")
git_info_json = load_data_file(TEST_DATA_DIR, "git_info1.json")

LINKING_SESSION_INITIAL = load_data_file(
    TEST_DATA_DIR, "linking_session_record_initial.json"
)
LINKING_SESSION_STARTED = load_data_file(
    TEST_DATA_DIR, "linking_session_record_started.json"
)
LINKING_SESSION_COMPLETED = load_data_file(
    TEST_DATA_DIR, "linking_session_record_completed.json"
)


@pytest.fixture
def fake_fs(fs):
    fs.create_file(
        f"{os.environ['SERVICE_DIRECTORY']}/SERVICE_DESCRIPTION.toml",
        contents=service_description_toml,
    )
    fs.create_file(
        f"{os.environ['SERVICE_DIRECTORY']}/build/git-info.json", contents=git_info_json
    )
    data_dir = os.environ["TEST_DATA_DIR"]
    fs.add_real_directory(data_dir)
    yield fs


@contextlib.contextmanager
def mock_services():
    with no_stderr():
        with mock_auth_service(MOCK_KBASE_SERVICES_PORT):
            with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT):
                with mock_orcid_api_service(MOCK_ORCID_API_PORT):
                    yield


@contextlib.contextmanager
def mock_services_with_errors():
    with no_stderr():
        with mock_auth_service(MOCK_KBASE_SERVICES_PORT):
            with mock_orcid_oauth_service2(MOCK_ORCID_OAUTH_PORT):
                with mock_orcid_api_service_with_errors(MOCK_ORCID_API_PORT):
                    yield


TEST_LINK = load_data_json(TEST_DATA_DIR, "link1.json")


# Happy paths


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_startup(fake_fs):
    with TestClient(app, raise_server_exceptions=False):
        log_id = log_event("foo", {"bar": "baz"})
        assert isinstance(log_id, str)
        with open("/tmp/orcidlink.log", "r") as fin:
            log = json.load(fin)
        assert log["event"]["name"] == "foo"
        assert log["event"]["data"] == {"bar": "baz"}


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_docs(fake_fs):
    response = client.get("/docs")
    assert response.status_code == 200


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_docs_error(fake_fs):
    openapi_url = app.openapi_url
    app.openapi_url = None
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/docs")
    assert response.status_code == 404
    # TODO: test assertions about this..
    app.openapi_url = openapi_url


# Error conditions


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_main_404(fake_fs):
    response = client.get("/foo")
    assert response.status_code == 404


# @mock.patch.dict(os.environ, TEST_ENV, clear=True)
# def test_validation_exception_handler(fake_fs):
#     response = client.get("/doc", json={"foo": "bar"})
#     assert response.status_code == 422
#     assert response.headers["content-type"] == "application/json"
#     content = response.json()
#     assert content["code"] == errors.ERRORS.request_validation_error.code
#     assert content["title"] == errors.ERRORS.request_validation_error.title
#     assert (
#         content["message"]
#         == "This request does not comply with the schema for this endpoint"
#     )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_bad_method_call(fake_fs):
    """
    A poorly formed JSON-RPC call should result in a specific error response
    as tested below.
    """
    response = client.post("/api/v1", json={"foo": "bar"})
    assert_json_rpc_error(response, -32600, "Invalid Request")


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_bad_params(fake_fs):
    """
    A poorly formed JSON-RPC call should result in a specific error response
    as tested below.
    """
    rpc = {
        "jsonrpc": "2.0",
        "id": "123",
        "method": "get-link",
        "params": {"bar": "foo"},
    }
    response = client.post("/api/v1", json=rpc)
    assert_json_rpc_error(response, -32602, "Invalid params")


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_kbase_auth_exception_handler(fake_fs):
    with mock_services():
        # call with missing token
        rpc = {
            "jsonrpc": "2.0",
            "id": "123",
            "method": "get-link",
            "params": {"username": "foo"},
        }
        response = client.post("/api/v1", json=rpc, headers={})
        assert_json_rpc_error(response, 1010, "Authorization Required")

        # call with invalid token
        response = client.post(
            "/api/v1", json=rpc, headers={"Authorization": INVALID_TOKEN}
        )
        assert_json_rpc_error(response, 1010, "Authorization Required")

        # Call with actual empty token; should be caught at the validator boundary
        # as it is invalid according to the rules for tokens.
        response = client.post("/api/v1", json=rpc, headers={"Authorization": ""})
        assert_json_rpc_error(response, -32602, "Invalid params")

        # make a call which triggers a bug to trigger a JSON parse error
        # this simulates a 500 error in the auth service which emits text
        # rather than JSON - in other words, a deep and actual server error,
        # not the usuall, silly 500 response we emit for all JSON-RPC!!
        response = client.post(
            "/api/v1", json=rpc, headers={"Authorization": TEXT_JSON}
        )
        assert_json_rpc_error(response, 1040, "Error decoding JSON response")


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_native_errors():
    with no_stderr():
        # make some call which triggers a non-404 error caught by FastAPI/Starlette,
        # in this case an endpoint not found.
        response = client.get("/linx", headers={"Authorization": "x" * 32})

        assert response.status_code == 404
        assert response.headers["content-type"] == "application/json"
        response.json()
        #
        # TODO: We should make these JSON-RPC!
        #
        # assert content["code"] == errors.ERRORS.not_found.code
        # assert content["title"] == errors.ERRORS.not_found.title
        # assert content["message"] == "The requested resource was not found"
        # assert content["data"]["detail"] == "Not Found"
        # assert content["data"]["path"] == "/linx"

        # make some call which triggers a non-404 error caught by FastAPI/Starlette,
        # in this case a method not supported.
        response = client.get("/api/v1", headers={"Authorization": "x" * 32})
        assert response.status_code == 405
        assert response.headers["content-type"] == "application/json"
        response.json()
        # assert content["code"] == errors.ERRORS.fastapi_error.code
        # assert content["title"] == errors.ERRORS.fastapi_error.title
        # assert content["message"] == "Internal FastAPI Exception"
        # assert content["data"]["detail"] == "Method Not Allowed"


def test_config_to_log_level():
    assert config_to_log_level("DEBUG") == logging.DEBUG
    assert config_to_log_level("INFO") == logging.INFO
    assert config_to_log_level("WARNING") == logging.WARNING
    assert config_to_log_level("ERROR") == logging.ERROR
    assert config_to_log_level("CRITICAL") == logging.CRITICAL


def test_config_to_log_level_error():
    with pytest.raises(ValueError, match='Invalid log_level config setting "FOO"'):
        config_to_log_level("FOO")


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_status_handler(fake_fs):
    with mock_services():
        # call with missing token
        response = rpc_call("status", None, generate_kbase_token("foo"))
        result = assert_json_rpc_result_ignore_result(response)
        assert "status" in result
        assert result["status"] == "ok"


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_info_handler(fake_fs):
    with mock_services():
        # call with missing token
        response = rpc_call("info", None, generate_kbase_token("foo"))
        result = assert_json_rpc_result_ignore_result(response)
        assert "service-description" in result
        assert result["service-description"]["name"] == "ORCIDLink"


def test_error_info_handler(fake_fs):
    with mock_services():
        # call with missing token
        error_code = 1000
        params = {"error_code": error_code}
        response = rpc_call("error-info", params, generate_kbase_token("foo"))
        result = assert_json_rpc_result_ignore_result(response)
        assert "error_info" in result
        assert result["error_info"]["code"] == error_code


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_is_linked():
    with mock_services():
        await clear_database()
        params = {"username": "foo"}

        response = rpc_call("is-linked", params, generate_kbase_token("foo"))
        assert_json_rpc_result(response, False)

        await create_link(TEST_LINK)

        response = rpc_call("is-linked", params, generate_kbase_token("foo"))
        assert_json_rpc_result(response, True)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_owner_link():
    with mock_services():
        await clear_database()
        params = {"username": "foo"}

        # Trying to get a link if it doesn't exist results in the
        # NotFoundError error
        response = rpc_call("owner-link", params, generate_kbase_token("foo"))
        assert_json_rpc_error(response, NotFoundError.CODE, NotFoundError.MESSAGE)

        # So now let us create a link for this user and try again.
        await create_link(TEST_LINK)

        public_link = LinkRecordPublic.model_validate(TEST_LINK).model_dump()

        response = rpc_call("owner-link", params, generate_kbase_token("foo"))
        assert_json_rpc_result(response, public_link)

        # If another user tries this, it should fail with a NotAuthorized error.
        response = rpc_call("owner-link", params, generate_kbase_token("bar"))
        assert_json_rpc_error(
            response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
        )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_other_link():
    with mock_services():
        await clear_database()
        params = {"username": "foo"}

        response = rpc_call("other-link", params, generate_kbase_token("foo"))
        assert_json_rpc_error(response, NotFoundError.CODE, NotFoundError.MESSAGE)

        await create_link(TEST_LINK)

        public_link = LinkRecordPublicNonOwner.model_validate(TEST_LINK).model_dump()

        # Can get own
        response = rpc_call("other-link", params, generate_kbase_token("foo"))
        assert_json_rpc_result(response, public_link)

        # Can get other
        response = rpc_call("other-link", params, generate_kbase_token("bar"))
        assert_json_rpc_result(response, public_link)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_delete_own_link():
    with mock_services():
        await clear_database()

        # Create a link
        await create_link(TEST_LINK)

        # Ensure it exists.
        link = await get_link("foo")
        assert link is not None

        # Delete link.
        params = {"username": "foo"}
        response = rpc_call("delete-own-link", params, generate_kbase_token("foo"))
        assert_json_rpc_result_ignore_result(response)

        # Ensure it doesn't exist.
        link = await get_link("foo")
        assert link is None


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_delete_own_link_errors():
    with mock_services():
        await clear_database()

        # Delete link that doesn't exist, should return NotFoundError
        params = {"username": "foo"}
        response = rpc_call("delete-own-link", params, generate_kbase_token("foo"))
        assert_json_rpc_error(response, NotFoundError.CODE, NotFoundError.MESSAGE)

        # Delete link for other user, should return NotAuthorizedError
        await create_link(TEST_LINK)
        params = {"username": "foo"}
        response = rpc_call("delete-own-link", params, generate_kbase_token("bar"))
        assert_json_rpc_error(
            response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
        )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_create_linking_session():
    with mock_services():
        await clear_database()

        # Create a linking session for user "foo"
        params = {"username": "foo"}
        response = rpc_call(
            "create-linking-session", params, generate_kbase_token("foo")
        )
        result = assert_json_rpc_result_ignore_result(response)
        session_id = result["session_id"]

        # Fetch the linking session to ensure it exists.
        session = await get_linking_session_initial(session_id)
        assert session is not None
        assert session.session_id == session_id


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_get_linking_session():
    with mock_services():
        await clear_database()

        # Create a linking session for user "foo"
        linking_session = json.loads(LINKING_SESSION_COMPLETED)
        await add_linking_session_completed(
            LinkingSessionComplete.model_validate(linking_session)
        )

        # Fetch the linking session
        params = {"session_id": linking_session["session_id"]}
        response = rpc_call("get-linking-session", params, generate_kbase_token("foo"))
        result = assert_json_rpc_result_ignore_result(response)
        assert result["session_id"] == linking_session["session_id"]


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_delete_linking_session():
    with mock_services():
        await clear_database()

        # Create a linking session for user "foo"
        linking_session = json.loads(LINKING_SESSION_COMPLETED)
        await add_linking_session_completed(
            LinkingSessionComplete.model_validate(linking_session)
        )

        # Fetch the linking session
        params = {"session_id": linking_session["session_id"]}
        response = rpc_call("get-linking-session", params, generate_kbase_token("foo"))
        result = assert_json_rpc_result_ignore_result(response)
        assert result["session_id"] == linking_session["session_id"]

        # Delete the linking session.
        params = {"session_id": linking_session["session_id"]}
        response = rpc_call(
            "delete-linking-session", params, generate_kbase_token("foo")
        )
        result = assert_json_rpc_result_ignore_result(response)

        # TODO: More error conditions


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_finish_linking_session():
    with mock_services():
        await clear_database()

        # Create a linking session for user "foo"
        linking_session = json.loads(LINKING_SESSION_COMPLETED)
        await add_linking_session_completed(
            LinkingSessionComplete.model_validate(linking_session)
        )

        # Fetch the linking session
        params = {"session_id": linking_session["session_id"]}
        response = rpc_call("get-linking-session", params, generate_kbase_token("foo"))
        result = assert_json_rpc_result_ignore_result(response)
        assert result["session_id"] == linking_session["session_id"]

        # Now "finish" the linking session, which will remove it from the completed
        # sessions collection and create a link, so test both of those outcomes.
        response = rpc_call(
            "finish-linking-session", params, generate_kbase_token("foo")
        )
        result = assert_json_rpc_result_ignore_result(response)
        assert result is None

        # Now there shouldn't be one.
        response = rpc_call("get-linking-session", params, generate_kbase_token("foo"))
        result = assert_json_rpc_error(
            response, NotFoundError.CODE, NotFoundError.MESSAGE
        )

        # But there should be a link.
        link = await get_link("foo")
        assert link is not None
        assert link.username == "foo"


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_is_manager():
    with mock_services():
        await clear_database()

        # The test user "amanager" is ... a manager.
        params = {"username": "amanager"}
        response = rpc_call("is-manager", params, generate_kbase_token("amanager"))
        assert_json_rpc_result(response, {"is_manager": True})

        # But "foo" isn't
        params = {"username": "foo"}
        response = rpc_call("is-manager", params, generate_kbase_token("foo"))
        assert_json_rpc_result(response, {"is_manager": False})

        # And we can only ask about manager status for the authorized user.
        params = {"username": "amanager"}
        response = rpc_call("is-manager", params, generate_kbase_token("foo"))
        assert_json_rpc_error(
            response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
        )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_find_links():
    with mock_services():
        await clear_database()

        # With a clear database, there should be no links.
        # Also, as we don't have filtering or paging, we leave the
        # parameters empty.
        params = {"query": {}}
        response = rpc_call("find-links", params, generate_kbase_token("amanager"))
        result = assert_json_rpc_result_ignore_result(response)
        links = result["links"]
        assert len(links) == 0

        # Let us populate with some links.
        await create_link(TEST_LINK)

        # Now they should be found.
        response = rpc_call("find-links", params, generate_kbase_token("amanager"))
        result = assert_json_rpc_result_ignore_result(response)
        links = result["links"]
        assert len(links) == 1


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_find_links_error():
    with mock_services():
        await clear_database()

        # Only an admin may call this.
        params = {"query": {}}
        response = rpc_call("find-links", params, generate_kbase_token("foo"))
        assert_json_rpc_error(
            response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
        )


#
# get-link
#


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_get_link():
    with mock_services():
        # Let us populate with a links.
        await create_link(TEST_LINK)

        # Now they should be found.
        params = {"username": "foo"}
        response = rpc_call("get-link", params, generate_kbase_token("amanager"))
        result = assert_json_rpc_result_ignore_result(response)
        link = result["link"]
        assert link["username"] == "foo"


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_get_link_error():
    with mock_services():
        await clear_database()

        # Only an admin may call this.
        params = {"username": "foo"}
        response = rpc_call("get-link", params, generate_kbase_token("foo"))
        assert_json_rpc_error(
            response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
        )

        # If the link doesn't exist, we get a NotFoundError
        params = {"username": "foo"}
        response = rpc_call("get-link", params, generate_kbase_token("amanager"))
        assert_json_rpc_error(response, NotFoundError.CODE, NotFoundError.MESSAGE)


#
# refresh-tokens
#


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_refresh_tokens():
    with mock_services():
        # Let us populate with a links.
        await create_link(TEST_LINK)

        # Now they should be found.
        params = {"username": "foo"}
        response = rpc_call("refresh-tokens", params, generate_kbase_token("amanager"))
        result = assert_json_rpc_result_ignore_result(response)
        link = result["link"]
        assert link["username"] == "foo"


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_refresh_tokens_errors():
    with mock_services():
        # Let us populate with a links.
        await create_link(TEST_LINK)

        # Only admins!
        params = {"username": "foo"}
        response = rpc_call("refresh-tokens", params, generate_kbase_token("foo"))
        assert_json_rpc_error(
            response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
        )

        # What, no bar?
        params = {"username": "bar"}
        response = rpc_call("refresh-tokens", params, generate_kbase_token("amanager"))
        assert_json_rpc_error(response, NotFoundError.CODE, NotFoundError.MESSAGE)


#
# get-linking-sessions
#


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_get_linking_sessions():
    with mock_services():
        await clear_database()

        # At first there should be no linking sessions.
        response = rpc_call(
            "get-linking-sessions", None, generate_kbase_token("amanager")
        )
        expected = {
            "initial_linking_sessions": [],
            "started_linking_sessions": [],
            "completed_linking_sessions": [],
        }
        result = assert_json_rpc_result(response, expected)

        # Let us add one of each.

        # Create a linking session for user "foo"
        linking_session = json.loads(LINKING_SESSION_INITIAL)
        await add_linking_session_initial(
            LinkingSessionInitial.model_validate(linking_session)
        )

        linking_session = json.loads(LINKING_SESSION_STARTED)
        await add_linking_session_started(
            LinkingSessionStarted.model_validate(linking_session)
        )

        linking_session = json.loads(LINKING_SESSION_COMPLETED)
        await add_linking_session_completed(
            LinkingSessionComplete.model_validate(linking_session)
        )

        # Now there should be one of each!
        response = rpc_call(
            "get-linking-sessions", None, generate_kbase_token("amanager")
        )
        result = assert_json_rpc_result_ignore_result(response)
        assert len(result["initial_linking_sessions"]) == 1
        assert len(result["started_linking_sessions"]) == 1
        assert len(result["completed_linking_sessions"]) == 1


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_get_linking_sessions_errors():
    with mock_services():
        await clear_database()

        # At first there should be no linking sessions.
        response = rpc_call("get-linking-sessions", None, generate_kbase_token("foo"))
        assert_json_rpc_error(
            response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
        )


def assert_linking_sessions(
    initial_count: int, started_count: int, completed_count: int
) -> None:
    response = rpc_call("get-linking-sessions", None, generate_kbase_token("amanager"))
    result = assert_json_rpc_result_ignore_result(response)
    assert len(result["initial_linking_sessions"]) == initial_count
    assert len(result["started_linking_sessions"]) == started_count
    assert len(result["completed_linking_sessions"]) == completed_count


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_delete_expired_linking_sessions():
    with mock_services():
        await clear_database()

        assert_linking_sessions(0, 0, 0)

        # Deleting when there is nothing to delete is okay.
        response = rpc_call(
            "delete-expired-linking-sessions", None, generate_kbase_token("amanager")
        )
        assert_json_rpc_result_ignore_result(response)

        # There should be no linking sessions.
        assert_linking_sessions(0, 0, 0)

        # Create linking sessions for user "foo", ensuring that each linking session
        # expires in the future.
        now = posix_time_millis()
        future_now = now + 60_000
        initial_linking_session = LinkingSessionInitial.model_validate(
            json.loads(LINKING_SESSION_INITIAL)
        )
        initial_linking_session.expires_at = future_now
        await add_linking_session_initial(initial_linking_session)

        started_linking_session = LinkingSessionStarted.model_validate(
            json.loads(LINKING_SESSION_STARTED)
        )
        started_linking_session.expires_at = future_now
        await add_linking_session_started(started_linking_session)

        completed_linking_session = LinkingSessionComplete.model_validate(
            json.loads(LINKING_SESSION_COMPLETED)
        )
        completed_linking_session.expires_at = future_now
        await add_linking_session_completed(completed_linking_session)

        # There should be one of each
        assert_linking_sessions(1, 1, 1)

        response = rpc_call(
            "delete-expired-linking-sessions", None, generate_kbase_token("amanager")
        )
        assert_json_rpc_result_ignore_result(response)

        # There should still be one of each
        assert_linking_sessions(1, 1, 1)

        # Now repeat, but this time adding another linking session of each type, with an
        # expiration in the past.
        now = posix_time_millis()
        future_now = now - 60_000
        initial_linking_session = LinkingSessionInitial.model_validate(
            json.loads(LINKING_SESSION_INITIAL)
        )
        initial_linking_session.expires_at = future_now
        await add_linking_session_initial(initial_linking_session)

        started_linking_session = LinkingSessionStarted.model_validate(
            json.loads(LINKING_SESSION_STARTED)
        )
        started_linking_session.expires_at = future_now
        await add_linking_session_started(started_linking_session)

        completed_linking_session = LinkingSessionComplete.model_validate(
            json.loads(LINKING_SESSION_COMPLETED)
        )
        completed_linking_session.expires_at = future_now
        await add_linking_session_completed(completed_linking_session)

        assert_linking_sessions(2, 2, 2)

        response = rpc_call(
            "delete-expired-linking-sessions", None, generate_kbase_token("amanager")
        )
        assert_json_rpc_result_ignore_result(response)

        assert_linking_sessions(1, 1, 1)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_delete_expired_linking_sessions_error():
    with mock_services():
        await clear_database()

        # Can only be called by a manager.
        response = rpc_call(
            "delete-expired-linking-sessions", None, generate_kbase_token("foo")
        )
        assert_json_rpc_error(
            response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
        )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_delete_linking_session_initial():
    with mock_services():
        await clear_database()

        assert_linking_sessions(0, 0, 0)

        # Deleting when there is nothing to delete is okay.
        params = {"session_id": "bar"}
        response = rpc_call(
            "delete-linking-session-initial", params, generate_kbase_token("amanager")
        )
        assert_json_rpc_result_ignore_result(response)

        initial_linking_session = LinkingSessionInitial.model_validate(
            json.loads(LINKING_SESSION_INITIAL)
        )
        await add_linking_session_initial(initial_linking_session)

        assert_linking_sessions(1, 0, 0)

        # This should delete the one we added above.
        response = rpc_call(
            "delete-linking-session-initial", params, generate_kbase_token("amanager")
        )
        assert_json_rpc_result_ignore_result(response)

        # There should be no linking sessions.
        assert_linking_sessions(0, 0, 0)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_delete_linking_session_initial_error():
    with mock_services():
        await clear_database()

        # Can only be called by a manager.
        params = {"session_id": "bar"}
        response = rpc_call(
            "delete-linking-session-initial", params, generate_kbase_token("foo")
        )
        assert_json_rpc_error(
            response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
        )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_delete_linking_session_started():
    with mock_services():
        await clear_database()

        assert_linking_sessions(0, 0, 0)

        # Deleting when there is nothing to delete is okay.
        params = {"session_id": "bar"}
        response = rpc_call(
            "delete-linking-session-started", params, generate_kbase_token("amanager")
        )
        assert_json_rpc_result_ignore_result(response)

        started_linking_session = LinkingSessionStarted.model_validate(
            json.loads(LINKING_SESSION_STARTED)
        )
        await add_linking_session_started(started_linking_session)

        assert_linking_sessions(0, 1, 0)

        # This should delete the one we added above.
        response = rpc_call(
            "delete-linking-session-started", params, generate_kbase_token("amanager")
        )
        assert_json_rpc_result_ignore_result(response)

        # There should be no linking sessions.
        assert_linking_sessions(0, 0, 0)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_delete_linking_session_started_error():
    with mock_services():
        await clear_database()

        # Can only be called by a manager.
        params = {"session_id": "bar"}
        response = rpc_call(
            "delete-linking-session-started", params, generate_kbase_token("foo")
        )
        assert_json_rpc_error(
            response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
        )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_delete_linking_session_completed():
    with mock_services():
        await clear_database()

        assert_linking_sessions(0, 0, 0)

        # Deleting when there is nothing to delete is okay.
        params = {"session_id": "bar"}
        response = rpc_call(
            "delete-linking-session-completed", params, generate_kbase_token("amanager")
        )
        assert_json_rpc_result_ignore_result(response)

        completed_linking_session = LinkingSessionComplete.model_validate(
            json.loads(LINKING_SESSION_COMPLETED)
        )
        await add_linking_session_completed(completed_linking_session)

        assert_linking_sessions(0, 0, 1)

        # This should delete the one we added above.
        response = rpc_call(
            "delete-linking-session-completed", params, generate_kbase_token("amanager")
        )
        assert_json_rpc_result_ignore_result(response)

        # There should be no linking sessions.
        assert_linking_sessions(0, 0, 0)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_delete_linking_session_completed_error():
    with mock_services():
        await clear_database()

        # Can only be called by a manager.
        params = {"session_id": "bar"}
        response = rpc_call(
            "delete-linking-session-completed", params, generate_kbase_token("foo")
        )
        assert_json_rpc_error(
            response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
        )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_get_stats():
    with mock_services():
        await clear_database()

        expected = {
            "stats": {
                "links": {
                    "last_24_hours": 0,
                    "last_7_days": 0,
                    "last_30_days": 0,
                    "all_time": 0,
                },
                "linking_sessions_initial": {"active": 0, "expired": 0},
                "linking_sessions_started": {"active": 0, "expired": 0},
                "linking_sessions_completed": {"active": 0, "expired": 0},
            }
        }

        response = rpc_call("get-stats", None, generate_kbase_token("amanager"))
        assert_json_rpc_result(response, expected)

        # TODO: cover all cases; but for now just a couple.

        # add a link, should appear twice.
        expected["stats"]["links"]["last_24_hours"] = 1
        expected["stats"]["links"]["last_7_days"] = 1
        expected["stats"]["links"]["last_30_days"] = 1
        expected["stats"]["links"]["all_time"] = 1

        test_link = LinkRecord.model_validate(TEST_LINK)
        now = posix_time_millis()
        test_link.created_at = now

        await create_link(test_link.model_dump())

        response = rpc_call("get-stats", None, generate_kbase_token("amanager"))
        assert_json_rpc_result(response, expected)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_get_stats_error():
    with mock_services():
        await clear_database()

        # Can only be called by a manager.
        params = {"session_id": "bar"}
        response = rpc_call("get-stats", params, generate_kbase_token("foo"))
        assert_json_rpc_error(
            response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
        )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_get_orcid_profile():
    with mock_services():
        await clear_database()

        # Create a link
        # Note that the orcid id in the link must match the orcid id in the
        # mock orcid api; although, in our mock this isn't enforced (yet!)
        orcid_id = "0000-0003-4997-3076"
        test_link = LinkRecord.model_validate(TEST_LINK)
        test_link.orcid_auth.orcid = orcid_id
        await create_link(test_link.model_dump())

        params = {"username": "foo"}
        response = rpc_call("get-orcid-profile", params, generate_kbase_token("foo"))
        assert_json_rpc_result_ignore_result(response)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_get_orcid_profile_errors():
    with mock_services_with_errors():
        await clear_database()

        # Create a link
        # Note that the orcid id in the link must match the orcid id in the
        # mock orcid api; although, in our mock this isn't enforced (yet!)
        orcid_id = "0000-0003-4997-3076"
        test_link = LinkRecord.model_validate(TEST_LINK)
        test_link.orcid_auth.orcid = orcid_id
        await create_link(test_link.model_dump())

        # No link for user bar
        params = {"username": "bar"}
        response = rpc_call("get-orcid-profile", params, generate_kbase_token("bar"))
        assert_json_rpc_error(response, NotFoundError.CODE, NotFoundError.MESSAGE)

        # Can't do unless owner.
        params = {"username": "foo"}
        response = rpc_call("get-orcid-profile", params, generate_kbase_token("bar"))
        assert_json_rpc_error(
            response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
        )

        # errors propagated from ORCID API

        # Set the orcid id to "not-found" so that it triggers this condition in
        # the mock_orcid service.
        orcid_id = "not-found"
        test_link = LinkRecord.model_validate(TEST_LINK)
        test_link.orcid_auth.orcid = orcid_id
        await create_link(test_link.model_dump())

        params = {"username": "foo"}

        response = rpc_call("get-orcid-profile", params, generate_kbase_token("foo"))

        assert_json_rpc_error(
            response, ORCIDNotFoundError.CODE, ORCIDNotFoundError.MESSAGE
        )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_getorcid_works():
    with mock_services():
        await clear_database()

        # As with all other ORCID-fetched data, it only works if the
        # user has a link.
        orcid_id = "0000-0003-4997-3076"
        test_link = LinkRecord.model_validate(TEST_LINK)
        test_link.orcid_auth.orcid = orcid_id
        await create_link(test_link.model_dump())

        params = {"username": "foo"}
        response = rpc_call("get-orcid-works", params, generate_kbase_token("foo"))
        result = assert_json_rpc_result_ignore_result(response)
        assert isinstance(result, list)


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_get_orcid_works_errors():
    with mock_services():
        await clear_database()

        params = {
            "username": "bar",
        }
        response = rpc_call("get-orcid-works", params, generate_kbase_token("bar"))
        assert_json_rpc_error(response, NotFoundError.CODE, NotFoundError.MESSAGE)

        params = {
            "username": "foo",
        }
        response = rpc_call("get-orcid-works", params, generate_kbase_token("bar"))
        assert_json_rpc_error(
            response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
        )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_get_work():
    with mock_services():
        orcid_id = "0000-0003-4997-3076"
        test_link = LinkRecord.model_validate(TEST_LINK)
        test_link.orcid_auth.orcid = orcid_id
        await create_link(test_link.model_dump())

        put_code = 1526002
        params = {"username": "foo", "put_code": put_code}
        response = rpc_call("get-orcid-work", params, generate_kbase_token("foo"))
        result = assert_json_rpc_result_ignore_result(response)
        assert result["work"]["putCode"] == put_code


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_get_work2():
    with mock_services():
        orcid_id = "0000-0003-4997-3076"
        test_link = LinkRecord.model_validate(TEST_LINK)
        test_link.orcid_auth.orcid = orcid_id
        await create_link(test_link.model_dump())

        put_code = 1487805
        params = {"username": "foo", "put_code": put_code}
        response = rpc_call("get-orcid-work", params, generate_kbase_token("foo"))
        result = assert_json_rpc_result_ignore_result(response)
        assert result["work"]["putCode"] == put_code


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_get_work_errors():
    with mock_services():
        await clear_database()

        # Link not found for this user.
        params = {"username": "foo", "put_code": 1234}
        response = rpc_call("get-orcid-work", params, generate_kbase_token("foo"))
        assert_json_rpc_error(response, NotFoundError.CODE, NotFoundError.MESSAGE)

        await create_link(TEST_LINK)
        #
        # Omitting a param
        # TODO: do we really need to test this?
        #
        params = {
            "username": "bar",
        }

        # Another cause of not-found is if the work is not found.
        params = {"username": "foo", "put_code": 1234}
        response = rpc_call("get-orcid-work", params, generate_kbase_token("foo"))
        assert_json_rpc_error(
            response, ORCIDNotFoundError.CODE, ORCIDNotFoundError.MESSAGE
        )

        params = {"username": "foo", "put_code": 12345}
        response = rpc_call("get-orcid-work", params, generate_kbase_token("bar"))
        assert_json_rpc_error(
            response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
        )

        #
        # An api misuse which penetrates the call; ideally
        # there should not be anything like this.
        # In this case, the mock orcid server is set up
        # to return a 200 text response for the "123" putCode, which
        # triggers a parse error.
        #
        # TODO: this is rather terrible - the test client does not call the
        # endpoint in the same way as calling the running server. Specifically,
        # the middleware is not run, including that which catches all exceptions
        # calls custom exception handlers. So we can't actually test the
        # respose here. I think we'll need integration tests for that.
        #
        # Or perhaps we should just catch all exceptions w/in the endpoint
        # handlers and always return a response.
        orcid_id = "0000-0003-4997-3076"
        test_link = LinkRecord.model_validate(TEST_LINK)
        test_link.orcid_auth.orcid = orcid_id
        await create_link(test_link.model_dump())

        params = {"username": "foo", "put_code": 123}
        response = rpc_call("get-orcid-work", params, generate_kbase_token("foo"))
        # TODO: properly design standard error message AND specific error message.
        # assert_json_rpc_error(response, UpstreamError.CODE, "Received Incorrect Content Type")
        assert_json_rpc_error(response, UpstreamError.CODE, UpstreamError.MESSAGE)

        #
        # A bad put code results in a 400 from ORCID
        #
        params = {"username": "foo", "put_code": 456}
        response = rpc_call("get-orcid-work", params, generate_kbase_token("foo"))
        assert_json_rpc_error(response, 1050, "Upstream Error")


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_update_orcid_work(fake_fs):
    with mock_services():
        orcid_id = "0000-0003-4997-3076"
        test_link = LinkRecord.model_validate(TEST_LINK)
        test_link.orcid_auth.orcid = orcid_id
        await create_link(test_link.model_dump())

        # TODO: get from file.
        new_work_data = {
            "putCode": 1526002,
            "title": "Some Data Set, yo, bro, whoa",
            "journal": "Me myself and I and me",
            "date": "2021",
            "workType": "online-resource",
            "url": "https://kbase.us",
            "externalIds": [
                {
                    "type": "doi",
                    "value": "123",
                    "url": "https://example.com",
                    "relationship": "self",
                },
                # adds an extra one
                # TODO: should model different relationship
                # TODO: what about mimicking errors in the
                # api like a duplicate "self" relationship?
                {
                    "type": "doi",
                    "value": "1234",
                    "url": "https://example.com",
                    "relationship": "self",
                },
            ],
            "citation": {
                "type": "formatted-vancouver",
                "value": "my reference here",
            },
            "shortDescription": "my short description",
            "doi": "123",
            "selfContributor": {
                "orcidId": "1111-2222-3333-4444",
                "name": "Bar Baz",
                "roles": [],
            },
            "otherContributors": [],
        }
        params = {"username": "foo", "work_update": new_work_data}
        response = rpc_call("update-orcid-work", params, generate_kbase_token("foo"))
        result = assert_json_rpc_result_ignore_result(response)
        assert result["work"]["putCode"] == 1526002


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_update_orcid_work_errors(fake_fs):
    with mock_services():
        # TODO: get from file.
        new_work_data = {
            "putCode": 1526002,
            "title": "Some Data Set, yo, bro, whoa",
            "journal": "Me myself and I and me",
            "date": "2021",
            "workType": "online-resource",
            "url": "https://kbase.us",
            "externalIds": [
                {
                    "type": "doi",
                    "value": "123",
                    "url": "https://example.com",
                    "relationship": "self",
                }
            ],
            "citation": {
                "type": "formatted-vancouver",
                "value": "my reference here",
            },
            "shortDescription": "my short description",
            "doi": "123",
            "selfContributor": {
                "orcidId": "1111-2222-3333-4444",
                "name": "Bar Baz",
                "roles": [],
            },
            "otherContributors": [],
        }
        params = {"username": "bar", "work_update": new_work_data}
        response = rpc_call("update-orcid-work", params, generate_kbase_token("bar"))
        assert_json_rpc_error(response, NotFoundError.CODE, NotFoundError.MESSAGE)

        params = {"username": "foo", "work_update": new_work_data}
        response = rpc_call("update-orcid-work", params, generate_kbase_token("bar"))
        assert_json_rpc_error(
            response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
        )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_delete_work(fake_fs):
    with mock_services():
        orcid_id = "0000-0003-4997-3076"
        test_link = LinkRecord.model_validate(TEST_LINK)
        test_link.orcid_auth.orcid = orcid_id
        await create_link(test_link.model_dump())

        put_code = 1526002
        params = {"username": "foo", "put_code": put_code}
        response = rpc_call("delete-orcid-work", params, generate_kbase_token("foo"))

        result = assert_json_rpc_result_ignore_result(response)
        assert result is None


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_delete_work_bad_no_link(fake_fs):
    with mock_services():
        orcid_id = "0000-0003-4997-3076"
        test_link = LinkRecord.model_validate(TEST_LINK)
        test_link.orcid_auth.orcid = orcid_id
        await create_link(test_link.model_dump())

        put_code = 1526002
        params = {"username": "bar", "put_code": put_code}
        response = rpc_call("delete-orcid-work", params, generate_kbase_token("bar"))
        assert_json_rpc_error(response, 1020, "Not Found")


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_delete_work_not_source(fake_fs):
    with mock_services():
        orcid_id = "0000-0003-4997-3076"
        test_link = LinkRecord.model_validate(TEST_LINK)
        test_link.orcid_auth.orcid = orcid_id
        await create_link(test_link.model_dump())

        # Use a put code not in the mock service, in this case we
        # transpose the final 2 with 3.
        put_code = 123

        params = {"username": "foo", "put_code": put_code}
        response = rpc_call("delete-orcid-work", params, generate_kbase_token("foo"))
        assert_json_rpc_error(response, 1050, "Upstream Error")


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_delete_work_not_authorized(fake_fs):
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        with mock_services():
            orcid_id = "0000-0003-4997-3076"
            test_link = LinkRecord.model_validate(TEST_LINK)
            test_link.orcid_auth.orcid = orcid_id
            await create_link(test_link.model_dump())

            # Use a put code not in the mock service, in this case we
            # transpose the final 2 with 3.
            put_code = 456

            params = {"username": "foo", "put_code": put_code}
            response = rpc_call(
                "delete-orcid-work", params, generate_kbase_token("bar")
            )
            assert_json_rpc_error(
                response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
            )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_delete_work_put_code_not_found(fake_fs):
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        with mock_services():
            orcid_id = "0000-0003-4997-3076"
            test_link = LinkRecord.model_validate(TEST_LINK)
            test_link.orcid_auth.orcid = orcid_id
            await create_link(test_link.model_dump())

            # Use a put code not in the mock service, in this case we
            # transpose the final 2 with 3.
            put_code = 456

            params = {"username": "foo", "put_code": put_code}
            response = rpc_call(
                "delete-orcid-work", params, generate_kbase_token("foo")
            )
            assert_json_rpc_error(response, 1050, "Upstream Error")


# TODO: left off here, copied from test_get_work - added work_1526002_normalized.json to
# serve as a basis for input work records - will need to copy that and perhaps modify
# slightly for put_work.
@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_create_work(fake_fs):
    with mock_services():
        orcid_id = "0000-0003-4997-3076"
        test_link = LinkRecord.model_validate(TEST_LINK)
        test_link.orcid_auth.orcid = orcid_id
        await create_link(test_link.model_dump())

        # TODO: get from file.
        new_work_data = {
            "putCode": 1526002,
            "createdAt": 1663706262725,
            "updatedAt": 1671119638386,
            "source": "KBase CI",
            "title": "Some Data Set, yo, bro, whoa",
            "journal": "Me myself and I and me",
            "date": "2021",
            "workType": "online-resource",
            "url": "https://kbase.us",
            "doi": "123",
            "externalIds": [
                {
                    "type": "doi",
                    "value": "123",
                    "url": "https://example.com",
                    "relationship": "self",
                }
            ],
            "citation": {
                "type": "formatted-vancouver",
                "value": "my reference here",
            },
            "shortDescription": "my short description",
            "selfContributor": {
                "orcidId": "1111-2222-3333-4444",
                "name": "Bar Baz",
                "roles": [],
            },
            "otherContributors": [],
        }

        params = {"username": "foo", "new_work": new_work_data}
        response = rpc_call("create-orcid-work", params, generate_kbase_token("foo"))
        result = assert_json_rpc_result_ignore_result(response)
        assert result["work"]["putCode"] == 1526002


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_create_work_errors(fake_fs):
    with mock_services():
        # Note that we do not need to launch a mock server here,
        # though we might want to later as that really tests the API
        # front to back.
        orcid_id = "0000-0003-4997-3076"
        test_link = LinkRecord.model_validate(TEST_LINK)
        test_link.orcid_auth.orcid = orcid_id
        await create_link(test_link.model_dump())

        # TODO: get from file.
        new_work_data = {
            "putCode": 1526002,
            "createdAt": 1663706262725,
            "updatedAt": 1671119638386,
            "source": "KBase CI",
            "title": "Some Data Set, yo, bro, whoa",
            "journal": "Me myself and I and me",
            "date": "2021",
            "workType": "online-resource",
            "url": "https://kbase.us",
            "externalIds": [
                {
                    "type": "doi",
                    "value": "123",
                    "url": "https://example.com",
                    "relationship": "self",
                }
            ],
            "citation": {
                "type": "formatted-vancouver",
                "value": "my reference here",
            },
            "shortDescription": "my short description",
            "doi": "123",
            "selfContributor": {
                "orcidId": "1111-2222-3333-4444",
                "name": "Bar Baz",
                "roles": [],
            },
            "otherContributors": [],
        }

        params = {"username": "bar", "new_work": new_work_data}
        response = rpc_call("create-orcid-work", params, generate_kbase_token("bar"))
        assert_json_rpc_error(response, NotFoundError.CODE, NotFoundError.MESSAGE)

        params = {"username": "foo", "new_work": new_work_data}
        response = rpc_call("create-orcid-work", params, generate_kbase_token("bar"))
        assert_json_rpc_error(
            response, NotAuthorizedError.CODE, NotAuthorizedError.MESSAGE
        )

        # Error: exception saving work record to orcid; i.e.
        # thrown by the http call.
        new_work_data["title"] = "trigger-http-exception"
        params = {"username": "foo", "new_work": new_work_data}
        response = rpc_call("create-orcid-work", params, generate_kbase_token("foo"))
        assert_json_rpc_error(response, 1050, "Upstream Error")

        # Error: 500 returned from orcid
        # Invoke this with a special put code
        new_work_data["title"] = "trigger-500"
        params = {"username": "foo", "new_work": new_work_data}
        response = rpc_call("create-orcid-work", params, generate_kbase_token("foo"))
        assert_json_rpc_error(response, 1050, "Upstream Error")

        # Error: Any other non-200 returned from orcid
        new_work_data["title"] = "trigger-400"
        params = {"username": "foo", "new_work": new_work_data}
        response = rpc_call("create-orcid-work", params, generate_kbase_token("foo"))
        assert_json_rpc_error(response, 1050, "Upstream Error")
