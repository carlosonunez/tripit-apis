"""
Handles retrieving tokens from access keys.
"""
from tripit.auth.models import TripitAccessToken


def get_token_data_for_access_key(access_key):
    """
    Fetches a token for an access key, if it has one.
    """
    return TripitAccessToken.as_dict(access_key)
