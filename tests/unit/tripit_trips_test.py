"""
Tests for summarizing trip data from the TripIt API.

This API is meant to be used to get quick facts about trips in one's profile
to assist with other, downstream automations like setting Slack statuses
(the motivation for this API) or creating messages to send to other people.

It is meant to be read-only.
"""
import pytest
from freezegun import freeze_time
from tripit.core.v1.trips import get_all_trips, normalize_flight_time_to_tz


@pytest.mark.unit
@freeze_time("Jan 1 1970 00:01:02")
def test_fetching_trips_when_none_are_present(monkeypatch, fake_response_from_route):
    """
    We shouldn't get anything back when no trips are present.

    NOTE:
    You might be wondering "`get_from_tripit_v1` belongs in `tripit.core.v1.api`,
    but we're patching it from `tripit.core.v1.trips`. What gives?"

    This is due to a limitation of how modules work in Python.

    See here: https://alexmarandon.com/articles/python_mock_gotchas/
    """
    # pylint: disable=unnecessary-lambda
    # Unfortunately it is because monkeypatch sucks at this.
    monkeypatch.setattr(
        "tripit.core.v1.trips.get_from_tripit_v1",
        lambda *args, **kwargs: fake_response_from_route(*args, **kwargs),
    )
    assert get_all_trips(token="token", token_secret="token_secret") == []


@pytest.mark.unit
@freeze_time("Jan 1 1970 00:01:02")
def test_fetching_trips_without_flights(monkeypatch, fake_response_from_route):
    """
    We should get back a valid trip for personal trips.
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


@pytest.mark.unit
@freeze_time("Jan 1 1970 00:01:02")
def test_fetching_trips_with_flights(monkeypatch, fake_response_from_route):
    """
    We should get back a valid trip with flight dat for trips with flights
    in them.

    Additionally, the start and end time of the trip should now match the
    departure time and arrival time of the first and last flight segment,
    respectively, with some additional padding for trip ingress (getting to the
    airport and waiting for the flight to depart) to the start time.
    """
    test_outbound_ingress_seconds = 90 * 60
    outbound_date = "2019-12-01"
    outbound_tz = "-06:00"
    inbound_date = "2019-12-05"
    inbound_tz = "-06:00"
    outbound_start_time = normalize_flight_time_to_tz(
        {"date": outbound_date, "time": "17:11:00", "utc_offset": outbound_tz}
    )
    outbound_end_time = normalize_flight_time_to_tz(
        {"date": outbound_date, "time": "18:56:00", "utc_offset": outbound_tz}
    )
    inbound_start_time = normalize_flight_time_to_tz(
        {"date": inbound_date, "time": "16:02:00", "utc_offset": inbound_tz}
    )
    inbound_end_time = normalize_flight_time_to_tz(
        {"date": inbound_date, "time": "17:58:00", "utc_offset": inbound_tz}
    )
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
    expected_trips = [
        {
            "id": 293554134,
            "name": "Work: Test Client - Week 2",
            "city": "Omaha, NE",
            "ends_on": inbound_end_time,  # Should match AA2360 arrive_time
            "link": "https://www.tripit.com/trip/show/id/293554134",
            "starts_on": (
                outbound_start_time + test_outbound_ingress_seconds
            ),  # Should match AA356 depart_time + ingress
            "ended": False,
            "flights": [
                {
                    "flight_number": "AA356",
                    "origin": "DFW",
                    "destination": "OMA",
                    "depart_time": outbound_start_time,
                    "arrive_time": outbound_end_time,  # offset should be accounted for
                    "offset": "-06:00",
                },
                {
                    "flight_number": "AA2360",
                    "origin": "OMA",
                    "destination": "DFW",
                    "depart_time": inbound_start_time,  # offset should be accounted for
                    "arrive_time": inbound_end_time,  # offset should be accounted for
                    "offset": "-06:00",
                },
            ],
        }
    ]
    assert get_all_trips(token="token", token_secret="token_secret") == expected_trips


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
        "tripit.core.v1.trips.get_from_tripit_v1",
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


@pytest.mark.unit
@freeze_time("2019-11-28 08:00:00")
# Pylint doesn't like black's formatting choices here.
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
