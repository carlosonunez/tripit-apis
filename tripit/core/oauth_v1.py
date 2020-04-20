"""
Functions for authenticating calls to TripIt via OAuth v1.
"""
from datetime import datetime
import html
from hashlib import sha1
import base64
import os
import hmac
import logging
import secrets
import requests
from tripit.environment import EnvironmentCheck
from tripit.helpers import sort_dict


def request_token(token=None, token_secret=None):
    """
    Get a new request token from the TripIt API.
    """
    env_check = EnvironmentCheck(['TRIPIT_APP_CLIENT_SECRET',
                                  'TRIPIT_APP_CLIENT_ID'])
    if not env_check.ready:
        raise RuntimeError(f"Please define these environment variables: {env_check.missing_vars}")
    client_id = os.environ.get("TRIPIT_APP_CLIENT_ID")
    client_secret = os.environ.get("TRIPIT_APP_CLIENT_SECRET")
    """ If we are trying to request tokens and already have a token
        secret, then that means we already went through the first step
        of the OAuth process and are now trying to get access tokens. """
    if token_secret is not None:
        request_uri = "https://api.tripit.com/oauth/access_token"
    else:
        request_uri = "https://api.tripit.com/oauth/request_token"

    common_arguments = {"uri": request_uri,
                        "consumer_key": client_id,
                        "nonce": secrets.token_hex(),
                        "timestamp": datetime.now().timestamp()}
    access_token_arguments = {}
    if token_secret is not None:
        access_token_arguments["token"] = token
        access_token_arguments["token_secret"] = token_secret

    oauth_sig = generate_signature(method="GET",
                                   consumer_secret=client_secret,
                                   **common_arguments,
                                   **access_token_arguments)
    auth_header = generate_sha1_auth_header(signature=oauth_sig,
                                            **common_arguments)
    response = requests.get(request_uri, headers={'Authorization': auth_header})
    if response.status_code != 200:
        logging.error("Failed to get an OAuth authentication header: %s)", response.text)
        return None
    token_data = {}
    for token_part in response.text.split("&"):
        key, value = token_part.split('=')
        token_data[key.replace('oauth_', '')] = value
    return token_data


def request_request_token():
    """ Request a request token.
    This is here temporarily while I refactor request_token(). """
    return request_token()


def request_access_token(req_token, request_token_secret):
    """ Fetch an access token after fetching a request token. """
    return request_token(req_token, request_token_secret)

# pylint: disable=too-many-arguments


def generate_sha1_auth_header(uri, signature, consumer_key, nonce, timestamp, token=None):
    """
    Generates an OAuth v1 authencation header for HTTP requests to endpoints
    requiring OAuth v1 authentication.
    """
    headers = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": nonce,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": int(timestamp),
        "oauth_version": "1.0"
    }
    if token is not None:
        headers['oauth_token'] = token
    escaped_sig = html.escape(signature)
    auth_header_parts = [f'OAuth realm="{uri}"',
                         ",".join([f"{k}={v}" for k, v in sort_dict(headers).items()]),
                         f'oauth_signature="{escaped_sig}"']
    print(f"Header parts: {auth_header_parts}")
    return ','.join(auth_header_parts)


# pylint: disable=too-many-arguments
def generate_signature(method, uri, consumer_key, consumer_secret,
                       nonce, timestamp, token=None, token_secret=None):
    """
    Generates an OAuth v1 signature. These are used to form authentication headers.

    Unfortunately, because we really require these many arguments while working
    with OAuth v1, we need to tell pylint to disable the, usually correct,
    "too-many-arguments" error. Otherwise, we'll need to resort to using
    **kwargs, which is too unsafe for my liking.
    """
    params = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": nonce,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": int(timestamp),
        "oauth_version": "1.0"
    }
    if token:
        params["oauth_token"] = token

    encrypt_key = "&".join([consumer_secret,
                            (token_secret if token_secret is not None else '')])
    serialized_param_parts = [f"{key}={params[key]}" for key, value in sort_dict(params).items()]
    base_string_for_signature = "&".join([method,
                                          html.escape(uri),
                                          html.escape("&".join(serialized_param_parts))])
    signature = hmac.new(bytes(encrypt_key, 'utf8'),
                         bytes(base_string_for_signature, 'utf8'),
                         sha1)
    return str(base64.b64encode(signature.digest()))
