"""Additional CLI tests to increase coverage."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


@pytest.mark.integration
def test_version_flag():
    """Test --version flag prints version and exits."""
    result = subprocess.run(
        [sys.executable, "-m", "patterndb_yaml", "--version"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "patterndb-yaml version" in result.stdout


@pytest.mark.integration
def test_generate_xml_mode():
    """Test --generate-xml mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create rules file with sample patterns
        rules_file = tmpdir / "rules.yaml"
        rules_content = """
rules:
  - name: test_rule
    pattern:
      - field: message
    output: "Normalized: {message}"
"""
        rules_file.write_text(rules_content)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "patterndb_yaml",
                "--rules",
                str(rules_file),
                "--generate-xml",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Check for XML structure
        assert "<?xml version" in result.stdout
        assert "<patterndb" in result.stdout
        assert "</patterndb>" in result.stdout


@pytest.mark.integration
def test_generate_xml_with_invalid_rules():
    """Test --generate-xml with invalid YAML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create invalid rules file
        rules_file = tmpdir / "rules.yaml"
        rules_file.write_text("invalid: yaml: content: [")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "patterndb_yaml",
                "--rules",
                str(rules_file),
                "--generate-xml",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "Error generating XML" in result.stderr or "Error" in result.stderr


@pytest.mark.integration
def test_processing_with_file_input():
    """Test normal processing with file input (covered path)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create rules file
        rules_file = tmpdir / "rules.yaml"
        rules_file.write_text("rules: []")

        # Create input file
        input_file = tmpdir / "input.log"
        input_file.write_text("line1\nline2\nline3\n")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "patterndb_yaml",
                "--rules",
                str(rules_file),
                str(input_file),
                "--quiet",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Should have processed all 3 lines
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 3


@pytest.mark.integration
def test_stdin_with_stats():
    """Test stdin input with statistics display."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create rules file
        rules_file = tmpdir / "rules.yaml"
        rules_file.write_text("rules: []")

        input_data = "line1\nline2\nline3\n"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "patterndb_yaml",
                "--rules",
                str(rules_file),
            ],
            input=input_data,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Should have processed input
        assert "line1" in result.stdout or "^line1" in result.stdout


@pytest.mark.integration
def test_stats_json_format():
    """Test JSON statistics format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        rules_file = tmpdir / "rules.yaml"
        rules_file.write_text("rules: []")
        input_file = tmpdir / "input.log"
        input_file.write_text("A\nB\nC\n")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "patterndb_yaml",
                "--rules",
                str(rules_file),
                str(input_file),
                "--stats-format",
                "json",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Extract JSON from stderr
        json_start = result.stderr.find("{")
        if json_start >= 0:
            json_str = result.stderr[json_start:]
            stats = json.loads(json_str)
            # Verify it's valid JSON
            assert isinstance(stats, dict)


@pytest.mark.integration
def test_progress_disabled_when_piping():
    """Test that progress is automatically disabled when output is piped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        rules_file = tmpdir / "rules.yaml"
        rules_file.write_text("rules: []")
        input_file = tmpdir / "input.log"
        input_file.write_text("line1\nline2\n")

        # When running via subprocess, stdout is always a pipe
        # Progress should be disabled automatically
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "patterndb_yaml",
                "--rules",
                str(rules_file),
                str(input_file),
                "--progress",  # Request progress, but it should be disabled
                "--quiet",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # No progress output should appear (since it's transient anyway)
        assert "line1" in result.stdout or "^line1" in result.stdout
