"""
Helpers for working with the API Gateway.
"""
import pytest


@pytest.fixture
def create_api_gateway_url():
    """
    The API Gateway FQDN will be dynamically created. Create URLs with this
    FQDN affixed.
    """

    def _run(endpoint):
        return f"https://foo/{endpoint}"
