"""Config to setup pytest."""

# https://docs.pytest.org/en/stable/fixture.html
# You can use this fixture object in your entire test suite.

# @pytest.fixture
# def example():
#     ...       # setup code
#     yield x   # yield instead of return to use setup/teardown structure
#     ...       # teardown code


import os

import pytest


def pytest_collection_modifyitems(config, items):
    """Ignore tests if CHORALEDB_PATH is not set."""
    # Define the required environment variable name
    required_env_var = "CHORALEDB_PATH"

    # Check if the required environment variable is set
    if not os.getenv(required_env_var):
        # If not set, remove all tests in the specified file from collection
        target_file = "test_data.py"

        items[:] = [item for item in items if target_file not in str(item.fspath)]
