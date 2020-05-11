"""
API endpoint for authorizing one's access key for use with TripIt.
"""

import pytest
from tripit.api.aws_api_gateway.auth import begin_authentication
from tripit.cloud_helpers.aws.api_gateway import return_ok


@pytest.mark.unit
# pylint: disable=bad-continuation
def test_begin_authentication_endpoint(
    monkeypatch, query_request_token_table, drop_request_token_table
):
    # pylint: enable=bad-continuation
    """
    Ensure that we can get an authorization URL from this endpoint.
    We'll only test the happy path where our access key doesn't have any tokens yet,
    since the other paths are covered in tests/unit/auth/step_1.
    """
    monkeypatch.setattr(
        "tripit.core.v1.oauth.fetch_token",
        lambda: {"token": "fake_request_token", "token_secret": "fake-secret"},
    )
    fake_event = {
        "requestContext": {"path": "/develop/auth", "identity": {"apiKey": "fake-key"},},
        "headers": {"Host": "example.fake"},
    }
    expected_message = "".join(
        [
            "You will need to authenticate into TripIt first; ",
            "click on or copy/paste this URL to get started: ",
            "https://www.tripit.com/oauth/authorize?oauth_token=fake_request_token&",
            "oauth_callback=https://example.fake/develop/callback",
        ]
    )
    expected_response = return_ok(message=expected_message)
    assert begin_authentication(fake_event, None) == expected_response
    request_token_mapping = query_request_token_table("fake_request_token")
    assert request_token_mapping == {
        "access_key": "fake-key",
        "token": "fake_request_token",
        "token_secret": "fake-secret",
    }
    drop_request_token_table()
