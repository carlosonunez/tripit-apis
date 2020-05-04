"""
AWS fixtures.
"""
import pytest


@pytest.fixture
def mock_dynamodb(monkeypatch):
    """
    Configure DynamoDB to use a local endpoint.
    """
    monkeypatch.setenv("AWS_DYNAMODB_ENDPOINT_URL", "http://dynamodb:9000")
