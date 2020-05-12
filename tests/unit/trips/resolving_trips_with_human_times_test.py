"""
This API will return Unix times by default. However, there are times in which
we want to see these times as human-readable dates.

This test covers that.
"""
import pytest
from freezegun import freeze_time
from tripit.trips import get_all_trips, normalize_flight_time_to_tz


@pytest.mark.unit
@freeze_time("Jan 1 1970 00:01:02")
# pylint: disable=bad-continuation
def test_fetching_trips_with_flights(
    monkeypatch, fake_response_from_route, show_as_human_readable_date
):
    # pylint: enable=bad-continuation
    """
    We should get back a valid trip with flight data for trips with flights
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
            "link": "https://www.tripit.com/trip/show/id/293554134",
            "starts_on": (
                outbound_start_time_with_ingress
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
    assert (
        get_all_trips(token="token", token_secret="token_secret", human_times=True)
        == expected_trips
    )
