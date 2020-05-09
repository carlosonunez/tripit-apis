"""
Fixtures and stuff.
"""

# This is a magic variable used by Pytest to load modularized fixtures.
# pylint: disable=invalid-name
pytest_plugins = [
    "tests.fixtures.autoload.wait_for_persistence",
    "tests.fixtures.unit.fake_response",
    "tests.fixtures.unit.token_state_table",
    "tests.fixtures.unit.access_token_state_table",
    "tests.fixtures.unit.show_as_human_readable_date",
    "tests.fixtures.integration.aws_api_gateway",
]
