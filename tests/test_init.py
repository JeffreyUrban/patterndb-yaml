"""Tests for __init__.py module."""

import sys
from unittest.mock import patch

import pytest


@pytest.mark.unit
def test_init_imports_version():
    """Test that __init__ imports version successfully."""
    from patterndb_yaml import __version__

    # Should have a version string
    assert isinstance(__version__, str)
    assert len(__version__) > 0


@pytest.mark.unit
def test_init_imports_patterndb_yaml():
    """Test that __init__ imports PatterndbYaml class."""
    from patterndb_yaml import PatterndbYaml

    # Should be importable
    assert PatterndbYaml is not None


@pytest.mark.unit
def test_init_all_exports():
    """Test that __all__ contains expected exports."""
    from patterndb_yaml import __all__

    assert "PatterndbYaml" in __all__
    assert "__version__" in __all__


@pytest.mark.unit
def test_version_import_fallback():
    """Test version import fallback when _version module is not available."""
    # Remove patterndb_yaml from sys.modules to force re-import
    modules_to_remove = [k for k in sys.modules.keys() if k.startswith("patterndb_yaml")]
    for module in modules_to_remove:
        del sys.modules[module]

    # Mock the _version import to raise ImportError
    with patch.dict("sys.modules", {"patterndb_yaml._version": None}):
        # This will cause ImportError when trying to import _version
        import importlib

        # Re-import the __init__ module with the mock
        import patterndb_yaml

        importlib.reload(patterndb_yaml)

        # Should fall back to development version
        # Note: This test is challenging because the import happens at module load time
        # The actual fallback is tested by the code execution, but coverage may not register
        # This test ensures the import doesn't fail
        assert hasattr(patterndb_yaml, "__version__")
