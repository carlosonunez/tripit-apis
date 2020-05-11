"""
API endpoint for handling callbacks from TripIt.
"""

import json
import pytest
from tripit.api.aws_api_gateway.callback import callback


@pytest.mark.unit
# pylint: disable=bad-continuation
def test_callback_endpoint(
    monkeypatch,
    set_request_token_table,
    query_access_token_table,
    drop_request_token_table,
    drop_access_token_table,
):
    # pylint: enable=bad-continuation
    """
    Ensure that we can handle callbacks.

    See the test for handle_callback for more info.
    """
    monkeypatch.setattr(
        "tripit.core.v1.oauth.fetch_token",
        lambda *args, **kwargs: {"token": "access-token", "token_secret": "token-secret"},
    )
    set_request_token_table(
        access_key="fake-key", token="request-token", secret="request-token-secret"
    )
    fake_event = {
        "requestContext": {"path": "/develop/callback", "identity": {"apiKey": "fake-key"},},
        "queryStringParameters": {"oauth_token": "request-token"},
        "headers": {"Host": "example.fake"},
    }
    expected_response = {
        "statusCode": 200,
        "body": json.dumps({"status": "ok"}),
    }
    assert callback(fake_event) == expected_response
    assert query_access_token_table(access_key="fake-key") == {
        "access_key": "fake-key",
        "token": "access-token",
        "token_secret": "token-secret",
    }
    drop_request_token_table()
    drop_access_token_table()
