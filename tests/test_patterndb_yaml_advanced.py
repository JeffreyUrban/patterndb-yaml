"""Advanced tests for patterndb_yaml module - edge cases and sequences."""

import tempfile
from io import StringIO
from pathlib import Path

import pytest
import yaml

from patterndb_yaml import PatterndbYaml
from patterndb_yaml.pattern_matching import (
    match_pattern_components,
    render_component_sequence,
)
from patterndb_yaml.patterndb_yaml import _load_sequence_config


@pytest.mark.unit
class TestMatchPatternComponents:
    """Tests for match_pattern_components function."""

    def test_match_with_alternatives(self):
        """Test pattern matching with alternatives."""
        pattern = [
            {"text": "Level: "},
            {
                "alternatives": [
                    [{"text": "ERROR"}],
                    [{"text": "WARN"}],
                    [{"text": "INFO"}],
                ]
            },
        ]

        # Match first alternative
        matched, fields = match_pattern_components("Level: ERROR", pattern)
        assert matched is True

        # Match second alternative
        matched, fields = match_pattern_components("Level: WARN", pattern)
        assert matched is True

        # No match
        matched, fields = match_pattern_components("Level: DEBUG", pattern)
        assert matched is False

    def test_match_with_number_parser(self):
        """Test pattern matching with NUMBER parser."""
        pattern = [
            {"text": "Count: "},
            {"field": "count", "parser": "NUMBER"},
        ]

        # Match number
        matched, fields = match_pattern_components("Count: 123", pattern, extract_fields=True)
        assert matched is True
        assert fields == {"count": "123"}

        # No number
        matched, fields = match_pattern_components("Count: abc", pattern, extract_fields=True)
        assert matched is False

    def test_match_with_number_parser_no_extract(self):
        """Test NUMBER parser without field extraction."""
        pattern = [
            {"text": "Count: "},
            {"field": "count", "parser": "NUMBER"},
        ]

        # Match but don't extract
        matched, fields = match_pattern_components("Count: 456", pattern, extract_fields=False)
        assert matched is True
        assert fields == {}

    def test_match_with_serialized(self):
        """Test pattern matching with serialized component."""
        pattern = [
            {"text": "Start"},
            {"serialized": "→"},
            {"text": "End"},
        ]

        # Match with serialized character
        matched, fields = match_pattern_components("Start→End", pattern)
        assert matched is True

        # No match with different character
        matched, fields = match_pattern_components("Start->End", pattern)
        assert matched is False

    def test_match_runs_past_end(self):
        """Test pattern matching when position exceeds line length."""
        pattern = [
            {"text": "Short"},
            {"text": " line"},
            {"text": " that continues"},
            {"text": " way too long"},
        ]

        # Line is too short for pattern
        matched, fields = match_pattern_components("Short line", pattern)
        assert matched is False

    def test_match_alternatives_no_match(self):
        """Test alternatives when none match."""
        pattern = [
            {
                "alternatives": [
                    [{"text": "FOO"}],
                    [{"text": "BAR"}],
                ]
            },
        ]

        matched, fields = match_pattern_components("BAZ", pattern)
        assert matched is False


@pytest.mark.unit
class TestRenderComponentSequence:
    """Tests for render_component_sequence function."""

    def test_render_text_components(self):
        """Test rendering text components."""
        components = [
            {"text": "Hello"},
            {"text": " "},
            {"text": "World"},
        ]

        result = render_component_sequence(components)
        assert result == "Hello World"

    def test_render_serialized_components(self):
        """Test rendering serialized components."""
        components = [
            {"text": "Start"},
            {"serialized": "→"},
            {"text": "End"},
        ]

        result = render_component_sequence(components)
        assert result == "Start→End"

    def test_render_mixed_components(self):
        """Test rendering mixed text and serialized."""
        components = [
            {"text": "A"},
            {"serialized": "•"},
            {"text": "B"},
        ]

        result = render_component_sequence(components)
        assert result == "A•B"

    def test_render_ignores_fields(self):
        """Test that field components are ignored in rendering."""
        components = [
            {"text": "Start"},
            {"field": "ignored_field"},
            {"text": "End"},
        ]

        result = render_component_sequence(components)
        assert result == "StartEnd"


@pytest.mark.unit
class TestLoadSequenceConfig:
    """Tests for _load_sequence_config function."""

    def test_load_no_sequences(self):
        """Test loading config with no sequences."""
        rules = {"rules": [{"name": "simple_rule", "pattern": [], "output": "simple"}]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            configs, markers = _load_sequence_config(rules_path)
            assert configs == {}
            assert markers == set()
        finally:
            rules_path.unlink()

    def test_load_sequence_with_field_placeholder(self):
        """Test loading sequence with field placeholder in output."""
        rules = {
            "rules": [
                {
                    "name": "dialog_question",
                    "pattern": [],
                    "output": "[dialog-question:{content}]",
                    "sequence": {"followers": []},
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            configs, markers = _load_sequence_config(rules_path)
            assert "dialog_question" in configs
            assert "[dialog-question:" in markers
        finally:
            rules_path.unlink()

    def test_load_sequence_without_field_placeholder(self):
        """Test loading sequence without field placeholder."""
        rules = {
            "rules": [
                {
                    "name": "simple_sequence",
                    "pattern": [],
                    "output": "[simple-output]",
                    "sequence": {"followers": []},
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            configs, markers = _load_sequence_config(rules_path)
            assert "simple_sequence" in configs
            assert "[simple-output]" in markers
        finally:
            rules_path.unlink()

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file."""
        configs, markers = _load_sequence_config(Path("/nonexistent/file.yaml"))
        assert configs == {}
        assert markers == set()


@pytest.mark.integration
class TestSequenceProcessing:
    """Tests for sequence processing functionality."""

    def test_sequence_with_followers(self):
        """Test processing multi-line sequences."""
        rules = {
            "rules": [
                {
                    "name": "question_sequence",
                    "pattern": [
                        {"text": "Q: "},
                        {"field": "question"},
                    ],
                    "output": "[Q:{question}]",
                    "sequence": {
                        "followers": [
                            {
                                "pattern": [
                                    {"text": "A: "},
                                    {"field": "answer"},
                                ],
                                "output": "[A:{answer}]",
                            }
                        ]
                    },
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            processor = PatterndbYaml(rules_path=rules_path)

            # Process question and answer sequence
            logs = ["Q: What is the answer?", "A: 42", "Q: Another question?"]

            input_data = StringIO("\n".join(logs))
            output_data = StringIO()
            processor.process(input_data, output_data)

            # Flush any buffered sequence
            processor.flush(output_data)

            output_data.seek(0)
            result = output_data.read()

            # Check that sequences were processed
            assert "[Q:What is the answer?]" in result
            assert "[A:42]" in result

            processor.seq_processor.sequence_buffer = []
        finally:
            rules_path.unlink()

    def test_follower_with_no_output_template(self):
        """Test follower with no output template."""
        rules = {
            "rules": [
                {
                    "name": "leader",
                    "pattern": [{"text": "START"}],
                    "output": "[START]",
                    "sequence": {
                        "followers": [
                            {
                                "pattern": [{"text": "FOLLOW"}],
                                # No output specified
                            }
                        ]
                    },
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            processor = PatterndbYaml(rules_path=rules_path)

            # The follower should return raw line when no template
            raw_line = "FOLLOW"
            result = processor.seq_processor.normalize_follower(raw_line, "leader")

            # Should return raw line since no output template
            assert result == "FOLLOW"
        finally:
            rules_path.unlink()

    def test_follower_template_missing_field(self):
        """Test follower template with missing field."""
        rules = {
            "rules": [
                {
                    "name": "leader",
                    "pattern": [{"text": "START"}],
                    "output": "[START]",
                    "sequence": {
                        "followers": [
                            {
                                "pattern": [
                                    {"text": "DATA: "},
                                    {"field": "value"},
                                ],
                                "output": "[FOLLOWER:{value}:{missing_field}]",
                            }
                        ]
                    },
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            processor = PatterndbYaml(rules_path=rules_path)

            # The follower template references missing_field which won't be extracted
            raw_line = "DATA: test_value"
            result = processor.seq_processor.normalize_follower(raw_line, "leader")

            # Should return raw line due to KeyError
            assert result == "DATA: test_value"
        finally:
            rules_path.unlink()

    def test_follower_unknown_rule(self):
        """Test normalize_follower with unknown rule."""
        rules = {"rules": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            processor = PatterndbYaml(rules_path=rules_path)

            result = processor.seq_processor.normalize_follower("test", "nonexistent_rule")
            assert result == "test"
        finally:
            rules_path.unlink()

    def test_is_sequence_follower_unknown_rule(self):
        """Test is_sequence_follower with unknown rule."""
        rules = {"rules": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            processor = PatterndbYaml(rules_path=rules_path)

            result = processor.seq_processor.is_sequence_follower("test", "nonexistent_rule")
            assert result is False
        finally:
            rules_path.unlink()


@pytest.mark.unit
class TestPatterndbYamlEdgeCases:
    """Edge case tests for PatterndbYaml."""

    def test_get_stats_no_processing(self):
        """Test get_stats before any processing."""
        rules = {"rules": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            processor = PatterndbYaml(rules_path=rules_path)
            stats = processor.get_stats()

            assert stats["lines_processed"] == 0
            assert stats["lines_matched"] == 0
            assert stats["match_rate"] == 0.0
        finally:
            rules_path.unlink()

    def test_flush_empty_buffer(self):
        """Test flush with empty sequence buffer."""
        rules = {"rules": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            processor = PatterndbYaml(rules_path=rules_path)
            output = StringIO()

            # Flush with no buffered data - should not raise
            processor.flush(output)

            assert output.getvalue() == ""
        finally:
            rules_path.unlink()

    def test_print_explain_outputs_to_stderr(self, capsys):
        """Test that _print_explain method outputs to stderr when explain=True."""
        rules = {"rules": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            # Test with explain=True
            processor = PatterndbYaml(rules_path=rules_path, explain=True)
            processor._print_explain("Test explanation message")

            captured = capsys.readouterr()
            assert "EXPLAIN: Test explanation message" in captured.err
        finally:
            rules_path.unlink()

    def test_print_explain_silent_when_disabled(self, capsys):
        """Test that _print_explain method is silent when explain=False."""
        rules = {"rules": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            # Test with explain=False (default)
            processor = PatterndbYaml(rules_path=rules_path, explain=False)
            processor._print_explain("Test explanation message")

            captured = capsys.readouterr()
            assert captured.err == ""
        finally:
            rules_path.unlink()
