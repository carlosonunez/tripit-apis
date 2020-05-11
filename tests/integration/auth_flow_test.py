"""
This tests covers the entire flow of authenticating into the TripIt API and
authorizing this application to access their TripIt account details.
"""

import re
import time
import pytest
import requests
import timeout_decorator


@timeout_decorator.timeout(5)
def get_and_wait_for_lambda_ready(url, access_key=None):
    """
    We might get 403 Forbidden's while Lambda starts up.
    This waits for them to clear out.
    """
    while True:
        headers = {}
        if access_key:
            headers = {"x-api-key": access_key}
        response = requests.get(url, headers=headers)
        if response.status_code != 403:
            return response
        time.sleep(1)


@pytest.mark.integration
def test_getting_an_authorization_url(create_api_gateway_url, access_key):
    """
    Do we get a URL that we can click on to authorize our application?
    """
    expected_callback_url = create_api_gateway_url("callback")
    response = get_and_wait_for_lambda_ready(create_api_gateway_url("auth"), access_key)

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


# @pytest.mark.integration
# def test_getting_a_token_after_callback(create_api_gateway_url, access_key):
