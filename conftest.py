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
    "tests.fixtures.integration.authorize_tripit",
    "tests.fixtures.integration.current_trip",
    "tests.fixtures.integration.aws.api_gateway.create_api_gateway_url",
    "tests.fixtures.integration.aws.api_gateway.get_and_wait_for_lambda_ready",
    "tests.fixtures.integration.aws.api_gateway.access_key",
]
