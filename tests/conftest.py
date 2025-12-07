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
    The version_check tests handle their own mocking completely.
    """
    # Skip mocking for version_check tests - they handle their own mocking
    test_file = str(request.node.fspath) if hasattr(request.node, "fspath") else ""

    if "test_version_check.py" in test_file:
        # Don't apply any mocks - version_check tests handle everything themselves
        yield
        return

    # For other tests, mock at the CLI level to avoid version checks entirely
    with patch(
        "patterndb_yaml.cli.check_syslog_ng_version",
        return_value="4.10.1",
    ):
        yield
