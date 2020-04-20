"""
Tests for TripIt OAuth v1.
"""
import secrets
import pytest
import requests
from freezegun import freeze_time
from tripit.core.oauth_v1 import request_token


# pylint: disable=too-few-public-methods
class FakeResponse:
    """ We need this to mock calls to TripIt's API so that we don't get junk back. """
    """ We aren't using anything else from Requests yet, so until we do, tell
        pylint to relax. """

    def __init__(self):
        self.status_code = 200
        self.text = "oauth_token=fake-token&oauth_token_secret=fake-secret"


@pytest.mark.unit
@freeze_time("Jan 1, 1970 00:02:03")
def test_getting_oauth_request_tokens(monkeypatch):
    """
    Ensure that we can get request tokens and secrets from OAuth v1.
    """
    fake_token = 'fake-token'
    fake_token_secret = 'fake-secret'
    fake_nonce = 'fake-nonce'
    monkeypatch.setattr(secrets, "token_hex", lambda *args, **kwargs: fake_nonce)
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: FakeResponse())
    assert request_token() == {"token": fake_token,
                               "token_secret": fake_token_secret}
