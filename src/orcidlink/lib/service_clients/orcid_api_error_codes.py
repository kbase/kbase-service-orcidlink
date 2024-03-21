from enum import Enum
from typing import Dict, List

from pydantic import Field

from orcidlink.lib.type import ServiceBaseModel


class ORCIDAPIErrorCategory(str, Enum):
    connection = "connection"
    bad_request = "bad_request"
    internal_error = "internal_error"
    not_authorized = "not_authorized"
    insufficient_authorization = "insufficient_authorization"
    not_found = "not_found"
    other_error = "other_error"


class ORCIDAPIErrorCode(ServiceBaseModel):
    code: int = Field(...)
    developer_message: str = Field(...)
    user_message: str = Field(...)
    category: ORCIDAPIErrorCategory = Field(...)


ORCID_API_ERROR_CODES: List[ORCIDAPIErrorCode] = [
    ORCIDAPIErrorCode(
        code=9000,
        developer_message="There was an error connecting to ORCID.",
        user_message="There was an error connecting to ORCID.",
        category=ORCIDAPIErrorCategory.connection,
    ),
    ORCIDAPIErrorCode(
        code=9001,
        developer_message=(
            "400 Bad Request: There is an issue with your data or the API endpoint. "
            "405 Method Not Allowed: Endpoint and method mismatch. "
            "415 Unsupported Media Type: data must be in XML or JSON format."
        ),
        user_message="ORCID could not process the data, because they were invalid.",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9002,
        developer_message="The client application is not authorized.",
        user_message="The client application is not authorized.",
        category=ORCIDAPIErrorCategory.not_authorized,
    ),
    ORCIDAPIErrorCode(
        code=9003,
        developer_message="The client application is not authorized.",
        user_message="The client application is not authorized.",
        category=ORCIDAPIErrorCategory.not_authorized,
    ),
    ORCIDAPIErrorCode(
        code=9004,
        developer_message="403 Forbidden: Insufficient or wrong scope.",
        user_message="The client application is forbidden to perform the action.",
        category=ORCIDAPIErrorCategory.insufficient_authorization,
    ),
    ORCIDAPIErrorCode(
        code=9005,
        developer_message="403 Forbidden: Insufficient or wrong scope.",
        user_message="The client application is forbidden to perform the action.",
        category=ORCIDAPIErrorCategory.insufficient_authorization,
    ),
    ORCIDAPIErrorCode(
        code=9006,
        developer_message="The client application sent a bad request to ORCID.",
        user_message="The client application sent a bad request to ORCID.",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9007,
        developer_message=(
            "301 Moved Permanently: This account is deprecated. "
            "Please refer to account: ${orcid}. ORCID ${deprecated_orcid}"
        ),
        user_message="This account is deprecated. Please refer to account: ${orcid}.",
        category=ORCIDAPIErrorCategory.not_found,
    ),
    ORCIDAPIErrorCode(
        code=9008,
        developer_message="Something went wrong in ORCID.",
        user_message="Something went wrong in ORCID.",
        category=ORCIDAPIErrorCategory.internal_error,
    ),
    ORCIDAPIErrorCode(
        code=9009,
        developer_message="403 Forbidden: The notification has already been read and cannot be archived.",
        user_message="The client application tried to archive a message that has already been read.",
        category=ORCIDAPIErrorCategory.other_error,
    ),
    ORCIDAPIErrorCode(
        code=9010,
        developer_message=(
            "403 Forbidden: "
            "You are not the source of the ${activity}, so you are not allowed to update it."
        ),
        user_message="The client application is not the source of the resource it is trying to access.",
        category=ORCIDAPIErrorCategory.insufficient_authorization,
    ),
    ORCIDAPIErrorCode(
        code=9011,
        developer_message="404 Not Found: The ORCID record or item was not found.",
        user_message="The resource was not found.",
        category=ORCIDAPIErrorCategory.not_found,
    ),
    ORCIDAPIErrorCode(
        code=9012,
        developer_message="The client application made a bad request to the ORCID API.",
        user_message="The client application made a bad request to the ORCID API.",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9013,
        developer_message="403 Forbidden: The item is private and you are not the source.",
        user_message="The client application is forbidden to perform the action.",
        category=ORCIDAPIErrorCategory.insufficient_authorization,
    ),
    ORCIDAPIErrorCode(
        code=9014,
        developer_message="The client application is forbidden to perform the action.",
        user_message="The client application is forbidden to perform the action.",
        category=ORCIDAPIErrorCategory.insufficient_authorization,
    ),
    ORCIDAPIErrorCode(
        code=9015,
        developer_message=(
            "One of the provided scopes is not allowed. "
            "Please refer to the list of allowed scopes at: "
            "https://github.com/ORCID/ORCID-Source/tree/master/orcid-model/"
            "src/main/resources/record_2.0#scopes."
        ),
        user_message="The client application tried to use an invalid permission on the ORCID API.",
        category=ORCIDAPIErrorCategory.insufficient_authorization,
    ),
    ORCIDAPIErrorCode(
        code=9016,
        developer_message="404 Not Found: The resource was not found.",
        user_message="The resource was not found.",
        category=ORCIDAPIErrorCategory.not_found,
    ),
    ORCIDAPIErrorCode(
        code=9017,
        developer_message=(
            "401 Unauthorized: The client application is not authorized for this ORCID record."
        ),
        user_message="The client application is not authorized.",
        category=ORCIDAPIErrorCategory.insufficient_authorization,
    ),
    ORCIDAPIErrorCode(
        code=9018,
        developer_message="409 Conflict: The ORCID record is locked and cannot be edited. ORCID ${orcid}",
        user_message="The ORCID record is locked.",
        category=ORCIDAPIErrorCategory.insufficient_authorization,
    ),
    ORCIDAPIErrorCode(
        code=9019,
        developer_message=(
            "400 Bad Request: "
            "The put code in the URL was ${urlPutCode} whereas the one in the body was ${bodyPutCode}."
        ),
        user_message=(
            "There was an error when updating the record. Please try again. "
            "If the error persists, please contact ${clientName} for assistance."
        ),
        category=ORCIDAPIErrorCategory.other_error,
    ),
    ORCIDAPIErrorCode(
        code=9020,
        developer_message="400 Bad Request: Invalid incoming message.",
        user_message="Invalid incoming message.",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9021,
        developer_message=(
            "409 Conflict: You have already added this activity (matched by external identifiers), "
            "please see element with put-code ${putCode}. "
            "If you are trying to edit the item, please use PUT instead of POST."
        ),
        user_message=(
            "There was an error when updating the record. Please try again. "
            "If the error persists, please contact ${clientName} for assistance."
        ),
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9022,
        developer_message="400 Bad Request: Invalid activity, a title is required.",
        user_message="Invalid activity:  A title is required.",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9023,
        developer_message="400 Bad Request: Invalid activity, an external identifier is required.",
        user_message="Invalid activity: an external identifier is required.",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9024,
        developer_message=(
            "400 Bad Request: Put-code is included when not expected. "
            "When posting new activities, the put code should be omitted."
        ),
        user_message=(
            "There was an error when updating the record. Please try again. "
            "If the error persists, please contact ${clientName} for assistance."
        ),
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9025,
        developer_message="409 Conflict: The given group-id-record already exists.",
        user_message="The given group-id-record already exists.",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9026,
        developer_message=(
            "400 Bad Request: "
            "The group you are trying to access does not exist, you may need to create it."
        ),
        user_message="The group-id-record does not exist.",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9027,
        developer_message="Unable to find client profile associated with client:${client}.",
        user_message="The resource was not found.",
        category=ORCIDAPIErrorCategory.not_found,
    ),
    ORCIDAPIErrorCode(
        code=9028,
        developer_message="No webhook found for orcid=${orcid}, and uri=${uri}.",
        user_message="The resource was not found.",
        category=ORCIDAPIErrorCategory.not_found,
    ),
    ORCIDAPIErrorCode(
        code=9029,
        developer_message=(
            "404 Not Found: Could not find notification with id: ${id} for ORCID: ${orcid}."
        ),
        user_message="The resource was not found.",
        category=ORCIDAPIErrorCategory.not_found,
    ),
    ORCIDAPIErrorCode(
        code=9030,
        developer_message="The element '${value}' of type '${type}' is duplicated. ",
        user_message="The element '${value}' of type '${type}' is duplicated. ",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9031,
        developer_message="Put-code is required to update elements.",
        user_message=(
            "There was an error when updating the record. Please try again. "
            "If the error persists, please contact ${clientName} for assistance."
        ),
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9032,
        developer_message=(
            "409 Conflict: "
            "The user has opted not to receive notifications so you cannot post notifications."
        ),
        user_message="The user ${orcid} doesn't allow notifications.",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9033,
        developer_message="The other name does not exist.",
        user_message="The other name does not exist.",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9034,
        developer_message="400 Bad Request: The put code provided is not valid.",
        user_message=(
            "There was an error when updating the record. Please try again. "
            "If the error persists, please contact ${clientName} for assistance."
        ),
        category=ORCIDAPIErrorCategory.not_found,
    ),
    ORCIDAPIErrorCode(
        code=9035,
        developer_message=(
            "403 Forbidden: You can't change the visibility of an item, "
            "please remove the visibility or set it to the current value."
        ),
        user_message=(
            "There was an error when updating the record. Please try again. "
            "If the error persists, please contact ${clientName} for assistance."
        ),
        category=ORCIDAPIErrorCategory.insufficient_authorization,
    ),
    ORCIDAPIErrorCode(
        code=9036,
        developer_message="409 Conflict: This record has not been claimed.",
        user_message=(
            "This record has not been claimed, if this is your record you can "
            "claim it at https://orcid.org/resend-claim."
        ),
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9037,
        developer_message="Invalid ${type}, valid values are: ${values}.",
        user_message="Please specify a work type.",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9038,
        developer_message=(
            "409 Conflict: The item has a limited or private visibility and "
            "your request doesn't have the required scope."
        ),
        user_message="You don't have the permissions to execute this action.",
        category=ORCIDAPIErrorCategory.insufficient_authorization,
    ),
    ORCIDAPIErrorCode(
        code=9039,
        developer_message=(
            "403 Forbidden: The item is not public and cannot be accessed with the Public API."
        ),
        user_message="The client application is forbidden to perform the action.",
        category=ORCIDAPIErrorCategory.insufficient_authorization,
    ),
    ORCIDAPIErrorCode(
        code=9040,
        developer_message="The item can't be deleted.",
        user_message="The item can't be deleted.",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9041,
        developer_message="404 Not Found: Biography for the given record is null.",
        user_message="There is no biography for the given record.",
        category=ORCIDAPIErrorCategory.not_found,
    ),
    ORCIDAPIErrorCode(
        code=9042,
        developer_message="Too many put codes supplied",
        user_message="Too many put codes supplied",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9043,
        developer_message=(
            "The start parameter for API users without credentials must be an integer between 0 and 10,000"
        ),
        user_message=(
            "The start parameter for API users without credentials must be an integer between 0 and 10,000"
        ),
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9044,
        developer_message="409 Conflict: The ORCID record is deactivated and cannot be edited.",
        user_message="The ORCID record is deactivated.",
        category=ORCIDAPIErrorCategory.not_found,
    ),
    ORCIDAPIErrorCode(
        code=9045,
        developer_message="400 Bad request: disambiguated-organization must be present and valid",
        user_message="No valid disambiguated-organization is included in the data.",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9046,
        developer_message="400 Bad request: organization must be present and valid",
        user_message="No valid organization is included in the data.",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9047,
        developer_message="400 Bad request: invalid JSON - ${error}",
        user_message="Invalid JSON.",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9048,
        developer_message=(
            "409 Conflict: The maximum number of works that can be connected to an ORCID record is 10,000"
        ),
        user_message=(
            "The maximum number of works that can be connected to an ORCID record is 10,000 and "
            "you have now exceeded this limit. Please remove some works and try again. "
            "For more information, see https://support.orcid.org/hc/articles/360006973133"
        ),
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9049,
        developer_message="400 Bad request: invalid date: ${dateString} ",
        user_message="Invalid date",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9050,
        developer_message=(
            "400 Bad request: missing start-date. If you specify an end-date, you must specify a start-date"
        ),
        user_message="Missing start-date. If you specify an end-date, you must specify a start-date",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9051,
        developer_message="400 Bad request: invalid value '${value}' for enum '${enum}'",
        user_message="Invalid value for type. ",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9052,
        developer_message="403 Forbidden: this access_token is only valid on API v3.0_rc2 and above",
        user_message="This access_token is only valid on API v3.0_rc2 and above.",
        category=ORCIDAPIErrorCategory.not_authorized,
    ),
    ORCIDAPIErrorCode(
        code=9053,
        developer_message="400 Bad Request: invalid ISSN",
        user_message="This does not appear to be a valid ISSN",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9054,
        developer_message="400 Bad Request: invalid amount",
        user_message="This does not appear to be a valid funding amount",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9055,
        developer_message="400 Bad Request: End date must come after start date.",
        user_message="End date must come after start date.",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9056,
        developer_message=(
            "Release candidates for V{0} are now disabled, your request will be redirected to the "
            "corresponding V{0} end point"
        ),
        user_message=(
            "Release candidates for V{0} are now disabled, your request will be redirected to "
            "the corresponding V{0} end point"
        ),
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9057,
        developer_message="409 Conflict: The client is locked.",
        user_message="The client is locked.",
        category=ORCIDAPIErrorCategory.other_error,
    ),
    ORCIDAPIErrorCode(
        code=9058,
        developer_message=(
            "404 Bad Request: Invalid contributor role: ${role}. Expected one of ${validRoles}. "
        ),
        user_message="Invalid contributor role.",
        category=ORCIDAPIErrorCategory.bad_request,
    ),
    ORCIDAPIErrorCode(
        code=9059,
        developer_message=(
            "Release candidates for V3.0 are now disabled, your request will be redirected to "
            "the corresponding V3.0 end point"
        ),
        user_message=(
            "Release candidates for V3.0 are now disabled, your request will be redirected to "
            "the corresponding V3.0 end point"
        ),
        category=ORCIDAPIErrorCategory.other_error,
    ),
]

_ORCID_API_ERROR_MAP: Dict[int, ORCIDAPIErrorCode] = {}

for error_code in ORCID_API_ERROR_CODES:
    _ORCID_API_ERROR_MAP[error_code.code] = error_code


def get_orcid_api_error(code: int) -> ORCIDAPIErrorCode | None:
    return _ORCID_API_ERROR_MAP.get(code)
