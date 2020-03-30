"""
Functions for authenticating calls to TripIt via OAuth v1.
"""
from datetime import datetime
import html
from hashlib import sha1
import os
import hmac
import logging
import secrets
import requests
from tripit.environment import EnvironmentCheck


def request_token():
    """
    Get a new request token from the TripIt API.
    """
    env_check = EnvironmentCheck(['TRIPIT_APP_CLIENT_SECRET',
                                  'TRIPIT_APP_CLIENT_ID'])
    if not env_check.ready:
        raise RuntimeError(f"Please define these environment variables: {env_check.missing_vars}")
    client_id = os.environ.get("TRIPIT_APP_CLIENT_ID")
    client_secret = os.environ.get("TRIPIT_APP_CLIENT_SECRET")
    request_uri = "https://api.tripit.com/oauth/request_token"
    nonce = secrets.token_hex()
    timestamp = datetime.now().timestamp()
    common_arguments = {"uri": request_uri,
                        "consumer_key": client_id,
                        "nonce": nonce,
                        "timestamp": timestamp}
    oauth_sig = generate_signature(method="GET",
                                   consumer_secret=client_secret,
                                   **common_arguments)
    auth_header = generate_sha1_auth_header(signature=oauth_sig,
                                            **common_arguments)
    response = requests.get(request_uri, headers={'Authorization': auth_header})
    if response.status_code != 200:
        logging.error(f"Failed to get an OAuth authentication header: {response.text})")
        return None
    token_data = {}
    for token_part in response.text.split("&"):
        key, value = token_part.split('=')
        token_data[key.replace('oauth_', '')] = value
    return token_data


def generate_sha1_auth_header(uri, signature, consumer_key, nonce, timestamp, token=None):
    """
    Generates an OAuth v1 authencation header for HTTP requests to endpoints
    requiring OAuth v1 authentication.
    """
    headers = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": nonce,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": timestamp,
        "oauth_version": "1.0"
    }
    if token is not None:
        headers['oauth_token'] = token
    sorted_headers = {k: v for k, v in sorted(headers.items())}
    escaped_sig = html.escape(signature)
    auth_header_parts = [f'OAuth realm="{uri}"',
                         ",".join([f"{k}={v}" for k, v in sorted_headers]),
                         f'oauth_signature="{escaped_sig}"']
    return ','.join(auth_header_parts)


def generate_signature(method, uri, consumer_key, consumer_secret,
                       nonce, timestamp, token=None, token_secret=None):
    """
    Generates an OAuth v1 signature. These are used to form authentication headers.
    """
    params = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": nonce,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": timestamp,
        "oauth_token": (token if token is not None else ''),
        "oauth_version": "1.0"
    }
    encrypt_key = "&".join([consumer_secret,
                            (token_secret if token_secret is not None else '')])
    sorted_params = {key: params[key] for key in sorted(params.keys())}
    serialized_params = "&".join([f"{key}={value}" for key, value in sorted_params])
    base_string_for_signature = "&".join([method,
                                          html.escape(uri),
                                          html.escape(serialized_params)])
    signature = hmac.new(encrypt_key, base_string_for_signature, sha1)
    return signature.digest().encode("base64").rstrip("\n")
