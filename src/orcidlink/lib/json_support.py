from types import NoneType
from typing import Dict, List, Tuple

JSONValue = (
    str | int | float | bool | NoneType | List["JSONValue"] | Dict[str, "JSONValue"]
)

JSONObject = Dict[str, JSONValue]

JSONArray = List[JSONValue]

#
# This is not good for now, as the cast can actually throw runtime errors, due to
# JSONObject having type errors.
#
# def as_json_object(value: Any) -> JSONObject:
#     if isinstance(value, dict):
#         return cast(value, JSONObject)
#     else:
#         raise ValueError("Not a JSON object")


def json_path(value: JSONValue, path: List[str | int]) -> Tuple[bool, JSONValue]:
    """
    Dig into a JSON Object or Array to locate the element on the path.
    """
    temp = value
    for element in path:
        if isinstance(element, str):
            if isinstance(temp, dict):
                if element in temp:
                    temp = temp[element]
                else:
                    return False, None
            else:
                return False, None
        else:
            if isinstance(temp, list):
                if len(temp) > element:
                    temp = temp[element]
                else:
                    return False, None
            else:
                return False, None
    return True, temp
