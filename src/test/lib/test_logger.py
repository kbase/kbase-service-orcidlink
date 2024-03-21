import json
import logging

import pytest

from orcidlink.lib.logger import JSONLogger


@pytest.fixture
def fake_fs(fs):
    fs.create_dir("/bar")
    yield fs


# def test_log_event(fake_fs):
#     log_level(logging.DEBUG)
#     log_id = log_event("foo", {"bar": "baz"})
#     assert isinstance(log_id, str)
#     with open("/tmp/orcidlink.log", "r") as fin:
#         # text = fin.read()
#         # assert True is False, text
#         # print('TEXT', text)
#         # raise ValueError(text)
#         log = json.load(fin)
#     assert log["event"]["name"] == "foo"
#     assert log["event"]["data"] == {"bar": "baz"}


def test_JSONLogger(fake_fs):
    logger = JSONLogger("/bar", "foo")
    logger.log_level(logging.DEBUG)
    log_id = logger.log_event("foo", {"bar": "baz"})
    assert isinstance(log_id, str)
    with open("/bar/foo.log", "r") as fin:
        log = json.load(fin)
    assert log["event"]["name"] == "foo"
    assert log["event"]["data"] == {"bar": "baz"}
