"""
Tests for TripIt OAuth v1.
"""
import datetime
import os
import secrets
import pytest
import requests
from freezegun import freeze_time
from tripit.core.oauth_v1 import (request_request_token,
                                  request_access_token,
                                  generate_signature)


# pylint: disable=too-few-public-methods
class FakeResponse:
    """ We need this to mock calls to TripIt's API so that we don't get junk back. """
    """ We aren't using anything else from Requests yet, so until we do, tell
        pylint to relax. """

    def __init__(self, text):
        self.status_code = 200
        self.text = text


@pytest.mark.unit
@freeze_time("Jan 1, 1970 00:02:03")
def test_generating_request_token_oauth_signature(monkeypatch):
    """ Ensures that we generate the correct signature as per
    the awesome test server at http://lti.tools/oauth/ """
    fake_nonce = 'fake-nonce'
    monkeypatch.setattr(secrets, "token_hex", lambda *args, **kwargs: fake_nonce)
    signature = generate_signature('GET',
                                   'https://api.tripit.com/oauth/request_token',
                                   os.getenv('TRIPIT_APP_CLIENT_ID'),
                                   os.getenv('TRIPIT_APP_CLIENT_SECRET'),
                                   fake_nonce,
                                   datetime.datetime.now().timestamp())
    expected_sig = str(b'h6Azudvr61sWzIoqJbU8TVS1Lhw=')
    assert signature == expected_sig


@pytest.mark.unit
@freeze_time("Jan 1, 1970 00:02:03")
def test_generating_access_token_oauth_signature(monkeypatch):
    """ Ensures that we generate the correct signature as per
    the awesome test server at http://lti.tools/oauth/ """
    fake_nonce = 'fake-nonce'
    fake_token = 'fake-token'
    fake_token_secret = 'fake-token-secret'
    monkeypatch.setattr(secrets, "token_hex", lambda *args, **kwargs: fake_nonce)
    signature = generate_signature('GET',
                                   'https://api.tripit.com/oauth/request_token',
                                   os.getenv('TRIPIT_APP_CLIENT_ID'),
                                   os.getenv('TRIPIT_APP_CLIENT_SECRET'),
                                   fake_nonce,
                                   datetime.datetime.now().timestamp(),
                                   fake_token,
                                   fake_token_secret)
    expected_sig = str(b't3KGdhG2f3H9Vc9Xb1q9i3JvdkA=')
    assert signature == expected_sig


@pytest.mark.unit
@freeze_time("Jan 1, 1970 00:02:03")
def test_getting_oauth_request_tokens(monkeypatch):
    """
    Ensure that we can get request tokens and secrets from OAuth v1.
    """
    fake_token = 'fake-token'
    fake_token_secret = 'fake-secret'
    fake_nonce = 'fake-nonce'
    fake_response = "oauth_token=fake-token&oauth_token_secret=fake-secret"
    monkeypatch.setattr(secrets, "token_hex", lambda *args, **kwargs: fake_nonce)
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: FakeResponse(fake_response))
    assert request_request_token() == {"token": fake_token,
                                       "token_secret": fake_token_secret}


@pytest.mark.unit
@freeze_time("Jan 1, 1970 00:02:03")
def test_getting_access_tokens_from_oauth(monkeypatch):
    """
    Ensure that we can get authenticated tokens after getting a request
    token and token secret from TripIt.
    """
    fake_token = 'fake-token'
    fake_token_secret = 'fake-secret'
    fake_nonce = 'fake-nonce'
    fake_request_token = 'fake-request-token'
    fake_request_token_secret = 'fake-request-token-secret'
    fake_response = f"oauth_token={fake_token}&oauth_token_secret={fake_token_secret}"
    monkeypatch.setattr(secrets, "token_hex", lambda *args, **kwargs: fake_nonce)
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: FakeResponse(fake_response))
    token_data = request_access_token(fake_request_token, fake_request_token_secret)
    assert token_data == {"token": fake_token, "token_secret": fake_token_secret}
