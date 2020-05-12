"""
This tests getting our current trip.
"""
import re
import pytest


@pytest.mark.integration
# pylint: disable=bad-continuation
# Yes, pylint; we need all of these fixtures.
# pylint: disable=too-many-arguments
def test_current_trip_api(
    create_api_gateway_url,
    access_key,
    get_and_wait_for_lambda_ready,
    authorize_tripit,
    set_current_trip,
    delete_current_trip,
):
    """
    Do we get a current trip back?
    """
    current_trip_id = set_current_trip()
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

    trips_response = get_and_wait_for_lambda_ready(
        create_api_gateway_url("current_trip"), access_key
    )
    actual_trip = trips_response.json()["trip"]

    assert trips_response.status_code == 200
    assert re.match("Test Trip [0-9]{1,}", actual_trip["trip_name"])
    assert actual_trip["current_city"] == "Dallas, TX"
    assert actual_trip["todays_flight"] == {}
    delete_current_trip(current_trip_id)
