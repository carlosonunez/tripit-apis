"""
These functions test the helpers I wrote for returning messages
from AWS API gatweay.
"""
import json
import pytest
from tripit.cloud_helpers.aws.api_gateway import (
    return_ok,
    return_error,
    return_unauthenticated,
    return_not_found,
)


@pytest.mark.unit
def test_ok_with_no_message():
    """
    Test returning basic successful API calls.
    """
    assert return_ok() == {"statusCode": 200, "body": json.dumps({"status": "ok"})}


@pytest.mark.unit
def test_ok_with_message():
    """
    Tests returning basic successful API calls with messages attached.
    """
    assert return_ok(message="Howdy") == {
        "statusCode": 200,
        "body": json.dumps({"status": "ok", "message": "Howdy"}),
    }


@pytest.mark.unit
def test_error():
    """
    Tests yielding errors
    """
    assert return_error(message="Howdy") == {
        "statusCode": 400,
        "body": json.dumps({"status": "error", "message": "Howdy"}),
    }


@pytest.mark.unit
def test_unauthenticated_without_message():
    """
    Tests generic unauthenticated responses
    """
    assert return_unauthenticated() == {
        "statusCode": 403,
        "body": json.dumps({"status": "error", "message": "Access denied."}),
    }


@pytest.mark.unit
def test_unauthenticated_with_message():
    """
    Tests non-generic unauthenticated responses
    """
    assert return_unauthenticated("Nope") == {
        "statusCode": 403,
        "body": json.dumps({"status": "error", "message": "Nope"}),
    }


@pytest.mark.unit
def test_not_found():
    """
    Tests response when something wasn't found
    """
    assert return_not_found("Not found") == {
        "statusCode": 404,
        "body": json.dumps({"status": "error", "message": "Not found"}),
    }
