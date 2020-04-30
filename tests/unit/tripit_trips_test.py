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
from tripit.core.v1.trips import (get_all_trips)


# pylint: disable=too-few-public-methods
class FakeResponse:
    """Used to stub calls to TripIt's API."""
    def __init__(self, url, status_code, text=None, json_object=None):
        self.url = url
        self.status_code = status_code
        if text:
            self.text = text
            self.json = json.loads(text)
        elif json_object:
            self.json = json_object
            self.text = json.dumps(json_object)


@pytest.mark.unit
def test_fetching_trips_when_none_are_present(monkeypatch):
    """
    We shouldn't get anything back when no trips are present.
    """
    mock_response_body = {'timestamp': 123, 'num_bytes': 78}
    mock_response = FakeResponse(url="https://api.tripit.com/v1/list/trip/format/json",
                                 status_code=200,
                                 json_object=mock_response_body)
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_response)
    assert get_all_trips(token='token', token_secret='token_secret') == []
