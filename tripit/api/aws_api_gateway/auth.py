"""
API endpoint for authentication functions
"""
from tripit.auth.step_1 import get_authn_url
from tripit.cloud_helpers.aws.api_gateway import (
    get_endpoint,
    get_access_key,
    get_host,
    return_ok,
    return_error,
)


def begin_authentication(event, begin_auth_function_name):
    """
    Begin authenticating into TripIt by authorizing your account (and AWS access key)
    with Tripit.
    """
    access_key = get_access_key(event)
    if not access_key:
        return return_error(message="Failed to get access key from event.")
    endpoint = trim_auth_from_endpoint(get_endpoint(event), begin_auth_function_name)
    if not endpoint:
        return return_error(message="Failed to get endpoint from event.")
    host = get_host(event)
    if not host:
        return return_error(message="Failed to get endpoint from event.")
    auth_url = get_authn_url(access_key=access_key, host=host, api_gateway_endpoint=endpoint)
    if not auth_url:
        return return_error(message="No authorization URL received.")
    message = "".join(
        [
            "You will need to authenticate into TripIt first; ",
            "click on or copy/paste this URL to get started: ",
            auth_url,
        ]
    )
    return return_ok(message=message)


def trim_auth_from_endpoint(endpoint, endpoint_to_remove):
    """
    The event payload from API Gateway will contain the entire path for the call that was made.
    For example, issuing a GET request to https://example.com/v1/foo will produce
    an endpoint called '/v1/foo'.

    This is a problem for our callback function since it's a separate endpoint.
    Appending the entire endpoint path to '/callback' would produce '/v1/foo/callback',
    which is invalid.

    This function strips the actual API Gateway endpoint name from the endpoint path
    so that we get a callback function that's correct.
    """
    return endpoint.replace(f"/{endpoint_to_remove}", "")
