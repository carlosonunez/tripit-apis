"""
Tests for summarizing trip data from the TripIt API.

This API is meant to be used to get quick facts about trips in one's profile
to assist with other, downstream automations like setting Slack statuses
(the motivation for this API) or creating messages to send to other people.

It is meant to be read-only.
"""
import json
from pathlib import Path
import re
import pytest
from tripit.core.v1.trips import get_all_trips, normalize_flight_time_to_tz


# pylint: disable=too-few-public-methods
class FakeResponse:
    """Used to stub calls to TripIt's API."""

    def __init__(self, url, status_code, text=None, json_object=None):
        self.url = url
        self.status_code = status_code
        if text:
            self.text = text
            self.json = json.loads(text)
        elif json_object:
            self.json = json_object
            self.text = json.dumps(json_object)


# pylint: disable=too-few-public-methods
class FakeTrip:
    """
    Convenience class for creating mocked trips.
    """

    def __init__(self, trip_name):
        self.fake_trip_data = json.loads(Path("./tests/fixtures/trips.json").read_text())
        self.trip_data = self.filter_trips(trip_name)

    def filter_trips(self, trip_name):
        """ Reads the test trips fixture and filters the trip list based
        on the name provided. """
        trips = self.fake_trip_data
        trips["Trip"] = [trip for trip in trips["Trip"] if trip["display_name"] == trip_name]
        return trips

    @staticmethod
    # We need to assume that we will get anonymous arguments here, since
    # this is a function being monkeypatched-in.
    # pylint: disable=unused-argument
    def fake_response_from_route(*args, **kwargs):
        """
        monkeypatch sucks at conditional mocking, so this function
        fills in this gap by returning the right response from mock TripIt
        based on the path requested.
        """
        fake_trip_name = kwargs.get("fake_trip_name")
        fake_flights_to_load = kwargs.get("fake_flights_scenario")
        endpoint = kwargs.get("endpoint")
        if fake_flights_to_load:
            fake_flights = json.loads(
                Path(f"./tests/fixtures/{fake_flights_to_load}.json").read_text()
            )
        else:
            fake_flights = None

        fake_response = None

        if not fake_trip_name and not fake_flights_to_load:
            fake_response = FakeResponse(
                url="https://api.tripit.com/v1/list/trip/format/json",
                status_code=200,
                json_object={"timestamp": 123, "num_bytes": 78},
            )

        if endpoint == "/trips":
            if kwargs.get("fake_trip_data"):
                fake_trip_data = kwargs["fake_trip_data"]
            else:
                fake_trip_data = FakeTrip(fake_trip_name).trip_data
            fake_response = FakeResponse(
                url="https://api.tripit.com/v1/list/trip/format/json",
                status_code=200,
                json_object=fake_trip_data,
            )

        if re.match(r"/get/trip/id", kwargs["endpoint"]):
            fake_response = FakeResponse(
                url="https://api.tripit.com/v1/get/trip/id/123/includeObjects/true",
                status_code=200,
                json_object=fake_flights,
            )

        return fake_response


@pytest.mark.unit
def test_fetching_trips_when_none_are_present(monkeypatch):
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
        lambda *args, **kwargs: FakeTrip.fake_response_from_route(*args, **kwargs),
    )
    assert get_all_trips(token="token", token_secret="token_secret") == []


@pytest.mark.unit
def test_fetching_trips_without_flights(monkeypatch):
    """
    We should get back a valid trip for personal trips.
    """
    monkeypatch.setattr(
        "tripit.core.v1.trips.get_from_tripit_v1",
        lambda *args, **kwargs: FakeTrip.fake_response_from_route(
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
def test_that_we_can_get_multiple_trips(monkeypatch):
    """
    Ensure that our threads can actually yield multiple trips.
    """

    # Duplicate the object, since I only care about getting multiple trips back.
    fake_trip = FakeTrip("Personal: Some Trip")
    fake_trip.trip_data["Trip"] = fake_trip.trip_data["Trip"] + fake_trip.trip_data["Trip"]

    monkeypatch.setattr(
        "tripit.core.v1.trips.get_from_tripit_v1",
        lambda *args, **kwargs: FakeTrip.fake_response_from_route(
            fake_trip_name="Personal: Some Trip",
            fake_flights_scenario="personal_trip_without_flights",
            fake_trip_data=fake_trip.trip_data,
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
def test_fetching_trips_with_flights(monkeypatch):
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
        lambda *args, **kwargs: FakeTrip.fake_response_from_route(
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
def test_fetching_trips_with_single_segment_flights(monkeypatch):
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
        lambda *args, **kwargs: FakeTrip.fake_response_from_route(
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
