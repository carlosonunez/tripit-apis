"""
This tests executing TripIt API requests.
"""
import pytest
from tripit.core.v1.api import get_from_tripit_v1


# pylint: disable=too-few-public-methods
class MockResponse:
    """ Fake response. """

    def __init__(self, status_code, url):
        self.status_code = status_code
        self.url = url


@pytest.mark.unit
def test_get_from_tripit(monkeypatch):
    """ Tests getting stuff from TripIt. """
    endpoint = "/ping"
    mock_response = MockResponse(200, "https://api.tripit.com/v1/ping")
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: mock_response)
    token = "fake-token"
    token_secret = "fake-token-secret"
    assert get_from_tripit_v1(endpoint, token, token_secret) == mock_response
