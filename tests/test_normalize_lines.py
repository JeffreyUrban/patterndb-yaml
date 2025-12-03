"""Tests for normalize_lines method - batch normalization with sequence support."""

import tempfile
from pathlib import Path

import pytest
import yaml

from patterndb_yaml import PatterndbYaml


@pytest.mark.unit
class TestNormalizeLinesBasic:
    """Basic normalization tests without sequences."""

    def test_normalize_empty_list(self):
        """Test normalizing an empty list."""
        rules = {"rules": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            processor = PatterndbYaml(rules_path=rules_path)
            result = processor.normalize_lines([])
            assert result == []
        finally:
            rules_path.unlink()

    def test_normalize_single_line(self):
        """Test normalizing a single line."""
        rules = {
            "rules": [
                {
                    "name": "simple",
                    "pattern": [{"text": "test"}],
                    "output": "[TEST]",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            processor = PatterndbYaml(rules_path=rules_path)
            result = processor.normalize_lines(["test"])
            assert result == ["[TEST]"]
        finally:
            rules_path.unlink()

    def test_normalize_multiple_lines(self):
        """Test normalizing multiple lines without sequences."""
        rules = {
            "rules": [
                {
                    "name": "error",
                    "pattern": [{"text": "ERROR: "}, {"field": "msg"}],
                    "output": "[ERROR:{msg}]",
                },
                {
                    "name": "warn",
                    "pattern": [{"text": "WARN: "}, {"field": "msg"}],
                    "output": "[WARN:{msg}]",
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            processor = PatterndbYaml(rules_path=rules_path)
            lines = [
                "ERROR: Something failed",
                "WARN: Low memory",
                "ERROR: Connection lost",
            ]
            result = processor.normalize_lines(lines)
            assert result == [
                "[ERROR:Something failed]",
                "[WARN:Low memory]",
                "[ERROR:Connection lost]",
            ]
        finally:
            rules_path.unlink()

    def test_normalize_unmatched_lines(self):
        """Test normalizing lines that don't match any pattern."""
        rules = {
            "rules": [
                {
                    "name": "error",
                    "pattern": [{"text": "ERROR: "}, {"field": "msg"}],
                    "output": "[ERROR:{msg}]",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            processor = PatterndbYaml(rules_path=rules_path)
            lines = [
                "ERROR: Matched line",
                "INFO: Unmatched line",
                "DEBUG: Another unmatched",
            ]
            result = processor.normalize_lines(lines)

            # Matched line should be normalized, unmatched lines pass through
            assert result[0] == "[ERROR:Matched line]"
            assert result[1] == "INFO: Unmatched line"
            assert result[2] == "DEBUG: Another unmatched"
        finally:
            rules_path.unlink()


@pytest.mark.integration
class TestNormalizeLinesSequences:
    """Tests for sequence processing in normalize_lines."""

    def test_simple_sequence(self):
        """Test a simple sequence with leader and follower."""
        rules = {
            "rules": [
                {
                    "name": "question",
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
            lines = [
                "Q: What is 2+2?",
                "A: 4",
            ]
            result = processor.normalize_lines(lines)

            # Both leader and follower should be in result
            assert result == ["[Q:What is 2+2?]", "[A:4]"]
        finally:
            rules_path.unlink()

    def test_sequence_with_multiple_followers(self):
        """Test sequence with multiple follower lines."""
        rules = {
            "rules": [
                {
                    "name": "question",
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
            lines = [
                "Q: What is 2+2?",
                "A: 4",
                "A: Or maybe 5?",
            ]
            result = processor.normalize_lines(lines)

            # Leader and both followers should be in result
            assert result == ["[Q:What is 2+2?]", "[A:4]", "[A:Or maybe 5?]"]
        finally:
            rules_path.unlink()

    def test_sequence_interrupted_by_non_follower(self):
        """Test sequence interrupted by a non-follower line."""
        rules = {
            "rules": [
                {
                    "name": "question",
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
                },
                {
                    "name": "info",
                    "pattern": [{"text": "INFO: "}, {"field": "msg"}],
                    "output": "[INFO:{msg}]",
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            processor = PatterndbYaml(rules_path=rules_path)
            lines = [
                "Q: What is 2+2?",
                "A: 4",
                "INFO: Some info",  # This interrupts the sequence
                "A: This won't be part of the sequence",
            ]
            result = processor.normalize_lines(lines)

            # First Q+A sequence should be complete
            # INFO should break the sequence
            # Last A won't match as a follower since sequence was broken
            assert "[Q:What is 2+2?]" in result
            assert "[A:4]" in result
            assert "[INFO:Some info]" in result
            # Last line won't match any pattern, so passes through unchanged
            assert result[3] == "A: This won't be part of the sequence"
        finally:
            rules_path.unlink()

    def test_multiple_sequences(self):
        """Test multiple sequences in one batch."""
        rules = {
            "rules": [
                {
                    "name": "question",
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
            lines = [
                "Q: First question?",
                "A: First answer",
                "Q: Second question?",
                "A: Second answer",
            ]
            result = processor.normalize_lines(lines)

            # Both sequences should be complete
            assert result == [
                "[Q:First question?]",
                "[A:First answer]",
                "[Q:Second question?]",
                "[A:Second answer]",
            ]
        finally:
            rules_path.unlink()

    def test_sequence_at_end_gets_flushed(self):
        """Test that a sequence at the end of input is properly flushed."""
        rules = {
            "rules": [
                {
                    "name": "start",
                    "pattern": [{"text": "START: "}, {"field": "msg"}],
                    "output": "[START:{msg}]",
                    "sequence": {
                        "followers": [
                            {
                                "pattern": [{"text": "  "}, {"field": "detail"}],
                                "output": "[DETAIL:{detail}]",
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
            lines = [
                "START: Process beginning",
                "  First detail",
                "  Second detail",
            ]
            result = processor.normalize_lines(lines)

            # All lines should be in result (sequence flushed at end)
            assert result == [
                "[START:Process beginning]",
                "[DETAIL:First detail]",
                "[DETAIL:Second detail]",
            ]
        finally:
            rules_path.unlink()

    def test_sequence_only_leader_no_followers(self):
        """Test sequence with only leader line, no followers."""
        rules = {
            "rules": [
                {
                    "name": "question",
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
            lines = ["Q: Unanswered question?"]
            result = processor.normalize_lines(lines)

            # Leader should be flushed at end even without followers
            assert result == ["[Q:Unanswered question?]"]
        finally:
            rules_path.unlink()


@pytest.mark.integration
class TestNormalizeLinesEdgeCases:
    """Edge case tests for normalize_lines."""

    def test_normalize_lines_preserves_state_isolation(self):
        """Test that multiple calls to normalize_lines don't interfere."""
        rules = {
            "rules": [
                {
                    "name": "question",
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

            # First batch
            result1 = processor.normalize_lines(["Q: First?", "A: First answer"])
            assert result1 == ["[Q:First?]", "[A:First answer]"]

            # Second batch should not be affected by first
            result2 = processor.normalize_lines(["Q: Second?", "A: Second answer"])
            assert result2 == ["[Q:Second?]", "[A:Second answer]"]
        finally:
            rules_path.unlink()

    def test_normalize_lines_with_mixed_content(self):
        """Test normalize_lines with sequences and non-sequences mixed."""
        rules = {
            "rules": [
                {
                    "name": "question",
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
                },
                {
                    "name": "log",
                    "pattern": [{"text": "LOG: "}, {"field": "msg"}],
                    "output": "[LOG:{msg}]",
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            processor = PatterndbYaml(rules_path=rules_path)
            lines = [
                "LOG: Starting",
                "Q: What's up?",
                "A: Not much",
                "LOG: Done",
            ]
            result = processor.normalize_lines(lines)

            assert result == [
                "[LOG:Starting]",
                "[Q:What's up?]",
                "[A:Not much]",
                "[LOG:Done]",
            ]
        finally:
            rules_path.unlink()

    def test_normalize_lines_performance_optimization(self):
        """Test that normalize_lines handles large batches efficiently."""
        rules = {
            "rules": [
                {
                    "name": "log",
                    "pattern": [{"text": "LOG "}, {"field": "num", "parser": "NUMBER"}],
                    "output": "[LOG:{num}]",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rules, f)
            rules_path = Path(f.name)

        try:
            processor = PatterndbYaml(rules_path=rules_path)

            # Create a large batch of lines
            lines = [f"LOG {i}" for i in range(1000)]

            result = processor.normalize_lines(lines)

            # Verify all lines were normalized
            assert len(result) == 1000
            assert result[0] == "[LOG:0]"
            assert result[999] == "[LOG:999]"
        finally:
            rules_path.unlink()
