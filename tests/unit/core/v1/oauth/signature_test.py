"""
Tests for generating TripIt OAuth v1 signatures.
"""
import datetime
import os
import secrets
import pytest
from freezegun import freeze_time
from tripit.core.v1.oauth import generate_signature


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
    fake_nonce = "fake-nonce"
    monkeypatch.setattr(secrets, "token_hex", lambda *args, **kwargs: fake_nonce)
    signature = generate_signature(
        "GET",
        "https://api.tripit.com/oauth/request_token",
        os.getenv("TRIPIT_APP_CLIENT_ID"),
        os.getenv("TRIPIT_APP_CLIENT_SECRET"),
        fake_nonce,
        datetime.datetime.now().timestamp(),
    )
    expected_sig = b"h6Azudvr61sWzIoqJbU8TVS1Lhw="
    assert signature == expected_sig


@pytest.mark.unit
@freeze_time("Jan 1, 1970 00:02:03")
def test_generating_access_token_oauth_signature(monkeypatch):
    """ Ensures that we generate the correct signature as per
    the awesome test server at http://lti.tools/oauth/ """
    fake_nonce = "fake-nonce"
    fake_token = "fake-token"
    fake_token_secret = "fake-token-secret"
    monkeypatch.setattr(secrets, "token_hex", lambda *args, **kwargs: fake_nonce)
    signature = generate_signature(
        "GET",
        "https://api.tripit.com/oauth/access_token",
        os.getenv("TRIPIT_APP_CLIENT_ID"),
        os.getenv("TRIPIT_APP_CLIENT_SECRET"),
        fake_nonce,
        datetime.datetime.now().timestamp(),
        fake_token,
        fake_token_secret,
    )
    expected_sig = b"Gfs0FXIZZm07QMYjPr61yKFgGLk="
    assert signature == expected_sig
