"""
API endpoint for our health check.
"""

import json
import pytest
from tripit.api.aws_api_gateway.ping import ping


@pytest.mark.unit
def test_that_ping_works():
    """
    Ensure that we can ping from API Gateway.
    """
    assert ping(None, None) == {
        "body": json.dumps({"status": "ok"}),
        "statusCode": 200,
    }
