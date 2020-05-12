"""
Helpers for working with the API Gateway.
"""
import pytest
from tests.fixtures.integration.helpers.secrets import read_secret


@pytest.fixture
def create_api_gateway_url():
    """
    The API Gateway FQDN will be dynamically created. Create URLs with this
    FQDN affixed.
    """

    def _run(endpoint):
        return f"{read_secret('endpoint_name')}/{endpoint}"

    return _run
