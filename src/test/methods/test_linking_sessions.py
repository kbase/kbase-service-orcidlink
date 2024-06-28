import contextlib
import copy
import json
import os
from test.mocks.data import load_data_json
from test.mocks.env import MOCK_KBASE_SERVICES_PORT, MOCK_ORCID_OAUTH_PORT, TEST_ENV
from test.mocks.mock_contexts import (
    mock_auth_service,
    mock_orcid_oauth_service,
    no_stderr,
)
from test.mocks.testing_utils import (
    TOKEN_BAR,
    TOKEN_FOO,
    assert_json_rpc_error,
    assert_json_rpc_result_ignore_result,
    clear_storage_model,
    create_link,
    generate_kbase_token,
    repeat_str,
    rpc_call,
)
from unittest import mock
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from httpx import Response

from orcidlink.jsonrpc.errors import NotAuthorizedError
from orcidlink.main import app

TEST_DATA_DIR = os.environ["TEST_DATA_DIR"]
TEST_LINK = load_data_json(TEST_DATA_DIR, "link2.json")
TEST_LINK1 = load_data_json(TEST_DATA_DIR, "link1.json")
TEST_LINK_BAR = load_data_json(TEST_DATA_DIR, "link-bar.json")


#
# Canned assertions
#
async def assert_create_linking_session(authorization: str):
    params = {"username": "foo"}
    response = rpc_call("create-linking-session", params, authorization)
    result = assert_json_rpc_result_ignore_result(response)
    assert "session_id" in result
    assert isinstance(result["session_id"], str)
    return result


async def assert_create_linking_session_error(
    username: str, authorization: str, code: int, message: str
):
    response = rpc_call("create-linking-session", {"username": username}, authorization)
    assert_json_rpc_error(response, code, message)


async def assert_create_linking_session_error2(
    username: str, authorization: str | None, code: int, message: str
):
    response = rpc_call("create-linking-session", {"username": username}, authorization)
    assert_json_rpc_error(response, code, message)


def assert_get_linking_session(session_id: str):
    response = rpc_call(
        "get-linking-session", {"session_id": session_id}, generate_kbase_token("foo")
    )
    assert response.status_code == 200
    session_info = response.json()
    session_id = session_info["session_id"]
    assert isinstance(session_id, str)
    return session_info


def assert_start_linking_session(
    client: TestClient,
    session_id: str,
    kbase_session: str | None = None,
    kbase_session_backup: str | None = None,
    return_link: str | None = None,
    skip_prompt: str | None = None,
):
    headers = {}
    if kbase_session is not None:
        headers["Cookie"] = f"kbase_session={kbase_session}"
    elif kbase_session_backup is not None:
        headers["Cookie"] = f"kbase_session_backup={kbase_session_backup}"

    params = {}
    if return_link is not None:
        params["return_link"] = return_link
    if skip_prompt is not None:
        params["skip_prompt"] = skip_prompt

    # TODO: should be put or post
    response = client.get(
        f"/linking-sessions/{session_id}/oauth/start",
        headers=headers,
        params=params,
        follow_redirects=False,
    )
    assert response.status_code == 302

    # # TODO: assertion on the Location for the redirect

    # #
    # # Get linking session again.
    # #
    # response = client.get(
    #     f"/linking-sessions/{session_id}", headers={"Authorization": kbase_session}
    # )

    # assert response.status_code == 200
    # session_info = response.json()

    # assert isinstance(session_info["session_id"], str)
    # assert session_info["session_id"] == session_id
    # assert session_info["kind"] == "started"
    # assert "orcid_auth" not in session_info

    # return session_info


def assert_start_linking_session_error(
    client: TestClient,
    session_id: str,
    expected_error_code: int,
    kbase_session: str | None = None,
    return_link: str | None = None,
    skip_prompt: str | None = None,
) -> None:
    headers = {}
    if kbase_session is not None:
        headers["Cookie"] = f"kbase_session={kbase_session}"
    # elif kbase_session_backup is not None:
    #     headers["Cookie"] = f"kbase_session_backup={kbase_session_backup}"

    params = {}
    if return_link is not None:
        params["return_link"] = return_link
    if skip_prompt is not None:
        params["skip_prompt"] = skip_prompt

    # TODO: should be put or post
    response = client.get(
        f"/linking-sessions/{session_id}/oauth/start",
        headers=headers,
        params=params,
        follow_redirects=False,
    )
    assert response.status_code == 302

    assert_ui_error_response(response, expected_error_code)


def assert_continue_linking_session(
    client: TestClient,
    session_id: str,
    kbase_session: str | None = None,
    expected_response_code: int | None = None,
):
    # FINISH
    #
    # Get linking session again.
    #

    params = {
        "code": "foo",
        "state": json.dumps({"session_id": session_id}),
    }

    headers = {}
    headers["Cookie"] = f"kbase_session={kbase_session}"

    response = client.get(
        "/linking-sessions/oauth/continue",
        headers=headers,
        params=params,
        follow_redirects=False,
    )

    assert response.status_code == 302

    return response


def as_str(something: str | bytes) -> str:
    if isinstance(something, str):
        return something
    else:
        return str(something, encoding="utf-8")


def assert_ui_error_response(response: Response, expected_error_code: int) -> None:
    assert response.status_code == 302
    assert "location" in response.headers
    location_value = response.headers.get("location")
    assert location_value is not None

    url = urlparse(response.headers.get("location"))
    assert url.scheme == "http"
    assert url.hostname == "127.0.0.1"
    assert url.path == "/orcidlink/error"
    # assert url.query
    # annoyingly, may be string or bytes, so coerce, primarily to make
    # typing happy.
    query_string = as_str(url.query)
    query = parse_qs(query_string)  # type: ignore
    assert "code" in query
    assert query["code"] == [str(expected_error_code)]


def assert_continue_linking_session_error(
    client: TestClient,
    session_id: str,
    expected_error_code: int,
    kbase_session: str | None = None,
) -> None:
    # FINISH
    #
    # Get linking session again.
    #

    params = {
        "code": "foo",
        "state": json.dumps({"session_id": session_id}),
    }

    headers = {}
    if kbase_session is not None:
        headers["Cookie"] = f"kbase_session={kbase_session}"

    response = client.get(
        "/linking-sessions/oauth/continue",
        headers=headers,
        params=params,
        follow_redirects=False,
    )

    assert response.status_code == 302

    assert_ui_error_response(response, expected_error_code)


def assert_continue_linking_session_internal_error(
    client: TestClient,
    session_id: str,
    expected_error_code: int,
    kbase_session: str | None = None,
) -> None:
    """
    Here we test the bahvior of the oauth/continue endpoint in the face
    of an internal error.

    An internal error will be handled by the custom route handler
    (InteractiveRoute).

    So the trick is to orchestrate an internal error be triggered during
    this call. We do that with the specially-named oauth code
    "trigger-internal-error".
    """
    params = {
        "code": "trigger-internal-error",
        "state": json.dumps({"session_id": session_id}),
    }

    headers = {}
    if kbase_session is not None:
        headers["Cookie"] = f"kbase_session={kbase_session}"

    response = client.get(
        "/linking-sessions/oauth/continue",
        headers=headers,
        params=params,
        follow_redirects=False,
    )

    assert response.status_code == 302

    assert_ui_error_response(response, expected_error_code)

    # Now upwrap the location header, etc.


def assert_finish_linking_session(session_id: str, authorization: str):
    response = rpc_call(
        "finish-linking-session", {"session_id": session_id}, authorization
    )
    assert_json_rpc_result_ignore_result(response)


def assert_finish_linking_session_error(
    session_id: str, authorization: str, code: int, message: str
):
    response = rpc_call(
        "finish-linking-session", {"session_id": session_id}, authorization
    )
    assert_json_rpc_error(response, code, message)


def assert_location_params(response: Response, params: dict[str, str]):
    location = response.headers["location"]
    location_url = urlparse(location)
    location_params = parse_qs(location_url.query)
    for key, value in params.items():
        assert key in location_params
        param = location_params[key]
        assert len(param) == 1
        param_value = param[0]
        assert param_value == value


@contextlib.contextmanager
def mock_services():
    with no_stderr():
        with mock_auth_service(MOCK_KBASE_SERVICES_PORT):
            yield


#
# Tests
#


async def test_create_linking_session():
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        with mock_services():
            await clear_storage_model()
            await assert_create_linking_session(TOKEN_FOO)


async def test_create_linking_session_errors():
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        with mock_services():
            await clear_storage_model()

            #
            # Create a link for user "foo"
            #
            await create_link(TEST_LINK1)

            #
            # Create linking session; this should fail with errors.AlreadyLinkedError
            #
            await assert_create_linking_session_error(
                "foo", TOKEN_FOO, 1000, "User already linked"
            )

            await assert_create_linking_session_error(
                "foo", TOKEN_BAR, 1011, "Not Authorized"
            )


async def test_get_linking_session():
    """
    Now we create a session, and get it back, in order
    to test the "get linking session" call.
    """
    with mock_services():
        with mock.patch.dict(os.environ, TEST_ENV, clear=True):
            with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT):
                client = TestClient(app)

                await clear_storage_model()

                #
                # Create linking session.
                #
                initial_session_info = await assert_create_linking_session(TOKEN_FOO)
                initial_session_id = initial_session_info["session_id"]

                assert_start_linking_session(
                    client,
                    initial_session_id,
                    kbase_session=TOKEN_FOO,
                    kbase_session_backup=TOKEN_FOO,
                    return_link="baz",
                    skip_prompt="no",
                )

                assert_continue_linking_session(
                    client,
                    initial_session_id,
                    TOKEN_FOO,
                    expected_response_code=302,
                )

                response = rpc_call(
                    "get-linking-session", {"session_id": initial_session_id}, TOKEN_FOO
                )
                result = assert_json_rpc_result_ignore_result(response)
                assert result["username"] == "foo"
                # TODO: assert more stuff about the response?

                # linking_session = client.get_linking_session(initial_session_id)
                # assert linking_session["session_id"] == initial_session_id

                # initial_session_id = initial_session_info["session_id"]

                #
                # Get the session info.
                #
                # session_info = assert_get_linking_session(client, initial_session_id)
                # assert session_info["session_id"] == initial_session_id

                # Note that the call will fail if the result does not comply with either
                # LinkingSessionComplete or LinkingSessionInitial

                # The call after creating a linking session will return a
                # LinkingSessionInitial which we only know from the absense of
                # orcid_auth assert "orcid_auth" not in initial_session_info


async def test_delete_linking_session():
    """
    Now we create a session, and get it back, in order
    to test the "get linking session" call.
    """
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        with mock_services():
            with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT):
                client = TestClient(app)

                await clear_storage_model()

                #
                # Create linking session.
                #
                initial_session_info = await assert_create_linking_session(TOKEN_FOO)
                initial_session_id = initial_session_info["session_id"]

                assert_start_linking_session(
                    client,
                    initial_session_id,
                    kbase_session=TOKEN_FOO,
                    kbase_session_backup=TOKEN_FOO,
                    return_link="baz",
                    skip_prompt="no",
                )

                assert_continue_linking_session(
                    client,
                    initial_session_id,
                    TOKEN_FOO,
                    expected_response_code=302,
                )

                # Prove we have a completed linking session
                response = rpc_call(
                    "get-linking-session", {"session_id": initial_session_id}, TOKEN_FOO
                )
                result = assert_json_rpc_result_ignore_result(response)
                assert result["username"] == "foo"

                # Now delete the linking session - it should succeed with an empty response
                response = rpc_call(
                    "delete-linking-session",
                    {"session_id": initial_session_id},
                    TOKEN_FOO,
                )
                result = assert_json_rpc_result_ignore_result(response)
                assert result is None

                # Now try again, and we should find that the session is not found.
                response = rpc_call(
                    "get-linking-session", {"session_id": initial_session_id}, TOKEN_FOO
                )
                result = assert_json_rpc_error(response, 1020, "Not Found")


async def test_delete_linking_session_not_found():
    """
    Now we create a session, and get it back, in order
    to test the "get linking session" call.
    """
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        with mock_services():
            with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT):
                await clear_storage_model()

                fake_session_id = repeat_str("x", 36)

                response = rpc_call(
                    "delete-linking-session", {"session_id": fake_session_id}, TOKEN_FOO
                )
                assert_json_rpc_error(response, 1020, "Not Found")


async def test_get_linking_session_errors():
    """
    Now we create a session, and get it back, in order
    to test the "get linking session" call.
    """
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        with mock_services():
            with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT):
                client = TestClient(app, raise_server_exceptions=False)

                await clear_storage_model()

                # Get a non-existent linking session id
                fake_session_id = repeat_str("x", 36)

                response = rpc_call(
                    "get-linking-session", {"session_id": fake_session_id}, TOKEN_FOO
                )
                assert_json_rpc_error(response, 1020, "Not Found")

                # Get a malformed linking session id
                response = rpc_call(
                    "get-linking-session", {"session_id": "bar"}, TOKEN_FOO
                )

                # Should also be 404, because it is not completed yet.
                await clear_storage_model()
                session_info = await assert_create_linking_session(TOKEN_FOO)

                session_id = session_info["session_id"]

                response = rpc_call(
                    "get-linking-session", {"session_id": session_id}, TOKEN_FOO
                )
                assert_json_rpc_error(response, 1020, "Not Found")

                # To get a 403, we need a valid session with a different username.

                assert_start_linking_session(
                    client,
                    session_id,
                    kbase_session=TOKEN_FOO,
                    kbase_session_backup=TOKEN_FOO,
                    return_link="baz",
                    skip_prompt="no",
                )

                #
                # By using an token not matching the linking session, we get a
                # Not Authorized Error
                #
                assert_continue_linking_session_error(
                    client, session_id, NotAuthorizedError.CODE, kbase_session=TOKEN_BAR
                )

                #
                # Triggers a _real_ internal error within the code by
                # orchestrating an invalid response from the mock orcid oauth server.
                #
                assert_continue_linking_session_internal_error(
                    client, session_id, -32603, kbase_session=TOKEN_FOO
                )

                assert_continue_linking_session(
                    client,
                    session_id,
                    TOKEN_FOO,
                    expected_response_code=302,
                )

                assert_finish_linking_session_error(
                    session_id, TOKEN_BAR, 1011, "Not Authorized"
                )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_start_linking_session():
    """
    Now we create a session, and get it back, in order
    to test the "get linking session" call.
    """
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        with mock_services():
            with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT):
                client = TestClient(app)

                await clear_storage_model()

                initial_session_info = await assert_create_linking_session(TOKEN_FOO)
                initial_session_id = initial_session_info["session_id"]

                assert_start_linking_session(
                    client,
                    initial_session_id,
                    kbase_session=TOKEN_FOO,
                    return_link="baz",
                    skip_prompt="no",
                )


async def test_start_linking_session_backup_cookie():
    """
    Now we create a session, and get it back, in order
    to test the "get linking session" call.
    """
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        with mock_services():
            with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT):
                client = TestClient(app)

                await clear_storage_model()

                #
                # Create linking session.
                #
                initial_session_info = await assert_create_linking_session(TOKEN_FOO)
                initial_session_id = initial_session_info["session_id"]

                assert_start_linking_session(
                    client,
                    initial_session_id,
                    kbase_session_backup=TOKEN_FOO,
                    return_link="baz",
                    skip_prompt="no",
                )


async def test_start_linking_session_errors():
    """
    Now we create a session, and get it back, in order
    to test the "get linking session" call.
    """
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        with mock_services():
            client = TestClient(app, raise_server_exceptions=False)

            await clear_storage_model()

            #
            # Create linking session.
            #
            initial_session_info = await assert_create_linking_session(TOKEN_FOO)

            initial_session_id = initial_session_info["session_id"]

            #
            # Get the session info.
            #
            # session_info = assert_get_linking_session(client, initial_session_id)
            # assert session_info["session_id"] == initial_session_id

            # Note that the call will fail if the result does not comply with either
            # LinkingSessionComplete or LinkingSessionInitial

            # The call after creating a linking session will return a
            # LinkingSessionInitial which we only know from the absense of orcid_auth
            assert "orcid_auth" not in initial_session_info

            #
            # Start the linking session.
            #

            # If we start the linking session, the linking session will be updated, but
            # remain LinkingSessionInitial assert_start_linking_session(client,
            # initial_session_id)

            # No auth cookie

            assert_start_linking_session_error(client, initial_session_id, 1011, None)

            # username doesn't match
            assert_start_linking_session_error(
                client, initial_session_id, 1011, generate_kbase_token("bar")
            )

            # linking session id not correct format (s.b. 36 characters)
            assert_start_linking_session_error(
                client, "foo", -30602, generate_kbase_token("bar")
            )

            # linking session not found
            assert_start_linking_session_error(
                client, repeat_str("x", 36), 1020, generate_kbase_token("bar")
            )


async def test_linking_session_continue():
    """
    Here we simulate the oauth flow with ORCID - in which
    we redirect the browser to ORCID, which ends up returning
    to our return url which in turn may ask the user to confirm
    the linking, after which we exchange the code for an access token.
    """
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):

        async def assert_continue_linking_session(
            kbase_session: str | None = None,
            kbase_session_backup: str | None = None,
            return_link: str | None = None,
            skip_prompt: str | None = None,
            expected_response_code: int | None = None,
        ):
            client = TestClient(app)

            #
            # Create linking session.
            #
            await clear_storage_model()
            initial_session_info = await assert_create_linking_session(TOKEN_FOO)
            initial_session_id = initial_session_info["session_id"]

            #
            # Get the session info.
            # #
            # session_info = assert_get_linking_session(client, initial_session_id)
            # assert session_info["session_id"] == initial_session_id

            # Note that the call will fail if the result does not comply with either
            # LinkingSessionComplete or LinkingSessionInitial

            # The call after creating a linking session will return a
            # LinkingSessionInitial which we only know from the absence of orcid_auth
            assert "orcid_auth" not in initial_session_info

            #
            # Start the linking session.
            #

            # If we start the linking session, the linking session will be updated, but
            #  remain LinkingSessionInitial
            assert_start_linking_session(
                client,
                initial_session_id,
                kbase_session=TOKEN_FOO,
                return_link=return_link,
                skip_prompt=skip_prompt,
            )

            #
            # In the actual OAuth flow, the browser would invoke the start link endpoint
            # above, and naturally follow the redirect to ORCID OAuth.
            # We can't do that here, but we can simulate it via the mock oauth
            # service. That service also has a non-interactive endpoint "/authorize"
            # which exchanges the code for an access_token (amongst other things)
            #
            params = {
                "code": "foo",
                "state": json.dumps({"session_id": initial_session_id}),
            }

            headers = {}
            if kbase_session is not None:
                headers["Cookie"] = f"kbase_session={kbase_session}"
            if kbase_session_backup is not None:
                headers["Cookie"] = f"kbase_session_backup={kbase_session_backup}"

            response = client.get(
                "/linking-sessions/oauth/continue",
                headers=headers,
                params=params,
                follow_redirects=False,
            )
            assert response.status_code == expected_response_code

            # TODO assertions about Location

            #
            # Get the session info post-continuation, which will complete the
            # ORCID OAuth.
            #
            # session_info = assert_get_linking_session(client, initial_session_id)
            # assert started_linking_session["session_id"] == initial_session_id
            # # session_info is not in the public session info
            # assert "orcid_auth" in started_linking_session
            # TODO: test that it is in the raw session info, though.

            #
            # Finish the linking session
            #
            assert_finish_linking_session(initial_session_id, TOKEN_FOO)

            # TODO more assertions?

        # Use individual context managers here, as we only need this
        # setup once. If we need to use it again, we can can it in a
        # function above.
        with mock_services():
            with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT):
                await clear_storage_model()

                await assert_continue_linking_session(
                    kbase_session=TOKEN_FOO,
                    skip_prompt="no",
                    expected_response_code=302,
                )

                await clear_storage_model()
                await assert_continue_linking_session(
                    kbase_session_backup=TOKEN_FOO,
                    skip_prompt="no",
                    expected_response_code=302,
                )

                await clear_storage_model()
                await assert_continue_linking_session(
                    kbase_session=TOKEN_FOO,
                    return_link="bar",
                    skip_prompt="no",
                    expected_response_code=302,
                )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_continue_linking_session_errors():
    """
    Here we simulate the oauth flow with ORCID - in which
    we redirect the browser to ORCID, which ends up returning
    to our return url which in turn may ask the user to confirm
    the linking, after which we exchange the code for an access token.
    """
    with mock_services():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT):
            client = TestClient(app)
            await clear_storage_model()

            #
            # Create linking session.
            #
            initial_session_info = await assert_create_linking_session(TOKEN_FOO)
            initial_session_id = initial_session_info["session_id"]

            #
            # Get the session info.
            # #
            # session_info = assert_get_linking_session(client, initial_session_id)
            # assert session_info["session_id"] == initial_session_id

            # Note that the call will fail if the result does not comply with either
            # LinkingSessionComplete or LinkingSessionInitial

            # The call after creating a linking session will return a
            # LinkingSessionInitial which we only know from the absense of orcid_auth
            assert "orcid_auth" not in initial_session_info

            #
            # Start the linking session.
            #

            # If we start the linking session, the linking session will be updated, but
            # remain LinkingSessionInitial
            assert_start_linking_session(
                client,
                initial_session_id,
                kbase_session=TOKEN_FOO,
                skip_prompt="yes",
            )

            #
            # In the actual OAuth flow, the browser would invoke the start link endpoint
            # above, and naturally follow the redirect to ORCID OAuth.
            # We can't do that here, but we can simulate it via the mock oauth
            # service. That service also has a non-interactive endpoint "/authorize"
            # which exchanges the code for an access_token (amongst other things)
            #
            params = {
                "code": "foo",
                "state": json.dumps({"session_id": initial_session_id}),
            }

            response = assert_continue_linking_session_error(
                client, initial_session_id, 1010
            )

            # No auth cookie: no kbase_session or kbase_session_backup
            # response = client.get(
            #     "/linking-sessions/oauth/continue",
            #     params=params,
            #     follow_redirects=False,
            # )
            # assert response.status_code == 401

            # Error returned from orcid
            # TODO: double check the ORCID error structure; here we assume it is a
            # string.
            params = {"error": "foo"}
            response = client.get(
                "/linking-sessions/oauth/continue",
                headers={"Cookie": f"kbase_session={TOKEN_FOO}"},
                params=params,
                follow_redirects=False,
            )
            assert response.status_code == 302
            # TODO: test the response Location and the location info.

            # No code
            params = {"state": json.dumps({"session_id": initial_session_id})}
            response = client.get(
                "/linking-sessions/oauth/continue",
                headers={"Cookie": f"kbase_session={TOKEN_FOO}"},
                params=params,
                follow_redirects=False,
            )
            assert response.status_code == 302
            assert_location_params(
                response,
                {
                    "code": str("-32602"),
                    # "title": errors.ERRORS.linking_session_continue_invalid_param.title,
                    # "message": "The 'code' query param is required but missing",
                },
            )

            # No state
            params = {"code": "foo"}
            response = client.get(
                "/linking-sessions/oauth/continue",
                headers={"Cookie": f"kbase_session={TOKEN_FOO}"},
                params=params,
                follow_redirects=False,
            )
            assert response.status_code == 302
            assert_location_params(
                response,
                {
                    "code": str("-32602"),
                },
            )

            # No session_id
            params = {"code": "foo", "state": json.dumps({})}
            response = client.get(
                "/linking-sessions/oauth/continue",
                headers={"Cookie": f"kbase_session={TOKEN_FOO}"},
                params=params,
                follow_redirects=False,
            )
            assert response.status_code == 302
            assert_location_params(
                response,
                {
                    "code": str("-32602"),
                    # "title": errors.ERRORS.linking_session_continue_invalid_param.title,
                    # "message": (
                    #     "The 'session_id' was not provided in the 'state' query param"
                    # ),
                },
            )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_continue_linking_session_error_already_continued():
    """
    Here we simulate the oauth flow with ORCID - in which
    we redirect the browser to ORCID, which ends up returning
    to our return url which in turn may ask the user to confirm
    the linking, after which we exchange the code for an access token.
    """
    with mock_services():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT):
            client = TestClient(app)

            await clear_storage_model()

            #
            # Create linking session.
            #
            initial_session_info = await assert_create_linking_session(TOKEN_FOO)
            initial_session_id = initial_session_info["session_id"]

            #
            # Get the session info.
            #
            # session_info = assert_get_linking_session(client, initial_session_id)
            # assert session_info["session_id"] == initial_session_id

            # Note that the call will fail if the result does not comply with either
            # LinkingSessionComplete or LinkingSessionInitial

            # The call after creating a linking session will return a
            # LinkingSessionInitial which we only know from the absense of orcid_auth
            assert "orcid_auth" not in initial_session_info

            #
            # Start the linking session.
            #

            # If we start the linking session, the linking session will be updated, but
            # remain LinkingSessionInitial
            assert_start_linking_session(
                client,
                initial_session_id,
                kbase_session=TOKEN_FOO,
                skip_prompt="yes",
            )

            #
            # In the actual OAuth flow, the browser would invoke the start link endpoint
            # above, and naturally follow the redirect to ORCID OAuth.
            # We can't do that here, but we can simulate it via the mock oauth
            # service. That service also has a non-interactive endpoint "/authorize"
            # which exchanges the code for an access_token (amongst other things)
            #
            params = {
                "code": "foo",
                "state": json.dumps({"session_id": initial_session_id}),
            }

            headers = {
                "Cookie": f"kbase_session={TOKEN_FOO}",
            }

            # First time, it should be fine, returning a 302 as expected, with a
            # location to ORCID
            response = client.get(
                "/linking-sessions/oauth/continue",
                headers=headers,
                params=params,
                follow_redirects=False,
            )
            assert response.status_code == 302
            # TODO: make assertion about location

            # Second time it should produce an error
            response = client.get(
                "/linking-sessions/oauth/continue",
                headers=headers,
                params=params,
                follow_redirects=False,
            )
            assert response.status_code == 302
            assert_location_params(
                response,
                {
                    "code": str("1020"),
                    # "title": errors.ERRORS.linking_session_continue_invalid_param.title,
                    # "message": (
                    #     "The 'session_id' was not provided in the 'state' query param"
                    # ),
                },
            )

            # TODO: should be a 302, redirected to the error page.
            # assert response.status_code == 302
            # assert_location_params(
            #     response,
            #     {
            #         "code": "linking_session.wrong_state",
            #         "title": "Linking Error",
            #         "message": "The session is not in 'started' state",
            #     },
            # )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_finish_linking_session_error_already_finished():
    """
    Here we simulate the oauth flow with ORCID - in which
    we redirect the browser to ORCID, which ends up returning
    to our return url which in turn may ask the user to confirm
    the linking, after which we exchange the code for an access token.
    """
    with mock_services():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT):
            await clear_storage_model()

            #
            # Create linking session.
            #
            initial_session_info = await assert_create_linking_session(TOKEN_FOO)
            initial_session_id = initial_session_info["session_id"]

            #
            # Get the session info.
            #
            # session_info = assert_get_linking_session(client, initial_session_id)
            # assert session_info["session_id"] == initial_session_id

            # Note that the call will fail if the result does not comply with either
            # LinkingSessionComplete or LinkingSessionInitial

            # The call after creating a linking session will return a
            # LinkingSessionInitial which we only know from the absense of orcid_auth
            assert "orcid_auth" not in initial_session_info

            #
            # If we try to finish before starting, we should get a 400 error
            #
            assert_finish_linking_session_error(
                initial_session_id, TOKEN_FOO, 1020, "Not Found"
            )

            # # "invalidState",
            # # "Invalid Linking Session State",
            # # "The linking session must be in 'complete' state, but is not",
            # assert response.json() == {
            #     "code": "notFound",
            #     "title": "Not Found",
            #     "message": "Linking session not found",
            # }

            # #
            # # Start the linking session.
            # #

            # # If we start the linking session, the linking session will be updated, but remain
            # # LinkingSessionInitial
            # assert_start_linking_session(
            #     client,
            #     initial_session_id,
            #     kbase_session=TOKEN_FOO,
            #     skip_prompt="yes",
            # )

            # #
            # # In the actual OAuth flow, the browser would invoke the start link endpoint
            # # above, and naturally follow the redirect to ORCID OAuth.
            # # We can't do that here, but we can simulate it via the mock oauth
            # # service. That service also has a non-interactive endpoint "/authorize"
            # # which exchanges the code for an access_token (amongst other things)
            # #
            # params = {
            #     "code": "foo",
            #     "state": json.dumps({"session_id": initial_session_id}),
            # }

            # headers = {
            #     "Cookie": f"kbase_session={TOKEN_FOO}",
            # }

            # # First time, it should be fine, returning a 302 as expected, with a
            # # location to ORCID
            # response = client.get(
            #     "/linking-sessions/oauth/continue",
            #     headers=headers,
            #     params=params,
            #     follow_redirects=False,
            # )
            # assert response.status_code == 302

            # #
            # # Get the session info post-continuation, which will complete the
            # # ORCID OAuth.
            # #
            # session_info = assert_get_linking_session(client, initial_session_id)
            # assert session_info["session_id"] == initial_session_id
            # # The api should not reveal the orcid_auth
            # assert session_info["kind"] == "complete"
            # assert "orcid_auth" in session_info

            # #
            # # Finish the linking session; first time, ok.
            # #
            # response = client.put(
            #     f"/linking-sessions/{initial_session_id}/finish",
            #     headers={"Authorization": TOKEN_FOO},
            # )
            # assert response.status_code == 200

            # # Second time it should produce a 404 since it will have been deleted!
            # response = client.put(
            #     f"/linking-sessions/{initial_session_id}/finish",
            #     headers={"Authorization": TOKEN_FOO},
            # )
            # assert response.status_code == 404


# TODO: revive this.
# Need to get the linking session all the way to completed.
# def test_delete_linking_session(fake_fs):
#     with mock_services():
#         client = TestClient(app)

#         #
#         # Create the linking session.
#         #
#         initial_session_info = await assert_create_linking_session(client, TOKEN_FOO)
#         initial_session_id = initial_session_info["session_id"]

#         #
#         # Get the session info.
#         #
#         # session_info = assert_get_linking_session(client, initial_session_id)
#         # session_id = session_info["session_id"]
#         # assert session_id == initial_session_id

#         #
#         # Delete the session
#         #
#         response = client.delete(
#             f"/linking-sessions/{initial_session_id}", headers={"Authorization": TOKEN_FOO}
#         )
#         assert response.status_code == 204

#         #
#         # Check if it exists.
#         #
#         with pytest.raises(Exception) as ex:
#             assert_get_linking_session(client, initial_session_id)
#         assert ex is not None


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
async def test_continue_linking_session_error_link_already_exists():
    """
    Here we simulate the case in which, when a user returns to the orcidlink ui's
    "continue" step, the user has chosen an orcid account which is already linked.


    """
    with mock_services():
        with mock_orcid_oauth_service(MOCK_ORCID_OAUTH_PORT):
            client = TestClient(app)

            await clear_storage_model()

            #
            # Create a link for user "bar", but we replace the orcid id with that
            # for user "foo". This should let us simulate trying to create an orcid link
            # when the orcid id is already linked.
            #
            bar_link = copy.deepcopy(TEST_LINK_BAR)
            # Note that the orcid id is taken from the mock orcid oauth service.
            # TODO: we should improve the mock support so that the various mock data
            # is perfectly consistent.
            bar_link["orcid_auth"]["orcid"] = "abc123"
            await create_link(bar_link)

            #
            # Create linking session; this should fail with errors.AlreadyLinkedError
            #
            client = TestClient(app)
            await assert_create_linking_session_error(
                "bar", TOKEN_BAR, 1000, "User already linked"
            )

            #
            # Create linking session.
            #
            initial_session_info = await assert_create_linking_session(TOKEN_FOO)
            initial_session_id = initial_session_info["session_id"]

            #
            # Get the session info.
            #
            # session_info = assert_get_linking_session(client, initial_session_id)
            # assert session_info["session_id"] == initial_session_id

            # Note that the call will fail if the result does not comply with either
            # LinkingSessionComplete or LinkingSessionInitial

            # The call after creating a linking session will return a
            # LinkingSessionInitial which we only know from the absense of orcid_auth
            assert "orcid_auth" not in initial_session_info

            #
            # Start the linking session.
            #

            # If we start the linking session, the linking session will be updated, but
            # remain LinkingSessionInitial
            assert_start_linking_session(
                client,
                initial_session_id,
                kbase_session=TOKEN_FOO,
                skip_prompt="yes",
            )

            #
            # In the actual OAuth flow, the browser would invoke the start link endpoint
            # above, and naturally follow the redirect to ORCID OAuth.
            # We can't do that here, but we can simulate it via the mock oauth
            # service. That service also has a non-interactive endpoint "/authorize"
            # which exchanges the code for an access_token (amongst other things)
            #
            params = {
                "code": "foo",
                "state": json.dumps({"session_id": initial_session_id}),
            }

            headers = {
                "Cookie": f"kbase_session={TOKEN_FOO}",
            }

            # We should get an error response. In this case, since it will be a 302, as
            # for the success case, but the url will be to the error page at the orcid
            # link ui.
            response = client.get(
                "/linking-sessions/oauth/continue",
                headers=headers,
                params=params,
                follow_redirects=False,
            )
            assert response.status_code == 302
