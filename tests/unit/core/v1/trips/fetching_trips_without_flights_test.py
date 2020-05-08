"""
This test ensures that we can resolve trips that do not have flights in them.
Trips like these are created for things like future trips I'm planning (that have
dates, but no flights booked yet) or placeholders (like an assignment I did while
COVID-19 was happening; it had no flights, but it was remote and I wanted my
status on Slack to reflect that.)
"""
import pytest
from freezegun import freeze_time
from tripit.trips import get_all_trips


@pytest.mark.unit
@freeze_time("Jan 1 1970 00:01:02")
def test_fetching_trips_without_flights(monkeypatch, fake_response_from_route):
    """
    We should get back a valid trip for personal trips.
    """
    monkeypatch.setattr(
        "tripit.trips.get_from_tripit_v1",
        lambda *args, **kwargs: fake_response_from_route(
            fake_trip_name="Personal: Some Trip",
            fake_flights_scenario="personal_trip_without_flights",
            *args,
            **kwargs,
        ),
    )
    expected_trips = [
        {
            "id": 123456789,
            "name": "Personal: Some Trip",
            "city": "Dayton, OH",
            "ends_on": 1576713600,
            "link": "https://www.tripit.com/trip/show/id/123456789",
            "starts_on": 1576368000,
            "ended": False,
            "flights": [],
        }
    ]
    assert get_all_trips(token="token", token_secret="token_secret") == expected_trips
