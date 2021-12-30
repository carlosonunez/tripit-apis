"""
This API can also show me when trips have ended. These tests account for that.
"""
import pytest
from freezegun import freeze_time
from tripit.trips import get_all_trips, normalize_flight_time_to_tz


@pytest.mark.unit
@freeze_time("2019-11-28 08:00:00")
def test_fetching_trips_with_empty_trips(monkeypatch, fake_response_from_route):
    """
    TripIt will, sometimes, create empty trips with no start/end times or location data.
    These should be filtered out from the list of trips returned.
    """
    monkeypatch.setattr(
        "tripit.trips.get_from_tripit_v1",
        lambda *args, **kwargs: fake_response_from_route(
            fake_trip_name="Your trip",
            fake_flights_scenario="empty_trip",
            *args,
            **kwargs,
        ),
    )
    expected_trips = []
    assert get_all_trips(token="token", token_secret="token_secret") == expected_trips
