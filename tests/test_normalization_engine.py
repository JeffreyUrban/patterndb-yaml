"""Tests for normalization_engine module."""

import tempfile
from pathlib import Path

import pytest
import yaml

from patterndb_yaml.normalization_engine import NormalizationEngine


@pytest.fixture
def simple_rules_file():
    """Create a simple rules file for testing."""
    rules = {
        "rules": [
            {
                "name": "test_rule",
                "pattern": [{"field": "message"}],
                "output": "Test: {message}",
            }
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(rules, f)
        return Path(f.name)


@pytest.fixture
def transform_rules_file():
    """Create rules file with field transforms."""
    rules = {
        "rules": [
            {
                "name": "ansi_rule",
                "pattern": [{"field": "text"}],
                "output": "Cleaned: {text}",
                "field_transforms": {
                    "text": ["strip_ansi", "strip_text_ansi"],
                },
            }
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(rules, f)
        return Path(f.name)


@pytest.mark.unit
class TestNormalizationEngineInit:
    """Tests for NormalizationEngine initialization."""

    def test_engine_initialization(self, simple_rules_file):
        """Test basic engine initialization."""
        engine = NormalizationEngine(simple_rules_file)

        assert engine.rules_path == simple_rules_file
        assert not engine.explain
        assert len(engine.rules) == 1
        assert engine.rules[0]["name"] == "test_rule"

        # Cleanup
        engine.close()

    def test_engine_with_explain_mode(self, simple_rules_file):
        """Test engine initialization with explain mode."""
        engine = NormalizationEngine(simple_rules_file, explain=True)

        assert engine.explain is True

        # Cleanup
        engine.close()


@pytest.mark.unit
class TestParseEncodedMessage:
    """Tests for _parse_encoded_message method."""

    def test_parse_encoded_message_no_brackets(self, simple_rules_file):
        """Test parsing message without brackets."""
        engine = NormalizationEngine(simple_rules_file)

        result = engine._parse_encoded_message("plain text")
        assert result is None

        engine.close()

    def test_parse_encoded_message_malformed(self, simple_rules_file):
        """Test parsing malformed encoded message."""
        engine = NormalizationEngine(simple_rules_file)

        # Missing closing bracket
        result = engine._parse_encoded_message("[rule_name")
        assert result is None

        engine.close()

    def test_parse_encoded_message_with_fields(self, simple_rules_file):
        """Test parsing encoded message with fields."""
        engine = NormalizationEngine(simple_rules_file)

        result = engine._parse_encoded_message("[test_rule]|field1=value1|field2=value2|")
        assert result is not None
        rule_name, fields = result
        assert rule_name == "test_rule"
        assert fields == {"field1": "value1", "field2": "value2"}

        engine.close()

    def test_parse_encoded_message_no_fields(self, simple_rules_file):
        """Test parsing encoded message without fields."""
        engine = NormalizationEngine(simple_rules_file)

        result = engine._parse_encoded_message("[test_rule]")
        assert result is not None
        rule_name, fields = result
        assert rule_name == "test_rule"
        assert fields == {}

        engine.close()

    def test_parse_encoded_message_empty_fields(self, simple_rules_file):
        """Test parsing encoded message with empty field section."""
        engine = NormalizationEngine(simple_rules_file)

        result = engine._parse_encoded_message("[test_rule]||")
        assert result is not None
        rule_name, fields = result
        assert rule_name == "test_rule"
        assert fields == {}

        engine.close()


@pytest.mark.unit
class TestNormalizeEdgeCases:
    """Tests for normalize method edge cases."""

    def test_normalize_with_control_characters(self, simple_rules_file):
        """Test normalizing line with control characters."""
        engine = NormalizationEngine(simple_rules_file)

        # Line with control character (bell)
        line = "test\x07message"
        result = engine.normalize(line)

        # Should process the line (exact output depends on pattern matching)
        assert isinstance(result, str)

        engine.close()

    def test_normalize_unknown_rule(self, simple_rules_file):
        """Test normalize when matched rule is not in configuration."""
        engine = NormalizationEngine(simple_rules_file)

        # Manually test with encoded message for unknown rule
        result = engine._parse_encoded_message("[unknown_rule]|field=value|")
        assert result is not None
        rule_name, fields = result
        assert rule_name == "unknown_rule"

        # Rule lookup would fail for unknown_rule
        assert "unknown_rule" not in engine.rule_by_name

        engine.close()

    def test_normalize_template_missing_field(self, simple_rules_file):
        """Test normalize when output template references missing field."""
        # Create rules with template that references a field not in pattern
        rules = {
            "rules": [
                {
                    "name": "bad_template",
                    "pattern": [{"field": "field1"}],
                    "output": "Output: {field1} {missing_field}",
                }
            ]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_file = Path(f.name)

        try:
            engine = NormalizationEngine(rules_file)

            # Simulate a match with only field1
            encoded = "[bad_template]|field1=value1|"
            parsed = engine._parse_encoded_message(encoded)
            assert parsed is not None

            rule_name, fields = parsed
            rule = engine.rule_by_name[rule_name]
            output_template = str(rule.get("output", ""))

            # Template formatting should fail due to missing_field
            with pytest.raises(KeyError):
                output_template.format(**fields)

            engine.close()
        finally:
            rules_file.unlink()


@pytest.mark.unit
class TestFieldTransforms:
    """Tests for field transformation."""

    def test_apply_field_transforms_single(self, simple_rules_file):
        """Test applying single field transform."""
        engine = NormalizationEngine(simple_rules_file)

        result = engine._apply_field_transforms(
            "\x1b[31mRed text\x1b[0m", ["strip_ansi"], "test_field"
        )
        assert result == "Red text"

        engine.close()

    def test_apply_field_transforms_multiple(self, simple_rules_file):
        """Test applying multiple field transforms."""
        engine = NormalizationEngine(simple_rules_file)

        # Apply both strip_ansi and strip_text_ansi
        result = engine._apply_field_transforms(
            "\x1b[31m[31mText[39m\x1b[0m", ["strip_ansi", "strip_text_ansi"], "test_field"
        )
        assert result == "Text"

        engine.close()

    def test_apply_field_transforms_no_change(self, simple_rules_file):
        """Test transform that doesn't change value."""
        engine = NormalizationEngine(simple_rules_file)

        # Plain text with strip_ansi should be unchanged
        result = engine._apply_field_transforms("plain text", ["strip_ansi"], "test_field")
        assert result == "plain text"

        engine.close()


@pytest.mark.unit
class TestEngineCleanup:
    """Tests for engine cleanup."""

    def test_cleanup_on_close(self, simple_rules_file):
        """Test that cleanup is called on close."""
        engine = NormalizationEngine(simple_rules_file)

        xml_path = engine.xml_path
        assert xml_path.exists()

        engine.close()

        # Temp file should be cleaned up
        assert not xml_path.exists()

    def test_cleanup_handles_missing_attrs(self, simple_rules_file):
        """Test cleanup handles missing attributes gracefully."""
        engine = NormalizationEngine(simple_rules_file)

        # Remove attributes to test error handling
        xml_path = engine.xml_path
        delattr(engine, "xml_tempfile")

        # Cleanup should not raise
        engine._cleanup()

        # Manually clean up the file
        if xml_path.exists():
            xml_path.unlink()

    def test_close_with_no_pattern_matcher(self, simple_rules_file):
        """Test close when pattern_matcher is None."""
        engine = NormalizationEngine(simple_rules_file)

        # Set pattern_matcher to None
        engine.pattern_matcher.close()
        engine.pattern_matcher = None

        # Should not raise
        engine.close()


@pytest.mark.unit
class TestExplainMode:
    """Tests for explain mode output."""

    def test_explain_outputs_messages(self, simple_rules_file, capsys):
        """Test that explain mode outputs messages to stderr."""
        engine = NormalizationEngine(simple_rules_file, explain=True)

        # Set line number
        engine.current_line_number = 42

        # Call _explain
        engine._explain("Test message")

        captured = capsys.readouterr()
        assert "EXPLAIN:" in captured.err
        assert "[Line 42]" in captured.err
        assert "Test message" in captured.err

        engine.close()

    def test_explain_no_line_number(self, simple_rules_file, capsys):
        """Test explain without line number."""
        engine = NormalizationEngine(simple_rules_file, explain=True)

        engine.current_line_number = 0

        engine._explain("Test message")

        captured = capsys.readouterr()
        assert "EXPLAIN:" in captured.err
        assert "[Line" not in captured.err
        assert "Test message" in captured.err

        engine.close()
