"""Tests for normalization transformation functions."""

import pytest

from patterndb_yaml.normalization_transforms import (
    TRANSFORMS,
    get_transform,
    normalize_spinner,
    strip_ansi,
    strip_text_ansi,
)


@pytest.mark.unit
class TestStripAnsi:
    """Tests for strip_ansi function."""

    def test_strip_binary_ansi_codes(self):
        """Test removing binary ANSI escape sequences."""
        text = "\x1b[31mRed text\x1b[0m"
        result = strip_ansi(text)
        assert result == "Red text"

    def test_strip_multiple_ansi_codes(self):
        """Test removing multiple ANSI codes."""
        text = "\x1b[1m\x1b[31mBold Red\x1b[0m\x1b[39m"
        result = strip_ansi(text)
        assert result == "Bold Red"

    def test_strip_ansi_from_plain_text(self):
        """Test that plain text is unchanged."""
        text = "Plain text without codes"
        result = strip_ansi(text)
        assert result == text

    def test_strip_ansi_empty_string(self):
        """Test handling empty string."""
        result = strip_ansi("")
        assert result == ""

    def test_strip_complex_ansi_sequences(self):
        """Test removing complex ANSI sequences."""
        text = "\x1b[38;5;174mColor\x1b[0m \x1b[1mBold\x1b[22m"
        result = strip_ansi(text)
        assert result == "Color Bold"


@pytest.mark.unit
class TestStripTextAnsi:
    """Tests for strip_text_ansi function."""

    def test_strip_text_ansi_annotations(self):
        """Test removing text-format ANSI annotations."""
        text = "[38;5;174mColored text[39m"
        result = strip_text_ansi(text)
        assert result == "Colored text"

    def test_strip_multiple_text_ansi(self):
        """Test removing multiple text-format annotations."""
        text = "[1mBold[22m [31mRed[39m"
        result = strip_text_ansi(text)
        assert result == "Bold Red"

    def test_strip_text_ansi_from_plain_text(self):
        """Test that plain text is unchanged."""
        text = "Plain text"
        result = strip_text_ansi(text)
        assert result == text

    def test_strip_text_ansi_empty_string(self):
        """Test handling empty string."""
        result = strip_text_ansi("")
        assert result == ""

    def test_strip_text_ansi_preserves_brackets(self):
        """Test that normal brackets are preserved."""
        text = "[normal brackets] remain"
        result = strip_text_ansi(text)
        assert result == text


@pytest.mark.unit
class TestNormalizeSpinner:
    """Tests for normalize_spinner function."""

    def test_normalize_spinner_centered_dot(self):
        """Test normalizing centered dot spinner (U+00B7)."""
        text = "·Spinner message"
        result = normalize_spinner(text)
        assert result == "*Spinner message"

    def test_normalize_spinner_four_teardrop_spoked(self):
        """Test normalizing four teardrop-spoked asterisk (U+2722)."""
        text = "✢Spinner message"
        result = normalize_spinner(text)
        assert result == "*Spinner message"

    def test_normalize_spinner_eight_spoked(self):
        """Test normalizing eight spoked asterisk (U+2733)."""
        text = "✳Spinner message"
        result = normalize_spinner(text)
        assert result == "*Spinner message"

    def test_normalize_spinner_six_pointed_black_star(self):
        """Test normalizing six pointed black star (U+2736)."""
        text = "✶Spinner message"
        result = normalize_spinner(text)
        assert result == "*Spinner message"

    def test_normalize_spinner_heavy_teardrop_spoked(self):
        """Test normalizing heavy teardrop-spoked asterisk (U+273B)."""
        text = "✻Spinner message"
        result = normalize_spinner(text)
        assert result == "*Spinner message"

    def test_normalize_spinner_heavy_teardrop_pinwheel(self):
        """Test normalizing heavy teardrop-spoked pinwheel (U+273D)."""
        text = "✽Spinner message"
        result = normalize_spinner(text)
        assert result == "*Spinner message"

    def test_normalize_spinner_no_spinner(self):
        """Test that text without spinner is unchanged."""
        text = "Normal message"
        result = normalize_spinner(text)
        assert result == text

    def test_normalize_spinner_empty_string(self):
        """Test handling empty string."""
        result = normalize_spinner("")
        assert result == ""

    def test_normalize_spinner_only_spinner(self):
        """Test normalizing string with only a spinner."""
        text = "·"
        result = normalize_spinner(text)
        assert result == "*"


@pytest.mark.unit
class TestTransformRegistry:
    """Tests for transform registry and get_transform."""

    def test_transforms_registry_contains_all_functions(self):
        """Test that TRANSFORMS registry contains all expected functions."""
        assert "strip_ansi" in TRANSFORMS
        assert "strip_text_ansi" in TRANSFORMS
        assert "normalize_spinner" in TRANSFORMS

    def test_get_transform_strip_ansi(self):
        """Test getting strip_ansi transform."""
        transform = get_transform("strip_ansi")
        assert transform is strip_ansi
        # Test it works
        result = transform("\x1b[31mRed\x1b[0m")
        assert result == "Red"

    def test_get_transform_strip_text_ansi(self):
        """Test getting strip_text_ansi transform."""
        transform = get_transform("strip_text_ansi")
        assert transform is strip_text_ansi
        # Test it works
        result = transform("[31mRed[39m")
        assert result == "Red"

    def test_get_transform_normalize_spinner(self):
        """Test getting normalize_spinner transform."""
        transform = get_transform("normalize_spinner")
        assert transform is normalize_spinner
        # Test it works
        result = transform("·Message")
        assert result == "*Message"

    def test_get_transform_unknown_raises_keyerror(self):
        """Test that unknown transform raises KeyError."""
        with pytest.raises(KeyError, match="Unknown transformation function: invalid_transform"):
            get_transform("invalid_transform")

    def test_get_transform_empty_string_raises_keyerror(self):
        """Test that empty transform name raises KeyError."""
        with pytest.raises(KeyError, match="Unknown transformation function"):
            get_transform("")
