"""
We need to do three things in order for our API Gateway functions to work:

1. We need to expose an endpoint that gives us a URL to manually authenticate
   through,

2. We need to expose a callback endpoint to give to TripIt when we successfully authenticate, and

3. We need to save the access token and token secret provided in a database and map
   that to our API key from AWS or GCP.

These tests cover these scenarios.
"""

import urllib
import pytest
from tripit.auth.step_1 import get_authn_url


@pytest.mark.unit
def test_generating_auth_url_without_tokens(monkeypatch, query_request_token_table):
    """
    This is step 1 of the authentication process. If we don't have a token stored
    in our database, then we'll need to click on a URL to retrieve one.
    """
    request_tokens = lambda: {"token": "fake-request-token", "token_secret": "fake-secret"}
    monkeypatch.setattr("tripit.core.v1.oauth.fetch_token", request_tokens)
    expected_callback_url = urllib.parse.urlunparse(
        ("https", "foo.com", "/develop/callback", "", "", "")
    )
    expected_url = urllib.parse.urlunparse(
        (
            "https",
            "www.tripit.com",
            "/oauth/authorize",
            "",
            "".join(["oauth_token=fake-request-token&oauth_callback=", expected_callback_url]),
            "",
        )
    )
    url = get_authn_url(access_key="fake-key", host="foo.com", api_gateway_endpoint="/develop")
    assert url == expected_url
    request_token_mapping = query_request_token_table("fake-key")
    assert request_token_mapping == {
        "access_key": "fake-key",
        "token": "fake-request-token",
        "token_secret": "fake-secret",
    }


@pytest.mark.unit
def test_generating_auth_url_with_tokens(set_access_token_table, drop_access_token_table):
    """
    During step 1, if our access key already has an access token associated with it,
    then it should not continue with the authorization process.
    """
    set_access_token_table("fake-key", "fake-token", "fake-token-secret")
    assert get_authn_url(access_key="fake-key", host="foo", api_gateway_endpoint="foo") is None
    drop_access_token_table()


@pytest.mark.unit
def test_asking_for_reauthorization(monkeypatch, query_request_token_table, set_access_token_table):
    """
    If we already have tokens during step 1 of the authentication process, but we ask
    to reauthorize, we should delete what's in the tokens table and begin reauthenticating.
    """
    request_tokens = lambda: {"token": "fake-request-token", "token_secret": "fake-secret"}
    set_access_token_table("fake-key", "fake-access-token", "fake-secret")
    monkeypatch.setattr("tripit.core.v1.oauth.fetch_token", request_tokens)
    expected_callback_url = urllib.parse.urlunparse(
        ("https", "foo.com", "/develop/callback", "", "", "")
    )
    expected_url = urllib.parse.urlunparse(
        (
            "https",
            "www.tripit.com",
            "/oauth/authorize",
            "",
            "".join(["oauth_token=fake-request-token&oauth_callback=", expected_callback_url]),
            "",
        )
    )
    url = get_authn_url(
        access_key="fake-key", host="foo.com", api_gateway_endpoint="/develop", reauthorize=True,
    )
    assert url == expected_url
    request_token_mapping = query_request_token_table("fake-key")
    assert request_token_mapping == {
        "access_key": "fake-key",
        "token": "fake-request-token",
        "token_secret": "fake-secret",
    }
