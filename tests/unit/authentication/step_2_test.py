"""
These are the tests for step 2 of the authentication flow.

Once we've manually authorized our account to use the TripIt API, TripIt will provide the
access token and token secret to the callback function.

Once we receive this token, we need to associate it with our access key in the database.

Once that's done, that access key should be authenticated for all future TripIt calls for
as long as the access token/secret pair is active.
"""

import pytest
from tripit.auth.step_2 import handle_callback


@pytest.mark.unit
# pylint: disable=bad-continuation
def test_callbacks_when_access_key_has_token(
    query_access_token_table, set_request_token_table, drop_access_token_table
):
    # pylint: enable=bad-continuation
    """
    This is step 2 of the authentication process. TripIt will provide our token to
    this callback handler in the URL as query parameters. The token secret
    is the same as the secret we retrieved in step 1.
    """
    access_key = "fake-key"
    request_token = "fake-request-token"
    request_token_secret = "fake-request-token-secret"
    set_request_token_table(access_key, request_token, request_token_secret)

    access_token_from_tripit = "access-token"
    assert handle_callback(access_key, access_token_from_tripit, request_token_secret) is None
    assert query_access_token_table(access_key="fake-key") == {
        "access_key": access_key,
        "access_token": access_token_from_tripit,
        "access_token_secret": "token-secret",
    }
    drop_access_token_table()
