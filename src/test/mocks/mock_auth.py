import json
import os
from test.mocks.mock_server import MockService


def load_test_data(filename: str):
    data_dir = os.environ["TEST_DATA_DIR"]
    test_data_path = f"{data_dir}/test_KBaseAuth/{filename}.json"
    # fs.add_real_directory(data_dir)
    # test_data_path = (
    #     f"{config().service_directory}/src/test/service_clients"
    #     "/test_KBaseAuth/{filename}.json"
    # )
    with open(test_data_path) as fin:
        return json.load(fin)


class MockAuthServiceBase(MockService):
    # @staticmethod
    # def error_no_token():
    #     return {
    #         "error": {
    #             "httpcode": 400,
    #             "httpstatus": "Bad Request",
    #             "appcode": 10010,
    #             "apperror": "No authentication token",
    #             "message": "10010 No authentication token: No user token provided",
    #             "callid": "abc",
    #             "time": 123,
    #         }
    #     }

    @staticmethod
    def error_invalid_token():
        return {
            "error": {
                "httpcode": 401,
                "httpstatus": "Unauthorized",
                "appcode": 10020,
                "apperror": "Invalid Token",
                "message": "10020 Invalid Token",
                "callid": "123",
                "time": 123,
            }
        }

    @staticmethod
    def error_other():
        return {
            "error": {
                # don't know about the status
                "httpcode": 401,
                "httpstatus": "Unauthorized",
                "appcode": 10050,
                "apperror": "Password / username mismatch",
                "message": "10050 Password / username mismatch",
                "callid": "123",
                "time": 123,
            }
        }


GET_TOKEN_FOO = load_test_data("get-token-foo")
GET_TOKEN_BAR = load_test_data("get-token-bar")
GET_TOKEN_AMANAGER = load_test_data("get-token-bar")

GET_ME_FOO = load_test_data("get-me-foo")
GET_ME_BAR = load_test_data("get-me-bar")
GET_ME_AMANAGER = load_test_data("get-me-amanager")


class MockAuthService(MockAuthServiceBase):
    def do_GET(self):
        # TODO: Reminder - switch to normal auth2 endpoint in config and here.
        if self.path == "/services/auth/api/V2/token":
            authorization = self.headers.get("authorization")
            if authorization is None:
                # self.send_json_error(self.error_no_token())
                raise ValueError(
                    "Impossible - we never fail to set the authorization header "
                    "for auth"
                )
            else:
                if authorization.startswith("foo"):
                    self.send_json(GET_TOKEN_FOO, content_type="application/json")
                elif authorization.startswith("bar"):
                    self.send_json(GET_TOKEN_BAR, content_type="application/json")
                elif authorization.startswith("amamanger"):
                    self.send_json(GET_TOKEN_AMANAGER, content_type="application/json")
                # elif authorization.startswith("no_token"):
                #     self.send_json_error(self.error_no_token())
                elif authorization.startswith("invalid_token"):
                    self.send_json_error(
                        self.error_invalid_token(), 500, "application/json"
                    )
                elif authorization.startswith("other_error"):
                    self.send_json_error(self.error_other(), 500, "application/json")
                elif authorization.startswith("bad_content_type"):
                    self.send_text("Bad JSON!")
                # elif authorization.startswith("bad_json"):
                #     self.send_json("Bad JSON!")
                elif authorization.startswith("text_json"):
                    self.send_json_text("Bad JSON!", content_type="application/json")
                elif authorization == "internal_server_error":
                    self.send_text_error("Internal Server Error", 500)
                else:
                    self.send_json_error(
                        self.error_invalid_token(), 500, "application/json"
                    )

        if self.path == "/services/auth/api/V2/me":
            authorization = self.headers.get("authorization")
            if authorization is None:
                raise ValueError(
                    "Impossible - we never fail to set the authorization header "
                    "for auth"
                )
            else:
                if authorization.startswith("foo"):
                    self.send_json(GET_ME_FOO, content_type="application/json")
                elif authorization.startswith("bar"):
                    self.send_json(GET_ME_BAR, content_type="application/json")
                elif authorization.startswith("amanager"):
                    self.send_json(GET_ME_AMANAGER, content_type="application/json")
                # elif authorization.startswith("no_token"):
                #     self.send_json_error(self.error_no_token())
                elif authorization.startswith("invalid_token"):
                    self.send_json_error(
                        self.error_invalid_token(), 500, "application/json"
                    )
                elif authorization.startswith("other_error"):
                    self.send_json_error(self.error_other(), 500, "application/json")
                elif authorization.startswith("bad_content_type"):
                    self.send_text("Bad JSON!")
                # elif authorization.startswith("bad_json"):
                #     self.send_json("Bad JSON!")
                elif authorization.startswith("text_json"):
                    self.send_json_text("Bad JSON!", content_type="application/json")
                elif authorization.startswith("something_bad"):
                    # just do something bad:
                    x = 1 / 0
                    print(x)
                elif authorization == "internal_server_error":
                    self.send_text_error("Internal Server Error", 500)
                else:
                    self.send_json_error(
                        self.error_invalid_token(), 500, "application/json"
                    )
