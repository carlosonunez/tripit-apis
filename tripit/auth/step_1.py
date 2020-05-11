"""
Functions for handling OAuth auth flow.

Core functions can be found in tripit/core/v1.
"""
import urllib
from pynamodb.exceptions import TableDoesNotExist, GetError
from tripit.core.v1.oauth import request_request_token
from tripit.auth.models import TripitRequestToken, TripitAccessToken
from tripit.logging import logger


def get_authn_url(api_gateway_endpoint, host, access_key, reauthorize=False):
    """
    Generates an authentication URL for an access key if no request or access
    tokens exist for it.
    """
    if access_key_has_access_token(access_key) and not reauthorize:
        logger.debug("Access key already has token: %s", access_key)
        return None
    if reauthorize:
        delete_existing_request_tokens(access_key)

    token_data = request_request_token()
    if token_data is None:
        logger.error("Unable to get token; see previous logs for why.")
        return None

    callback_url = urllib.parse.urlunparse(
        ("https", host, f"{api_gateway_endpoint}/callback", "", "", "")
    )
    auth_url = urllib.parse.urlunparse(
        (
            "https",
            "www.tripit.com",
            "/oauth/authorize",
            "",
            f"oauth_token={token_data['token']}&oauth_callback={callback_url}",
            "",
        )
    )
    associate_access_key_with_request_token(
        access_key, token_data["token"], token_data["token_secret"]
    )
    return auth_url


def access_key_has_access_token(access_key):
    """
    Checks if an access key has an access token associated with it.
    """
    try:
        TripitAccessToken.get(access_key)
        logger.info("Access key has token: %s", access_key)
        return True
    except GetError:
        return False
    except TableDoesNotExist:
        return False
    except TripitAccessToken.DoesNotExist:
        return False


def associate_access_key_with_request_token(access_key, token, token_secret):
    """
    Associates access keys with request token/secret pairs so that
    we can retrieve an access token after manually authorizing this application
    on TripIt.
    """
    logger.debug("Inserting a new access token for key %s", access_key)
    TripitRequestToken.insert(access_key=access_key, token=token, token_secret=token_secret)


def delete_existing_request_tokens(access_key):
    """
    Delete request tokens associated with an access key, if any found.
    """
    logger.debug("Deleting existing access tokens for key %s", access_key)
    try:
        TripitRequestToken.delete_tokens_by_access_key(access_key)
    except (GetError, TripitRequestToken.DoesNotExist):
        logger.warning("No request tokens found for key: %s", access_key)
