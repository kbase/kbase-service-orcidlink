from test.mocks.data import load_data_file, load_data_json

import pytest
import os
from unittest import mock

from orcidlink.lib import utils, errors
from orcidlink.model import (
    LinkingSessionComplete,
    LinkingSessionInitial,
    LinkRecord,
    ORCIDAuth,
)

# TODO: is it really worth it separately testing the mongo storage model? If so,
# we should not use the generic storage_model!
from orcidlink.storage.storage_model import storage_model
from test.mocks.env import TEST_ENV


@pytest.fixture
def fake_fs(fs):
    fs.add_real_directory(utils.module_path("test/data"))
    yield fs


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_constructor():
    model = storage_model()
    assert model is not None


#
# User records
#

EXAMPLE_LINK_RECORD_1 = {
    "session_id": "bar",
    "username": "foo",
    "created_at": 1,
    "expires_at": 2,
    "orcid_auth": {
        "access_token": "foo",
        "token_type": "bar",
        "refresh_token": "baz",
        "expires_in": 3,
        "scope": "boo",
        "name": "abc",
        "orcid": "def",
        "id_token": "xyz",
    },
}

EXAMPLE_LINK_RECORD_2 = {"session_id": "bar", "username": "foo"}


EXAMPLE_LINKING_SESSION_COMPLETED_1 = load_data_json(
    "linking_session_record_completed.json"
)

@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_create_link_record():
    sm = storage_model()
    sm.reset_database()
    sm.create_link_record(LinkRecord.model_validate(EXAMPLE_LINK_RECORD_1))
    record = sm.get_link_record("foo")
    assert record is not None
    assert record.orcid_auth.access_token == "foo"

@mock.patch.dict(os.environ, TEST_ENV, clear=True)

def test_save_link_record():
    sm = storage_model()
    sm.reset_database()
    sm.create_link_record(LinkRecord.model_validate(EXAMPLE_LINK_RECORD_1))
    record = sm.get_link_record("foo")
    assert record is not None
    assert record.orcid_auth.access_token == "foo"

    updated_record = LinkRecord.model_validate(EXAMPLE_LINK_RECORD_1)
    updated_record.orcid_auth.access_token = "fee"
    sm.save_link_record(updated_record)
    record = sm.get_link_record("foo")
    assert record is not None
    assert record.orcid_auth.access_token == "fee"

@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_delete_link_record():
    sm = storage_model()
    sm.reset_database()
    sm.create_link_record(LinkRecord.model_validate(EXAMPLE_LINK_RECORD_1))
    record = sm.get_link_record("foo")
    assert record is not None
    assert record.orcid_auth.access_token == "foo"

    sm.delete_link_record("foo")

    record = sm.get_link_record("foo")
    assert record is None


#
# LInking session records
#

EXAMPLE_LINKING_SESSION_RECORD_1 = {
    "session_id": "bar",
    "username": "foo",
    "created_at": 123,
    "expires_at": 456,
}

@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_create_linking_session():
    sm = storage_model()
    sm.reset_database()
    sm.create_linking_session(
        LinkingSessionInitial.model_validate(EXAMPLE_LINKING_SESSION_RECORD_1)
    )
    record = sm.get_linking_session_initial("bar")
    assert record is not None
    assert record.session_id == "bar"


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_save_linking_record():
    sm = storage_model()
    sm.reset_database()
    sm.create_linking_session(
        LinkingSessionInitial.model_validate(EXAMPLE_LINKING_SESSION_RECORD_1)
    )
    record = sm.get_linking_session_initial("bar")
    assert record is not None
    assert record.session_id == "bar"

    # updated_record = copy.deepcopy(EXAMPLE_LINKING_SESSION_RECORD_1)
    sm.update_linking_session_to_started("bar", "return-link", False, "ui-options")
    record2 = sm.get_linking_session_started("bar")
    assert record2 is not None
    assert record2.return_link == "return-link"
    assert record2.skip_prompt == False
    assert record2.ui_options == "ui-options"

    orcid_auth = ORCIDAuth(
        access_token="a",
        token_type="b",
        refresh_token="c",
        expires_in=123,
        scope="d",
        name="e",
        orcid="f",
        id_token="g",
    )

    sm.update_linking_session_to_finished("bar", orcid_auth)
    record3 = sm.get_linking_session_completed("bar")
    assert record3 is not None
    assert record3.orcid_auth.access_token == "a"

    sm.delete_linking_session("bar")

    record = sm.get_linking_session_completed("bar")
    assert record is None


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_update_linking_session_to_started_bad_session_id():
    sm = storage_model()
    sm.reset_database()
    sm.create_linking_session(
        LinkingSessionInitial.model_validate(EXAMPLE_LINKING_SESSION_RECORD_1)
    )
    record = sm.get_linking_session_initial("bar")
    assert record is not None
    assert record.session_id == "bar"

    # updated_record = copy.deepcopy(EXAMPLE_LINKING_SESSION_RECORD_1)
    with pytest.raises(errors.NotFoundError):
        sm.update_linking_session_to_started("baz", "return-link", False, "ui-options")


@mock.patch.dict(os.environ, TEST_ENV, clear=True)
def test_update_linking_session_to_finished_bad_session_id():
    sm = storage_model()
    sm.reset_database()
    sm.create_linking_session(
        LinkingSessionInitial.model_validate(EXAMPLE_LINKING_SESSION_RECORD_1)
    )
    record = sm.get_linking_session_initial("bar")
    assert record is not None
    assert record.session_id == "bar"

    # updated_record = copy.deepcopy(EXAMPLE_LINKING_SESSION_RECORD_1)
    sm.update_linking_session_to_started("bar", "return-link", False, "ui-options")
    orcid_auth = ORCIDAuth(
        access_token="a",
        token_type="b",
        refresh_token="c",
        expires_in=123,
        scope="d",
        name="e",
        orcid="f",
        id_token="g",
    )

    with pytest.raises(errors.NotFoundError):
        sm.update_linking_session_to_finished("baz", orcid_auth)
