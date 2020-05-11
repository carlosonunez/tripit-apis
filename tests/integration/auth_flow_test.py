"""
This tests covers the entire flow of authenticating into the TripIt API and
authorizing this application to access their TripIt account details.
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


def authorize_tripit(authz_url):
    """
    Authorizes TripIt through an automated web browser.
    """
    session = TripitWebDriver()
    try:
        session.visit(authz_url)
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


@pytest.mark.integration
def test_getting_a_token_after_callback(create_api_gateway_url, access_key):
    """
    Do we get an OAuth token back after authorizing Tripit?
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
    response = get_and_wait_for_lambda_ready(create_api_gateway_url("auth"), access_key)
    matches = tripit_auth_url_pattern.match(response.json()["message"])
    authz_url = matches.groups()[0]
    expected_callback_response = authorize_tripit(authz_url + "&is_sign_in=1")
    assert "status" in expected_callback_response
    assert expected_callback_response["status"] == "ok"
