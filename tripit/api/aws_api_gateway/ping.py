"""
Health checks.
"""
from tripit.cloud_helpers.aws.api_gateway import return_ok


def ping(_event, _context):
    """ If API Gateway is working, we should see an ok back. """
    return return_ok()
