"""
This API can also show me when trips have ended. These tests account for that.
"""
import pytest
from freezegun import freeze_time
from tripit.trips import get_all_trips, normalize_flight_time_to_tz


@pytest.mark.unit
@freeze_time("2019-11-28 08:00:00")
def test_fetching_trips_that_have_ended_due_to_flight_time(monkeypatch, fake_response_from_route):
    """
    Trips are considered to have ended if our current time is greater than the time
    of the last flight in our trip or if there is a note on the trip marking the
    trip as having ended.

    Note that "ended" in this case means that the end_time is earlier than now.
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
        "tripit.trips.get_from_tripit_v1",
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


@pytest.mark.unit
@freeze_time("2019-11-28 08:00:00")
def test_fetching_trips_that_end_beyond_last_flight(monkeypatch, fake_response_from_route):
    """
    Some trips will have an end date that exceeds the date of the last flight.

    This test accounts for those cases.
    """
    fake_trip_name = "Personal: Some Trip That Ended"
    test_outbound_ingress_seconds = 90 * 60
    outbound_date = "2019-11-27"
    outbound_tz = "-05:00"
    end_date = "2019-12-01"
    end_date_tz = "-00:00"
    end_date_time = normalize_flight_time_to_tz(
        {"date": end_date, "time": "00:00:00", "utc_offset": end_date_tz}
    )
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
            fake_trip_name=fake_trip_name,
            fake_flights_scenario="trip_that_ended_but_trip_still_active",
            filter_notes=True,
            *args,
            **kwargs,
        ),
    )
    expected_trips = [
        {
            "id": 345678901,
            "name": fake_trip_name,
            "city": "Dallas, TX",
            "ends_on": end_date_time,
            "link": "https://www.tripit.com/trip/show/id/345678901",
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


@pytest.mark.unit
@freeze_time("Jan 1 1970 00:01:02")
def test_fetching_trips_that_have_ended_due_to_note(monkeypatch, fake_response_from_route):
    """
    If there's a note in the trip that says "TRIP_ENDED", then that means that
    we need to manually mark the trip as such.

    This is a legacy feature from the Ruby version of this API that did not adjust
    the end times of trips to match the last flight on the trip. (It was too difficult
    to write a test for this because I was newb at testing then). I plan on deprecating
    this eventually, but I want to include it in the port-over to maintain
    feature parity.
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
        "tripit.trips.get_from_tripit_v1",
        lambda *args, **kwargs: fake_response_from_route(
            fake_trip_name=fake_trip_name,
            fake_flights_scenario="trip_that_ended",
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
