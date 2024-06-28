import contextlib
import os
from test.mocks.mock_auth import MockAuthService

# from test.mocks.mock_imaginary_service import MockImaginaryService
from test.mocks.mock_orcid import (
    MockORCIDAPI,
    MockORCIDAPIWithErrors,
    MockORCIDOAuth,
    MockORCIDOAuth2,
)
from test.mocks.mock_server import MockSDKJSON11Service, MockServer
from unittest import mock


@contextlib.contextmanager
def no_stderr():
    """
    Traps and disposes of stderr to clean up test output (like a poor programmer's
    "quiet")
    """
    with contextlib.redirect_stderr(open(os.devnull, "w", encoding="utf-8")):
        yield


@contextlib.contextmanager
def mock_auth_service(port: int):
    service = MockServer("127.0.0.1", port, MockAuthService)
    try:
        service.start_service()
        url = f"{service.base_url()}/services/auth"
        yield [service, MockAuthService, url, port]
    finally:
        service.stop_service()


@contextlib.contextmanager
def mock_orcid_oauth_service(port: int):
    service = MockServer("127.0.0.1", port, MockORCIDOAuth)
    try:
        service.start_service()
        url = service.base_url()
        yield [service, MockORCIDOAuth, url, port]
    finally:
        service.stop_service()


@contextlib.contextmanager
def mock_orcid_oauth_service2(port: int):
    service = MockServer("127.0.0.1", port, MockORCIDOAuth2)
    try:
        service.start_service()
        url = service.base_url()
        yield [service, MockORCIDOAuth2, url, port]
    finally:
        service.stop_service()


@contextlib.contextmanager
def mock_orcid_api_service(port: int):
    service = MockServer("127.0.0.1", port, MockORCIDAPI)
    try:
        service.start_service()
        url = service.base_url()
        yield [service, MockORCIDAPI, url, port]
    finally:
        service.stop_service()


@contextlib.contextmanager
def mock_orcid_api_service_with_errors(port: int):
    service = MockServer("127.0.0.1", port, MockORCIDAPIWithErrors)
    try:
        service.start_service()
        url = service.base_url()
        yield [service, MockORCIDAPIWithErrors, url, port]
    finally:
        service.stop_service()


# @contextlib.contextmanager
# def mock_imaginary_service(port: int):
#     server = MockServer("127.0.0.1", port, MockImaginaryService)
#     MockImaginaryService.reset_call_counts()
#     try:
#         server.start_service()
#         url = f"{server.base_url()}/services/imaginary_service"
#         yield [server, MockImaginaryService, url, port]
#     finally:
#         server.stop_service()


@contextlib.contextmanager
def mock_jsonrpc11_service(port: int):
    server = MockServer("127.0.0.1", port, MockSDKJSON11Service)
    MockSDKJSON11Service.reset_call_counts()
    try:
        server.start_service()
        url = f"{server.base_url()}/services/my_service"
        yield [server, MockSDKJSON11Service, url, port]
    finally:
        server.stop_service()


TEST_ENV = {
    "KBASE_ENDPOINT": "http://foo/services/",
    "SERVICE_DIRECTORY": os.environ.get("SERVICE_DIRECTORY"),
    "ORCID_API_BASE_URL": "http://orcidapi",
    "ORCID_OAUTH_BASE_URL": "http://orcidoauth",
    "ORCID_SITE_BASE_URL": "https://sandbox.orcid.org",
    "ORCID_CLIENT_ID": "CLIENT-ID",
    "ORCID_CLIENT_SECRET": "CLIENT-SECRET",
    "LINKING_SESSION_RETURN_URL": "https://ci.kbase.us/orcidlink/linkcontinue",
    "MONGO_HOST": "MONGO-HOST",
    "MONGO_PORT": "1234",
    "MONGO_DATABASE": "MONGO-DATABASE",
    "MONGO_USERNAME": "MONGO-USERNAME",
    "MONGO_PASSWORD": "MONGO-PASSWORD",
    "FOO": "123",
}


@contextlib.contextmanager
def mock_config():
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        yield
