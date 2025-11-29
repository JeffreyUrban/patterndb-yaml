#!/usr/bin/env python3
"""
Pattern generator for normalization rules.

Converts simple YAML pattern definitions into verbose syslog-ng XML patterns.
Handles inline alternatives and cartesian products automatically.
"""

import re
import xml.etree.ElementTree as ET
from itertools import product
from typing import Any, Optional, Union
from xml.dom import minidom

# Type aliases for clarity
PatternVariant = Union[list[str], tuple[list[str], tuple[str, str]]]
PatternVariantList = list[PatternVariant]


def unicode_escape(char: str) -> str:
    """
    Convert a character to Unicode escape format for syslog-ng patterns.

    Args:
        char: Single character to escape

    Returns:
        Unicode escape string like [U+2026]
    """
    if len(char) != 1:
        raise ValueError(f"Expected single character, got: {char}")
    codepoint = ord(char)
    return f"[U+{codepoint:04X}]"


def expand_parser_placeholders(template: str) -> str:
    """
    Expand parser placeholders in a template string.

    Placeholders like {NUMBER:field} become @NUMBER:field@
    Literal text is Unicode-escaped as needed.

    Args:
        template: String with optional {PARSER:field} placeholders

    Returns:
        Expanded pattern fragment
    """
    # Pattern to match {PARSER:field} placeholders
    placeholder_pattern = r"\{([A-Z]+):([a-z_]+)\}"

    result = []
    last_end = 0

    for match in re.finditer(placeholder_pattern, template):
        # Add literal text before this placeholder (with Unicode escaping)
        literal = template[last_end : match.start()]
        escaped_literal = "".join(unicode_escape(ch) if ord(ch) > 127 else ch for ch in literal)
        if escaped_literal:
            result.append(escaped_literal)

        # Add the parser
        parser_type = match.group(1)
        field_name = match.group(2)
        result.append(f"@{parser_type}:{field_name}@")

        last_end = match.end()

    # Add any remaining literal text
    literal = template[last_end:]
    escaped_literal = "".join(unicode_escape(ch) if ord(ch) > 127 else ch for ch in literal)
    if escaped_literal:
        result.append(escaped_literal)

    return "".join(result)


def expand_pattern_element(element: dict[str, Any]) -> PatternVariantList:
    """
    Expand a pattern element into all possible variants.

    Args:
        element: Pattern element dict

    Returns:
        List of variant lists. Each variant is a list of pattern fragments.
        For 'options', each variant is a tuple: (pattern_fragments, option_value)
    """
    # Check for inline alternatives first
    if "alternatives" in element:
        # Each alternative can be either:
        # 1. A single element dict: {text: "foo"}
        # 2. A list of elements: [{serialized: "..."}, {text: "..."}]
        all_variants: PatternVariantList = []
        for alt in element["alternatives"]:
            if isinstance(alt, list):
                # Alternative is a sequence of elements - expand each and combine
                sequence_variants = []
                for elem in alt:
                    sequence_variants.append(expand_pattern_element(elem))
                # Compute cartesian product of the sequence
                from itertools import product

                for combo in product(*sequence_variants):
                    # Flatten the combination - only dealing with List[str] here, not options
                    variant: list[str] = []
                    for elem_variant in combo:
                        if isinstance(elem_variant, list):
                            variant.extend(elem_variant)
                        # Options not expected in alternatives sequence
                    all_variants.append(variant)
            else:
                # Alternative is a single element
                alt_variants = expand_pattern_element(alt)
                all_variants.extend(alt_variants)
        return all_variants

    # Check for options - like alternatives but captured
    if "options" in element:
        # Options must have a 'name' and 'values' list
        if not isinstance(element["options"], dict):
            raise ValueError(f"Options must be a dict with 'name' and 'values' keys: {element}")

        option_name = element["options"].get("name")
        option_values = element["options"].get("values")

        if not option_name or not option_values:
            raise ValueError(f"Options must have 'name' and 'values': {element}")

        # Generate one variant per option value, with the name and value attached
        option_variants: PatternVariantList = []
        for opt in option_values:
            # Each option should be a dict with 'text' key
            if not isinstance(opt, dict) or "text" not in opt:
                raise ValueError(f"Each option value must be a dict with 'text' key: {opt}")
            option_text = opt["text"]
            # Expand the text (handles Unicode escaping and parser placeholders)
            expanded = expand_parser_placeholders(option_text)
            # Return as tuple: (pattern_fragments, (option_name, option_value))
            option_variants.append(([expanded], (option_name, option_text)))
        return option_variants

    if "text" in element:
        # Literal text - may contain {PARSER:field} placeholders
        text = element["text"]
        expanded = expand_parser_placeholders(text)
        return [[expanded]]

    elif "serialized" in element:
        # Serialized characters (like \u00a0) - need to be Unicode-escaped
        # The YAML string "\u00a0" becomes the actual NBSP character when parsed
        serialized_str = element["serialized"]
        # Escape each character to Unicode format
        escaped = "".join(unicode_escape(ch) if ord(ch) > 127 else ch for ch in serialized_str)
        return [[escaped]]

    elif "char" in element:
        # Character set - expand to all character variants
        char = element["char"]
        return [[unicode_escape(ch)] for ch in char]

    elif "field" in element:
        # Field extraction
        field_name = element["field"]
        parser = element.get("parser")  # Explicit parser type (e.g., 'NUMBER', 'FLOAT')
        delimiter = element.get("until", "")

        # Check if explicit parser specified (e.g., parser: NUMBER)
        if parser:
            return [[f"@{parser.upper()}:{field_name}@"]]
        elif delimiter:
            # Escape non-ASCII characters in delimiter
            escaped_delim = "".join(unicode_escape(ch) if ord(ch) > 127 else ch for ch in delimiter)
            # ESTRING extracts until delimiter
            return [[f"@ESTRING:{field_name}:{escaped_delim}@"]]
        else:
            # ANYSTRING extracts rest of line
            return [[f"@ANYSTRING:{field_name}@"]]

    else:
        raise ValueError(f"Unknown pattern element type: {element}")


def _infer_delimiter(pattern_elements: list[dict[str, Any]], field_index: int) -> str:
    """
    Infer the delimiter for a field by looking at the next element.

    Args:
        pattern_elements: List of all pattern elements
        field_index: Index of the field element

    Returns:
        Delimiter string (Unicode-escaped) or empty string if no delimiter can be inferred
    """
    if field_index + 1 >= len(pattern_elements):
        return ""  # No next element

    next_elem = pattern_elements[field_index + 1]

    # If next element is fixed text, use it as delimiter
    if "text" in next_elem:
        # Expand any parser placeholders in the text
        text = next_elem["text"]
        expanded = expand_parser_placeholders(text)
        return expanded

    # If next element is serialized, use it as delimiter
    if "serialized" in next_elem:
        serialized_str = next_elem["serialized"]
        escaped = "".join(unicode_escape(ch) if ord(ch) > 127 else ch for ch in serialized_str)
        return escaped

    # If next element is alternatives, try to find a common delimiter
    # For now, don't infer from alternatives (too complex)
    return ""


def generate_pattern_variants(
    pattern_elements: list[dict[str, Any]],
) -> list[tuple[str, dict[str, str]]]:
    """
    Generate all pattern variants from pattern elements.

    Handles cartesian products when multiple alternatives are used.
    Automatically infers delimiters for field extraction by looking ahead.

    Args:
        pattern_elements: List of pattern element dicts

    Returns:
        List of tuples: (pattern_string, option_values_dict)
        where option_values_dict maps 'option' -> matched option text
    """
    # Check if the last element is a field without a delimiter
    # If so, we need to use ESTRING with $ anchor instead of ANYSTRING + $
    last_elem = pattern_elements[-1] if pattern_elements else None
    last_is_field_without_delim = (
        last_elem
        and "field" in last_elem
        and not last_elem.get("until")
        and not last_elem.get("parser")
        and "alternatives" not in last_elem
    )

    # Track which elements are used as delimiters (to skip them)
    skip_elements = set()

    # First pass: identify which elements are inferred delimiters
    for i, elem in enumerate(pattern_elements):
        if "field" in elem and not elem.get("until") and not elem.get("parser"):
            # Check if next element can be used as delimiter
            if i + 1 < len(pattern_elements):
                next_elem = pattern_elements[i + 1]
                # Only simple text or serialized elements can be delimiters
                if "text" in next_elem or "serialized" in next_elem:
                    skip_elements.add(i + 1)

    # Expand each element to its variants, handling automatic delimiter inference
    # Also track which variants have options (for later processing)
    element_variants: list[PatternVariantList] = []
    variant_has_options: list[bool] = []  # Parallel array tracking if each variant has options

    for i, elem in enumerate(pattern_elements):
        if i in skip_elements:
            # This element was consumed as a delimiter, skip it
            continue

        if i == len(pattern_elements) - 1 and last_is_field_without_delim:
            # Last element is a field without delimiter - use ESTRING with $ anchor
            field_name = elem["field"]
            anchor_variant: PatternVariantList = [[f"@ESTRING:{field_name}:$@"]]
            element_variants.append(anchor_variant)
            variant_has_options.append(False)
        elif "field" in elem and not elem.get("until") and not elem.get("parser"):
            # Field without explicit delimiter - look ahead to infer delimiter
            delimiter = _infer_delimiter(pattern_elements, i)
            if delimiter:
                # Use ESTRING with inferred delimiter
                field_name = elem["field"]
                delim_variant: PatternVariantList = [[f"@ESTRING:{field_name}:{delimiter}@"]]
                element_variants.append(delim_variant)
            else:
                # No delimiter found, use ANYSTRING
                element_variants.append(expand_pattern_element(elem))
            variant_has_options.append(False)
        else:
            element_variants.append(expand_pattern_element(elem))
            variant_has_options.append("options" in elem)

    # Compute cartesian product of all element variants
    all_combinations = product(*element_variants)

    # Join each combination into a complete pattern string
    patterns = []
    for combo in all_combinations:
        # Extract option values and pattern fragments
        option_values = {}
        pattern_parts = []

        for i, variant in enumerate(combo):
            # Check if this is an options element (returns tuple with (name, value))
            if variant_has_options[i] and isinstance(variant, tuple):
                fragments, opt_data = variant
                pattern_parts.extend(fragments)
                # opt_data is (option_name, option_value)
                option_name, option_value = opt_data
                option_values[option_name] = option_value
            elif isinstance(variant, list):
                # Regular element (returns list of fragments)
                pattern_parts.extend(variant)

        # Add anchors for full-line matching (critical for performance)
        # If last element was ESTRING with $ anchor, don't add another $
        if last_is_field_without_delim:
            pattern = "^" + "".join(pattern_parts)
        else:
            pattern = "^" + "".join(pattern_parts) + "$"

        # Store pattern with its option values
        patterns.append((pattern, option_values))

    return patterns


def extract_field_names(pattern_elements: list[dict[str, Any]]) -> list[str]:
    """
    Extract field names from pattern elements.

    Args:
        pattern_elements: List of pattern element dicts

    Returns:
        List of field names in order (includes option names as pseudo-fields)
    """
    fields = []
    for elem in pattern_elements:
        if "field" in elem:
            fields.append(elem["field"])
        elif "options" in elem:
            # Options contribute their name as a pseudo-field
            if isinstance(elem["options"], dict):
                option_name = elem["options"].get("name")
                if option_name:
                    fields.append(option_name)
        elif "text" in elem:
            # Extract field names from {PARSER:field} placeholders
            placeholder_pattern = r"\{[A-Z]+:([a-z_]+)\}"
            for match in re.finditer(placeholder_pattern, elem["text"]):
                fields.append(match.group(1))
        elif "alternatives" in elem:
            # Recursively extract from alternatives (all should have same fields)
            alt_fields = extract_field_names([elem["alternatives"][0]])
            fields.extend(alt_fields)
    return fields


def generate_message_value(
    rule_name: str, fields: list[str], option_values: Optional[dict[str, str]] = None
) -> str:
    """
    Generate the MESSAGE value template with encoded fields.

    Format: [rule_name]|field1=$field1|field2=$field2|

    Args:
        rule_name: Name of the rule
        fields: List of field names
        option_values: Dict mapping option names to their literal values (for this variant)

    Returns:
        MESSAGE value template string
    """
    if option_values is None:
        option_values = {}

    if not fields:
        return f"[{rule_name}]"

    # Build field parts, substituting option values with literals
    field_parts = []
    for field in fields:
        if field in option_values:
            # Option field - use literal value instead of $field
            field_parts.append(f"{field}={option_values[field]}")
        else:
            # Regular field - use $field placeholder
            field_parts.append(f"{field}=${field}")

    return f"[{rule_name}]|{'|'.join(field_parts)}|"


def generate_xml_rule(rule: dict[str, Any]) -> list[ET.Element]:
    """
    Generate syslog-ng XML rule elements from YAML rule definition.

    Args:
        rule: Rule dict from YAML

    Returns:
        List of XML Elements (one per option variant if options are used, otherwise one rule)
    """
    rule_name = rule["name"]
    pattern_elements = rule["pattern"]

    # Generate all pattern variants (returns list of tuples: (pattern, option_values))
    pattern_variants = generate_pattern_variants(pattern_elements)

    # Extract field names for MESSAGE encoding
    fields = extract_field_names(pattern_elements)

    # Check if any variants have option values
    has_options = any(option_values for _, option_values in pattern_variants)

    if has_options:
        # Create one rule per variant (each with different option value)
        rule_elems = []
        for i, (pattern_str, option_values) in enumerate(pattern_variants):
            rule_elem = ET.Element("rule")
            rule_elem.set("provider", "claude-logging")

            # Generate descriptive ID using option values
            # For action rule with action_type=Web Search, this becomes: action_Web_Search
            if option_values:
                # Use option values to create a descriptive suffix
                # Replace spaces with underscores for valid XML IDs
                option_suffix = "_".join(v.replace(" ", "_") for v in option_values.values())
                variant_id = f"{rule_name}_{option_suffix}"
            else:
                variant_id = f"{rule_name}_{i}"

            rule_elem.set("id", variant_id)
            rule_elem.set("class", "normalization")

            # Add pattern
            patterns_elem = ET.SubElement(rule_elem, "patterns")
            pattern_elem = ET.SubElement(patterns_elem, "pattern")
            pattern_elem.text = pattern_str

            # Add values with option values substituted as literals
            values_elem = ET.SubElement(rule_elem, "values")
            value_elem = ET.SubElement(values_elem, "value")
            value_elem.set("name", "MESSAGE")
            value_elem.text = generate_message_value(rule_name, fields, option_values)

            rule_elems.append(rule_elem)
        return rule_elems
    else:
        # No options - create single rule with all patterns
        rule_elem = ET.Element("rule")
        rule_elem.set("provider", "claude-logging")
        rule_elem.set("id", rule_name)
        rule_elem.set("class", "normalization")

        # Add patterns
        patterns_elem = ET.SubElement(rule_elem, "patterns")
        for pattern_str, _ in pattern_variants:
            pattern_elem = ET.SubElement(patterns_elem, "pattern")
            pattern_elem.text = pattern_str

        # Add values
        values_elem = ET.SubElement(rule_elem, "values")
        value_elem = ET.SubElement(values_elem, "value")
        value_elem.set("name", "MESSAGE")
        value_elem.text = generate_message_value(rule_name, fields, {})

        return [rule_elem]


def generate_patterndb(rules: list[dict[str, Any]]) -> str:
    """
    Generate complete syslog-ng patterndb XML from YAML rules.

    Args:
        rules: List of rule dicts from YAML

    Returns:
        Complete XML string
    """
    # Create root patterndb element
    root = ET.Element("patterndb")
    root.set("version", "6")
    root.set("pub_date", "2025-01-18")

    # Create ruleset
    ruleset = ET.SubElement(root, "ruleset")
    ruleset.set("name", "normalization")
    ruleset.set("id", "normalization")

    # Add description
    desc = ET.SubElement(ruleset, "description")
    desc.text = "Normalization rules for diff comparison"

    # Add pattern (matches all from 'claude' program)
    pattern = ET.SubElement(ruleset, "pattern")
    pattern.text = "claude"

    # Add rules
    rules_elem = ET.SubElement(ruleset, "rules")
    for rule in rules:
        # generate_xml_rule returns a list of rule elements (one or more)
        rule_elems = generate_xml_rule(rule)
        for rule_elem in rule_elems:
            rules_elem.append(rule_elem)

    # Convert to string with pretty printing
    xml_str = ET.tostring(root, encoding="unicode")

    # Use minidom for pretty printing
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")

    # Remove extra blank lines
    lines = [line for line in pretty_xml.split("\n") if line.strip()]
    return "\n".join(lines)


def generate_from_yaml(rules_data: dict[str, Any]) -> str:
    """
    Generate syslog-ng XML from YAML rules data.

    Args:
        rules_data: Parsed YAML dict with 'rules' key

    Returns:
        Complete XML string
    """
    rules = rules_data.get("rules", [])
    return generate_patterndb(rules)
