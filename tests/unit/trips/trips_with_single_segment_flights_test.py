"""
This covers situations where a trip only has a single flight with a single segment.

This has happened during multi-city itineraries where each leg of the flight was on a different
ticket, either because of different carriers or because ticketing each leg was cheaper.
"""
import pytest
from freezegun import freeze_time
from tripit.trips import get_all_trips, normalize_flight_time_to_tz


@pytest.mark.unit
@freeze_time("Jan 1 1970 00:01:02")
def test_fetching_trips_with_single_segment_flights(monkeypatch, fake_response_from_route):
    """
    Same as test_fetching_trips_with_flights except for situations where
    we only have one segment in the flight.
    """
    test_outbound_ingress_seconds = 90 * 60
    outbound_date = "2019-11-27"
    outbound_tz = "-05:00"
    inbound_date = "2019-11-27"
    inbound_tz = "-08:00"
    outbound_start_time = normalize_flight_time_to_tz(
        {"date": outbound_date, "time": "11:19:00", "utc_offset": outbound_tz}
    )
    inbound_end_time = normalize_flight_time_to_tz(
        {"date": inbound_date, "time": "13:01:00", "utc_offset": inbound_tz}
    )
    monkeypatch.setenv("TRIPIT_INGRESS_TIME_MINUTES", "90")
    monkeypatch.setattr(
        "tripit.trips.get_from_tripit_v1",
        lambda *args, **kwargs: fake_response_from_route(
            fake_trip_name="Work: Test Client - Week 3",
            fake_flights_scenario="trip_with_single_segment",
            *args,
            **kwargs,
        ),
    )
    expected_trips = [
        {
            "id": 234567890,
            "name": "Work: Test Client - Week 3",
            "city": "Los Angeles, CA",
            "ends_on": inbound_end_time,
            "link": "https://www.tripit.com/trip/show/id/234567890",
            "starts_on": (outbound_start_time + test_outbound_ingress_seconds),
            "ended": False,
            "flights": [
                {
                    # Since this is a one-way single-segment flight,
                    # its end time == inbound end time.
                    "flight_number": "AA1",
                    "origin": "JFK",
                    "destination": "LAX",
                    "depart_time": outbound_start_time,
                    "arrive_time": inbound_end_time,
                    "offset": "-05:00",
                }
            ],
        }
    ]
    assert get_all_trips(token="token", token_secret="token_secret") == expected_trips
