"""Tests for syslog-ng version checking."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from patterndb_yaml.version_check import (
    MIN_SYSLOG_NG_VERSION,
    SyslogNgVersionError,
    check_syslog_ng_version,
    get_syslog_ng_version,
)


@pytest.mark.unit
class TestGetSyslogNgVersion:
    """Test get_syslog_ng_version function."""

    def test_parses_version_successfully(self) -> None:
        """Test parsing syslog-ng version from standard output."""
        mock_result = MagicMock()
        mock_result.stdout = "syslog-ng 4 (4.10.1)\n"

        with patch("subprocess.run", return_value=mock_result):
            version = get_syslog_ng_version()
            assert version == "4.10.1"

    def test_parses_different_version_format(self) -> None:
        """Test parsing different version numbers."""
        mock_result = MagicMock()
        mock_result.stdout = "syslog-ng 4 (4.11.0)\n"

        with patch("subprocess.run", return_value=mock_result):
            version = get_syslog_ng_version()
            assert version == "4.11.0"

    def test_raises_when_syslog_ng_not_found(self) -> None:
        """Test error when syslog-ng binary is not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(SyslogNgVersionError) as exc_info:
                get_syslog_ng_version()

            assert "syslog-ng not found" in str(exc_info.value)
            assert "SYSLOG_NG_INSTALLATION.md" in str(exc_info.value)

    def test_raises_when_version_parse_fails(self) -> None:
        """Test error when version output cannot be parsed."""
        mock_result = MagicMock()
        mock_result.stdout = "unexpected output format\n"

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(SyslogNgVersionError) as exc_info:
                get_syslog_ng_version()

            assert "Could not parse syslog-ng version" in str(exc_info.value)

    def test_raises_when_syslog_ng_command_fails(self) -> None:
        """Test error when syslog-ng --version command fails."""
        with patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "syslog-ng"),
        ):
            with pytest.raises(SyslogNgVersionError) as exc_info:
                get_syslog_ng_version()

            assert "Error running syslog-ng --version" in str(exc_info.value)


@pytest.mark.unit
class TestCheckSyslogNgVersion:
    """Test check_syslog_ng_version function."""

    @patch("patterndb_yaml.version_check.get_syslog_ng_version")
    def test_accepts_minimum_version(self, mock_get_version: MagicMock, capsys) -> None:
        """Test that minimum version (4.10.1) is accepted."""
        mock_get_version.return_value = MIN_SYSLOG_NG_VERSION
        version = check_syslog_ng_version()
        assert version == MIN_SYSLOG_NG_VERSION

        # Should not print any warnings for known working version
        captured = capsys.readouterr()
        assert captured.err == ""

    @patch("patterndb_yaml.version_check.get_syslog_ng_version")
    def test_accepts_known_working_version(self, mock_get_version: MagicMock, capsys) -> None:
        """Test that known working versions are accepted without warnings."""
        mock_get_version.return_value = "4.10.1"
        version = check_syslog_ng_version()
        assert version == "4.10.1"

        # Should not print any warnings
        captured = capsys.readouterr()
        assert captured.err == ""

    @patch("patterndb_yaml.version_check.get_syslog_ng_version")
    def test_rejects_incompatible_version(self, mock_get_version: MagicMock) -> None:
        """Test that known incompatible version (4.3) is rejected."""
        mock_get_version.return_value = "4.3"
        with pytest.raises(SyslogNgVersionError) as exc_info:
            check_syslog_ng_version()

        assert "4.3" in str(exc_info.value)
        assert "incompatible" in str(exc_info.value)
        assert "SYSLOG_NG_INSTALLATION.md" in str(exc_info.value)

    @patch("patterndb_yaml.version_check.get_syslog_ng_version")
    def test_rejects_version_below_minimum(self, mock_get_version: MagicMock) -> None:
        """Test that versions below minimum are rejected."""
        mock_get_version.return_value = "4.9.0"
        with pytest.raises(SyslogNgVersionError) as exc_info:
            check_syslog_ng_version()

        assert "below minimum" in str(exc_info.value)
        assert MIN_SYSLOG_NG_VERSION in str(exc_info.value)
        assert "SYSLOG_NG_INSTALLATION.md" in str(exc_info.value)

    @patch("patterndb_yaml.version_check.get_syslog_ng_version")
    def test_allows_incompatible_with_flag(self, mock_get_version: MagicMock, capsys) -> None:
        """Test that incompatible version is allowed with allow_version_mismatch."""
        mock_get_version.return_value = "4.3"
        version = check_syslog_ng_version(allow_version_mismatch=True)
        assert version == "4.3"

        # Should print warning to stderr
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "incompatible" in captured.err

    @patch("patterndb_yaml.version_check.get_syslog_ng_version")
    def test_allows_below_minimum_with_flag(self, mock_get_version: MagicMock, capsys) -> None:
        """Test that version below minimum is allowed with allow_version_mismatch."""
        mock_get_version.return_value = "4.9.0"
        version = check_syslog_ng_version(allow_version_mismatch=True)
        assert version == "4.9.0"

        # Should print warning to stderr
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "below minimum" in captured.err

    @patch("patterndb_yaml.version_check.get_syslog_ng_version")
    def test_warns_about_newer_version(self, mock_get_version: MagicMock, capsys) -> None:
        """Test that newer untested version shows info message."""
        mock_get_version.return_value = "4.12.0"
        version = check_syslog_ng_version()
        assert version == "4.12.0"

        # Should print info message to stderr
        captured = capsys.readouterr()
        assert "INFO" in captured.err
        assert "newer than tested versions" in captured.err
        assert "4.12.0" in captured.err

    @patch("patterndb_yaml.version_check.get_syslog_ng_version")
    def test_quiet_suppresses_newer_version_warning(
        self, mock_get_version: MagicMock, capsys
    ) -> None:
        """Test that --quiet suppresses newer version info message."""
        mock_get_version.return_value = "4.12.0"
        version = check_syslog_ng_version(quiet=True)
        assert version == "4.12.0"

        # Should not print anything
        captured = capsys.readouterr()
        assert captured.err == ""

    @patch("patterndb_yaml.version_check.get_syslog_ng_version")
    def test_accepts_newer_version_without_quiet(self, mock_get_version: MagicMock, capsys) -> None:
        """Test that newer version is accepted (just with info message)."""
        mock_get_version.return_value = "5.0.0"
        version = check_syslog_ng_version()
        assert version == "5.0.0"

        # Should show info but not fail
        captured = capsys.readouterr()
        assert "INFO" in captured.err
        assert "newer than tested" in captured.err

    @patch("patterndb_yaml.version_check.get_syslog_ng_version")
    def test_version_comparison_logic(self, mock_get_version: MagicMock) -> None:
        """Test that version comparison works correctly."""
        # Test that 4.10.1 > 4.3
        mock_get_version.return_value = "4.10.1"
        version = check_syslog_ng_version()
        assert version == "4.10.1"

        # Test that 4.10.2 > 4.10.1
        mock_get_version.return_value = "4.10.2"
        version = check_syslog_ng_version(quiet=True)
        assert version == "4.10.2"

    @patch("patterndb_yaml.version_check.get_syslog_ng_version")
    def test_handles_unparseable_version_gracefully(
        self, mock_get_version: MagicMock, capsys
    ) -> None:
        """Test that unparseable versions are handled gracefully."""
        mock_get_version.return_value = "unknown"
        # Should not raise, just warn
        version = check_syslog_ng_version()
        assert version == "unknown"

        # Should show warning about parsing
        captured = capsys.readouterr()
        assert "WARNING" in captured.err or "Could not parse" in captured.err

    @patch("patterndb_yaml.version_check.get_syslog_ng_version")
    def test_error_messages_include_installation_link(self, mock_get_version: MagicMock) -> None:
        """Test that all error messages include link to installation guide."""
        # Test incompatible version error
        mock_get_version.return_value = "4.3"
        with pytest.raises(SyslogNgVersionError) as exc_info:
            check_syslog_ng_version()
        assert "SYSLOG_NG_INSTALLATION.md" in str(exc_info.value)

        # Test below minimum version error
        mock_get_version.return_value = "4.0.0"
        with pytest.raises(SyslogNgVersionError) as exc_info:
            check_syslog_ng_version()
        assert "SYSLOG_NG_INSTALLATION.md" in str(exc_info.value)

        # Test syslog-ng not found error
        mock_get_version.side_effect = SyslogNgVersionError(
            "syslog-ng not found. Please install syslog-ng 4.10.1 or higher.\n\n"
            "See installation instructions at:\n"
            "https://github.com/JeffreyUrban/patterndb-yaml/blob/main/SYSLOG_NG_INSTALLATION.md"
        )
        with pytest.raises(SyslogNgVersionError) as exc_info:
            check_syslog_ng_version()
        assert "SYSLOG_NG_INSTALLATION.md" in str(exc_info.value)
