"""
Tests for getting all trips endpoint.
"""
import json
import pytest
from tripit.api.aws_api_gateway.trips import get_trips


@pytest.mark.unit
def test_trips_endpoint_unauthenticated():
    """
    Gets all of the trips associated with ones Tripit account.
    """
    fake_event = {
        "requestContext": {"path": "/develop/trips", "identity": {"apiKey": "fake-key"},},
    }
    expected_response = {
        "statusCode": 403,
        "body": json.dumps({"status": "error", "message": "Access denied; go to /auth first."}),
    }
    assert get_trips(fake_event) == expected_response
