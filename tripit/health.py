"""
Healthiness methods
"""
from aws_helpers.api_gateway import return_ok


def ping():
    """
    Returns 200 if everything's fine or the cloud provider will
    (hopefully) return 5xx if not.
    """
    return return_ok(message="sup dawg")
