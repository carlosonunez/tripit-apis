"""
Fixture for creating fake TripIt Trip objects.
"""

import json
from pathlib import Path
import pytest

# pylint: disable=too-few-public-methods
class FakeTrip:
    """
    Convenience class for creating mocked trips.
    """

    def __init__(self, trip_name):
        self.fake_trip_data = json.loads(Path("./tests/mocks/trips.json").read_text())
        self.trip_data = self.filter_trips(trip_name)

    def filter_trips(self, trip_name):
        """ Reads the test trips fixture and filters the trip list based
        on the name provided. """
        trips = self.fake_trip_data
        trips["Trip"] = [trip for trip in trips["Trip"] if trip["display_name"] == trip_name]
        return trips


@pytest.fixture()
def fake_trip():
    """
    Creates a fake trip from a given trip name.
    """

    def _create(trip_name):
        """
        more fucking pytest hacks.
        https://stackoverflow.com/a/44701916/314212
        """
        return FakeTrip(trip_name)

    return _create
