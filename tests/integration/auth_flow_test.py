"""
This tests covers the entire flow of authenticating into the TripIt API and
authorizing this application to access their TripIt account details.
"""
import re
import pytest


@pytest.mark.integration
# pylint: disable=bad-continuation
def test_getting_an_authorization_url(
    create_api_gateway_url, access_key, get_and_wait_for_lambda_ready
):
    """
    Do we get a URL that we can click on to authorize our application?
    """
    expected_callback_url = create_api_gateway_url("callback")
    response = get_and_wait_for_lambda_ready(
        create_api_gateway_url("auth") + "?reauthorize=true", access_key
    )

    # pylint doesn't know that this will be compiled into a regex
    # pylint:disable=anomalous-backslash-in-string
    expected_tripit_auth_url_pattern = re.compile(
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
    assert response.status_code == 200

    matches = expected_tripit_auth_url_pattern.match(response.json()["message"])
    assert matches is not None
    assert len(matches.groups()) == 1


@pytest.mark.integration
# pylint: disable=bad-continuation
def test_getting_a_token_after_callback(
    create_api_gateway_url, authorize_tripit, access_key, get_and_wait_for_lambda_ready
):
    """
    Do we get an OAuth token back after authorizing Tripit?
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
