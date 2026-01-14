"""Pytest configuration and shared fixtures."""

import pytest
from testiq.analyzer import CoverageDuplicateFinder

# Test file constants to avoid duplication
AUTH_FILE = "auth.py"
USER_FILE = "user.py"
FILE_PY = "file.py"
UTILS_FILE = "utils.py"


@pytest.fixture
def sample_coverage_data():
    """Sample coverage data for testing."""
    return {
        "test_login": {
            AUTH_FILE: [10, 11, 12, 15, 20],
            USER_FILE: [5, 6, 7]
        },
        "test_logout": {
            AUTH_FILE: [10, 11, 12, 15, 16],
            USER_FILE: [5, 6]
        },
        "test_signup": {
            AUTH_FILE: [10, 11, 25, 26],
            "user.py": [5, 6, 7, 8, 9]
        }
    }


@pytest.fixture
def finder():
    """Create a fresh CoverageDuplicateFinder instance."""
    return CoverageDuplicateFinder()


@pytest.fixture
def finder_with_data(finder, sample_coverage_data):
    """Finder instance pre-loaded with sample data."""
    for test_name, coverage in sample_coverage_data.items():
        finder.add_test_coverage(test_name, coverage)
    return finder


@pytest.fixture
def duplicate_coverage_data():
    """Coverage data with exact duplicates for testing."""
    return {
        "test_dup_1": {FILE_PY: [1, 2, 3]},
        "test_dup_2": {FILE_PY: [1, 2, 3]},
        "test_unique_1": {FILE_PY: [1, 2, 3, 4, 5]},
        "test_unique_2": {FILE_PY: [10, 11, 12]}
    }


@pytest.fixture
def subset_coverage_data():
    """Coverage data with subset relationships for testing."""
    return {
        "test_short": {UTILS_FILE: [1, 2]},
        "test_long": {UTILS_FILE: [1, 2, 3, 4, 5]},
        "test_medium": {UTILS_FILE: [1, 2, 3]}
    }
