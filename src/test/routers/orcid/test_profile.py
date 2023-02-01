import contextlib

import pytest
from fastapi.testclient import TestClient
from orcidlink import model
from orcidlink.lib.config import config
from orcidlink.main import app
from orcidlink.routers.orcid.profile import get_profile_to_ORCIDProfile
from orcidlink.service_clients import orcid_api
from orcidlink.storage import storage_model
from test.data.utils import load_data_file, load_data_json, load_test_data
from test.mocks.mock_contexts import (
    mock_auth_service,
    mock_orcid_api_service,
    no_stderr,
)
from test.mocks.testing_utils import TOKEN_BAR, TOKEN_FOO

client = TestClient(app)

config_yaml = load_data_file("config1.toml")


@pytest.fixture
def fake_fs(fs):
    fs.create_file("/kb/module/config/config.toml", contents=config_yaml)
    fs.add_real_directory("/kb/module/src/test/data")
    yield fs


TEST_LINK = load_data_json("link2.json")


@contextlib.contextmanager
def mock_services():
    with no_stderr():
        with mock_auth_service():
            with mock_orcid_api_service():
                yield


@pytest.fixture(autouse=True)
def around_tests(fake_fs):
    config(True)
    yield


def create_link():
    sm = storage_model.storage_model()
    sm.db.links.drop()
    sm.create_link_record(model.LinkRecord.parse_obj(TEST_LINK))


#
# Tests
#


def test_router_profile_to_normalized():
    orcid_id = "0000-0003-4997-3076"
    raw_profile = orcid_api.ORCIDProfile.parse_obj(load_test_data("orcid", "profile"))
    model_profile = model.ORCIDProfile.parse_obj(
        load_test_data("orcid", "profile-model")
    )
    assert (
        get_profile_to_ORCIDProfile(orcid_id, raw_profile).dict()
        == model_profile.dict()
    )


def test_router_profile_to_normalized_single_affiliation():
    orcid_id = "0000-0003-4997-3076"
    orcid_data = load_test_data("orcid", "profile-single-affiliation")
    raw_profile = orcid_api.ORCIDProfile.parse_obj(orcid_data)
    model_data = load_test_data("orcid", "profile-model-single-affiliation")
    model_profile = model.ORCIDProfile.parse_obj(model_data)
    assert get_profile_to_ORCIDProfile(orcid_id, raw_profile) == model_profile


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


def test_get_profile(fake_fs):
    with mock_services():
        create_link()
        response = TestClient(app).get(
            "/orcid/profile", headers={"Authorization": TOKEN_FOO}
        )
        assert response.status_code == 200


def test_get_profile_not_found(fake_fs):
    with mock_services():
        response = TestClient(app).get(
            "/orcid/profile", headers={"Authorization": TOKEN_BAR}
        )
        assert response.status_code == 404