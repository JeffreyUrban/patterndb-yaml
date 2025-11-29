"""Tests for CLI statistics printing."""

import pytest

from patterndb_yaml.cli import print_stats
from patterndb_yaml.patterndb_yaml import PatterndbYaml


@pytest.mark.unit
def test_print_stats_normal(tmp_path):
    """Test print_stats with normal processor."""
    # Create rules file
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text("rules: []")

    processor = PatterndbYaml(rules_file)

    # print_stats writes to stderr via rich Console
    # Just verify it doesn't crash
    print_stats(processor)


@pytest.mark.unit
def test_print_stats_empty(tmp_path):
    """Test print_stats with no lines processed."""
    # Create rules file
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text("rules: []")

    processor = PatterndbYaml(rules_file)

    # print_stats should handle empty stats
    print_stats(processor)
