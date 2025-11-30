"""Version checking for syslog-ng dependency.

This module verifies that the installed syslog-ng version is compatible with
patterndb-yaml, checking against known working and incompatible versions.
"""

import re
import subprocess
import sys

from packaging.version import Version  # type: ignore[import-not-found]

# Minimum tested version - do not lower without adding tests for older versions
MIN_SYSLOG_NG_VERSION = "4.10.1"

# Known working versions (tested in CI)
KNOWN_WORKING_VERSIONS = [
    "4.10.1",  # Latest from official repos as of 2024-11-30, tested in CI
]

# Known incompatible versions
KNOWN_INCOMPATIBLE_VERSIONS = [
    "4.3",  # Distro default, incompatible - failed in CI
]


class SyslogNgVersionError(Exception):
    """Raised when syslog-ng version is incompatible or not found."""

    pass


def get_syslog_ng_version() -> str:
    """Get the installed syslog-ng version.

    Returns:
        Version string (e.g., "4.10.1").

    Raises:
        SyslogNgVersionError: If syslog-ng is not installed or version cannot be determined.
    """
    try:
        result = subprocess.run(
            ["syslog-ng", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        # Parse version from output like "syslog-ng 4 (4.10.1)"
        match = re.search(r"syslog-ng \d+ \(([0-9.]+)\)", result.stdout)
        if match:
            return match.group(1)
        else:
            raise SyslogNgVersionError("Could not parse syslog-ng version from output")
    except FileNotFoundError as e:
        raise SyslogNgVersionError(
            "syslog-ng not found. Please install syslog-ng 4.10.1 or higher.\n\n"
            "See installation instructions at:\n"
            "https://github.com/JeffreyUrban/patterndb-yaml/blob/main/SYSLOG_NG_INSTALLATION.md"
        ) from e
    except subprocess.CalledProcessError as e:
        raise SyslogNgVersionError(f"Error running syslog-ng --version: {e}") from e


def check_syslog_ng_version(allow_version_mismatch: bool = False, quiet: bool = False) -> str:
    """Check that syslog-ng version is compatible.

    Args:
        allow_version_mismatch: If True, only warn about incompatible versions instead of failing.
        quiet: If True, suppress warnings about newer untested versions.

    Returns:
        The installed syslog-ng version string.

    Raises:
        SyslogNgVersionError: If version is incompatible (unless allow_version_mismatch=True).
    """
    version_str = get_syslog_ng_version()

    # Check against known incompatible versions
    for incompatible in KNOWN_INCOMPATIBLE_VERSIONS:
        if version_str.startswith(incompatible):
            error_msg = (
                f"syslog-ng version {version_str} is known to be incompatible.\n"
                f"Please install syslog-ng {MIN_SYSLOG_NG_VERSION} or higher.\n\n"
                f"See installation instructions at:\n"
                f"https://github.com/JeffreyUrban/patterndb-yaml/blob/main/SYSLOG_NG_INSTALLATION.md"
            )
            if allow_version_mismatch:
                print(f"WARNING: {error_msg}", file=sys.stderr)
            else:
                raise SyslogNgVersionError(error_msg)

    # Check minimum version
    try:
        installed_version = Version(version_str)
        min_version = Version(MIN_SYSLOG_NG_VERSION)

        if installed_version < min_version:
            error_msg = (
                f"syslog-ng version {version_str} is below minimum "
                f"required version {MIN_SYSLOG_NG_VERSION}.\n"
                f"Please upgrade to syslog-ng {MIN_SYSLOG_NG_VERSION} or higher.\n\n"
                f"See installation instructions at:\n"
                f"https://github.com/JeffreyUrban/patterndb-yaml/blob/main/SYSLOG_NG_INSTALLATION.md"
            )
            if allow_version_mismatch:
                print(f"WARNING: {error_msg}", file=sys.stderr)
            else:
                raise SyslogNgVersionError(error_msg)
    except SyslogNgVersionError:
        # Re-raise version errors
        raise
    except Exception as e:
        # Version parsing failed, but continue with warning
        if not quiet:
            print(
                f"WARNING: Could not parse syslog-ng version '{version_str}': {e}",
                file=sys.stderr,
            )

    # Alert if version is newer than any tested version (unless --quiet)
    if not quiet and version_str not in KNOWN_WORKING_VERSIONS:
        try:
            installed_version = Version(version_str)
            max_tested_version = max(Version(v) for v in KNOWN_WORKING_VERSIONS)

            if installed_version > max_tested_version:
                print(
                    f"INFO: syslog-ng version {version_str} is newer than tested versions.\n"
                    f"Tested versions: {', '.join(KNOWN_WORKING_VERSIONS)}\n"
                    f"If you encounter issues, please report at:\n"
                    f"https://github.com/JeffreyUrban/patterndb-yaml/issues",
                    file=sys.stderr,
                )
        except Exception:
            # Version comparison failed, skip the newer version check
            pass

    return version_str
