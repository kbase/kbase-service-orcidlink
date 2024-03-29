import http.server
import json
import threading
import time
from socket import socket
from urllib.parse import parse_qs

from orcidlink.jsonrpc.errors import INVALID_PARAMS, METHOD_NOT_FOUND

# from orcidlink.lib.errors import INVALID_PARAMS, METHOD_NOT_FOUND


class MockService(http.server.BaseHTTPRequestHandler):
    """
    Mock Auth Service HTTP Handler
    """

    total_call_count = {"success": 0, "error": 0}
    method_call_counts = {}

    def __init__(self, *args):
        super().__init__(*args)

    @classmethod
    def increment_call_count(cls, result_type: str):
        cls.total_call_count[result_type] += 1

    @classmethod
    def increment_method_call_count(cls, method: str, result_type: str):
        cls.increment_call_count(result_type)
        if method not in cls.method_call_counts:
            cls.method_call_counts[method] = {"success": 0, "error": 0}
        cls.method_call_counts[method][result_type] += 1

    @classmethod
    def get_method_call_count(cls, method: str):
        count = cls.method_call_counts.get(method)
        if count is None:
            return 0
        return count

    @classmethod
    def reset_call_counts(cls):
        cls.total_call_count = {"success": 0, "error": 0}
        cls.method_call_counts = {}

    def send(
        self, status_code: int, header: dict[str, str | int], data: str | None = None
    ):
        self.send_response(status_code)
        for key, value in header.items():
            self.send_header(key, str(value))
        self.end_headers()
        if data is not None:
            self.wfile.write(bytes(data, encoding="utf-8"))

    def send_json(self, output_data, content_type: str | None):
        output = json.dumps(output_data).encode()
        self.send_response(200)
        if content_type is not None:
            self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(output)))
        self.end_headers()
        self.wfile.write(output)

    def send_json_error(self, error_info, status_code: int, content_type: str):
        output = json.dumps(error_info).encode()
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(output)))
        self.end_headers()
        self.wfile.write(output)

    def send_text_error(self, text: str, status_code: int):
        # This is done intentionally by the backing http server,
        # which would correctly set the content type.
        self.send_response(status_code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(text)))
        self.end_headers()
        self.wfile.write(text.encode())

    def send_json_text_error(self, text: str):
        # This would be done erroneously by the service, so we use application/json
        self.send_response(500)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(text)))
        self.end_headers()
        self.wfile.write(text.encode())

    def send_json_text(self, text: str, content_type: str):
        # This would be done erroneously by the service, so we use application/json
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(text)))
        self.end_headers()
        self.wfile.write(text.encode())

    def send_text(self, text: str):
        # This could be done intentionally erroneously by the service too.
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(text)))
        self.end_headers()
        self.wfile.write(text.encode())

    def send_empty(self, status_code: int = 204):
        self.send_response(status_code)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def get_body_bytes(self):
        content_length_raw = self.headers.get("content-length")
        if content_length_raw is None:
            raise ValueError("Content length not present - cannot read")
        content_length = int(content_length_raw)
        return self.rfile.read(content_length)

    def get_body_string(self):
        content_length_raw = self.headers.get("content-length")
        if content_length_raw is None:
            raise ValueError("Content length not present - cannot read")
        content_length = int(content_length_raw)
        return self.rfile.read(content_length).decode(encoding="utf-8")

    def get_form_data(self):
        content_type = self.headers.get("content-type")
        if content_type != "application/x-www-form-urlencoded":
            raise Exception("expected 'application/x-www-form-urlencoded'")
        return parse_qs(self.get_body_string())


class MockServer:
    def __init__(self, ip_address: str, port: int, service_class):
        self.ip_address = ip_address
        self.port = port
        self.service_class = service_class
        self.server = None
        self.server_thread = None

        with socket() as s:
            # We bind to "" which means all interfaces, and port 0
            # which means to just pick an available one.
            s.bind(("", 0))
            self.port = port  # s.getsockname()[1]

    def base_url(self):
        """
        Returns the base url, or origin, of the service as determined
        in the constructor.

        This is the basis of the mock server being self-binding, with the
        test able to use the resulting url via this method.
        """
        return f"http://{self.ip_address}:{self.port}"

    def start_service(self):
        if self.server is not None:
            raise Exception("Server is already started")

        self.server = http.server.ThreadingHTTPServer(
            (self.ip_address, self.port), self.service_class
        )
        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        self.server_thread = server_thread

    def stop_service(self):
        if self.server is None:
            return
        self.server.shutdown()


class MockSDKJSON11ServiceBase(MockService):
    @staticmethod
    def success_response(result, call_id="123"):
        return {"version": "1.1", "id": call_id, "result": [result]}

    @staticmethod
    def empty_response(call_id="123"):
        return {"version": "1.1", "id": call_id, "result": []}

    @staticmethod
    def null_response(call_id="123"):
        return {"version": "1.1", "id": call_id, "result": None}

    @staticmethod
    def some_result(result, call_id="123"):
        return {"version": "1.1", "id": call_id, "result": result}

    @staticmethod
    def error_response(code, name, message=None, error=None, call_id="123"):
        error_data = {
            "code": code,
            "name": name,
        }
        if message is not None:
            error_data["message"] = message

        if error is not None:
            error_data["error"] = error

        return {"version": "1.1", "id": call_id, "error": error_data}

    @staticmethod
    def error_data_response(error_data, call_id="123"):
        return {"version": "1.1", "id": call_id, "error": error_data}

    def get_positional_params(self, request):
        method = request.get("method")
        positional_params = request.get("params")
        if positional_params is None:
            self.increment_method_call_count(method, "error")
            # Wrong, but we reflect it.
            return None, self.error_response(INVALID_PARAMS, "Invalid params")
        else:
            return positional_params[0], None

    def get_empty_positional_params(self, request):
        method = request.get("method")
        positional_params = request.get("params")
        if positional_params is None:
            self.increment_method_call_count(method, "error")
            # Wrong, but we reflect it.
            return None, self.error_response(INVALID_PARAMS, "Invalid params")
        elif len(positional_params) > 0:
            self.increment_method_call_count(method, "error")
            # Wrong, but we reflect it.
            return None, self.error_response(INVALID_PARAMS, "Invalid params")
        else:
            return None, None

    def get_body_json(self):
        return json.loads(self.get_body_string())


class MockSDKJSON11Service(MockSDKJSON11ServiceBase):
    def do_POST(self):
        # TODO: Reminder - switch to normal auth2 endpoint in config and here.
        if self.path == "/services/my_service":
            request = self.get_body_json()

            method = request.get("method")

            if method == "MyServiceModule.foo":
                # commit hash replaced with HASH for brevity; otherwise a real response
                positional_params = request.get("params")
                if positional_params is None:
                    self.increment_method_call_count(method, "error")
                    result = self.error_response(INVALID_PARAMS, "Invalid params")
                else:
                    params = positional_params[0]
                    if params.get("foo") == "bar":
                        self.increment_method_call_count(method, "success")
                        result = self.success_response({"bar": "baz"})
                    else:
                        self.increment_method_call_count(method, "error")
                        result = self.error_response(INVALID_PARAMS, "Invalid params")
            elif method == "MyServiceModule.no_params":
                positional_params = request.get("params")
                if positional_params is not None and len(positional_params) > 0:
                    self.increment_method_call_count(method, "error")
                    result = self.error_response(INVALID_PARAMS, "Invalid params")
                else:
                    self.increment_method_call_count(method, "success")
                    result = self.success_response({"bar": "baz"})
            elif method == "MyServiceModule.with_authorization":
                positional_params = request.get("params")
                if positional_params is not None and len(positional_params) > 0:
                    self.increment_method_call_count(method, "error")
                    result = self.error_response(INVALID_PARAMS, "Invalid params")
                else:
                    self.increment_method_call_count(method, "success")
                    authorization = self.headers.get("authorization")
                    if authorization is not None:
                        if authorization == "mytoken":
                            result = self.success_response({"token": authorization})
                        else:
                            result = self.error_response(
                                -32400, "Invalid authorization"
                            )
                    else:
                        result = self.error_response(-32500, "Missing authorization")

            elif method == "MyServiceModule.result_text":
                positional_params = request.get("params")
                if positional_params is not None and len(positional_params) > 0:
                    self.increment_method_call_count(method, "error")
                    result = self.error_response(INVALID_PARAMS, "Invalid params")
                else:
                    self.increment_method_call_count(method, "success")
                    self.send_text("This should fail")
                    return
            elif method == "MyServiceModule.result_json_text":
                positional_params = request.get("params")
                if positional_params is not None and len(positional_params) > 0:
                    self.increment_method_call_count(method, "error")
                    result = self.error_response(INVALID_PARAMS, "Invalid params")
                else:
                    self.increment_method_call_count(method, "success")
                    self.send_json_text(
                        "This should fail", content_type="application/json"
                    )
                    return
            elif method == "MyServiceModule.error_text":
                positional_params = request.get("params")
                if positional_params is not None and len(positional_params) > 0:
                    self.increment_method_call_count(method, "error")
                    result = self.error_response(INVALID_PARAMS, "Invalid params")
                else:
                    self.increment_method_call_count(method, "success")
                    self.send_text_error("This should fail", 500)
                    return
            elif method == "MyServiceModule.error_json_text":
                positional_params = request.get("params")
                if positional_params is not None and len(positional_params) > 0:
                    self.increment_method_call_count(method, "error")
                    result = self.error_response(INVALID_PARAMS, "Invalid params")
                else:
                    self.increment_method_call_count(method, "success")
                    self.send_json_text_error("This should fail")
                    return
            elif method == "MyServiceModule.empty_result":
                positional_params = request.get("params")
                if positional_params is not None and len(positional_params) > 0:
                    self.increment_method_call_count(method, "error")
                    result = self.error_response(INVALID_PARAMS, "Invalid params")
                else:
                    self.increment_method_call_count(method, "success")
                    result = self.empty_response()
            elif method == "MyServiceModule.null_result":
                positional_params = request.get("params")
                if positional_params is not None and len(positional_params) > 0:
                    self.increment_method_call_count(method, "error")
                    result = self.error_response(INVALID_PARAMS, "Invalid params")
                else:
                    self.increment_method_call_count(method, "success")
                    result = self.null_response()
            elif method == "MyServiceModule.invalid_result":
                positional_params = request.get("params")
                if positional_params is not None and len(positional_params) > 0:
                    self.increment_method_call_count(method, "error")
                    result = self.error_response(INVALID_PARAMS, "Invalid params")
                else:
                    self.increment_method_call_count(method, "success")
                    result = self.some_result(123)
            elif method == "MyServiceModule.wait":
                params, error = self.get_positional_params(request)
                if error is not None:
                    result = error
                else:
                    if params is None:
                        raise ValueError("Params is None")
                    sleep_for = params.get("for")
                    if sleep_for is None:
                        raise ValueError('Missing "for" parameter')
                    time.sleep(sleep_for)
                    self.increment_method_call_count(method, "success")
                    result = self.success_response({"bar": "baz"})
            else:
                self.increment_method_call_count(method, "error")
                result = self.error_response(METHOD_NOT_FOUND, "Method not found")

            self.send_json(result, content_type="application/json")
