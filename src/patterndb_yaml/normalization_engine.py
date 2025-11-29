#!/usr/bin/env python3
"""
Normalization engine for applying hierarchical transformation rules.

This module orchestrates:
1. Pattern generation (YAML → syslog-ng XML via pattern_generator.py)
2. Pattern matching via syslog-ng (PatternMatcher)
3. Field extraction from encoded MESSAGE output
4. Transformation application (via functions from normalization_transforms.py)
5. Output formatting using templates

The engine is data-driven: rules are defined in YAML, transformations in Python.
"""

import atexit
import re
import tempfile
from pathlib import Path
from typing import Optional

import yaml

from .normalization_transforms import get_transform
from .pattern_filter import PatternMatcher
from .pattern_generator import generate_from_yaml


class NormalizationEngine:
    """
    Engine for normalizing lines using pattern-based transformation rules.
    """

    def __init__(self, rules_path: Path):
        """
        Initialize the normalization engine.

        Args:
            rules_path: Path to YAML rules file
        """
        self.rules_path = rules_path

        # Load rules from YAML
        with open(rules_path) as f:
            rules_data = yaml.safe_load(f)
            self.rules = rules_data.get("rules", [])

        # Generate syslog-ng XML patterns from YAML
        self.xml_content = generate_from_yaml(rules_data)

        # Write XML to temporary file (cleaned up on exit)
        self.xml_tempfile = tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", prefix="patterndb_", delete=False
        )
        self.xml_tempfile.write(self.xml_content)
        self.xml_tempfile.flush()
        self.xml_path = Path(self.xml_tempfile.name)

        # Register cleanup on exit
        atexit.register(self._cleanup)

        # Initialize pattern matcher with generated XML
        self.pattern_matcher = PatternMatcher(self.xml_path)

        # Build mapping of rule name -> rule for fast lookup
        self.rule_by_name = {rule["name"]: rule for rule in self.rules}

    def _parse_encoded_message(self, message: str) -> Optional[tuple[str, dict[str, str]]]:
        """
        Parse encoded MESSAGE output from syslog-ng pattern.

        Format: [rule_name]|field1=value1|field2=value2|

        Args:
            message: Encoded MESSAGE string

        Returns:
            Tuple of (rule_name, fields_dict) or None if not encoded
        """
        # Check if message has encoded format
        if not message.startswith("["):
            return None

        # Extract rule name
        match = re.match(r"\[([^\]]+)\]", message)
        if not match:
            return None

        rule_name = match.group(1)
        remainder = message[match.end() :]

        # Parse fields if present
        fields = {}
        if remainder.startswith("|") and remainder.endswith("|"):
            # Remove surrounding pipes
            field_str = remainder[1:-1]
            # Split on | to get field=value pairs
            if field_str:
                for pair in field_str.split("|"):
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        fields[key] = value

        return rule_name, fields

    def normalize(self, line: str) -> str:
        """
        Normalize a line by applying transformation rules.

        Args:
            line: Input line to normalize

        Returns:
            Normalized line suitable for comparison
        """
        # Preprocess line for pattern matching
        import re

        # Binary ANSI escape codes: ESC[ followed by numbers/semicolons, ending with letter
        BINARY_ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

        line_clean = line.rstrip("\r\n")

        # Strip binary ANSI codes (formatting only, not semantic)
        # These are escape sequences like \x1b[38;5;174m, \x1b[1m, \x1b[39m
        # They represent visual formatting and should be ignored for pattern matching
        # Original line is always preserved for output
        line_clean = BINARY_ANSI_PATTERN.sub("", line_clean)

        # Convert special characters to Unicode escape format for pattern matching
        # This escapes binary ANSI codes, Unicode, and control characters
        result = []
        i = 0
        while i < len(line_clean):
            ch = line_clean[i]

            # Convert non-ASCII and control characters to Unicode escape format
            # Control characters (0x00-0x1F except tab/LF/CR) should be escaped
            # This handles binary ANSI codes like \x1b[7m
            if ord(ch) > 127 or (ord(ch) < 32 and ch not in "\t\n\r"):
                result.append(f"[U+{ord(ch):04X}]")
            else:
                # Keep ASCII characters as-is (XML escaping is handled by XML library)
                result.append(ch)
            i += 1

        line_escaped = "".join(result)

        # Add anchors to force full-line matching (prevents substring search)
        # This is critical for performance with long lines
        line_anchored = "^" + line_escaped + "$"

        # Try to match the line against patterns
        matched = self.pattern_matcher.match(line_anchored)

        # Remove anchors from matched output (they were only needed for matching)
        if matched.startswith("^") and matched.endswith("$"):
            matched = matched[1:-1]

        # Parse encoded MESSAGE
        parsed = self._parse_encoded_message(matched)
        if not parsed:
            # No pattern matched or invalid encoding - return as-is
            return matched

        rule_name, fields = parsed

        # Look up the rule
        if rule_name not in self.rule_by_name:
            # Unknown rule - return encoded message
            return matched

        rule = self.rule_by_name[rule_name]

        # Apply field transformations
        transformed_fields = {}
        for field_name, field_value in fields.items():
            # Check if this field has transforms
            field_transforms = rule.get("field_transforms", {}).get(field_name, [])
            if field_transforms:
                transformed_value = self._apply_field_transforms(field_value, field_transforms)
                transformed_fields[field_name] = transformed_value
            else:
                transformed_fields[field_name] = field_value

        # Format output using template
        output_template: str = str(rule.get("output", matched))
        try:
            return output_template.format(**transformed_fields)
        except KeyError:
            # Template references missing field - return encoded message
            return matched

    def _apply_field_transforms(self, field_value: str, transforms: list[str]) -> str:
        """
        Apply a sequence of transformations to a field value.

        Args:
            field_value: The field value to transform
            transforms: List of transformation function names

        Returns:
            Transformed field value
        """
        result = field_value
        for transform_name in transforms:
            transform_func = get_transform(transform_name)
            if transform_func:
                result = transform_func(result)
        return result

    def _cleanup(self) -> None:
        """Clean up temporary XML file."""
        try:
            if hasattr(self, "xml_tempfile"):
                self.xml_tempfile.close()
            if hasattr(self, "xml_path") and self.xml_path.exists():
                self.xml_path.unlink()
        except Exception:
            pass  # Ignore cleanup errors

    def close(self) -> None:
        """Close the pattern matcher and clean up resources."""
        if self.pattern_matcher:
            self.pattern_matcher.close()
        self._cleanup()
