"""
This provides a Selenium webdriver for interacting with the TripIt website.
"""
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from tripit.logging import logger


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

    def page(self):
        """
        Gets the text of the page.
        """
        return self.driver.page_source

    def has_element(self, element_id, element_type=None):
        """
        Tests whether an element is on the page or not.
        """
        return self._find_element(element_id, element_type) is not None

    def visit(self, site):
        """
        Ported from Capybara. Visits a page.
        """
        self.driver.get(site)

    def fill_in(self, element_id, value):
        """
        Ported from Capybara. Fill in an element.
        """
        element = self._find_element(element_id)
        if not element:
            raise NoSuchElementException(f"Couldn't find this in page: {element_id}")
        element.send_keys(value)

    def click_button(self, element_id):
        """
        Ported from Capybara. Click on a button by its element_id.
        """
        element = self._find_element(element_id)
        if not element:
            raise NoSuchElementException(f"Couldn't find this in page: {element_id}")
        element.click()

    def _find_element(self, element_id, element_type="*"):
        """
        Attempts to find a matching element, first by ID, then by (slower) XPath.
        """
        try:
            return self.driver.find_element_by_id(element_id)
        except NoSuchElementException:
            """
            Note that finding elements by XPath will return the first
            element that matches the value being sought after.

            This might be the wrong element!
            """
            try:
                xpath_query = f"//{element_type}[contains(text(), '{element_id}')]"
                return self.driver.find_element(By.XPATH, xpath_query)
            except NoSuchElementException:
                logger.warning("Element not found: %s", element_id)
                return None
