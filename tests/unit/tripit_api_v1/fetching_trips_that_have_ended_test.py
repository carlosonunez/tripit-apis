"""
This API can also show me when trips have ended. These tests account for that.
"""
import pytest
from freezegun import freeze_time
from tripit.core.v1.trips import get_all_trips, normalize_flight_time_to_tz


@pytest.mark.unit
@freeze_time("2019-11-28 08:00:00")
def test_fetching_trips_that_have_ended_due_to_flight_time(monkeypatch, fake_response_from_route):
    """
    Trips are considered to have ended if our current time is greater than the time
    of the last flight in our trip or if there is a note on the trip marking the
    trip as having ended.
    """
    fake_trip_name = "Personal: Some Trip That Ended"
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
        "tripit.core.v1.trips.get_from_tripit_v1",
        lambda *args, **kwargs: fake_response_from_route(
            fake_trip_name=fake_trip_name,
            fake_flights_scenario="trip_that_ended",
            filter_notes=True,  # we'll test notes in the next test.
            *args,
            **kwargs,
        ),
    )
    expected_trips = [
        {
            "id": 345678901,
            "name": fake_trip_name,
            "city": "Dallas, TX",
            "ends_on": inbound_end_time,
            "link": "https://www.tripit.com/trip/show/id/345678901",
            "starts_on": (outbound_start_time + test_outbound_ingress_seconds),
            "ended": True,
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
