"""
These functions test the helpers I wrote for returning messages
from AWS API gatweay.
"""
import pytest
from aws_helpers import api_gateway


@pytest.mark.unit
def test_ok_with_no_message():
    """
    Test returning basic successful API calls.
    """
    assert ok() == {'status': 'ok'}
