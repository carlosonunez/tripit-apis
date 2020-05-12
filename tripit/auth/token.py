"""
Handles retrieving tokens from access keys.
"""
from tripit.auth.models import TripitAccessToken
from tripit.logging import logger


def get_token_data_for_access_key(access_key):
    """
    Fetches a token for an access key, if it has one.
    """
    try:
        return TripitAccessToken.as_dict(access_key)
    except Exception as access_token_error:
        logger.warning("Failed to get an access token: %s", access_token_error)
        return None
