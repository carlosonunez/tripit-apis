"""
This is code that handles step 2 of the authentication process.

See the test for this file in tests/unit for more info.
"""
from pynamodb.exceptions import TransactWriteError
from tripit.auth.models import TripitRequestToken, TripitAccessToken
from tripit.core.v1.oauth import request_access_token
from tripit.logging import logger


def handle_callback(access_key, callback_token, request_token_secret):
    """
    Handles TripIt callbacks and persists access tokens with access keys for
    future use.
    """
    request_token_secret = get_request_token_secret_from_key(access_key)
    if request_token_secret is None:
        logger.error("This access key hasn't authorized yet: %s", access_key)
        return False
    access_token_data = request_access_token(callback_token, request_token_secret)
    if access_token_data is None:
        logger.error("Failed to obtain an access token for callback token %s", callback_token)
        return False
    try:
        TripitAccessToken.insert(
            access_key=access_key,
            token=access_token_data["token"],
            token_secret=access_token_data["token_secret"],
        )
        return True
    except TransactWriteError:
        logger.error("Failed to write new token; see logs above")
        return False


def get_request_token_secret_from_key(access_key):
    """
    Retrieves request token secrets from access keys.
    """
    try:
        return TripitRequestToken.as_dict(access_key)["token_secret"]
    except TripitRequestToken.DoesNotExist:
        return None
