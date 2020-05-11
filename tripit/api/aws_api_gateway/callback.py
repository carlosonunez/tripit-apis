"""
API endpoint for handling callbacks.
"""
from tripit.auth.step_2 import handle_callback
from tripit.cloud_helpers.aws.api_gateway import (
    get_endpoint,
    get_access_key,
    get_query_parameter,
    get_host,
    return_ok,
    return_error,
)

# TODO: Handle token reauthorizations. Do this after we get passing integration tests.
def callback(event, _context):
    """
    Handle the callback from TripIt.
    """
    access_key = get_access_key(event)
    if not access_key:
        return return_error(message="Failed to get access key from event.")
    endpoint = get_endpoint(event)
    if not endpoint:
        return return_error(message="Failed to get endpoint from event.")
    host = get_host(event)
    if not host:
        return return_error(message="Failed to get endpoint from event.")
    callback_token = get_query_parameter(event, "oauth_token")
    if not callback_token:
        return return_error(message="Failed to obtain a callback token.")
    if handle_callback(access_key, callback_token):
        return return_ok()
    return return_error(message="Authentication failed.")
