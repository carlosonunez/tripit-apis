"""
These functions test the helpers I wrote for returning messages
from AWS API gatweay.
"""
import json
import pytest
from aws_helpers.api_gateway import return_ok


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
    assert return_ok(message="Howdy") == {"statusCode": 200,
                                          "body": json.dumps({"status": "ok",
                                                              "message": "Howdy"})}
