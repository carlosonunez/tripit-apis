"""
This is code that handles step 2 of the authentication process.

See the test for this file in tests/unit for more info.
"""


def handle_callback(access_key, access_token, token_secret):
    """
    Handles TripIt callbacks and persists access tokens with access keys for
    future use.
    """
