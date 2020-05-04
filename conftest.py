"""
Fixtures and stuff.
"""

# This is a magic variable used by Pytest to load modularized fixtures.
# pylint: disable=invalid-name
pytest_plugins = [
    "tests.fixtures.fake_response",
    "tests.fixtures.token_state_table",
]
