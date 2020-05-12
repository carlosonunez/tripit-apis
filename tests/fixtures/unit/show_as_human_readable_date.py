"""
Formats dates as human-friendly ones.
"""
from datetime import datetime
import pytest


@pytest.fixture
def show_as_human_readable_date():
    """
    Converts a Unix time to a human readable datetime string.
    """

    def _run(timestamp):
        return datetime.utcfromtimestamp(timestamp).strftime("%a %b %d %H:%M:%S %Y %z UTC")

    return _run
