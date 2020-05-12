"""
Helper tests.
"""
import pytest
from tripit.helpers import sort_dict


@pytest.mark.unit
def test_sort_dict():
    """ Test that we can sort dictionaries. """
    dict_under_test = {'z': 4, 'b': 10, 'a': 20}
    expected = {'a': 20, 'b': 10, 'z': 4}
    assert(sort_dict(dict_under_test)) == expected
