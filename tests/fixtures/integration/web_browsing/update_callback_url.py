"""
We will need to update our callback URL in TripIt whenever our API Gateway
changes.

This fixture handles that.
"""
import os
import pytest
from tests.fixtures.integration.tripit_web_driver import TripitWebDriver


@pytest.fixture
def update_callback_url(callback_url):
    """ See module doc. """
    driver = TripitWebDriver()
    sign_in(driver)
    update_callback(driver, callback_url)


def sign_in(driver):
    """
    First, sign into TripIt.
    """
    driver.visit(f"https://{os.environ.get('TRIPIT_WORKSPACE_NAME')}.tripit.com/signin")
    driver.fill_in("email", driver.os.environ.get("TRIPIT_SANDBOX_ACCOUNT_EMAIL"))
    driver.fill_in("password", driver.os.environ.get("TRIPIT_SANDBOX_ACCOUNT_PASSWORD"))
    driver.click_button("signin_btn")


def update_callback(driver, url):
    """
    Next, update the callback URL.
    """
    driver.visit("https://api.tripit.com/apps/APDPV4M54/oauth?")
    driver.click_button('button[data-qa="url_delete"]')
    driver.fill_in('input[data-qa="app_unfurl_domain"]', url)
    driver.click_button("Add")
    driver.click_button("Save driver.URLs")
