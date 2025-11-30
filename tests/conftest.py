"""Pytest configuration and shared fixtures."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_dir():
    """Temporary directory for test files."""
    dirpath = Path(tempfile.mkdtemp())
    yield dirpath
    shutil.rmtree(dirpath)


@pytest.fixture(autouse=True, scope="function")
def mock_version_check(request):
    """Automatically mock syslog-ng version check for all tests except version_check tests.

    This prevents tests from failing when syslog-ng is not installed or has incompatible version.
    The version_check tests themselves skip this by using direct patches.
    """
    # Skip mocking for version_check tests - they handle their own mocking
    # We need to check the actual file path to be robust across pytest configurations
    test_file = str(request.node.fspath) if hasattr(request.node, "fspath") else ""

    # Skip if this is a version_check test file
    if "test_version_check.py" in test_file:
        yield
        return

    # Mock the version check to return a known working version
    # Note: This mock is at the CLI level, so version_check tests that directly
    # test the check_syslog_ng_version function aren't affected
    with patch(
        "patterndb_yaml.cli.check_syslog_ng_version",
        return_value="4.10.1",
    ):
        yield
