"""
Tests for TripIt OAuth v1.
"""
import pytest
from tripit.core.oauth_v1 import request_token


@pytest.mark.unit
def test_oauth_request_get_tokens():
    """
    Ensure that we can get request tokens and secrets from OAuth v1.
    """
    fake_token = 'fake-token'
    fake_token_secret = 'fake-secret'
    assert request_token() == {"token": fake_token,
                               "token_secret": fake_token_secret}
