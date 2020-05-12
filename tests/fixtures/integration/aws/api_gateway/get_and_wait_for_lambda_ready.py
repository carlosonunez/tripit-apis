"""
We might get 403 Forbidden's while Lambda starts up.
This waits for them to clear out.
"""
import time
import pytest
import requests
import timeout_decorator


@pytest.fixture()
@timeout_decorator.timeout(5)
def get_and_wait_for_lambda_ready():
    """
    See module doc.
    """

    def _run(url, access_key=None):
        while True:
            headers = {}
            if access_key:
                headers = {"x-api-key": access_key}
            response = requests.get(url, headers=headers)
            if response.status_code != 403:
                return response
            time.sleep(1)

    return _run
