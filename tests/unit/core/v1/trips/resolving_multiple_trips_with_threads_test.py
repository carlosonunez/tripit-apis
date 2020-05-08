"""
This test ensures that our threads for resolving flights works. Since we're using
Since we're using concurrent.futures for our thread pool, they should be thread safe.
"""

import pytest
from freezegun import freeze_time
from tripit.trips import get_all_trips


@pytest.mark.unit
@freeze_time("Jan 1 1970 00:01:02")
def test_that_we_can_get_multiple_trips(monkeypatch, fake_response_from_route):
    """
    Ensure that our threads can actually yield multiple trips.
    """

    monkeypatch.setattr(
        "tripit.trips.get_from_tripit_v1",
        lambda *args, **kwargs: fake_response_from_route(
            fake_trip_name="Personal: Multiple Trip",
            fake_flights_scenario="personal_multi_trip_without_flights",
            *args,
            **kwargs,
        ),
    )
    expected_trip = {
        "id": 123456789,
        "name": "Personal: Multiple Trip",
        "city": "Dayton, OH",
        "ends_on": 1576713600,
        "link": "https://www.tripit.com/trip/show/id/123456789",
        "starts_on": 1576368000,
        "ended": False,
        "flights": [],
    }
    expected_trips = [expected_trip, expected_trip]
    assert get_all_trips(token="token", token_secret="token_secret") == expected_trips
