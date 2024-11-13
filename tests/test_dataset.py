"""
All tests related to dataset.py and the involved logic.
"""
import pytest
from choralebricks.dataset import SongDB

# TODO: test for voice selection (is the correct track taken?)

def test_import_my_module():
    # Attempt to import the module
    try:
        import choralebricks.dataset
    except ImportError:
        pytest.fail("Importing my_module failed")
