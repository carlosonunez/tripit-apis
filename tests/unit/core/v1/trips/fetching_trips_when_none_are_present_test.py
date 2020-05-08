"""
We shouldn't get anything back when no trips are present.

NOTE:
You might be wondering "`get_from_tripit_v1` belongs in `tripit.core.v1.api`,
but we're patching it from `tripit.trips`. What gives?"

This is due to a limitation of how modules work in Python.

See here: https://alexmarandon.com/articles/python_mock_gotchas/
"""
import pytest
from freezegun import freeze_time
from tripit.trips import get_all_trips


@pytest.mark.unit
@freeze_time("Jan 1 1970 00:01:02")
def test_fetching_trips_when_none_are_present(monkeypatch, fake_response_from_route):
    """ Behold! The test. """

    monkeypatch.setattr("tripit.trips.get_from_tripit_v1", fake_response_from_route)
    assert get_all_trips(token="token", token_secret="token_secret") == []
