"""
Can we ping our endpoint from the Internet?
"""

import pytest
import requests


@pytest.mark.integration
def test_ping(create_api_gateway_url):
    """ See module doc. """
    url = create_api_gateway_url("ping")
    response = requests.get(url)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
