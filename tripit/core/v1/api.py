"""
All of the API things we do with TripIt live here.
"""

import os
import re
import requests
from tripit.logging import logger
from tripit.core.v1.oauth import generate_authenticated_headers_for_request


def get_from_tripit_v1(endpoint, token, token_secret, params=None):
    """GET against authenticated TripIt endpoints."""
    params_string = _join_params_by_slash(params)
    endpoint = _strip_leading_slash_from_endpoint(endpoint)
    clean_endpoint = f"{endpoint}/{params_string}format/json"
    uri = f"https://api.tripit.com/v1/{clean_endpoint}"
    headers = generate_authenticated_headers_for_request(
        "GET",
        uri,
        os.getenv("TRIPIT_APP_CLIENT_ID"),
        os.getenv("TRIPIT_APP_CLIENT_SECRET"),
        token,
        token_secret,
    )
    logger.debug("Sending GET to TripIt at: %s", uri)
    return requests.get(uri, headers={"Authorization": headers})


def _join_params_by_slash(params):
    """
    TripIt wants all of their parameters delimited by slashes in the URL.
    No idea why.
    """
    if params is not None:
        return "/".join([f"{key}/{value}" for key, value in sorted(params.items())]) + "/"
    return ""


def _strip_leading_slash_from_endpoint(endpoint):
    """
    Removes the leading slash so that we can generate a clean URI.
    """
    if re.match("^/", endpoint):
        return endpoint[1:]
    return endpoint
