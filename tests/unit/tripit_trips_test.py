"""
Tests for summarizing trip data from the TripIt API.

This API is meant to be used to get quick facts about trips in one's profile
to assist with other, downstream automations like setting Slack statuses
(the motivation for this API) or creating messages to send to other people.

It is meant to be read-only.
"""
import json
from pathlib import Path
import pytest
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


# pylint: disable=too-few-public-methods
class FakeTrip:
    """ Convenience method for picking and contorting fake TripIt trips. """
    fake_trip_data = json.loads(Path('./tests/fixtures/trips.json').read_text())

    def __init__(self, trip_name):
        self.trip_data = self.filter_trips(trip_name)

    @classmethod
    def filter_trips(cls, trip_name):
        """ Reads the test trips fixture and filters the trip list based
        on the name provided. """
        trips = FakeTrip.fake_trip_data
        trips['Trip'] = [trip for trip in trips['Trip'] if trip['display_name'] == trip_name]
        return trips


@pytest.mark.unit
def test_fetching_trips_when_none_are_present(monkeypatch):
    """
    We shouldn't get anything back when no trips are present.

    NOTE:
    You might be wondering "`get_from_tripit_v1` belongs in `tripit.core.v1.api`,
    but we're patching it from `tripit.core.v1.trips`. What gives?"

    This is due to a limitation of how modules work in Python.

    See here: https://alexmarandon.com/articles/python_mock_gotchas/
    """
    monkeypatch.setattr(
        'tripit.core.v1.trips.get_from_tripit_v1',
        lambda *args, **kwargs: FakeResponse(url="https://api.tripit.com/v1/list/trip/format/json",
                                             status_code=200,
                                             json_object={
                                                 'timestamp': 123,
                                                 'num_bytes': 78
                                             }))
    assert get_all_trips(token='token', token_secret='token_secret') == []


@pytest.mark.unit
def test_fetching_trips_without_flights(monkeypatch):
    """
    We should get back a valid trip for personal trips.
    """
    monkeypatch.setattr(
        'tripit.core.v1.trips.get_from_tripit_v1',
        lambda *args, **kwargs: FakeResponse(url="https://api.tripit.com/v1/list/trip/format/json",
                                             status_code=200,
                                             json_object=FakeTrip("Personal: Some Trip").trip_data))
    expected_trips = [{
        'id': 123456789,
        'name': 'Personal: Some Trip',
        'city': 'Dayton, OH',
        'ends_on': 1576713600,
        'link': "https://www.tripit.com/trip/show/id/123456789",
        'starts_on': 1576368000,
        'ended': False,
        'flights': []
    }]
    assert get_all_trips(token='token', token_secret='token_secret') == expected_trips


@pytest.mark.unit
def test_that_we_can_get_multiple_trips(monkeypatch):
    """
    Ensure that our threads can actually yield multiple trips.
    """

    # Duplicate the object, since I only care about getting multiple trips back.
    fake_trip = FakeTrip("Personal: Some Trip")
    fake_trip.trip_data['Trip'] = fake_trip.trip_data['Trip'] + fake_trip.trip_data['Trip']

    monkeypatch.setattr(
        'tripit.core.v1.trips.get_from_tripit_v1',
        lambda *args, **kwargs: FakeResponse(url="https://api.tripit.com/v1/list/trip/format/json",
                                             status_code=200,
                                             json_object=fake_trip.trip_data))
    expected_trip = {
        'id': 123456789,
        'name': 'Personal: Some Trip',
        'city': 'Dayton, OH',
        'ends_on': 1576713600,
        'link': "https://www.tripit.com/trip/show/id/123456789",
        'starts_on': 1576368000,
        'ended': False,
        'flights': []
    }
    expected_trips = [expected_trip, expected_trip]
    assert get_all_trips(token='token', token_secret='token_secret') == expected_trips
