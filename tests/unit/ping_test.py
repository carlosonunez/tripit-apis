"""
Healthiness tests.
"""
import json
import pytest
from tripit.health import ping


@pytest.mark.unit
def test_ping():
    """
    Basic healthiness function to indicate that all is well
    with our API.
    """
    response = {
        "body": json.dumps({"status": "ok", "message": "sup dawg"}),
        "statusCode": 200
    }
    assert ping() == response
