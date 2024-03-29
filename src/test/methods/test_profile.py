import contextlib
import os
from test.mocks.data import load_data_json
from test.mocks.env import MOCK_KBASE_SERVICES_PORT, MOCK_ORCID_API_PORT, TEST_ENV
from test.mocks.mock_contexts import (
    mock_auth_service,
    mock_orcid_api_service,
    no_stderr,
)
from test.mocks.testing_utils import (
    assert_json_rpc_error,
    assert_json_rpc_result_ignore_result,
    clear_database,
    generate_kbase_token,
    rpc_call,
)
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from orcidlink import model
from orcidlink.jsonrpc.errors import NotFoundError
from orcidlink.main import app
from orcidlink.storage import storage_model

client = TestClient(app)


@pytest.fixture
def fake_fs(fs):
    data_dir = os.environ["TEST_DATA_DIR"]
    fs.add_real_directory(data_dir)
    yield fs


TEST_DATA_DIR = os.environ["TEST_DATA_DIR"]
TEST_LINK = load_data_json(TEST_DATA_DIR, "link2.json")


@contextlib.contextmanager
def mock_services():
    with no_stderr():
        with mock_auth_service(MOCK_KBASE_SERVICES_PORT):
            with mock_orcid_api_service(MOCK_ORCID_API_PORT):
                yield


@pytest.fixture(autouse=True)
def around_tests(fake_fs):
    yield


async def create_link():
    sm = storage_model.storage_model()
    await sm.db.links.drop()
    await sm.create_link_record(model.LinkRecord.model_validate(TEST_LINK))


#
# Tests
#


# TODO: How did this ever work?
# def test_router_profile_to_normalized():
#     orcid_id = "0000-0003-4997-3076"
#     raw_profile = orcid_api.ORCIDProfile.model_validate(load_test_data("orcid", "profile"))
#     model_profile = model.ORCIDProfile.model_validate(
#         load_test_data("orcid", "profile-model")
#     )
#     assert (
#             get_profile(orcid_id, raw_profile).dict()
#             == model_profile.dict()
#     )
#
#
# def test_router_profile_to_normalized_single_affiliation():
#     orcid_id = "0000-0003-4997-3076"
#     orcid_data = load_test_data("orcid", "profile-single-affiliation")
#     raw_profile = orcid_api.ORCIDProfile.model_validate(orcid_data)
#     model_data = load_test_data("orcid", "profile-model-single-affiliation")
#     model_profile = model.ORCIDProfile.model_validate(model_data)
#     assert get_profile(orcid_id, raw_profile) == model_profile


# def xest_get_profile():
#     server = MockServer("127.0.0.1", MockORCIDOAuth2)
#     server.start_service()
#     try:
#         client = ORCIDOAuthClient(
#             url=server.base_url(),
#             access_token="access_token"
#         )
#         with pytest.raises(ServiceError, match="Error fetching data from ORCID Auth api"):
#             client.revoke_token()
#     except Exception as ex:
#         pytest.fail(f"Unexpected exception raised: {str(ex)}")
#     finally:
#         server.stop_service()


async def test_get_profile(fake_fs):
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        with mock_services():
            await create_link()
            response = rpc_call(
                "get-orcid-profile",
                {"username": "foo"},
                generate_kbase_token("foo"),
            )
            result = assert_json_rpc_result_ignore_result(response)
            assert result["orcidId"] == "0000-0003-4997-3076"
            # TODO: test something else about the result.


async def test_get_profile_not_found(fake_fs):
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        with mock_services():
            await clear_database()
            response = rpc_call(
                "get-orcid-profile",
                {"username": "foo"},
                generate_kbase_token("foo"),
            )
            assert_json_rpc_error(response, NotFoundError.CODE, NotFoundError.MESSAGE)
