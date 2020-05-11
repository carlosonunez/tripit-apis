"""
This tests covers the entire flow of authenticating into the TripIt API and
authorizing this application to access their TripIt account details.
"""

import re
import pytest
import requests


@pytest.mark.integration
def test_getting_an_authorization_url(create_api_gateway_url, access_key):
    """
    Do we get a URL that we can click on to authorize our application?
    """
    auth_url = create_api_gateway_url("auth") + "?reauthorize=true"
    expected_callback_url = create_api_gateway_url("callback")
    response = requests.get(auth_url, headers={"x-api-key": access_key})

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
