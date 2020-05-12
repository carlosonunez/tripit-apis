"""
Provides an access key for protected endpoints.
"""

import pytest
from tests.fixtures.integration.helpers.secrets import read_secret


@pytest.fixture()
def access_key():
    """
    See module doc.
    """
    return read_secret("api_key")
