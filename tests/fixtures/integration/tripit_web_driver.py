"""
This provides a Selenium webdriver for interacting with the TripIt website.
"""
import os
from selenium import webdriver


class TripitWebDriver:
    """
    Provides a webdriver that you can use to do all sorts of things to Tripit.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self):
        host = os.environ.get("SELENIUM_HOST") or "selenium"
        port = os.environ.get("SELENIUM_PORT") or 4444
        self.driver = webdriver.Remote(
            command_executor=f"http://{host}:{port}/wd/hub",
            desired_capabilities={"browserName": "chrome", "args": ["--no-default-browser-check"]},
        )

    def visit(self, site):
        """
        Ported from Capybara. Visits a page.
        """
        self.driver.get(site)

    def fill_in(self, element_id, value):
        """
        Ported from Capybara. Fill in an element.
        """
        self.driver.find_element_by_id(element_id).send_keys(value)

    def click_button(self, element_id):
        """
        Ported from Capybara. Click on a button by its element_id.
        """
        self.driver.find_element_by_id(element_id).click()
