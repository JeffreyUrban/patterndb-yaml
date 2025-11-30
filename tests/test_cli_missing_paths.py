"""Tests for CLI missing coverage paths."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from patterndb_yaml.cli import app

runner = CliRunner()


@pytest.mark.unit
class TestCLIInteractiveMode:
    """Tests for interactive mode (no input, TTY)."""

    def test_interactive_with_stdin_input(self):
        """Test with stdin input via CliRunner."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            # CliRunner provides stdin input, avoiding TTY check
            result = runner.invoke(
                app, ["--rules", str(rules_file), "--quiet"], input="line1\\nline2\\n"
            )

            # Should succeed
            assert result.exit_code == 0


@pytest.mark.unit
class TestCLIProgressBar:
    """Tests for progress bar functionality."""

    @patch("patterndb_yaml.cli.sys.stdout")
    def test_progress_with_file_and_tty(self, mock_stdout):
        """Test progress bar with file input and TTY output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            input_file = tmpdir / "input.log"
            input_file.write_text("\\n".join([f"line {i}" for i in range(100)]))

            # Mock stdout.isatty to return True (for progress bar)
            mock_stdout.isatty.return_value = True

            result = runner.invoke(
                app,
                [
                    "--rules",
                    str(rules_file),
                    str(input_file),
                    "--progress",
                    "--quiet",
                ],
            )

            assert result.exit_code == 0

    @patch("patterndb_yaml.cli.sys.stdout")
    def test_progress_with_stdin_and_tty(self, mock_stdout):
        """Test progress bar with stdin input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            # Mock stdout.isatty to return True
            mock_stdout.isatty.return_value = True

            result = runner.invoke(
                app,
                ["--rules", str(rules_file), "--progress", "--quiet"],
                input="line 1\\nline 2\\nline 3\\n",
            )

            assert result.exit_code == 0


@pytest.mark.unit
class TestCLIKeyboardInterrupt:
    """Tests for KeyboardInterrupt handling."""

    def test_keyboard_interrupt_during_processing(self):
        """Test KeyboardInterrupt during line processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            input_file = tmpdir / "input.log"
            input_file.write_text("line1\\nline2\\nline3\\n")

            # Patch processor.process to raise KeyboardInterrupt
            with patch("patterndb_yaml.cli.PatterndbYaml") as mock_class:
                mock_processor = Mock()
                mock_processor.process.side_effect = KeyboardInterrupt()
                mock_processor.get_stats.return_value = {
                    "lines_processed": 2,
                    "lines_matched": 1,
                    "match_rate": 0.5,
                }
                mock_class.return_value = mock_processor

                result = runner.invoke(
                    app,
                    [
                        "--rules",
                        str(rules_file),
                        str(input_file),
                    ],
                )

                # Should exit with code 1
                assert result.exit_code == 1

                # flush should be called
                mock_processor.flush.assert_called_once()


@pytest.mark.unit
class TestCLIStatsFormatting:
    """Tests for statistics output formatting."""

    def test_stats_table_output(self):
        """Test table format statistics output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_content = """
rules:
  - name: test_rule
    pattern:
      - field: message
    output: "Test: {message}"
"""
            rules_file.write_text(rules_content)

            input_file = tmpdir / "input.log"
            input_file.write_text("line1\\nline2\\nline3\\n")

            result = runner.invoke(
                app,
                [
                    "--rules",
                    str(rules_file),
                    str(input_file),
                    "--stats-format",
                    "table",
                ],
            )

            assert result.exit_code == 0
            # Stats should appear in stderr (which CliRunner doesn't capture separately)

    def test_stats_json_output(self):
        """Test JSON format statistics output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_content = """
rules:
  - name: test_rule
    pattern:
      - field: message
    output: "Test: {message}"
"""
            rules_file.write_text(rules_content)

            input_file = tmpdir / "input.log"
            input_file.write_text("line1\\nline2\\nline3\\n")

            result = runner.invoke(
                app,
                [
                    "--rules",
                    str(rules_file),
                    str(input_file),
                    "--stats-format",
                    "json",
                ],
            )

            assert result.exit_code == 0

    def test_stats_no_lines_processed(self):
        """Test statistics when no lines are processed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            input_file = tmpdir / "input.log"
            input_file.write_text("")  # Empty file

            result = runner.invoke(
                app,
                [
                    "--rules",
                    str(rules_file),
                    str(input_file),
                ],
            )

            assert result.exit_code == 0


@pytest.mark.unit
class TestCLIGenerateXMLExceptions:
    """Tests for --generate-xml exception paths."""

    def test_generate_xml_empty_rules(self):
        """Test --generate-xml with empty/minimal rules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"

            # Write minimal valid rules (empty rules list)
            rules_file.write_text("rules: []")

            # Should succeed and generate XML
            result = runner.invoke(app, ["--rules", str(rules_file), "--generate-xml"])

            # Should succeed
            assert result.exit_code == 0
            assert '<?xml version="1.0"' in result.stdout

    def test_generate_xml_generation_error(self):
        """Test --generate-xml with XML generation error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            # Patch generate_from_yaml to raise an exception
            with patch("patterndb_yaml.cli.generate_from_yaml") as mock_gen:
                mock_gen.side_effect = ValueError("Test generation error")

                result = runner.invoke(app, ["--rules", str(rules_file), "--generate-xml"])

                assert result.exit_code == 1


@pytest.mark.unit
class TestCLIValidateArguments:
    """Tests for argument validation."""

    def test_invalid_stats_format(self):
        """Test validation of invalid stats format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            input_file = tmpdir / "input.log"
            input_file.write_text("test\\n")

            result = runner.invoke(
                app,
                [
                    "--rules",
                    str(rules_file),
                    str(input_file),
                    "--stats-format",
                    "invalid_format",
                ],
            )

            # Should fail due to validation
            assert result.exit_code != 0


@pytest.mark.unit
class TestCLIProcessWithoutProgress:
    """Tests for processing without progress bar."""

    def test_process_file_without_progress(self):
        """Test processing file without progress bar."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_content = """
rules:
  - name: test_rule
    pattern:
      - field: message
    output: "{message}"
"""
            rules_file.write_text(rules_content)

            input_file = tmpdir / "input.log"
            input_file.write_text("\\n".join([f"line {i}" for i in range(10)]))

            result = runner.invoke(
                app,
                [
                    "--rules",
                    str(rules_file),
                    str(input_file),
                    "--quiet",
                ],
            )

            assert result.exit_code == 0
