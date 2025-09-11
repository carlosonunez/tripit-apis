"""
This test ensures that we can resolve trips even if they are missing primary locaitons.

This should only happen if we created a partial trip somehow without finishing the Trip Creation
wizard. It's pretty rare but will easily take out my TripIt API when resolving trips.
"""

import pytest
from freezegun import freeze_time
from tripit.trips import get_all_trips


@pytest.mark.unit
@freeze_time("Jan 1 1970 00:01:02")
def test_that_we_can_get_multiple_trips_missing_loc(monkeypatch, fake_response_from_route):
    """
    Ensure that our threads can actually yield multiple trips.
    """

    monkeypatch.setattr(
        "tripit.trips.get_from_tripit_v1",
        lambda *args, **kwargs: fake_response_from_route(
            fake_trip_name="Personal: Multiple Trip Without Location",
            fake_flights_scenario="personal_multi_trip_without_primary_locs",
            *args,
            **kwargs,
        ),
    )
    expected_trip = {
        "id": 123456789,
        "name": "Personal: Multiple Trip Without Location",
        "city": "Anywhere, Earth",
        "ends_on": 1692144000,
        "link": "https://www.tripit.com/trip/show/id/123456789",
        "starts_on": 1692144000,
        "ended": False,
        "flights": [],
    }
    assert get_all_trips(token="token", token_secret="token_secret") == [ expected_trip ]
