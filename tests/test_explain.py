"""Tests for explain functionality.

Tests the --explain feature which shows diagnostic messages to stderr
explaining why lines were processed.
"""

from io import StringIO

import pytest

from patterndb_yaml.patterndb_yaml import PatterndbYaml


@pytest.mark.unit
class TestExplainBasic:
    """Test basic explain functionality."""

    def test_explain_disabled_by_default(self, tmp_path, capsys):
        """Explain mode is disabled by default."""
        # Create rules file
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text("rules: []")

        processor = PatterndbYaml(rules_file, explain=False)
        input_stream = StringIO("test line\n")
        output = StringIO()
        processor.process(input_stream, output)

        # No stderr output when explain is disabled
        captured = capsys.readouterr()
        assert "EXPLAIN:" not in captured.err

    def test_explain_enabled(self, tmp_path, capsys):
        """Explain mode shows messages to stderr."""
        # Create rules file
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text("rules: []")

        processor = PatterndbYaml(rules_file, explain=True)
        input_stream = StringIO("test line\n")
        output = StringIO()

        # Process to trigger explain messages
        processor.process(input_stream, output)

        # Check that explain messages appear in stderr
        captured = capsys.readouterr()
        assert "EXPLAIN:" in captured.err
        # With empty rules, line doesn't match any pattern
        assert "No pattern matched" in captured.err

    def test_explain_message_format(self, tmp_path, capsys):
        """Explain messages have correct format."""
        # Create rules file
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text("rules: []")

        processor = PatterndbYaml(rules_file, explain=True)
        input_stream = StringIO("test line\n")
        output = StringIO()

        # Process to trigger explain messages
        processor.process(input_stream, output)

        captured = capsys.readouterr()
        # Check format: "EXPLAIN: [Line X] message"
        assert "EXPLAIN: [Line 1]" in captured.err

    def test_explain_does_not_affect_output(self, tmp_path, capsys):
        """Explain mode doesn't change stdout output."""
        # Create rules file
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text("rules: []")

        input_data = "test line\n"

        # Run without explain
        processor1 = PatterndbYaml(rules_file, explain=False)
        input1 = StringIO(input_data)
        output1 = StringIO()
        processor1.process(input1, output1)

        # Run with explain
        processor2 = PatterndbYaml(rules_file, explain=True)
        input2 = StringIO(input_data)
        output2 = StringIO()
        processor2.process(input2, output2)

        # Clear stderr
        capsys.readouterr()

        # Outputs should be identical
        assert output1.getvalue() == output2.getvalue()
