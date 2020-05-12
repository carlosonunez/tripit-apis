"""
We need our local DynamoDB instance to be active in order to
test things that use persistence.
"""

import os
import socket
import time
import urllib.parse
import pytest
import timeout_decorator
from tripit.logging import logger


@timeout_decorator.timeout(5, use_signals=False)
@pytest.fixture(scope="session", autouse=True)
def wait_for_persistence():
    """
    Ensure that the endpoint that we are using for persisting tokens is available before running
    any tests.
    """
    if not os.environ.get("AWS_DYNAMODB_ENDPOINT_URL"):
        return True
    db_parts = urllib.parse.urlparse(os.environ.get("AWS_DYNAMODB_ENDPOINT_URL"))
    db_host = db_parts.netloc.split(":")[0]
    db_port = db_parts.netloc.split(":")[1]
    while True:
        db_socket = socket.socket()
        try:
            logger.info("Connected to persistence at %s", db_parts.netloc)
            db_socket.connect((db_host, int(db_port)))
            db_socket.close()
            break
        except socket.error:
            logger.warning("Failed to connect to persistence at %s.", db_parts.netloc)
            time.sleep(1)
            continue
