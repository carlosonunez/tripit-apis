"""
We use a table in DynamoDB to map API access keys to access tokens and
token secrets.

This creates a mock model that we can use to confirm that auth functions created
this relationship.
"""

import pytest
from pynamodb.exceptions import TransactWriteError
from tripit.auth.models import TripitAccessToken
from tripit.logging import logger


@pytest.fixture
def query_access_token_table():
    """
    Retrieves request tokens associated with an access key.
    """

    def _run(access_key):
        try:
            item = TripitAccessToken.get(access_key)
            return {
                "access_key": item.access_key,
                "token": item.token,
                "token_secret": item.token_secret,
            }
        except TripitAccessToken.DoesNotExist:
            logger.error("Key not found during test: %s", access_key)

    return _run


@pytest.fixture
def set_access_token_table():
    """
    Allows you to create a mock access key to request token/secret pair mapping.
    """

    def _run(access_key, token, secret):
        try:
            TripitAccessToken.insert(access_key, token, secret)
        except TransactWriteError:
            logger.error("Failed to mock a request token mapping for %s", access_key)

    return _run


@pytest.fixture
def drop_access_token_table():
    """
    Deletes a mock access token table to guarantee a clean set of data
    in follow-on tests.
    """

    def _run():
        TripitAccessToken.delete_table()

    return _run
