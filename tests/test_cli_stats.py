"""Tests for CLI statistics printing."""

import pytest

from patterndb_yaml.cli import print_stats
from patterndb_yaml.patterndb_yaml import PatterndbYaml


@pytest.mark.unit
def test_print_stats_normal():
    """Test print_stats with normal processor."""
    processor = PatterndbYaml()

    # print_stats writes to stderr via rich Console
    # Just verify it doesn't crash
    print_stats(processor)


@pytest.mark.unit
def test_print_stats_empty():
    """Test print_stats with no lines processed."""
    processor = PatterndbYaml()

    # print_stats should handle empty stats
    print_stats(processor)
