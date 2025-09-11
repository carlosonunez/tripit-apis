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
        trips = json.loads(Path("./tests/mocks/trips.json").read_text())
        filtered_trip = [trip for trip in trips.get("Trip", []) if trip["display_name"] == trip_name]
        if len(filtered_trip) == 0:
            trips["Trip"] = []
            trips["AirObject"] = []
            trips["LodgingObject"] = []
        else:
            filtered_trip = filtered_trip[0]
            filtered_trip_id = filtered_trip["id"]
            trips["Trip"] = [trip for trip in trips.get("Trip", []) if trip["display_name"] == trip_name]
            trips["AirObject"] = [o for o in trips.get("AirObject", []) if o["trip_id"] == filtered_trip_id]
            trips["LodgingObject"] = [o for o in trips.get("LodgingObject", [])
                                      if o["trip_id"] == filtered_trip_id]
        self.fake_trip_data = trips


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
