"""
Can we ping our endpoint from the Internet?
"""

import pytest
import requests


@pytest.mark.integration
def ping_test(create_api_gateway_url):
    """ See module doc. """
    response = requests.get(create_api_gateway_url("/ping"))
    assert response.status_code == 200
    assert response.json == {"status": "ok"}
