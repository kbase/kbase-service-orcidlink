import pytest
from orcidlink.lib import config
from test.data.utils import load_data_file
from test.mocks.mock_contexts import mock_service_wizard_service, no_stderr

config_yaml = load_data_file("config1.yaml")

config_yaml = load_data_file("config1.yaml")
config_yaml2 = load_data_file("config2.yaml")


@pytest.fixture
def my_config_file(fs):
    fs.create_file("/kb/module/config/config.yaml", contents=config_yaml)
    fs.add_real_directory("/kb/module/src/test/data")
    yield fs


@pytest.fixture
def my_config_file2(fs):
    fs.create_file("/kb/module/config/config.yaml", contents=config_yaml2)
    fs.add_real_directory("/kb/module/src/test/data")
    yield fs


def test_get_config(my_config_file2):
    # Force reload of the mock config to a pristine state.
    config.config(reload=True)
    assert config.config().module.CLIENT_ID == "REDACTED-CLIENT-ID"
    assert config.config().module.CLIENT_SECRET == "REDACTED-CLIENT-SECRET"
    assert (
            config.config().kbase.services.Auth2.url
            == "https://ci.kbase.us/services/auth/api/V2/token"
    )


def test_config_initially_none(my_config_file2):
    """
    Various
    It is difficult to test this in the natural state, in which the
    global config manager in the config module starts life as None, but
    is initialized upon first usage. That lifecycle depends upon the
    application lifecycle, and with tests we don't
    have control over that. So we simulate that by resetting it to None first.
    """
    # Force reload of the mock config to a pristine state.
    config.GLOBAL_CONFIG_MANAGER = None
    assert config.GLOBAL_CONFIG_MANAGER is None
    config.config()
    assert config.GLOBAL_CONFIG_MANAGER is not None
    assert config.config().kbase.uiOrigin == "https://ci.kbase.us"


def test_set_config(my_config_file):
    with no_stderr():
        with mock_service_wizard_service() as [_, mock_class, _]:
            mock_class.reset_call_counts()

            # server address.
            config.config()

            config.config(reload=True)

            # Set to different value, should be changed.
            config.config().kbase.services.ServiceWizard.url = "FOO"
            assert config.config().kbase.services.ServiceWizard.url == "FOO"

            # Set to same value, nothing should change
            config.config().kbase.services.ServiceWizard.url = "FOO"
            assert config.config().kbase.services.ServiceWizard.url == "FOO"

            # with pytest.raises(ValueError, match="Config not found on path: kbase.services.ServiceWizard.url2") as ex:
            #     config.set_config(["kbase", "services", "ServiceWizard", "url2"], "FOO")
