#!/usr/bin/env python3
"""
Transformation functions for normalization rules.

These functions are referenced by name in normalization_rules.yaml.
Each function takes a string and returns a transformed string.
"""

import re

# ANSI escape sequence patterns
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")  # Binary ANSI codes
TEXT_ANSI_PATTERN = re.compile(r"\[([0-9;]+)m")  # Text-format ANSI annotations


def strip_ansi(text: str) -> str:
    """
    Remove ANSI escape sequences from text.

    Args:
        text: Input text potentially containing ANSI codes

    Returns:
        Text with all ANSI escape sequences removed
    """
    return ANSI_ESCAPE_PATTERN.sub("", text)


def strip_text_ansi(text: str) -> str:
    """
    Remove text-format ANSI annotations from escape_filter.py output.

    Text-format annotations look like: [38;5;174m, [1m, [39m, etc.
    These are the textual representation of ANSI codes, not binary codes.

    Args:
        text: Input text potentially containing text-format ANSI annotations

    Returns:
        Text with all text-format ANSI annotations removed
    """
    return TEXT_ANSI_PATTERN.sub("", text)


def normalize_spinner(text: str) -> str:
    """
    Replace any Unicode spinner symbol with a standard marker.

    Spinner symbols include: · ✢ ✳ ✶ ✻ ✽
    (U+00B7, U+2722, U+2733, U+2736, U+273B, U+273D)

    Args:
        text: Text that may start with a spinner symbol

    Returns:
        Text with spinner replaced by standard marker
    """
    spinner_chars = ["·", "✢", "✳", "✶", "✻", "✽"]
    for spinner in spinner_chars:
        if text.startswith(spinner):
            return "*" + text[len(spinner) :]
    return text


# Registry of available transformation functions
# Maps function names (as used in YAML) to actual functions
TRANSFORMS = {
    "strip_ansi": strip_ansi,
    "strip_text_ansi": strip_text_ansi,
    "normalize_spinner": normalize_spinner,
}


def get_transform(name: str):
    """
    Get a transformation function by name.

    Args:
        name: Name of the transformation function

    Returns:
        The transformation function

    Raises:
        KeyError: If transformation function not found
    """
    if name not in TRANSFORMS:
        raise KeyError(f"Unknown transformation function: {name}")
    return TRANSFORMS[name]
