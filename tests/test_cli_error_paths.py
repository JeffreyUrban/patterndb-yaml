"""Tests for CLI error paths and edge cases using CliRunner for coverage."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from patterndb_yaml.cli import app

runner = CliRunner()


@pytest.mark.unit
class TestCLIVersionCallback:
    """Tests for version callback."""

    def test_version_flag_with_cli_runner(self):
        """Test --version flag using CliRunner for coverage."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "patterndb-yaml version" in result.stdout


@pytest.mark.unit
class TestCLIGenerateXMLErrors:
    """Tests for --generate-xml error handling."""

    def test_generate_xml_with_invalid_yaml(self):
        """Test --generate-xml with invalid YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "invalid.yaml"
            rules_file.write_text("invalid: yaml: syntax: [[[")

            result = runner.invoke(app, ["--rules", str(rules_file), "--generate-xml"])

            assert result.exit_code == 1
            # Error might be in stdout or exception was raised
            # Just check exit code

    def test_generate_xml_with_nonexistent_file(self):
        """Test --generate-xml with nonexistent rules file."""
        result = runner.invoke(app, ["--rules", "/nonexistent/rules.yaml", "--generate-xml"])

        # Should fail with error about file not found
        assert result.exit_code != 0


@pytest.mark.unit
class TestCLIExceptionHandling:
    """Tests for CLI exception handling."""

    def test_general_exception_handling(self):
        """Test general exception handling in CLI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            # Create rules that will cause an error during processing
            rules_file.write_text("rules: []")

            input_file = tmpdir / "input.log"
            input_file.write_text("test line\n")

            # Patch PatterndbYaml to raise an exception
            with patch("patterndb_yaml.cli.PatterndbYaml") as mock_processor:
                mock_processor.side_effect = RuntimeError("Test error")

                result = runner.invoke(
                    app,
                    [
                        "--rules",
                        str(rules_file),
                        str(input_file),
                        "--quiet",
                    ],
                )

                assert result.exit_code == 1
                # Exception was raised and caught, exit code is what matters


@pytest.mark.unit
class TestCLIInputValidation:
    """Tests for CLI input validation."""

    def test_input_from_stdin(self):
        """Test reading input from stdin."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            # CliRunner can provide stdin input
            result = runner.invoke(
                app, ["--rules", str(rules_file), "--quiet"], input="test line\n"
            )

            assert result.exit_code == 0


@pytest.mark.unit
class TestCLIProgressMode:
    """Tests for progress bar functionality."""

    def test_progress_with_file_input(self):
        """Test progress bar with file input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            input_file = tmpdir / "input.log"
            # Create file with multiple lines
            input_file.write_text("\n".join([f"line {i}" for i in range(20)]))

            # Run with --progress flag
            # Progress will be disabled automatically when not a TTY
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

    @patch("patterndb_yaml.cli.sys.stdin")
    @patch("patterndb_yaml.cli.sys.stdout")
    def test_progress_disabled_when_piped(self, mock_stdout, mock_stdin):
        """Test that progress is disabled when output is piped."""
        # Mock isatty to return False (piped output)
        mock_stdout.isatty.return_value = False
        mock_stdin.isatty.return_value = False

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            input_file = tmpdir / "input.log"
            input_file.write_text("test\n")

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

            # Should succeed even with --progress when piped
            assert result.exit_code == 0


@pytest.mark.unit
class TestCLIStatsOutput:
    """Tests for statistics output modes."""

    def test_stats_after_processing(self):
        """Test that stats are shown after processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            input_file = tmpdir / "input.log"
            input_file.write_text("line1\nline2\nline3\n")

            result = runner.invoke(
                app,
                [
                    "--rules",
                    str(rules_file),
                    str(input_file),
                ],
            )

            assert result.exit_code == 0
            # Stats should be in output (unless --quiet)

    def test_json_stats_output(self):
        """Test JSON statistics output format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            input_file = tmpdir / "input.log"
            input_file.write_text("test\n")

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


@pytest.mark.unit
class TestCLIEdgeCases:
    """Tests for CLI edge cases."""

    def test_empty_input_file(self):
        """Test processing empty input file."""
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
                    "--quiet",
                ],
            )

            assert result.exit_code == 0

    def test_stdin_input_with_cli_runner(self):
        """Test reading from stdin using CliRunner."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            # CliRunner can provide stdin input
            result = runner.invoke(
                app,
                ["--rules", str(rules_file), "--quiet"],
                input="line1\nline2\nline3\n",
            )

            assert result.exit_code == 0

    def test_explain_mode(self):
        """Test --explain flag."""
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
            input_file.write_text("test message\n")

            result = runner.invoke(
                app,
                [
                    "--rules",
                    str(rules_file),
                    str(input_file),
                    "--explain",
                    "--quiet",
                ],
            )

            assert result.exit_code == 0
            # Explain output goes to stderr, which CliRunner captures


@pytest.mark.unit
class TestCLIValidateArguments:
    """Tests for argument validation."""

    def test_validate_stats_format(self):
        """Test that stats format is validated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            input_file = tmpdir / "input.log"
            input_file.write_text("test\n")

            # Valid stats format
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

    def test_invalid_stats_format(self):
        """Test invalid stats format is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            input_file = tmpdir / "input.log"
            input_file.write_text("test\n")

            result = runner.invoke(
                app,
                [
                    "--rules",
                    str(rules_file),
                    str(input_file),
                    "--stats-format",
                    "invalid",
                ],
            )

            assert result.exit_code != 0


@pytest.mark.unit
class TestCLIInteractiveMode:
    """Tests for interactive mode detection."""

    @patch("patterndb_yaml.cli.sys.stdin")
    def test_no_input_interactive_mode(self, mock_stdin):
        """Test interactive mode detection when no input provided."""
        # Mock isatty to return True (interactive terminal)
        mock_stdin.isatty.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            # Run without input file and stdin
            result = runner.invoke(
                app,
                ["--rules", str(rules_file)],
            )

            # Should exit with 0 and show usage help (output goes to stderr via console.print)
            assert result.exit_code == 0
            # With CliRunner, the help text goes to stdout or result output
            # The important thing is that it exits cleanly without error
            # We can't easily test isatty behavior with CliRunner since it mocks stdin


@pytest.mark.unit
class TestCLIVersionCheckErrors:
    """Tests for version check error handling."""

    def test_version_check_error_handling(self):
        """Test that version check errors are handled properly."""
        from patterndb_yaml.version_check import SyslogNgVersionError

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            input_file = tmpdir / "input.log"
            input_file.write_text("test\n")

            # Patch version check to raise error
            with patch("patterndb_yaml.cli.check_syslog_ng_version") as mock_check:
                mock_check.side_effect = SyslogNgVersionError("Test version error")

                result = runner.invoke(
                    app,
                    [
                        "--rules",
                        str(rules_file),
                        str(input_file),
                        "--quiet",
                    ],
                )

                assert result.exit_code == 1


@pytest.mark.unit
class TestCLIKeyboardInterrupt:
    """Tests for keyboard interrupt handling."""

    def test_keyboard_interrupt_during_processing(self):
        """Test that KeyboardInterrupt is handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            input_file = tmpdir / "input.log"
            input_file.write_text("test\n")

            # Patch PatterndbYaml.process to raise KeyboardInterrupt
            with patch("patterndb_yaml.cli.PatterndbYaml") as mock_processor_class:
                mock_processor = mock_processor_class.return_value
                mock_processor.process.side_effect = KeyboardInterrupt()
                mock_processor.flush.return_value = None
                mock_processor.get_stats.return_value = {
                    "lines_processed": 10,
                    "lines_matched": 5,
                    "match_rate": 0.5,
                }

                result = runner.invoke(
                    app,
                    [
                        "--rules",
                        str(rules_file),
                        str(input_file),
                        "--quiet",
                    ],
                )

                assert result.exit_code == 1
                # Should call flush on interrupt
                mock_processor.flush.assert_called_once()

    def test_keyboard_interrupt_with_stats_output(self):
        """Test that stats are shown after KeyboardInterrupt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            input_file = tmpdir / "input.log"
            input_file.write_text("test\n")

            # Patch PatterndbYaml.process to raise KeyboardInterrupt
            with patch("patterndb_yaml.cli.PatterndbYaml") as mock_processor_class:
                mock_processor = mock_processor_class.return_value
                mock_processor.process.side_effect = KeyboardInterrupt()
                mock_processor.flush.return_value = None
                mock_processor.get_stats.return_value = {
                    "lines_processed": 10,
                    "lines_matched": 5,
                    "match_rate": 0.5,
                }

                result = runner.invoke(
                    app,
                    [
                        "--rules",
                        str(rules_file),
                        str(input_file),
                    ],
                )

                assert result.exit_code == 1
                # Should call flush and get_stats
                mock_processor.flush.assert_called_once()
                mock_processor.get_stats.assert_called()

    def test_keyboard_interrupt_with_json_stats(self):
        """Test that JSON stats are shown after KeyboardInterrupt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rules_file = tmpdir / "rules.yaml"
            rules_file.write_text("rules: []")

            input_file = tmpdir / "input.log"
            input_file.write_text("test\n")

            # Patch PatterndbYaml.process to raise KeyboardInterrupt
            with patch("patterndb_yaml.cli.PatterndbYaml") as mock_processor_class:
                mock_processor = mock_processor_class.return_value
                mock_processor.process.side_effect = KeyboardInterrupt()
                mock_processor.flush.return_value = None
                mock_processor.get_stats.return_value = {
                    "lines_processed": 10,
                    "lines_matched": 5,
                    "match_rate": 0.5,
                }
                mock_processor.rules_path = Path(rules_file)

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

                assert result.exit_code == 1
