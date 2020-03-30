"""
Tests for TripIt OAuth v1.
"""
from datetime import datetime
import secrets
import pytest
import requests
from tripit.core.oauth_v1 import request_token


class FakeResponse:
    """ We need this to mock calls to TripIt's API so that we don't get junk back. """
    @staticmethod
    def status_code():
        """ status_code """
        return 200

    @staticmethod
    def text():
        """ response text """
        return "oauth_token=fake-token&oauth_token_secret=fake-token-secret"


class FakeDatetime:
    """ Since timestamps are used to generate OAuth signatures, we want to use fake
    times so that we can get consistent test results. """
    @classmethod
    def now(cls):
        """ mock now since we use it to generate a timestamp based on current time """
        return datetime(1970, 1, 1, 0, 2, 3)  # 123

    @classmethod
    def timestamp(cls):
        """ our fake timestamp """
        return 123


@pytest.mark.unit
def test_getting_oauth_request_tokens(monkeypatch):
    """
    Ensure that we can get request tokens and secrets from OAuth v1.
    """
    fake_token = 'fake-token'
    fake_token_secret = 'fake-secret'
    fake_nonce = 'fake-nonce'
    monkeypatch.setattr(secrets, "token_hex", lambda *args, **kwargs: fake_nonce)
    monkeypatch.setattr('datetime.datetime', lambda *args, **kwargs: FakeDatetime())
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: FakeResponse())
    assert request_token() == {"token": fake_token,
                               "token_secret": fake_token_secret}
