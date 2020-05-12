"""
This tests getting a list of trips.

--- FLAKY TEST ALERT ---

These are actual trips configured against a live TripIt account. They have end dates.
Since we can't mock dates over the wire, these tests will fail if the date this
test is run exceeds the end date of the trips in this account.

A future commit will add automation to ensure that this doesn't happen.
"""
import re
import pytest


@pytest.mark.integration
# pylint: disable=bad-continuation
def test_trips_api(
    create_api_gateway_url, access_key, get_and_wait_for_lambda_ready, authorize_tripit
):
    """
    Do we get trips back once we've been authorized?
    """
    expected_callback_url = create_api_gateway_url("callback")
    # Unfortunately we need that backslash in order for this re to compile.
    # pylint: disable=anomalous-backslash-in-string
    tripit_auth_url_pattern = re.compile(
        "".join(
            [
                ".*",
                "(https://www.tripit.com/oauth/authorize\?oauth_token=[a-zA-Z0-9]+&",
                "oauth_callback=",
                expected_callback_url,
                ")",
            ]
        )
    )
    response = get_and_wait_for_lambda_ready(
        create_api_gateway_url("auth") + "?reauthorize=true", access_key
    )
    matches = tripit_auth_url_pattern.match(response.json()["message"])
    authz_url = matches.groups()[0]
    expected_callback_response = authorize_tripit(authz_url + "&is_sign_in=1")
    assert "status" in expected_callback_response
    assert expected_callback_response["status"] == "ok"

    trips_response = get_and_wait_for_lambda_ready(create_api_gateway_url("trips"), access_key)
    expected_trips = [
        {
            "id": 293554303,
            "name": "Work: Test Client - Week 3",
            "city": "Dayton, OH",
            "ends_on": 1599955200,
            "ended": False,
            "link": "https://www.tripit.com/trip/show/id/293554303",
            "starts_on": 1599696000,
            "flights": [],
        },
        {
            "id": 293554288,
            "name": "Personal: Test Trip",
            "city": "New York, NY",
            "ends_on": 1599264000,
            "ended": False,
            "link": "https://www.tripit.com/trip/show/id/293554288",
            "starts_on": 1598918400,
            "flights": [],
        },
    ]

    assert trips_response.status_code == 200
    assert trips_response.json()["trips"] == expected_trips
