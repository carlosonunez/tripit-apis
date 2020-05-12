"""
This tests getting a list of trips.

--- FLAKY TEST ALERT ---

These are actual trips configured against a live TripIt account. They have end dates.
Since we can't mock dates over the wire, these tests will fail if the date this
test is run exceeds the end date of the trips in this account.

A future commit will add automation to ensure that this doesn't happen.
"""
import json
import os
import re
import time
import pytest
import requests
import timeout_decorator
from tripit.logging import logger
from tests.fixtures.integration.tripit_web_driver import TripitWebDriver

# TODO: Turn this into a fixture.
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


# TODO: Turn this into a fixture.
def authorize_tripit(authz_url):
    """
    Authorizes TripIt through an automated web browser.
    """
    session = TripitWebDriver()
    try:
        session.visit(authz_url)
        import pdb

        pdb.set_trace()
        if session.has_element("Agree and Proceed", element_type="a"):
            session.click_button("Agree and Proceed")
        session.fill_in("email_address", os.environ.get("TRIPIT_SANDBOX_ACCOUNT_EMAIL"))
        session.fill_in("password", os.environ.get("TRIPIT_SANDBOX_ACCOUNT_PASSWORD"))
        session.click_button("Sign In")
        junk_prefix = (
            '<html><head></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">'
        )
        junk_postfix = "</pre></body></html>"
        result = session.page().replace(junk_prefix, "").replace(junk_postfix, "")
        return json.loads(result)
    # We want a broad exception here.
    # pylint: disable=broad-except
    except Exception as failure:
        logger.error("Failed to authorize: %s", failure)
        return None


@pytest.mark.integration
def test_trips_api(create_api_gateway_url, access_key):
    """
    Do we get trips back once we've been authorized?
    """
    expected_callback_url = create_api_gateway_url("callback")
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

    trips_response = get_and_wait_for_lambda_ready(create_api_gateway_url("trips"))
    assert trips_response.status_code == 200
    assert trips_response.json() == {}
