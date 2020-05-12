"""
Tests for getting all trips endpoint.
"""
import json
from freezegun import freeze_time
import pytest
from tripit.trips import normalize_flight_time_to_tz
from tripit.api.aws_api_gateway.current_trip import current_trip


@pytest.mark.unit
def test_current_trip_endpoint_unauthenticated():
    """
    We should be denied access if we don't have an authenticated key yet.
    """
    fake_event = {
        "requestContext": {"path": "/develop/current_trip", "identity": {"apiKey": "fake-key"},},
    }
    expected_response = {
        "statusCode": 403,
        "body": json.dumps({"status": "error", "message": "Access denied; go to /auth first."}),
    }
    assert current_trip(fake_event) == expected_response


# pylint: disable=bad-continuation
@pytest.mark.unit
@freeze_time("2019-12-02 00:55:00")  # set to time during trip
def test_current_trip_endpoint_authenticated(
    monkeypatch, set_access_token_table, drop_access_token_table, fake_response_from_route
):
    # pylint: enable=bad-continuation
    # Lots of vars needed to mock this flight.
    # pylint: disable=too-many-locals
    """
    Gets the current trip in progress.
    Uses a trip with flights as an example.
    Full test suite is in tests/unit/flights.
    """
    set_access_token_table(access_key="fake-key", token="fake-token", secret="fake-secret")
    fake_event = {
        "requestContext": {"path": "/develop/current_trip", "identity": {"apiKey": "fake-key"},},
    }
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
            "offset": "-06:00",
            "depart_time": outbound_start_time,
            "arrive_time": outbound_end_time,  # offset should be accounted for
        },
    }
    expected_response = {
        "statusCode": 200,
        "body": json.dumps({"status": "ok", "trip": expected_trip}),
    }
    assert current_trip(fake_event) == expected_response
    drop_access_token_table()
