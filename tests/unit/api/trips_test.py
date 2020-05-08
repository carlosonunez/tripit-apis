"""
Tests for getting all trips endpoint.
"""
import json
from freezegun import freeze_time
import pytest
from tripit.trips import normalize_flight_time_to_tz
from tripit.api.aws_api_gateway.trips import get_trips


@pytest.mark.unit
def test_trips_endpoint_unauthenticated():
    """
    We should be denied access if we don't have an authenticated key yet.
    """
    fake_event = {
        "requestContext": {"path": "/develop/trips", "identity": {"apiKey": "fake-key"},},
    }
    expected_response = {
        "statusCode": 403,
        "body": json.dumps({"status": "error", "message": "Access denied; go to /auth first."}),
    }
    assert get_trips(fake_event) == expected_response


# pylint: disable=bad-continuation
@pytest.mark.unit
@freeze_time("Jan 1 1970 00:01:02")
def test_trips_endpoint_authenticated(
    monkeypatch, set_access_token_table, drop_access_token_table, fake_response_from_route
):
    # pylint: enable=bad-continuation
    # Lots of vars needed to mock this flight.
    # pylint: disable=too-many-locals
    """
    Gets all of the trips associated with ones Tripit account.
    Uses a trip with flights as an example.
    """
    set_access_token_table(access_key="fake-key", token="fake-token", secret="fake-secret")
    fake_event = {
        "requestContext": {"path": "/develop/trips", "identity": {"apiKey": "fake-key"},},
    }
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
        "tripit.trips.get_from_tripit_v1",
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
            "ends_on": inbound_end_time,
            "ended": False,
            "link": "https://www.tripit.com/trip/show/id/293554134",
            "starts_on": (outbound_start_time + test_outbound_ingress_seconds),
            "flights": [
                {
                    "flight_number": "AA356",
                    "origin": "DFW",
                    "destination": "OMA",
                    "offset": "-06:00",
                    "depart_time": outbound_start_time,
                    "arrive_time": outbound_end_time,
                },
                {
                    "flight_number": "AA2360",
                    "origin": "OMA",
                    "destination": "DFW",
                    "offset": "-06:00",
                    "depart_time": inbound_start_time,
                    "arrive_time": inbound_end_time,
                },
            ],
        }
    ]
    expected_response = {
        "statusCode": 200,
        "body": json.dumps({"status": "ok", "trips": expected_trips}),
    }
    assert get_trips(fake_event) == expected_response
    drop_access_token_table()


# pylint: disable=bad-continuation
@pytest.mark.unit
@freeze_time("Jan 1 1970 00:01:02")
def test_trips_endpoint_authenticated_human_times(
    monkeypatch,
    set_access_token_table,
    drop_access_token_table,
    fake_response_from_route,
    show_as_human_readable_date,
):
    # pylint: enable=bad-continuation
    # Lots of vars needed to mock this flight.
    # pylint: disable=too-many-locals
    """
    Gets all of the trips associated with ones Tripit account.
    Uses a trip with flights as an example.
    Should get human times if provided
    """
    set_access_token_table(access_key="fake-key", token="fake-token", secret="fake-secret")
    fake_event = {
        "requestContext": {"path": "/develop/trips", "identity": {"apiKey": "fake-key"},},
        "queryStringParameters": {"human_times": "true"},
    }
    test_outbound_ingress_seconds = 90 * 60
    outbound_date = "2019-12-01"
    outbound_tz = "-06:00"
    inbound_date = "2019-12-05"
    inbound_tz = "-06:00"
    outbound_start_time_ts = normalize_flight_time_to_tz(
        {"date": outbound_date, "time": "17:11:00", "utc_offset": outbound_tz}
    )
    outbound_start_time = show_as_human_readable_date(outbound_start_time_ts)
    outbound_start_time_with_ingress = show_as_human_readable_date(
        outbound_start_time_ts + test_outbound_ingress_seconds
    )
    outbound_end_time = show_as_human_readable_date(
        normalize_flight_time_to_tz(
            {"date": outbound_date, "time": "18:56:00", "utc_offset": outbound_tz}
        )
    )
    inbound_start_time = show_as_human_readable_date(
        normalize_flight_time_to_tz(
            {"date": inbound_date, "time": "16:02:00", "utc_offset": inbound_tz}
        )
    )
    inbound_end_time = show_as_human_readable_date(
        normalize_flight_time_to_tz(
            {"date": inbound_date, "time": "17:58:00", "utc_offset": inbound_tz}
        )
    )
    monkeypatch.setenv("TRIPIT_INGRESS_TIME_MINUTES", "90")
    monkeypatch.setattr(
        "tripit.trips.get_from_tripit_v1",
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
            "ended": False,
            "link": "https://www.tripit.com/trip/show/id/293554134",
            "starts_on": (
                outbound_start_time_with_ingress
            ),  # Should match AA356 depart_time + ingress
            "flights": [
                {
                    "flight_number": "AA356",
                    "origin": "DFW",
                    "destination": "OMA",
                    "offset": "-06:00",
                    "depart_time": outbound_start_time,
                    "arrive_time": outbound_end_time,  # offset should be accounted for
                },
                {
                    "flight_number": "AA2360",
                    "origin": "OMA",
                    "destination": "DFW",
                    "offset": "-06:00",
                    "depart_time": inbound_start_time,  # offset should be accounted for
                    "arrive_time": inbound_end_time,  # offset should be accounted for
                },
            ],
        }
    ]
    expected_response = {
        "statusCode": 200,
        "body": json.dumps({"status": "ok", "trips": expected_trips}),
    }
    assert get_trips(fake_event) == expected_response
    drop_access_token_table()
