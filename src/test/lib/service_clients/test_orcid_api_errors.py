from orcidlink.lib.service_clients.orcid_api_errors import (
    ORCIDAPIError,
    orcid_api_error_to_json_rpc_error,
)


def test_orcid_api_error_to_json_rpc_error():
    api_error = ORCIDAPIError(
        response_code=1,
        developer_message="foo",
        user_message="bar",
        error_code=123,
        more_info="baz",
    )

    json_rpc_error = orcid_api_error_to_json_rpc_error(api_error)
