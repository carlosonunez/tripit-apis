"""
Tests for TripIt OAuth v1.
"""
import os
import secrets
import pytest
from freezegun import freeze_time
from tripit.core.v1.oauth import generate_authenticated_headers_for_request


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
def test_generating_headers_for_authenticated_calls(monkeypatch):
    """ Tests for generating headers for API calls. """
    method = "GET"
    uri = "https://api.tripit.com/v1/ping"
    fake_nonce = "fake-nonce"
    fake_request_token = "fake-token"
    fake_request_token_secret = "fake-token-secret"
    fake_token_data = {"token": fake_request_token, "token_secret": fake_request_token_secret}
    monkeypatch.setattr(secrets, "token_hex", lambda *args, **kwargs: fake_nonce)
    monkeypatch.setattr("tripit.core.v1.oauth.request_access_token", fake_token_data)
    headers = generate_authenticated_headers_for_request(
        method,
        uri,
        os.getenv("TRIPIT_APP_CLIENT_ID"),
        os.getenv("TRIPIT_APP_CLIENT_SECRET"),
        fake_request_token,
        fake_request_token_secret,
    )
    expected_header = ",".join(
        [
            'OAuth realm="https://api.tripit.com/v1/ping"',
            'oauth_consumer_key="fake-client-id"',
            'oauth_nonce="fake-nonce"',
            'oauth_signature_method="HMAC-SHA1"',
            'oauth_timestamp="123"',
            'oauth_token="fake-token"',
            'oauth_version="1.0"',
            'oauth_signature="3lFQPx5hhs14UQ1r7NitP%2B6ZbYk%3D"',
        ]
    )
    assert headers == expected_header
