"""
Functions for working with trips.
"""
from tripit.auth.token import get_token_data_for_access_key
from tripit.cloud_helpers.aws.api_gateway import (
    get_access_key,
    return_ok,
    return_error,
)


def get_trips(event):
    """
    Gets all trips associated with a TripIt account.
    """
    access_key = get_access_key(event)
    if not access_key:
        return return_error(message="Failed to get access key from event.")
    token_data = get_token_data_for_access_key(access_key)
    if not token_data:
        return return_error(code=403, message="Access denied; go to /auth first.")
    return return_ok()
