"""
Fixture for mocking responses from TripIt based on route.
"""

import json
from pathlib import Path
import re
import pytest
from tests.fixtures.unit.fake_trip import FakeTrip

# pylint: disable=too-few-public-methods
class FakeResponse:
    """Used to stub calls to TripIt's API."""

    def __init__(self, url, status_code, text=None, json_object=None):
        self.url = url
        self.status_code = status_code
        if text:
            self.text = text
            self.json = lambda *args, **kwargs: json.loads(text)
        elif json_object:
            self.json = lambda *args, **kwargs: json_object
            self.text = json.dumps(json_object)


# We need to assume that we will get anonymous arguments here, since
# this is a function being monkeypatched-in.
# pylint: disable=unused-argument
@pytest.fixture()
def fake_response_from_route():
    """
    monkeypatch sucks at conditional mocking, so this function
    fills in this gap by returning the right response from mock TripIt
    based on the path requested.
    """

    def _run(*args, filter_notes=False, **kwargs):
        """
        more fucking pytest hacks.
        https://stackoverflow.com/a/44701916/314212
        """
        fake_trip_name = kwargs.get("fake_trip_name")
        fake_flights_to_load = kwargs.get("fake_flights_scenario")
        endpoint = kwargs.get("endpoint")
        fake_response = None

        if not fake_trip_name:
            return FakeResponse(
                url="https://api.tripit.com/v1/list/trip/include_objects/true/format/json",
                status_code=200,
                json_object={"timestamp": 123, "num_bytes": 78},
            )

        return FakeResponse(
                url="https://api.tripit.com/v1/list/trip/include_objects/true/format/json",
                status_code=200,
                json_object=FakeTrip(fake_trip_name).fake_trip_data
            )

    return _run
