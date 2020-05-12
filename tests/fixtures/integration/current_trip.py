"""
Fixture for automatically authorizing TripIt to our dev account.
"""

from datetime import datetime, timedelta
import os
import pytest
from tripit.logging import logger
from tests.fixtures.integration.tripit_web_driver import TripitWebDriver


def _sign_in(session):
    session.visit("https://tripit.com/account/login")
    session.fill_in("email_address", os.environ.get("TRIPIT_SANDBOX_ACCOUNT_EMAIL"))
    session.fill_in("password", os.environ.get("TRIPIT_SANDBOX_ACCOUNT_PASSWORD"))
    session.click_button("Sign In")


@pytest.fixture()
def set_current_trip():
    """
    Updates a dummy trip in our TripIt account to today so that we can get a valid trip
    during integration.
    """

    def _create_new_trip(session):
        today = datetime.now().strftime("%m/%d/%Y")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%m/%d/%Y")
        session.visit("https://tripit.com/trip/create")
        session.fill_in("place", "Dallas, TX")
        session.fill_in("display_name", "Test Trip " + str(int(datetime.now().timestamp())))
        session.fill_in("start_date", today)

        # This fills end date with junk data at first. Clearing the junk
        # and adding the date again seemed to clear it.
        session.fill_in("end_date", tomorrow)
        session.driver.find_element_by_id("end_date").clear()
        session.fill_in("end_date", tomorrow)
        session.fill_in("description", "Created during integration testing.")
        session.click_button("Add Trip")
        trip_id = session.driver.current_url.split("/")[-1]
        session.close()
        return trip_id

    def _run():
        session = TripitWebDriver()
        try:
            _sign_in(session)
            return _create_new_trip(session)
        # We want a broad exception here.
        # pylint: disable=broad-except
        except Exception as failure:
            logger.error("Failed to create a new test trip: %s", failure)

    return _run


@pytest.fixture()
def delete_current_trip():
    """
    Deletes a trip created by set_current_trip.
    """

    def _delete_current_trip(session, trip_id):
        session.visit(
            "".join(
                [
                    "https://tripit.com/trips/delete/",
                    trip_id,
                    "?redirect_url=https://www.tripit.com/trips",
                ]
            )
        )
        session.click_button("Delete", element_type="button")
        session.click_button("Confirm Delete", element_type="button")

    def _run(trip_id):
        session = TripitWebDriver()
        try:
            _sign_in(session)
            _delete_current_trip(session, trip_id)
            session.close()
        # We want a broad exception here.
        # pylint: disable=broad-except
        except Exception as failure:
            logger.error("Failed to create a new test trip: %s", failure)

    return _run
