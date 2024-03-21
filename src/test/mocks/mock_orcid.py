import json
import os
from test.mocks.data import load_test_data
from test.mocks.mock_server import MockService
from time import sleep
from urllib.parse import parse_qs

from orcidlink.lib import utils
from orcidlink.lib.service_clients.orcid_api import ORCID_API_CONTENT_TYPE

TEST_DATA_DIR = os.environ["TEST_DATA_DIR"]


class MockORCIDAPI(MockService):
    def do_GET(self):
        if self.path == "/0000-0003-4997-3076/record":
            test_data = load_test_data(TEST_DATA_DIR, "orcid", "profile")
            self.send_json(test_data, ORCID_API_CONTENT_TYPE)

        elif self.path == "/0000-0003-4997-3076/works":
            test_data = load_test_data(TEST_DATA_DIR, "orcid", "works_x")
            self.send_json(test_data, ORCID_API_CONTENT_TYPE)

        elif self.path == "/0000-0003-4997-3076/works/1526002":
            work_record = load_test_data(TEST_DATA_DIR, "orcid", "work_1526002")
            self.send_json(work_record, ORCID_API_CONTENT_TYPE)

        elif self.path == "/orcid-id-foo/works/1234":
            error = load_test_data(TEST_DATA_DIR, "orcid", "get-works-bad-put-code")
            # error = {
            #     "response-code": 400,
            #     "developer-message": (
            #         "400 Bad Request: The put code provided is not valid. "
            #         "Full validation error: '1234' is not a valid put code"
            #     ),
            #     "user-message": (
            #         "There was an error when updating the record. Please try again. "
            #         "If the error persists, please contact KBase CI for assistance."
            #     ),
            #     "error-code": 9034,
            #     "more-info": "https://members.orcid.org/api/resources/troubleshooting",
            # }
            self.send_json_error(error, 200, ORCID_API_CONTENT_TYPE)

        elif self.path == "/orcid-id-foo/works/12345":
            error = {
                "error": "invalid_token",
                "error_description": "Invalid access token: f276692e-c5e2-48ac-99ed-746817f42572x",
            }
            self.send_json_error(error, 400, "application/json")

        elif self.path == "/0000-0003-4997-3076/works/1487805":
            work_record = load_test_data(TEST_DATA_DIR, "orcid", "work_1487805")
            self.send_json(work_record, ORCID_API_CONTENT_TYPE)

        elif self.path == "/0000-0003-4997-3076/works/123":
            self.send_text("foobar")

        elif self.path == "/0000-0003-4997-3076/works/456":
            error = {
                "response-code": 400,
                "developer-message": (
                    "The client application sent a bad request to ORCID. "
                    'Full validation error: For input string: "1526002x"'
                ),
                "user-message": "The client application sent a bad request to ORCID.",
                "error-code": 9006,
                "more-info": "https://members.orcid.org/api/resources/troubleshooting",
            }
            self.send_json_error(error, 400, ORCID_API_CONTENT_TYPE)

        elif self.path == "/0000-0003-4997-3076/works/notsource":
            error = {
                "response-code": 403,
                "developer-message": (
                    "403 Forbidden: You are not the source of the work, "
                    "so you are not allowed to update it."
                ),
                "user-message": (
                    "The client application is not the source of the resource "
                    "it is trying to access."
                ),
                "error-code": 9010,
                "more-info": "https://members.orcid.org/api/resources/troubleshooting",
            }
            self.send_json_error(error, 403, ORCID_API_CONTENT_TYPE)
        else:
            raise Exception("Not a supported mock case")

    def do_DELETE(self):
        if self.path == "/0000-0003-4997-3076/work/1526002":
            # work_record = load_test_data(TEST_DATA_DIR, "orcid", "work_1526002")
            # test_data = {"bulk": [{"work": work_record}]}
            self.send_empty()
        elif self.path == "/0000-0003-4997-3076/work/123":
            error = {
                "response-code": 403,
                "developer-message": (
                    "403 Forbidden: You are not the source of the work, "
                    "so you are not allowed to update it."
                ),
                "user-message": (
                    "The client application is not the source of the resource "
                    "it is trying to access."
                ),
                "error-code": 9010,
                "more-info": "https://members.orcid.org/api/resources/troubleshooting",
            }
            self.send_json_error(error, 403, ORCID_API_CONTENT_TYPE)
        elif self.path == "/0000-0003-4997-3076/work/456":
            error = {
                "response-code": 404,
                "developer-message": (
                    "404 Not Found: The resource was not found. Full validation error: "
                    "No entity found for query"
                ),
                "user-message": "The resource was not found.",
                "error-code": 9016,
                "more-info": "https://members.orcid.org/api/resources/troubleshooting",
            }
            self.send_json_error(error, 404, ORCID_API_CONTENT_TYPE)

    def do_PUT(self):
        if self.path == "/0000-0003-4997-3076/work/1526002":
            test_data = load_test_data(TEST_DATA_DIR, "orcid", "work_1526002")["bulk"][
                0
            ]["work"]

            # simulates an updated last modified date.
            test_data["last-modified-date"]["value"] = utils.posix_time_millis()
            self.send_json(test_data, ORCID_API_CONTENT_TYPE)

    def do_POST(self):
        if self.path == "/0000-0003-4997-3076/works":
            new_work = json.loads(self.get_body_string())
            # TODO: just trust for now; simulate various error conditions
            # later.
            if new_work["bulk"][0]["work"]["title"]["title"]["value"] == "trigger-500":
                self.send_text_error("AN ERROR", status_code=500)
            elif (
                new_work["bulk"][0]["work"]["title"]["title"]["value"] == "trigger-400"
            ):
                error_data = {"user-message": "This is another error"}
                self.send_json_error(error_data, 400, ORCID_API_CONTENT_TYPE)
            elif (
                new_work["bulk"][0]["work"]["title"]["title"]["value"]
                == "trigger-http-exception"
            ):
                # Note that this assumes the client timeout is < 1 sec. Tests
                # should set the timeout to 0.5sec.
                sleep(1)
                # don't bother with sending data, as the connection
                # will probably be dead by the time this is reached.
            else:
                test_work = load_test_data(TEST_DATA_DIR, "orcid", "work_1526002")
                self.send_json(test_work, ORCID_API_CONTENT_TYPE)


class MockORCIDAPIWithErrors(MockService):
    def do_GET(self):
        # These handle ORCID Profile
        if self.path == "/0000-0003-4997-3076/record":
            test_data = load_test_data(TEST_DATA_DIR, "orcid", "profile")
            self.send_json(test_data, ORCID_API_CONTENT_TYPE)

        if self.path == "/not-found/record":
            test_data = load_test_data(TEST_DATA_DIR, "orcid", "get-profile-404-error")
            self.send_json_error(test_data, 404, ORCID_API_CONTENT_TYPE)

        elif self.path == "/trigger-401/record":
            test_data = load_test_data(TEST_DATA_DIR, "orcid", "get-profile-401-error")
            self.send_json_error(test_data, 401, ORCID_API_CONTENT_TYPE)

        elif self.path == "/trigger-415/record":
            test_data = load_test_data(TEST_DATA_DIR, "orcid", "get-profile-415-error")
            self.send_json_error(test_data, 415, ORCID_API_CONTENT_TYPE)

        elif self.path == "/trigger-500/record":
            test_data = load_test_data(TEST_DATA_DIR, "orcid", "get-profile-500-error")
            self.send_json_error(test_data, 500, ORCID_API_CONTENT_TYPE)

        elif self.path == "/trigger-no-content-type/record":
            test_data = load_test_data(TEST_DATA_DIR, "orcid", "profile")
            self.send_json(test_data, None)

        elif self.path == "/trigger-not-json/record":
            test_data = "this is not json!"
            self.send_json_text(test_data, ORCID_API_CONTENT_TYPE)

        elif self.path == "/trigger-invalid-token/record":
            test_data = load_test_data(
                TEST_DATA_DIR, "orcid", "get-profile-401-error-invalid-token"
            )
            self.send_json_error(test_data, 401, ORCID_API_CONTENT_TYPE)

        elif self.path == "/trigger-unauthorized/record":
            test_data = load_test_data(
                TEST_DATA_DIR, "orcid", "get-profile-401-error-unauthorized"
            )
            self.send_json_error(test_data, 401, ORCID_API_CONTENT_TYPE)

        elif self.path == "/trigger-error-some-other/record":
            test_data = load_test_data(
                TEST_DATA_DIR, "orcid", "get-profile-401-error-some-other"
            )
            self.send_json_error(test_data, 401, ORCID_API_CONTENT_TYPE)

        elif self.path == "/trigger-wrong-content-type/record":
            test_data = load_test_data(
                TEST_DATA_DIR, "orcid", "get-profile-401-error-some-other"
            )
            self.send_json_error(test_data, 401, ORCID_API_CONTENT_TYPE)

        # Handles email - used?
        elif self.path == "/0000-0003-4997-3076/email":
            test_data = load_test_data(TEST_DATA_DIR, "orcid", "email")
            self.send_json(test_data, ORCID_API_CONTENT_TYPE)

        # Handles ORCID profile work activity records
        elif self.path == "/0000-0003-4997-3076/works":
            test_data = load_test_data(TEST_DATA_DIR, "orcid", "orcid-works-error")
            self.send_json_error(test_data, 500, ORCID_API_CONTENT_TYPE)

        elif self.path == "/0000-0003-4997-3076/works/1526002":
            test_data = load_test_data(TEST_DATA_DIR, "orcid", "orcid-works-error")
            self.send_json_error(test_data, 500, ORCID_API_CONTENT_TYPE)
        else:
            # not found!
            test_data = load_test_data(
                TEST_DATA_DIR, "orcid", "get-profile-not-found-error"
            )
            self.send_json_error(test_data, 404, ORCID_API_CONTENT_TYPE)

    def do_PUT(self):
        if self.path == "/0000-0003-4997-3076/work/1526002":
            test_data = load_test_data(TEST_DATA_DIR, "orcid", "put_work_error")
            self.send_json_error(test_data, 500, ORCID_API_CONTENT_TYPE)


class MockORCIDOAuth(MockService):
    def do_POST(self):
        if self.path == "/revoke":
            data = parse_qs(self.get_body_string())
            token = data.get("token")
            if token is None:
                # what?
                pass

            elif token == ["access_token"]:
                # The "normal" case
                self.send_empty(status_code=200)

            elif token == ["access-token-foo"]:
                # The "normal" case
                # TODO: do we really need a duplicate case here?
                self.send_empty(status_code=200)

            elif token == ["access_token_for_foo"]:
                # The "normal" case
                # TODO: do we really need a duplicate case here?
                self.send_empty(status_code=200)

            elif token == ["foo"]:
                # The "normal" case
                # TODO: do we really need a duplicate case here?
                self.send_empty(status_code=200)

            elif token == ["error-unauthorized-client"]:
                error = {
                    "error": "unauthorized_client",
                    "error_description": "a description of the error",
                }
                # It is probably a 401, but who knows, and we don't care,
                # just that it is not 2xx and then we look at the json content
                self.send_json_error(error, 401, "application/json")

            elif token == ["error-invalid-scope"]:
                error = {
                    "error": "invalid_scope",
                    "error_description": "a description of the error",
                }
                self.send_json_error(error, 400, "application/json")

            elif token == ["non-empty-response"]:
                # The response is expected to be 200 and empty, so this triggers
                # an error.
                self.send(200, {"Content-Length": 3}, "foo")

            elif token == ["empty-response"]:
                # The response is expected to be 200 and not empty, so this triggers
                # an error.
                self.send(200, {"Content-Length": 0}, None)

            elif token == ["error-response-no-content-type"]:
                # We need to have a content length to get past that check
                self.send(400, {"Content-Length": 3}, "bar")

            elif token == ["error-response-not-json-content-type"]:
                self.send(400, {"Content-Length": 7, "Content-Type": "foo-son"}, None)

            elif token == ["error-response-not-json"]:
                self.send(
                    400,
                    {"Content-Length": 3, "Content-Type": "application/json"},
                    "foo",
                )

            elif token == ["error-response-invalid-json"]:
                self.send(
                    400,
                    {"Content-Length": 14, "Content-Type": "application/json"},
                    '{"foo": "bar"}',
                )

        elif self.path == "/token":
            data = parse_qs(self.get_body_string())
            if data["grant_type"] == ["refresh_token"]:
                # TODO: should load the test from our test data file
                # TODO: we should regularize the naming of such files to make it easier
                #       to coordinate them across test code.
                if data["refresh_token"] == ["refresh-token-foo"]:
                    test_data = {
                        "access_token": "access-token-foo-refreshed",
                        "token_type": "bearer",
                        "refresh_token": "refresh-token-foo-refreshed",
                        "expires_in": 631138518,
                        "scope": "/read-limited openid /activities/update",
                        "name": "Foo bar",
                        "orcid": "orcid-id-foo",
                    }
                    self.send_json(test_data, "application/json")

                elif data["refresh_token"] == ["refresh-token-bar"]:
                    test_data = {
                        "access_token": "access-token-bar-refreshed",
                        "token_type": "bearer",
                        "refresh_token": "refresh-token-bar-refreshed",
                        "expires_in": 631138518,
                        "scope": "/read-limited openid /activities/update",
                        "name": "Bar Bear",
                        "orcid": " 0000-1111-2222-3333",
                    }
                    self.send_json(test_data, "application/json")

                elif data["refresh_token"] == ["refresh-token-unauthorized-client"]:
                    error = {
                        "error": "unauthorized_client",
                        "error_description": "a description of the error",
                    }
                    self.send_json_error(error, 401, "application/json")

                elif data["refresh_token"] == ["refresh-token-invalid-grant"]:
                    error = {
                        "error": "invalid_grant",
                        "error_description": "a description of the error",
                    }
                    self.send_json_error(error, 401, "application/json")

                elif data["refresh_token"] == ["refresh-token-other-error"]:
                    error = {
                        "error": "invalid_request",
                        "error_description": "a description of the error",
                    }
                    self.send_json_error(error, 400, "application/json")

                elif data["refresh_token"] == ["empty-content"]:
                    # We need to have a content length to get past that check
                    self.send(
                        200,
                        {"Content-Length": 0, "Content-Type": "application/json"},
                        None,
                    )

                elif data["refresh_token"] == ["no-content-type"]:
                    # We need to have a content length to get past that check
                    self.send(200, {"Content-Length": 10}, None)

                elif data["refresh_token"] == ["not-json-content-type"]:
                    self.send(
                        200, {"Content-Length": 7, "Content-Type": "foo-son"}, None
                    )

                elif data["refresh_token"] == ["not-json-content"]:
                    self.send(
                        400,
                        {"Content-Length": 3, "Content-Type": "application/json"},
                        "foo",
                    )

                elif data["refresh_token"] == ["invalid-error"]:
                    self.send(
                        400,
                        {"Content-Length": 14, "Content-Type": "application/json"},
                        '{"foo": "bar"}',
                    )

                else:
                    raise Exception("Sorry, this case not handled")

            else:
                if data["code"] == ["foo"]:
                    # TODO: should this be in a file?
                    test_data = {
                        "access_token": "access_token_for_foo",
                        "token_type": "Bearer",
                        "refresh_token": "refresh_token",
                        "expires_in": 1000,
                        "scope": "scope1",
                        "name": "Foo Bear",
                        "orcid": "abc123",
                    }
                    self.send_json(test_data, "application/json")
                elif data["code"] == ["no-content-length"]:
                    # We need to have a content length to get past that check
                    self.send(200, {}, None)
                elif data["code"] == ["empty-content"]:
                    # We need to have a content length to get past that check
                    self.send(
                        200,
                        {"Content-Length": 0, "Content-Type": "application/json"},
                        None,
                    )
                elif data["code"] == ["no-content-type"]:
                    # We need to have a content length to get past that check
                    self.send(200, {"Content-Length": 10}, None)
                elif data["code"] == ["not-json-content-type"]:
                    self.send(
                        200, {"Content-Length": 7, "Content-Type": "foo-son"}, None
                    )
                elif data["code"] == ["error-incorrect-error-format"]:
                    self.send_json_error({"foo": "bar"}, 400, "application/json")
                elif data["code"] == ["error-correct-error-format"]:
                    error = {
                        "error": "invalid_request",
                        "error_description": "a description of some error",
                    }
                    self.send_json_error(error, 400, "application/json")
                elif data["code"] == ["not-json-content"]:
                    self.send_json_text("foo", "application/json")
                elif data["code"] == ["internal-error-500"]:
                    error = {
                        "error": "invalid_request",
                        "error_description": "a description of some error",
                    }
                    self.send_json_error(error, 500, "application/json")
                elif data["code"] == ["trigger-internal-error"]:
                    # Maybe sending and invalid response will do the trick?
                    # Yes, the trick is to set the content length too long for the
                    # content.
                    # This triggers a "ClientPayloadError", which is not specifically
                    # caught but rather caught in the "Exception" catchall in
                    # InteractiveRoute, and re-cast as an internal server error.
                    self.send(
                        200,
                        {"content-length": 100, "content-type": "application/json"},
                        '{"farr": "too short"}',
                    )
                else:
                    test_data = {
                        "access_token": "access_token",
                        "token_type": "Bearer",
                        "refresh_token": "refresh_token",
                        "expires_in": 1000,
                        "scope": "scope1",
                        "name": "Foo Bear",
                        "orcid": "abc123",
                    }
                    self.send_json(test_data, "application/json")

    def do_GET(self):
        if self.path == "/authorize":
            # this is a browser-interactive url -
            # worth simulating?
            pass


class MockORCIDOAuth2(MockService):
    def do_POST(self):
        # TODO: Reminder - switch to normal auth2 endpoint in config and here.
        if self.path == "/revoke":
            self.send_empty(status_code=204)
