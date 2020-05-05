"""
Functions for handling OAuth auth flow.

Core functions can be found in tripit/core/v1.
"""
import urllib
from tripit.core.v1.oauth import request_request_token
from tripit.auth.models import TripitRequestToken
from tripit.logging import logger


def get_authn_url(api_gateway_endpoint, access_key):
    """
    Generates an authentication URL for an access key if no request or access
    tokens exist for it.
    """
    token_data = request_request_token()
    if token_data is None:
        logger.error("Unable to get token; see previous logs for why.")
        return None
    callback_url = urllib.parse.urlunparse(("https", api_gateway_endpoint, "callback", "", "", ""))
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


def associate_access_key_with_request_token(access_key, token, token_secret):
    """
    Associates access keys with request token/secret pairs so that
    we can retrieve an access token after manually authorizing this application
    on TripIt.
    """
    if not TripitRequestToken.exists():
        TripitRequestToken.create_table(wait=True)

    new_request_token_mapping = TripitRequestToken(
        access_key, token=token, token_secret=token_secret
    )
    import pdb

    pdb.set_trace()  # vim breakpoint
    new_request_token_mapping.save()
