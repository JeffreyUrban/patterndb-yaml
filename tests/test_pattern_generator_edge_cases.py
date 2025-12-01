"""Tests for pattern_generator edge cases to increase coverage."""

import pytest

from patterndb_yaml.pattern_generator import (
    expand_pattern_element,
    extract_field_names,
    generate_message_value,
    generate_pattern_variants,
    generate_xml_rule,
)


@pytest.mark.unit
class TestOptionsElement:
    """Tests for options element handling (lines 121-141)."""

    def test_expand_options_element(self):
        """Test expanding options element with name and values."""
        element = {
            "options": {
                "name": "action_type",
                "values": [
                    {"text": "Web Search"},
                    {"text": "File Operation"},
                ],
            }
        }

        variants = expand_pattern_element(element)

        # Should return two variants, each with option value
        assert len(variants) == 2
        # Each variant is a tuple: (pattern_fragments, (option_name, option_value))
        assert variants[0] == (["Web Search"], ("action_type", "Web Search"))
        assert variants[1] == (["File Operation"], ("action_type", "File Operation"))

    def test_options_without_name_raises(self):
        """Test that options without name raises ValueError."""
        element = {
            "options": {
                "values": [{"text": "foo"}],
            }
        }

        with pytest.raises(ValueError, match="Options must have 'name' and 'values'"):
            expand_pattern_element(element)

    def test_options_without_values_raises(self):
        """Test that options without values raises ValueError."""
        element = {
            "options": {
                "name": "test",
            }
        }

        with pytest.raises(ValueError, match="Options must have 'name' and 'values'"):
            expand_pattern_element(element)

    def test_options_not_dict_raises(self):
        """Test that options as non-dict raises ValueError."""
        element = {"options": "not a dict"}

        with pytest.raises(ValueError, match="Options must be a dict"):
            expand_pattern_element(element)

    def test_options_value_without_text_raises(self):
        """Test that option value without text key raises ValueError."""
        element = {
            "options": {
                "name": "test",
                "values": [{"foo": "bar"}],
            }
        }

        with pytest.raises(ValueError, match="Each option value must be a dict with 'text' key"):
            expand_pattern_element(element)


@pytest.mark.unit
class TestCharElement:
    """Tests for char element handling (lines 159-160)."""

    def test_expand_char_element(self):
        """Test expanding char element to character variants."""
        element = {"char": "ABC"}

        variants = expand_pattern_element(element)

        # Should expand to one variant per character (all get Unicode-escaped)
        assert len(variants) == 3
        assert variants[0] == ["[U+0041]"]  # A
        assert variants[1] == ["[U+0042]"]  # B
        assert variants[2] == ["[U+0043]"]  # C

    def test_expand_char_with_unicode(self):
        """Test expanding char element with Unicode characters."""
        element = {"char": "→↓"}

        variants = expand_pattern_element(element)

        # Unicode chars get escaped
        assert len(variants) == 2
        assert variants[0] == ["[U+2192]"]  # →
        assert variants[1] == ["[U+2193]"]  # ↓


@pytest.mark.unit
class TestFieldDelimiterInference:
    """Tests for delimiter inference (lines 208-215)."""

    def test_infer_delimiter_from_serialized(self):
        """Test inferring delimiter from serialized element."""
        pattern_elements = [
            {"field": "message"},
            {"serialized": "\u00a0"},  # Non-breaking space
        ]

        patterns = generate_pattern_variants(pattern_elements)

        # Should use serialized char as delimiter
        assert len(patterns) == 1
        pattern, _ = patterns[0]
        # ESTRING with Unicode-escaped delimiter
        assert "@ESTRING:message:[U+00A0]@" in pattern


@pytest.mark.unit
class TestExtractFieldNamesFromAlternatives:
    """Tests for extracting field names from alternatives (lines 349-353)."""

    def test_extract_field_names_from_alternatives(self):
        """Test extracting field names when alternatives contain fields."""
        pattern_elements = [
            {
                "alternatives": [
                    {"field": "username"},
                    {"field": "userid"},
                ]
            }
        ]

        fields = extract_field_names(pattern_elements)

        # Should extract from first alternative
        assert "username" in fields


@pytest.mark.unit
class TestGenerateMessageValueWithOptions:
    """Tests for message value generation with options (lines 374, 384)."""

    def test_generate_message_value_with_option_substitution(self):
        """Test that option values are substituted as literals."""
        rule_name = "action"
        fields = ["action_type", "target"]
        option_values = {"action_type": "Web Search"}

        message = generate_message_value(rule_name, fields, option_values)

        # Option field should use literal value, regular field should use $field
        assert message == "[action]|action_type=Web Search|target=$target|"

    def test_generate_message_value_empty_fields(self):
        """Test message value with no fields."""
        rule_name = "simple"
        fields = []

        message = generate_message_value(rule_name, fields, None)

        assert message == "[simple]"


@pytest.mark.unit
class TestGenerateXMLRuleWithOptions:
    """Tests for XML rule generation with options (lines 416-446)."""

    def test_generate_xml_rule_with_options(self):
        """Test generating multiple XML rules for option variants."""
        rule = {
            "name": "action",
            "pattern": [
                {"text": "Action: "},
                {
                    "options": {
                        "name": "action_type",
                        "values": [
                            {"text": "Web Search"},
                            {"text": "File Operation"},
                        ],
                    }
                },
            ],
        }

        rule_elems = generate_xml_rule(rule)

        # Should create one rule per option variant
        assert len(rule_elems) == 2

        # First rule should have descriptive ID with option value
        assert rule_elems[0].get("id") == "action_Web_Search"
        # Second rule should have descriptive ID
        assert rule_elems[1].get("id") == "action_File_Operation"

        # Check that option values are substituted in MESSAGE value
        value_elem_0 = rule_elems[0].find(".//value[@name='MESSAGE']")
        assert "action_type=Web Search" in value_elem_0.text

        value_elem_1 = rule_elems[1].find(".//value[@name='MESSAGE']")
        assert "action_type=File Operation" in value_elem_1.text

    def test_generate_xml_rule_with_options_spaces_in_values(self):
        """Test that spaces in option values are replaced with underscores in IDs."""
        rule = {
            "name": "test",
            "pattern": [
                {
                    "options": {
                        "name": "type",
                        "values": [
                            {"text": "Multi Word Value"},
                        ],
                    }
                },
            ],
        }

        rule_elems = generate_xml_rule(rule)

        assert len(rule_elems) == 1
        # Spaces should be replaced with underscores in ID
        assert rule_elems[0].get("id") == "test_Multi_Word_Value"


@pytest.mark.unit
class TestFieldWithExplicitParser:
    """Tests for field with explicit parser (lines 169-170)."""

    def test_field_with_explicit_parser(self):
        """Test field element with explicit parser type."""
        element = {
            "field": "count",
            "parser": "NUMBER",
        }

        variants = expand_pattern_element(element)

        assert len(variants) == 1
        assert variants[0] == ["@NUMBER:count@"]

    def test_field_with_float_parser(self):
        """Test field element with FLOAT parser."""
        element = {
            "field": "value",
            "parser": "FLOAT",
        }

        variants = expand_pattern_element(element)

        assert len(variants) == 1
        assert variants[0] == ["@FLOAT:value@"]


@pytest.mark.unit
class TestFieldUntilDelimiter:
    """Tests for field with until delimiter (lines 173-175)."""

    def test_field_with_until_delimiter(self):
        """Test field with explicit until delimiter."""
        element = {
            "field": "message",
            "until": "]",
        }

        variants = expand_pattern_element(element)

        assert len(variants) == 1
        assert variants[0] == ["@ESTRING:message:]@"]

    def test_field_with_unicode_delimiter(self):
        """Test field with Unicode until delimiter."""
        element = {
            "field": "data",
            "until": "→",  # Unicode arrow
        }

        variants = expand_pattern_element(element)

        assert len(variants) == 1
        # Unicode delimiter should be escaped
        assert variants[0] == ["@ESTRING:data:[U+2192]@"]
