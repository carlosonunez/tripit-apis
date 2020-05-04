"""
These tests cover being able to get the trip that we are currently in.
"""
import pytest
from freezegun import freeze_time
from tripit.core.v1.trips import get_current_trip


@pytest.mark.unit
@freeze_time("2019-11-30 09:00")  # set to time before this trip is to commence.
def test_getting_current_trip_when_no_trips_active(monkeypatch, fake_response_from_route):
    """
    We shouldn't get any current trips if we aren't on a trip right now.
    """
    monkeypatch.setenv("TRIPIT_INGRESS_TIME_MINUTES", "90")
    monkeypatch.setattr(
        "tripit.core.v1.trips.get_from_tripit_v1",
        lambda *args, **kwargs: fake_response_from_route(
            fake_trip_name="Work: Test Client - Week 2",
            fake_flights_scenario="trip_with_flights",
            *args,
            **kwargs,
        ),
    )
    expected_trip = {}
    assert get_current_trip(token="token", token_secret="token_secret") == expected_trip
