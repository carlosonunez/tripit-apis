"""
This is code that handles step 2 of the authentication process.

See the test for this file in tests/unit for more info.
"""
from pynamodb.exceptions import TransactWriteError
from tripit.auth.models import TripitRequestToken, TripitAccessToken
from tripit.core.v1.oauth import request_access_token
from tripit.logging import logger


def handle_callback(request_token):
    """
    Handles TripIt callbacks and persists access tokens with access keys for
    future use.
    """
    access_key = get_access_key_from_request_token(request_token)
    if access_key is None:
        logger.error("This token hasn't been mapped yet: %s", request_token)
        return False
    request_token_secret = get_token_secret_from_request_token(request_token)
    if request_token_secret is None:
        logger.error("BUG: No token secret mapped to request token from step 1: %s", access_key)
        return False
    access_token_data = request_access_token(request_token, request_token_secret)
    if access_token_data is None:
        logger.error("Failed to obtain an access token from request token %s", request_token)
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


def get_token_secret_from_request_token(token):
    """
    Retrieves request token secrets from request_tokens
    """
    try:
        return TripitRequestToken.as_dict(token)["token_secret"]
    except TripitRequestToken.DoesNotExist:
        return None


def get_access_key_from_request_token(token):
    """
    Retrieves access key from request_tokens
    """
    try:
        return TripitRequestToken.as_dict(token)["access_key"]
    except TripitRequestToken.DoesNotExist:
        return None
