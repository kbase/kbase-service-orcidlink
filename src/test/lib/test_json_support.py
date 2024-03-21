from orcidlink.lib.json_support import JSONValue, json_path


def test_json_path_found():
    """
    In which we exercise cases in which the value is found.
    """
    # Simplest possible cases; the value is simply returned if there
    # is no path.
    json_values = [None, "foo", 1, True, False, {"foo": "bar"}, ["foo", "bar"]]
    for json_value in json_values:
        found, value = json_path(json_value, [])
        assert found is True
        assert value is json_value

    # A simple case to gets started with
    test_value: JSONValue = {"foo": "bar"}
    found, value = json_path(test_value, ["foo"])
    assert found is True
    assert value == "bar"

    # More complex case
    test_value: JSONValue = {"foo": [{"bar": [123, {"baz": "zing"}]}]}
    found, value = json_path(test_value, ["foo", 0, "bar", 1, "baz"])
    assert found is True
    assert value == "zing"


def test_json_path_not_found():
    """
    In which we exercise cases in which the value is not found.
    """
    # A simple case to gets started with; the key is simply not found in the dict
    test_value: JSONValue = {"foo": "bar"}
    found, value = json_path(test_value, ["bar"])
    assert found is False
    assert value is None

    # The value being inspected is not a dict at all!
    test_value: JSONValue = 123
    found, value = json_path(test_value, ["bar"])
    assert found is False
    assert value is None

    # A simple case to gets started with; the index is simply not found in the list
    test_value: JSONValue = ["foo", "bar", "baz"]
    found, value = json_path(test_value, [3])
    assert found is False
    assert value is None

    # The value being inspected is not a dict at all!
    test_value: JSONValue = 123
    found, value = json_path(test_value, [0])
    assert found is False
    assert value is None
