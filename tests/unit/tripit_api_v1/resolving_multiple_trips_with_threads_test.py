"""
This test ensures that our threads for resolving flights works. Since we're using
Since we're using concurrent.futures for our thread pool, they should be thread safe.
"""

import pytest
from freezegun import freeze_time
from tripit.core.v1.trips import get_all_trips


@pytest.mark.unit
@freeze_time("Jan 1 1970 00:01:02")
def test_that_we_can_get_multiple_trips(monkeypatch, fake_response_from_route, fake_trip):
    """
    Ensure that our threads can actually yield multiple trips.
    """

    # Duplicate the object, since I only care about getting multiple trips back.
    trip = fake_trip("Personal: Some Trip")
    trip.trip_data["Trip"] = trip.trip_data["Trip"] + trip.trip_data["Trip"]

    monkeypatch.setattr(
        "tripit.core.v1.trips.get_from_tripit_v1",
        lambda *args, **kwargs: fake_response_from_route(
            fake_trip_name="Personal: Some Trip",
            fake_flights_scenario="personal_trip_without_flights",
            fake_trip_data=trip.trip_data,
            *args,
            **kwargs,
        ),
    )
    expected_trip = {
        "id": 123456789,
        "name": "Personal: Some Trip",
        "city": "Dayton, OH",
        "ends_on": 1576713600,
        "link": "https://www.tripit.com/trip/show/id/123456789",
        "starts_on": 1576368000,
        "ended": False,
        "flights": [],
    }
    expected_trips = [expected_trip, expected_trip]
    assert get_all_trips(token="token", token_secret="token_secret") == expected_trips
