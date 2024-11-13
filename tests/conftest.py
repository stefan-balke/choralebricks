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
    """Test if CHORALEDB_PATH is set or skip the test."""
    # Define the required environment variable name
    required_env_var = "CHORALEDB_PATH"

    # Check if the required environment variable is set
    if not os.getenv(required_env_var):
        # If not set, skip all collected tests
        skip_reason = f"Environment variable '{required_env_var}' is not set. Skipping tests."
        skip_marker = pytest.mark.skip(reason=skip_reason)
        
        target_file = "test_data.py"

        for item in items:
            # Check if the test belongs to the specified file
            if target_file in str(item.fspath):
                item.add_marker(skip_marker)
