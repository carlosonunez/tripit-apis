"""
These tests cover being able to get the trip that we are currently in.
"""
import pytest
from freezegun import freeze_time
from tripit.core.v1.trips import get_current_trip, normalize_flight_time_to_tz, logger


@pytest.mark.unit
@freeze_time("2019-11-30 09:00")  # set to time before this trip is to commence.
def test_getting_current_trip_when_no_trips_active(monkeypatch, fake_response_from_route):
    """
    We shouldn't get any current trips if we aren't on a trip right now.
    """
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


@pytest.mark.unit
@freeze_time("2019-12-15 23:30:00")  # set to time during trip and flight
def test_getting_active_trip_without_flights(monkeypatch, fake_response_from_route):
    """
    If we're currently on a trip but are not flying yet, then we should
    get a trip back but with no flights in it.
    """
    monkeypatch.setattr(
        "tripit.core.v1.trips.get_from_tripit_v1",
        lambda *args, **kwargs: fake_response_from_route(
            fake_trip_name="Personal: Some Trip",
            fake_flights_scenario="personal_trip_without_flights",
            *args,
            **kwargs,
        ),
    )
    logger.info("Trip: Personal")
    expected_trip = {
        "trip_name": "Personal: Some Trip",
        "current_city": "Dayton, OH",
        "todays_flight": {},
    }
    assert get_current_trip(token="token", token_secret="token_secret") == expected_trip


@pytest.mark.unit
@freeze_time("2019-12-02 00:55:00")  # set to time during trip
def test_getting_active_trip_with_flight(monkeypatch, fake_response_from_route):
    """
    If we're currently on a trip and are flying, then we should
    get a trip back but with the flight that we're currently on.
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
    logger.info("Trip: Work")
    outbound_date = "2019-12-01"
    outbound_tz = "-06:00"
    outbound_start_time = normalize_flight_time_to_tz(
        {"date": outbound_date, "time": "17:11:00", "utc_offset": outbound_tz}
    )
    outbound_end_time = normalize_flight_time_to_tz(
        {"date": outbound_date, "time": "18:56:00", "utc_offset": outbound_tz}
    )
    expected_trip = {
        "trip_name": "Work: Test Client - Week 2",
        "current_city": "Omaha, NE",
        "todays_flight": {
            "flight_number": "AA356",
            "origin": "DFW",
            "destination": "OMA",
            "depart_time": outbound_start_time,
            "arrive_time": outbound_end_time,  # offset should be accounted for
            "offset": "-06:00",
        },
    }
    assert get_current_trip(token="token", token_secret="token_secret") == expected_trip
