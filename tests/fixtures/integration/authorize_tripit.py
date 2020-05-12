"""
Fixture for automatically authorizing TripIt to our dev account.
"""

import json
import os
import pytest
from tripit.logging import logger
from tests.fixtures.integration.tripit_web_driver import TripitWebDriver


@pytest.fixture()
def authorize_tripit():
    """
    Authorizes TripIt through an automated web browser.
    """

    def _run(authz_url):
        session = TripitWebDriver()
        try:
            session.visit(authz_url)
            session.fill_in("email_address", os.environ.get("TRIPIT_SANDBOX_ACCOUNT_EMAIL"))
            session.fill_in("password", os.environ.get("TRIPIT_SANDBOX_ACCOUNT_PASSWORD"))
            session.click_button("Sign In")
            junk_prefix = '<html><head></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">'
            junk_postfix = "</pre></body></html>"
            result = session.page().replace(junk_prefix, "").replace(junk_postfix, "")
            return json.loads(result)
        # We want a broad exception here.
        # pylint: disable=broad-except
        except Exception as failure:
            logger.error("Failed to authorize: %s", failure)
            return None

    return _run
