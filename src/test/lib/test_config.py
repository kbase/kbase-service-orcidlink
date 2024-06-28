import os

# from orcidlink.runtime import service_path
from test.mocks.data import load_data_file
from unittest import mock

import pytest

from orcidlink.lib.config import (
    IntEnvironmentVariable,
    ServiceConfig,
    StrEnvironmentVariable,
    get_git_info,
    get_service_description,
)

# from test.mocks.env import TEST_ENV


TEST_DATA_DIR = os.environ["TEST_DATA_DIR"]


service_description_toml = load_data_file(TEST_DATA_DIR, "service_description1.toml")
git_info_json = load_data_file(TEST_DATA_DIR, "git_info1.json")


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
    # "TOKEN_CACHE_LIFETIME": "60",
    # "TOKEN_CACHE_MAX_ITEMS": "10",
    # "REQUEST_TIMEOUT": "60",
    "FOO": "123",
}


def test_get_config():
    """
    Test all config properties with default behavior, if available.
    """
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        config = ServiceConfig().runtime_config
        assert config.auth_url == "http://foo/services/auth"
        # assert config.workspace_url == "http://foo/services/ws"
        assert config.orcidlink_url == "http://foo/services/orcidlink"
        assert config.token_cache_lifetime == 300
        assert config.token_cache_max_items == 20000
        assert config.request_timeout == 60
        assert config.ui_origin == "http://foo"
        assert config.orcid_api_base_url == "http://orcidapi"
        assert config.orcid_oauth_base_url == "http://orcidoauth"
        assert config.orcid_client_id == "CLIENT-ID"
        assert config.orcid_client_secret == "CLIENT-SECRET"
        assert config.mongo_host == "MONGO-HOST"
        assert config.mongo_port == 1234
        assert config.mongo_database == "MONGO-DATABASE"
        assert config.mongo_username == "MONGO-USERNAME"
        assert config.mongo_password == "MONGO-PASSWORD"


TEST_ENV_BAD = {
    "NO_KBASE_ENDPOINT": "http://foo/services/",
    "SERVICE_DIRECTORY": os.environ.get("SERVICE_DIRECTORY"),
    "FOO": "123",
}


def test_get_config_bad_env():
    with mock.patch.dict(os.environ, TEST_ENV_BAD, clear=True):
        with pytest.raises(
            ValueError,
            match=(
                'The environment variable "KBASE_ENDPOINT" is '
                "missing and there is no default value"
            ),
        ):
            ServiceConfig()


# get_int_constant


def test_get_int_constant_no_default():
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        value = ServiceConfig.get_int_environment_variable(
            IntEnvironmentVariable(
                required=True, env_name="FOO", unit="foo", description="my foo"
            )
        )
        assert value == 123


def test_get_int_constant_with_default():
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        value = ServiceConfig.get_int_environment_variable(
            IntEnvironmentVariable(
                required=True,
                env_name="FOO",
                value=456,
                unit="foo",
                description="my foo",
            )
        )
        assert value == 123


def test_get_int_constant_missing_with_default():
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        value = ServiceConfig.get_int_environment_variable(
            IntEnvironmentVariable(
                required=True,
                env_name="BAR",
                value=100,
                unit="foo",
                description="my foo",
            )
        )
        assert value == 100


def test_get_int_constant_missing_no_default():
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        with pytest.raises(
            ValueError,
            match=(
                'The environment variable "BAR" is missing and there is no '
                "default value"
            ),
        ):
            ServiceConfig.get_int_environment_variable(
                IntEnvironmentVariable(
                    required=True, env_name="BAR", unit="foo", description="my foo"
                )
            )


# get_str_constant


def test_get_str_constant_no_default():
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        value = ServiceConfig.get_str_environment_variable(
            StrEnvironmentVariable(required=True, env_name="FOO", description="my foo")
        )
        assert value == "123"


def test_get_str_constant_with_default():
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        value = ServiceConfig.get_str_environment_variable(
            StrEnvironmentVariable(
                required=True, env_name="FOO", value="456", description="my foo"
            )
        )
        assert value == "123"


def test_get_str_constant_missing_with_default():
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        value = ServiceConfig.get_str_environment_variable(
            StrEnvironmentVariable(
                required=True, env_name="BAR", value="baz", description="my bar"
            )
        )
        assert value == "baz"


def test_get_str_constant_missing_no_default():
    with mock.patch.dict(os.environ, TEST_ENV, clear=True):
        with pytest.raises(
            ValueError,
            match=(
                'The environment variable "BAR" is missing and there '
                "is no default value"
            ),
        ):
            ServiceConfig.get_str_environment_variable(
                StrEnvironmentVariable(
                    required=True, env_name="BAR", description="my bar"
                )
            )


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_get_service_description(fake_fs):
    service_description = get_service_description()
    assert service_description is not None
    assert service_description.version == "1.2.3"
    assert service_description.name == "ORCIDLink"


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_git_info(fake_fs):
    git_info = get_git_info()
    assert git_info.commit_hash_abbreviated == "678c42c"
    assert git_info.author_name == "Foo Bar"
