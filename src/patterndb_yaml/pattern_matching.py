"""Pattern matching utilities for component-based patterns.

This module provides utilities for matching and rendering pattern components
from YAML rule definitions. These utilities are used by SequenceProcessor
and other pattern-matching components.
"""

import re
from typing import Any

# Compile ANSI escape sequence regex once at module import time
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def match_pattern_components(
    line: str, pattern_components: list[dict[str, Any]], extract_fields: bool = False
) -> tuple[bool, dict[str, str]]:
    """
    Generic pattern matcher that walks through pattern components.

    Supports: alternatives, text, serialized, field (with parser).

    Args:
        line: Line to match against (ANSI codes will be stripped)
        pattern_components: List of component dicts from YAML pattern
        extract_fields: If True, extract and return field values

    Returns:
        Tuple of (matched: bool, fields: dict)
    """
    # Strip ANSI codes from line (use precompiled ANSI_RE)
    line_clean = ANSI_RE.sub("", line)

    pos = 0  # Current position in line_clean
    fields = {}  # Extracted field values

    for component in pattern_components:
        if pos > len(line_clean):
            return False, {}  # Ran past end of line

        if "alternatives" in component:
            # Try to match any alternative at current position
            matched = False
            for alt in component["alternatives"]:
                # Each alternative is a list of elements
                alt_text = render_component_sequence(alt)
                if line_clean[pos:].startswith(alt_text):
                    pos += len(alt_text)
                    matched = True
                    break

            if not matched:
                return False, {}  # No alternative matched

        elif "field" in component:
            # Extract field value from current position
            field_name = component["field"]
            parser = component.get("parser")

            if parser == "NUMBER":
                # Match digits
                match = re.match(r"\d+", line_clean[pos:])
                if not match:
                    return False, {}
                if extract_fields:
                    fields[field_name] = match.group()
                pos += len(match.group())
            else:
                # Extract until end of line (ANYSTRING behavior)
                # Note: ESTRING delimiter inference is handled in pattern_generator.py
                if extract_fields:
                    fields[field_name] = line_clean[pos:]
                pos = len(line_clean)

        elif "text" in component:
            # Fixed text must match exactly
            text = component["text"]
            if not line_clean[pos:].startswith(text):
                return False, {}
            pos += len(text)

        elif "serialized" in component:
            # Serialized characters must match exactly
            serialized_str = component["serialized"]
            if not line_clean[pos:].startswith(serialized_str):
                return False, {}
            pos += len(serialized_str)

    return True, fields


def render_component_sequence(components: list[dict[str, Any]]) -> str:
    """
    Render a sequence of pattern components to their literal text.

    Args:
        components: List of component dicts (text, serialized, etc.)

    Returns:
        Concatenated text representation
    """
    result = []
    for comp in components:
        if "text" in comp:
            result.append(comp["text"])
        elif "serialized" in comp:
            result.append(comp["serialized"])
        # Fields and alternatives not supported in literal rendering
    return "".join(result)
