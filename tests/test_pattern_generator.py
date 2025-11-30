"""Tests for pattern_generator module."""

import pytest

from patterndb_yaml.pattern_generator import (
    expand_parser_placeholders,
    expand_pattern_element,
    generate_from_yaml,
    unicode_escape,
)


@pytest.mark.unit
class TestUnicodeEscape:
    """Tests for unicode_escape function."""

    def test_unicode_escape_ascii(self):
        """Test escaping ASCII character."""
        result = unicode_escape("A")
        assert result == "[U+0041]"

    def test_unicode_escape_unicode(self):
        """Test escaping Unicode character."""
        result = unicode_escape("→")
        assert result == "[U+2192]"

    def test_unicode_escape_emoji(self):
        """Test escaping emoji."""
        result = unicode_escape("😀")
        assert result == "[U+1F600]"

    def test_unicode_escape_multiple_chars_raises(self):
        """Test that multiple characters raise ValueError."""
        with pytest.raises(ValueError, match="Expected single character"):
            unicode_escape("ABC")

    def test_unicode_escape_empty_raises(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Expected single character"):
            unicode_escape("")


@pytest.mark.unit
class TestExpandParserPlaceholders:
    """Tests for expand_parser_placeholders function."""

    def test_expand_no_placeholders(self):
        """Test template with no placeholders."""
        result = expand_parser_placeholders("plain text")
        assert result == "plain text"

    def test_expand_single_placeholder(self):
        """Test template with single placeholder."""
        result = expand_parser_placeholders("Count: {NUMBER:count}")
        assert result == "Count: @NUMBER:count@"

    def test_expand_multiple_placeholders(self):
        """Test template with multiple placeholders."""
        result = expand_parser_placeholders("{NUMBER:id} - {ANYSTRING:message}")
        assert result == "@NUMBER:id@ - @ANYSTRING:message@"

    def test_expand_with_unicode(self):
        """Test template with Unicode characters."""
        result = expand_parser_placeholders("Arrow→Value")
        assert "[U+2192]" in result
        assert "Arrow" in result
        assert "Value" in result

    def test_expand_placeholder_at_start(self):
        """Test placeholder at start of template."""
        result = expand_parser_placeholders("{NUMBER:value} items")
        assert result == "@NUMBER:value@ items"

    def test_expand_placeholder_at_end(self):
        """Test placeholder at end of template."""
        result = expand_parser_placeholders("Total: {NUMBER:total}")
        assert result == "Total: @NUMBER:total@"

    def test_expand_unicode_before_placeholder(self):
        """Test Unicode character before placeholder."""
        result = expand_parser_placeholders("•{NUMBER:count}")
        assert "[U+" in result
        assert "@NUMBER:count@" in result

    def test_expand_unicode_after_placeholder(self):
        """Test Unicode character after placeholder."""
        result = expand_parser_placeholders("{NUMBER:count}→")
        assert "@NUMBER:count@" in result
        assert "[U+2192]" in result


@pytest.mark.unit
class TestExpandPatternElement:
    """Tests for expand_pattern_element function."""

    def test_expand_simple_text(self):
        """Test expanding simple text element."""
        element = {"text": "Hello"}
        result = expand_pattern_element(element)
        assert len(result) == 1
        assert result[0] == ["Hello"]

    def test_expand_simple_field(self):
        """Test expanding simple field element."""
        element = {"field": "message"}
        result = expand_pattern_element(element)
        assert len(result) == 1
        assert result[0] == ["@ANYSTRING:message@"]

    def test_expand_field_with_parser(self):
        """Test expanding field with parser."""
        element = {"field": "count", "parser": "NUMBER"}
        result = expand_pattern_element(element)
        assert len(result) == 1
        assert result[0] == ["@NUMBER:count@"]

    def test_expand_serialized(self):
        """Test expanding serialized element."""
        element = {"serialized": "→"}
        result = expand_pattern_element(element)
        assert len(result) == 1
        assert "[U+2192]" in result[0][0]

    def test_expand_alternatives_simple(self):
        """Test expanding simple alternatives."""
        element = {
            "alternatives": [
                {"text": "ERROR"},
                {"text": "WARN"},
                {"text": "INFO"},
            ]
        }
        result = expand_pattern_element(element)
        assert len(result) == 3
        assert ["ERROR"] in result
        assert ["WARN"] in result
        assert ["INFO"] in result

    def test_expand_alternatives_with_sequences(self):
        """Test expanding alternatives with sequences."""
        element = {
            "alternatives": [
                [{"text": "Level: "}, {"text": "ERROR"}],
                [{"text": "Level: "}, {"text": "WARN"}],
            ]
        }
        result = expand_pattern_element(element)
        assert len(result) == 2
        # Each alternative should be a combined pattern
        assert any("Level: " in str(variant) for variant in result)

    def test_expand_empty_element_raises(self):
        """Test expanding element with no recognized keys raises ValueError."""
        element = {"unknown": "value"}
        with pytest.raises(ValueError, match="Unknown pattern element type"):
            expand_pattern_element(element)


@pytest.mark.integration
class TestGenerateFromYaml:
    """Tests for generate_from_yaml function."""

    def test_generate_simple_rule(self):
        """Test generating XML from simple rule."""
        rules_data = {
            "rules": [
                {
                    "name": "simple_rule",
                    "pattern": [{"field": "message"}],
                    "output": "Normalized: {message}",
                }
            ]
        }

        xml = generate_from_yaml(rules_data)

        # Verify XML structure
        assert '<?xml version="1.0"' in xml
        assert "<patterndb" in xml
        assert "</patterndb>" in xml
        assert "simple_rule" in xml

    def test_generate_with_alternatives(self):
        """Test generating XML with alternatives."""
        rules_data = {
            "rules": [
                {
                    "name": "level_rule",
                    "pattern": [
                        {"text": "Level: "},
                        {"alternatives": [{"text": "ERROR"}, {"text": "WARN"}]},
                    ],
                    "output": "Log level found",
                }
            ]
        }

        xml = generate_from_yaml(rules_data)

        assert "<patterndb" in xml
        assert "level_rule" in xml

    def test_generate_with_field_transforms(self):
        """Test generating XML with field transforms."""
        rules_data = {
            "rules": [
                {
                    "name": "transform_rule",
                    "pattern": [{"field": "text"}],
                    "output": "{text}",
                    "field_transforms": {"text": ["strip_ansi"]},
                }
            ]
        }

        xml = generate_from_yaml(rules_data)

        assert "<patterndb" in xml
        # Transforms are metadata in the output, not in patterns

    def test_generate_empty_rules(self):
        """Test generating XML with empty rules list."""
        rules_data = {"rules": []}

        xml = generate_from_yaml(rules_data)

        assert '<?xml version="1.0"' in xml
        assert "<patterndb" in xml

    def test_generate_with_unicode(self):
        """Test generating XML with Unicode characters."""
        rules_data = {
            "rules": [
                {
                    "name": "unicode_rule",
                    "pattern": [{"serialized": "→"}],
                    "output": "Arrow found",
                }
            ]
        }

        xml = generate_from_yaml(rules_data)

        # Unicode should be escaped in the pattern
        assert "[U+" in xml or "U+" in xml

    def test_generate_with_number_parser(self):
        """Test generating XML with NUMBER parser."""
        rules_data = {
            "rules": [
                {
                    "name": "number_rule",
                    "pattern": [
                        {"text": "Count: "},
                        {"field": "count", "parser": "NUMBER"},
                    ],
                    "output": "Count: {count}",
                }
            ]
        }

        xml = generate_from_yaml(rules_data)

        assert "<patterndb" in xml
        assert "number_rule" in xml

    def test_generate_with_sequence(self):
        """Test generating XML with sequence definition."""
        rules_data = {
            "rules": [
                {
                    "name": "question",
                    "pattern": [{"text": "Q: "}, {"field": "question"}],
                    "output": "[Q:{question}]",
                    "sequence": {
                        "followers": [
                            {
                                "pattern": [{"text": "A: "}, {"field": "answer"}],
                                "output": "[A:{answer}]",
                            }
                        ]
                    },
                }
            ]
        }

        xml = generate_from_yaml(rules_data)

        # Sequences are application-level, not in syslog-ng XML
        # But the rule should still be generated
        assert "<patterndb" in xml
        assert "question" in xml

    def test_generate_multiple_rules(self):
        """Test generating XML with multiple rules."""
        rules_data = {
            "rules": [
                {
                    "name": "rule1",
                    "pattern": [{"field": "msg1"}],
                    "output": "Rule 1",
                },
                {
                    "name": "rule2",
                    "pattern": [{"field": "msg2"}],
                    "output": "Rule 2",
                },
            ]
        }

        xml = generate_from_yaml(rules_data)

        assert "rule1" in xml
        assert "rule2" in xml

    def test_generate_preserves_order(self):
        """Test that rule order is preserved in XML."""
        rules_data = {
            "rules": [
                {
                    "name": "first_rule",
                    "pattern": [{"text": "FIRST"}],
                    "output": "First",
                },
                {
                    "name": "second_rule",
                    "pattern": [{"text": "SECOND"}],
                    "output": "Second",
                },
            ]
        }

        xml = generate_from_yaml(rules_data)

        # Check that first_rule appears before second_rule in XML
        first_pos = xml.find("first_rule")
        second_pos = xml.find("second_rule")
        assert first_pos < second_pos
