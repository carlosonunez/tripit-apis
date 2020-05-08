"""
Test for getting/verifying access tokens from access keys.
"""

import pytest
from tripit.auth.token import get_token_data_for_access_key


@pytest.mark.unit
def test_getting_token_data_when_access_key_unauthenticated(caplog):
    """
    If our access key doesn't have a token yet, we shouldn't get a token back.
    """
    assert get_token_data_for_access_key("fake-key") is None
    assert "Access token not created yet for key fake-key" in caplog.text


@pytest.mark.unit
# pylint: disable=bad-continuation
def test_getting_token_data_when_access_key_authenticated(
    set_access_token_table, drop_access_token_table
):
    # pylint: enable=bad-continuation
    """
    If the access key does have a token, then we should get both it and its secret back.
    """
    set_access_token_table(access_key="fake-key", token="fake-token", secret="token-secret")
    assert get_token_data_for_access_key("fake-key") == {
        "token": "fake-token",
        "token_secret": "token-secret",
        "access_key": "fake-key",
    }
    drop_access_token_table()
