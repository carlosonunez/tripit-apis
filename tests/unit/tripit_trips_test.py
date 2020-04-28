"""
Tests for summarizing trip data from the TripIt API.

This API is meant to be used to get quick facts about trips in one's profile
to assist with other, downstream automations like setting Slack statuses
(the motivation for this API) or creating messages to send to other people.

It is meant to be read-only.
"""
import json
import pytest
import requests
from freezegun import freeze_time
from tripit.core.trips_v1 import (get_all_trips)

# pylint: disable=too-few-public-methods
class FakeResponse:
    """Used to stub calls to TripIt's API."""
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text
        self.json = json.loads(text)

def mock_responses(url, *args, **kwargs):
    """ There doesn't seem to be a good way of monkeypatching things
    conditionally, which is annoying. So we need to implement a router."""
    if url == "":
        return FakeResponse(200, {'timestamp': '123', 'num_bytes': 73})
    return None

@pytest.mark.unit
@freeze_time("Jan 1, 1970 00:02:03")
def test_fetching_trips_when_none_are_present(monkeypatch):
    """
    We shouldn't get anything back when no trips are present.
    """
    fake_token = {'token': 'foo', 'token_secret': 'bar'}
    list_trips_url = "https://api.tripit.com/v1/list/trip/format/json"
    monkeypatch.setattr(requests, "get", mock_responses(list_trips_url))
    monkeypatch.setattr("tripit.core.oauth_v1", "get_access_token", fake_token)
    assert get_all_trips() == []
