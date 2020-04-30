"""
All of the API things we do with TripIt live here.
"""

import os
import requests
from tripit.core.v1.oauth import (generate_authenticated_headers_for_request)


def get_from_tripit_v1(endpoint, token, token_secret, params=None):
    """ GET against authenticated TripIt endpoints. """
    params_string = ""
    if params is not None:
        params_string = "/".join([f"{key}/{value}" for key, value in sorted(params.items())])
    clean_endpoint = f"{endpoint[:-1]}/{params_string}/format/json".replace("//", "/")
    uri = f"https://api.tripit.com/v1/{clean_endpoint}"
    headers = generate_authenticated_headers_for_request('GET', uri,
                                                         os.getenv('TRIPIT_APP_CLIENT_ID'),
                                                         os.getenv('TRIPIT_APP_CLIENT_SECRET'),
                                                         token, token_secret)
    return requests.get(uri, headers={'Authorization': headers})
