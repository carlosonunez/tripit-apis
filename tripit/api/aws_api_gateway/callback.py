"""
API endpoint for handling callbacks.
"""
from tripit.auth.step_2 import handle_callback
from tripit.cloud_helpers.aws.api_gateway import (
    get_endpoint,
    get_query_parameter,
    get_host,
    return_ok,
    return_error,
)

# TODO: Handle token reauthorizations. Do this after we get passing integration tests.
def callback(event, _context=None):
    """
    Handle the callback from TripIt.
    """
    endpoint = get_endpoint(event)
    if not endpoint:
        return return_error(message="Failed to get endpoint from event.")
    host = get_host(event)
    if not host:
        return return_error(message="Failed to get endpoint from event.")
    request_token = get_query_parameter(event, "oauth_token")
    if not request_token:
        return return_error(message="No request token in response.")
    if handle_callback(request_token):
        return return_ok()
    return return_error(message="Authentication failed.")
