"""
We use a table in DynamoDB to map API access keys to request tokens and
token secrets.

This creates a mock model that we can use to confirm that auth functions created
this relationship.
"""

import os
import socket
import time
import urllib.parse
import pytest
import timeout_decorator
from tripit.auth.models import TripitRequestToken
from tripit.logging import logger


@timeout_decorator.timeout(5, use_signals=False)
@pytest.fixture(scope="session", autouse=True)
def wait_for_persistence():
    """
    Ensure that the endpoint that we are using for persisting tokens is available before running
    any tests.
    """
    ddb_parts = urllib.parse.urlparse(os.environ.get("AWS_DYNAMODB_ENDPOINT_URL"))
    ddb_host = ddb_parts.netloc.split(":")[0]
    ddb_port = ddb_parts.netloc.split(":")[1]
    while True:
        ddb_socket = socket.socket()
        try:
            ddb_socket.connect((ddb_host, int(ddb_port)))
            ddb_socket.close()
            break
        except socket.error:
            logger.warning("Failed to connect to persistence at %s.", ddb_parts.netloc)
            time.sleep(1)
            continue


@pytest.fixture
def query_request_token_table():
    """
    Retrieves request tokens associated with an access key.
    """

    def _run(access_key):
        try:
            return TripitRequestToken.get(access_key)
        except TripitRequestToken.DoesNotExist:
            logger.error("Key not found during test: %s", access_key)

    return _run
