# Packaging Analysis: Handling syslog-ng Dependency (CORRECTED)

Analysis of how to handle the syslog-ng dependency across different packaging methods for `patterndb-yaml`.

## What We Actually Need

**Critical correction:** `patterndb-yaml` runs **syslog-ng itself as a subprocess** (not pdbtool).

See `src/patterndb_yaml/pattern_filter.py:90`:
```python
cmd = [
    "syslog-ng",
    "-f", self.config_file,
    "--foreground",
    "--stderr",
    "--no-caps",
    "--persist-file", persist_file,
]
self.process = subprocess.Popen(cmd, ...)
```

**What we need:**
- The `syslog-ng` binary executable
- With the `db-parser()` module/plugin included
- Ability to run syslog-ng in foreground mode

**Source:** [syslog-ng db-parser documentation](https://www.syslog-ng.com/technical-documents/doc/syslog-ng-open-source-edition/3.21/administration-guide/db-parser-process-message-content-with-a-pattern-database-patterndb/)

## Package Comparison

| Package | Provides syslog-ng binary? | Includes db-parser? | Size (Homebrew) |
|---------|---------------------------|---------------------|-----------------|
| **syslog-ng-core** (Linux) | ✅ Yes | ✅ Yes (built-in) | ~20-30MB |
| **syslog-ng** (Homebrew) | ✅ Yes | ✅ Yes (built-in) | 122.9MB (4,032 files) |

**Key insight:** Both packages provide what we need. The difference is:
- **syslog-ng-core**: Minimal install with core functionality
- **syslog-ng**: Includes additional modules (Kafka, MQTT, gRPC, MongoDB, Redis, SNMP, etc.)

**Source:** [Debian syslog-ng-core package](https://packages.debian.org/sid/syslog-ng-core)

## Packaging Method Analysis

### 1. Homebrew (macOS + Linux) ✅ Recommended

**Current situation:**
- Homebrew has the full `syslog-ng` formula (version 3.38.1+, updated to 4.0.1)
- Works on macOS and Linux
- No separate `syslog-ng-core` package available
- Formula already has 21 dependencies (abseil, glib, grpc, hiredis, ivykis, json-c, libdbi, libmaxminddb, libnet, libpaho-mqtt, librdkafka, mongo-c-driver, net-snmp, openssl@3, pcre2, protobuf, python@3.14, rabbitmq-c, riemann-client, gettext, pkgconf)

**Recommendation:** **Use `depends_on "syslog-ng"` in Homebrew formula**

```ruby
class PatterndbYaml < Formula
  desc "YAML-based pattern matching for log normalization using syslog-ng patterndb"
  homepage "https://github.com/JeffreyUrban/patterndb-yaml"
  url "..."
  sha256 "..."
  license "MIT"

  depends_on "syslog-ng"  # Automatic dependency

  # ... rest of formula
end
```

**Pros:**
- Zero user configuration needed
- Automatic installation and updates
- Well-tested by Homebrew community
- db-parser module included
- **Cross-platform:** Works on both macOS and Linux

**Cons:**
- Installs 122MB when we only need ~20-30MB functionality
- Includes modules we don't use (Kafka, MQTT, etc.)

**Verdict:** Trade-off accepted - user experience trumps disk space. Homebrew on Linux provides same automatic dependency management as macOS.

**Source:** [Syslog-ng in Homebrew](https://www.syslog-ng.com/community/b/blog/posts/syslog-ng-is-now-available-in-homebrew), [Homebrew Formula](https://formulae.brew.sh/formula/syslog-ng)

---

### 2. Linux Native Packages (apt/dnf) ⚠️ Manual Installation Required

**IMPORTANT:** Must use official syslog-ng repositories, not distro defaults (distro versions have compatibility issues).

**For Debian/Ubuntu (apt):**
```bash
# Add official syslog-ng repository (required - distro versions incompatible)
wget -qO - https://ose-repo.syslog-ng.com/apt/syslog-ng-ose-pub.asc | \
  sudo gpg --dearmor -o /etc/apt/keyrings/syslog-ng-ose.gpg
echo "deb [signed-by=/etc/apt/keyrings/syslog-ng-ose.gpg] \
  https://ose-repo.syslog-ng.com/apt/ stable ubuntu-noble" | \
  sudo tee /etc/apt/sources.list.d/syslog-ng-ose.list
sudo apt-get update

# Install syslog-ng-core (minimal)
sudo apt-get install syslog-ng-core

# Then install patterndb-yaml
pipx install patterndb-yaml
```

**For RHEL/Fedora (dnf):**
```bash
# Add official repository (required)
sudo dnf config-manager --add-repo https://ose-repo.syslog-ng.com/yum/nightly/rhel9/
sudo rpm --import https://ose-repo.syslog-ng.com/yum/nightly/rhel9/repodata/repomd.xml.key

# Install syslog-ng
sudo dnf install syslog-ng

# Then install patterndb-yaml
pipx install patterndb-yaml
```

**Pros:**
- Minimal installation (syslog-ng-core ~20-30MB)
- Native package management integration
- Well-understood by system administrators

**Cons:**
- **Requires manual setup** before installing patterndb-yaml
- **Multi-step process** (add repo, install syslog-ng, then install patterndb-yaml)
- Users may forget to add official repos and install incompatible distro versions
- Different commands per distro

**Verdict:** Works but requires careful documentation. Users must understand they need official repos, not distro defaults.

**Source:** [Installing syslog-ng on Ubuntu](https://www.syslog-ng.com/community/b/blog/posts/installing-the-latest-syslog-ng-on-ubuntu-and-other-deb-distributions)

---

### 3. pip/pipx (All platforms) ⚠️ Cannot Install System Dependencies

**Reality:** pip/pipx cannot install the syslog-ng binary.

**Solution:** Runtime check with helpful, platform-specific error messages.

**Implementation:**

```python
# In src/patterndb_yaml/__init__.py or cli.py
import shutil
import sys
import platform

def check_syslog_ng_binary():
    """Verify syslog-ng binary is available with db-parser support."""
    if not shutil.which("syslog-ng"):
        system = platform.system()

        if system == "Darwin":  # macOS
            msg = """
ERROR: syslog-ng is required but not found.

Install via Homebrew:
    brew install syslog-ng

Or install patterndb-yaml via Homebrew (recommended):
    brew tap jeffreyurban/patterndb-yaml
    brew install patterndb-yaml

See: https://github.com/JeffreyUrban/patterndb-yaml#installation
"""
        elif system == "Linux":
            # Try to detect distro
            try:
                with open("/etc/os-release") as f:
                    os_release = f.read()
                if "debian" in os_release.lower() or "ubuntu" in os_release.lower():
                    package_cmd = "sudo apt-get install syslog-ng-core"
                elif "fedora" in os_release.lower() or "rhel" in os_release.lower():
                    package_cmd = "sudo dnf install syslog-ng"
                else:
                    package_cmd = "# Use your package manager to install syslog-ng"
            except:
                package_cmd = "# Use your package manager to install syslog-ng-core"

            msg = f"""
ERROR: syslog-ng is required but not found.

Install syslog-ng:
    {package_cmd}

For detailed instructions:
    https://github.com/JeffreyUrban/patterndb-yaml/blob/main/SYSLOG_NG_INSTALLATION.md
"""
        else:  # Windows or unknown
            msg = """
ERROR: syslog-ng is required but not found.

Windows is not currently supported.
Consider using Docker or WSL2:
    https://github.com/JeffreyUrban/patterndb-yaml#docker
"""

        print(msg, file=sys.stderr)
        sys.exit(1)
```

**When to call:** At the start of `PatternMatcher.__init__()` or in CLI entry point.

**Pros:**
- Clear, actionable error messages
- Platform-specific guidance
- Fails fast with helpful information

**Cons:**
- Requires manual syslog-ng installation
- Extra step for users

---

### 4. Snap Packages 📦 Potential for Auto-Install

**What is Snap:**
- Universal Linux package format from Ubuntu
- Bundles all dependencies including system libraries
- Automatic updates
- Works across most Linux distributions

**How it could work for patterndb-yaml:**
```bash
# Single command installs both patterndb-yaml and syslog-ng
sudo snap install patterndb-yaml
```

**Technical approach:**
- Bundle syslog-ng binary and libraries inside the snap
- Use `stage-packages` to include syslog-ng from Ubuntu repos
- All dependencies automatically resolved and bundled

**Effort estimation:**

*Setup (one-time):*
- Create `snapcraft.yaml` configuration file (~30-60 minutes)
- Set up GitHub Actions for automated builds (~30-60 minutes)
- Test snap confinement with subprocess execution (~1-2 hours)
- Register snap name on Snapcraft store (~15 minutes)

*Example snapcraft.yaml for patterndb-yaml:*
```yaml
name: patterndb-yaml
summary: YAML-based pattern matching for log normalization
description: |
  YAML-based pattern matching with multi-line capabilities for log
  normalization using syslog-ng patterndb
base: core22
confinement: classic  # Likely needed for subprocess execution
grade: stable

apps:
  patterndb-yaml:
    command: bin/patterndb-yaml
    plugs: [home, network]

parts:
  patterndb-yaml:
    plugin: python
    source: .
    stage-packages:
      - syslog-ng-core  # Bundled automatically from Ubuntu repos
```

*Ongoing maintenance:*
- Automatic builds via GitHub Actions (zero effort after setup)
- Snap store automatically updates users
- May need to adjust confinement if subprocess issues arise

**Pros:**
- **Automatic dependency bundling** - snap includes syslog-ng automatically
- Works across many Linux distributions
- Automatic updates via snapd
- Single installation command
- Minimal ongoing maintenance once set up

**Cons:**
- Requires snapd installed (not universal on all Linux distros)
- Larger package size (bundles all dependencies)
- **Classic confinement likely required** for subprocess execution
- Classic snaps require manual approval for Snapcraft store publication
- May bundle Ubuntu's syslog-ng (need to verify version compatibility)

**Estimated total effort:** ~3-5 hours initial setup, minimal ongoing

**Verdict:** **Low-to-moderate effort, worth investigating** - could provide automatic syslog-ng installation on Linux without requiring Homebrew. Main unknown is confinement/subprocess compatibility.

**Sources:**
- [Craft a Python app - Snapcraft](https://snapcraft.io/docs/python-apps)
- [Classic confinement](https://snapcraft.io/docs/classic-confinement)
- [Example Python CLI snap](https://dmnfarrell.github.io/software/python-snap)
- [Complete working snapcraft.yaml examples](https://github.com/jhenstridge/python-snap-pkg/blob/master/examples/hello-world/snap/snapcraft.yaml)

---

### 5. Flatpak 📦 Limited Applicability

**What is Flatpak:**
- Desktop application sandboxing and distribution
- Bundles dependencies in runtimes
- Focused on GUI applications

**Applicability to patterndb-yaml:**

**Pros:**
- Can bundle dependencies automatically
- Runtime-based dependency sharing

**Cons:**
- **Primarily for desktop GUI apps** - not CLI tools
- Single-file bundles don't include dependencies (defeats purpose)
- **Not suitable for CLI tools or daemon processes**
- Sandboxing may interfere with subprocess execution
- Need to maintain flatpak packaging

**Verdict:** **Not recommended** - Flatpak is designed for desktop applications, not CLI tools that run system daemons as subprocesses.

**Source:** [Flatpak Dependencies](https://docs.flatpak.org/en/latest/dependencies.html), [Single-file bundles](https://docs.flatpak.org/en/latest/single-file-bundles.html)

---

### 6. AppImage 📦 Promising for Bundling

**What is AppImage:**
- Self-contained executable for Linux
- Bundles all dependencies (including system libraries)
- No installation required - just download and run
- Works across Linux distributions

**How it could work for patterndb-yaml:**
- Bundle patterndb-yaml + syslog-ng binary + all shared libraries
- Single executable file users can download and run
- Use `appimage-builder` to automatically resolve and bundle dependencies

**Technical approach:**
```bash
# User downloads single file
wget https://github.com/JeffreyUrban/patterndb-yaml/releases/download/v1.0.0/patterndb-yaml-x86_64.AppImage
chmod +x patterndb-yaml-x86_64.AppImage

# Run directly - syslog-ng bundled inside
./patterndb-yaml-x86_64.AppImage --rules rules.yaml < app.log
```

**Effort estimation:**

*Setup (one-time):*
- Create `AppImageBuilder.yml` recipe file (~1-2 hours)
- Set up GitHub Actions for automated builds (~1-2 hours)
- Test full bundle with syslog-ng on multiple distros (~2-3 hours)
- Configure multi-architecture builds (x86_64, aarch64) (~1-2 hours)

*Example AppImageBuilder.yml for patterndb-yaml:*
```yaml
version: 1

script:
  - rm -rf AppDir | true
  - mkdir -p AppDir/usr/src
  - cp -r src tests AppDir/usr/src/
  - python3 -m pip install --system --ignore-installed --prefix=/usr --root=AppDir .

AppDir:
  path: ./AppDir
  app_info:
    id: com.github.jeffreyurban.patterndb-yaml
    name: patterndb-yaml
    icon: utilities-terminal
    version: latest
    exec: usr/bin/python3
    exec_args: "$APPDIR/usr/bin/patterndb-yaml $@"

  apt:
    arch: amd64
    sources:
      - sourceline: 'deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ focal main universe'
    include:
      - python3
      - python3-pip
      - syslog-ng-core  # Bundled automatically

  runtime:
    env:
      PATH: '${APPDIR}/usr/bin:${PATH}'

  test:
    fedora:
      image: appimagecrafters/tests-env:fedora-35
    debian:
      image: appimagecrafters/tests-env:debian-stable
    ubuntu:
      image: appimagecrafters/tests-env:ubuntu-focal

AppImage:
  update-information: guess
  sign-key: None
  arch: x86_64
```

*GitHub Actions integration:*
```yaml
- name: Build AppImage
  uses: AppImageCrafters/build-appimage@master
  with:
    recipe: AppImageBuilder.yml
```

*Ongoing maintenance:*
- Automatic builds via GitHub Actions (zero effort after setup)
- Manual upload to GitHub Releases
- Users manually download updates (no auto-update)
- May need to rebuild for new architectures

**Pros:**
- **Complete bundling** - includes syslog-ng binary and all dependencies
- No installation or package manager required
- Works across Linux distributions
- Can create "full bundle" with all system libraries (~30MB overhead)
- Single file distribution
- Easy to distribute via GitHub Releases
- GitHub Actions integration well-documented

**Cons:**
- Linux only (no macOS/Windows)
- Larger file size (~50-60MB with full bundle, potentially larger with syslog-ng)
- Need to build for multiple architectures (x86_64, aarch64)
- No automatic updates for users
- More complex build process than snap
- Need to bundle from Ubuntu repos (may have version compatibility issues)

**Estimated total effort:** ~5-8 hours initial setup, ~30 min per release for manual upload

**Verdict:** **Moderate effort, very portable** - provides true "batteries included" distribution but requires more setup than snap. Best for users who can't or won't use package managers.

**Sources:**
- [AppImage Full Bundle](https://appimage-builder.readthedocs.io/en/latest/advanced/full_bundle.html)
- [Packaging Native Binaries](https://docs.appimage.org/packaging-guide/from-source/native-binaries.html)
- [Python AppImage Examples](https://github.com/niess/python-appimage)
- [appimage-builder Python Example](https://github.com/AppImageCrafters/appimage-builder-python-example)
- [GitHub Actions Integration](https://appimage-builder.readthedocs.io/en/latest/hosted-services/github-actions.html)
- [Complete Recipe Examples](https://appimage-builder.readthedocs.io/en/latest/examples/pyqt.html)

---

### 5. Native Linux Packages (.deb / .rpm) - Future

#### Debian/Ubuntu Package
```
Package: patterndb-yaml
Version: 0.1.0
Depends: python3 (>= 3.9), syslog-ng-core (>= 3.35)
Architecture: all
Description: YAML-based pattern matching for log normalization
```

Install: `sudo apt install patterndb-yaml`
- Automatically installs `syslog-ng-core` as dependency
- Native package management
- Proper system integration

#### RPM (RHEL/Fedora)
```
Name: patterndb-yaml
Version: 0.1.0
Requires: python3 >= 3.9
Requires: syslog-ng >= 3.35
```

**Pros:**
- Automatic dependency resolution
- Native to Linux ecosystem
- Clean installation/removal

**Cons:**
- Maintenance overhead (packaging for multiple distros)
- Need to set up package repositories
- Or submit to official repos (lengthy approval process)

**Verdict:** Worth considering if project gains traction on Linux servers.

---

## Packaging Methods Comparison Summary

| Method | Effort (Initial) | Effort (Ongoing) | Auto-bundles syslog-ng? | Cross-platform? | User friction | Best for |
|--------|-----------------|------------------|------------------------|----------------|---------------|----------|
| **Homebrew** | Low (~1 hr) | None | ✅ Yes | macOS + Linux | Very low | Primary recommendation |
| **Snap** | Low-Med (~3-5 hrs) | None | ✅ Yes | Linux only | Low | Linux users without Homebrew |
| **AppImage** | Medium (~5-8 hrs) | Low (~30 min/release) | ✅ Yes | Linux only | Very low | Users without package managers |
| **apt/dnf** | Low (~1 hr docs) | None | ❌ No | Linux only | High (manual setup) | Advanced users only |
| **pip/pipx** | Low (~2 hrs runtime check) | None | ❌ No | All platforms | High (manual syslog-ng install) | Library users |

**Key insights:**

1. **Homebrew wins for effort-to-value ratio:**
   - Minimal setup (just add `depends_on "syslog-ng"`)
   - Works on macOS and Linux
   - Zero ongoing maintenance
   - Recommended as primary method

2. **Snap is promising alternative for Linux:**
   - Low-moderate initial effort (~3-5 hours)
   - Automatic bundling like Homebrew
   - Main risk: confinement/subprocess compatibility (needs testing)
   - Worth investigating if Homebrew adoption is low on Linux

3. **AppImage provides maximum portability:**
   - Higher initial effort (~5-8 hours)
   - Truly portable - no package manager needed
   - Good for edge cases (air-gapped systems, unusual distros)
   - Worth considering as supplementary distribution method

4. **apt/dnf manual install is fallback only:**
   - High user friction (multi-step, error-prone)
   - Risk of version incompatibility if users forget official repos
   - Document for reference but don't emphasize

---

## Version Compatibility and Runtime Checks

**Critical requirement:** When relying on external package manager installs (Homebrew, apt, dnf), we must verify the syslog-ng version matches what we've tested in CI.

### Implementation Approach

**Runtime version check:**
```python
import re
import subprocess
import sys
from packaging import version

# Version requirements
MIN_SYSLOG_NG_VERSION = "4.10.1"  # Minimum tested version
KNOWN_WORKING_VERSIONS = [
    "4.10.1",  # Latest from official repos as of 2024-11-30, tested in CI
]
KNOWN_INCOMPATIBLE_VERSIONS = [
    "4.3",  # Distro default, incompatible - failed in CI
]

def parse_syslog_ng_version(version_output: str) -> str:
    """Parse version from 'syslog-ng --version' output.

    Example output: "syslog-ng 4 (4.10.1)"
    Returns: "4.10.1"
    """
    # Match pattern: "syslog-ng X (X.Y.Z)"
    match = re.search(r'syslog-ng\s+\d+\s+\(([0-9.]+)\)', version_output)
    if match:
        return match.group(1)
    raise ValueError(f"Cannot parse version from: {version_output}")

def check_syslog_ng_version(allow_override: bool = False, quiet: bool = False):
    """Verify syslog-ng version compatibility.

    Args:
        allow_override: If True, only warn on version mismatch instead of failing
        quiet: If True, suppress informational messages to stderr
    """
    # Get syslog-ng version
    try:
        result = subprocess.run(
            ["syslog-ng", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version_str = parse_syslog_ng_version(result.stdout)
        ver = version.parse(version_str)
        major_version = ver.major
    except FileNotFoundError:
        print("ERROR: syslog-ng not found in PATH", file=sys.stderr)
        print("\nInstall syslog-ng from official repositories:", file=sys.stderr)
        print("  https://www.syslog-ng.com/community/b/blog/posts/installing-the-latest-syslog-ng-on-ubuntu-and-other-deb-distributions", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Cannot determine syslog-ng version: {e}", file=sys.stderr)
        sys.exit(1)

    # Check for known incompatible versions (always enforced)
    if version_str in KNOWN_INCOMPATIBLE_VERSIONS:
        print(f"ERROR: syslog-ng {version_str} is known to be INCOMPATIBLE with patterndb-yaml", file=sys.stderr)
        print(f"  This version failed in CI testing", file=sys.stderr)
        print(f"\nKnown incompatible versions: {', '.join(KNOWN_INCOMPATIBLE_VERSIONS)}", file=sys.stderr)
        print("\nInstall from official syslog-ng repositories (NOT distro defaults):", file=sys.stderr)
        print("  https://www.syslog-ng.com/community/b/blog/posts/installing-the-latest-syslog-ng-on-ubuntu-and-other-deb-distributions", file=sys.stderr)
        print("\nQuick setup (Ubuntu/Debian):", file=sys.stderr)
        print("  wget -qO - https://ose-repo.syslog-ng.com/apt/syslog-ng-ose-pub.asc | \\", file=sys.stderr)
        print("    sudo gpg --dearmor -o /etc/apt/keyrings/syslog-ng-ose.gpg", file=sys.stderr)
        print("  echo \"deb [signed-by=/etc/apt/keyrings/syslog-ng-ose.gpg] \\", file=sys.stderr)
        print("    https://ose-repo.syslog-ng.com/apt/ stable ubuntu-noble\" | \\", file=sys.stderr)
        print("    sudo tee /etc/apt/sources.list.d/syslog-ng-ose.list", file=sys.stderr)
        print("  sudo apt-get update && sudo apt-get install syslog-ng-core", file=sys.stderr)
        sys.exit(1)

    # Check minimum version (always enforced)
    if ver < version.parse(MIN_SYSLOG_NG_VERSION):
        print(f"ERROR: syslog-ng {version_str} is too old (minimum tested: {MIN_SYSLOG_NG_VERSION})", file=sys.stderr)
        print("\nInstall from official syslog-ng repositories:", file=sys.stderr)
        print("  https://www.syslog-ng.com/community/b/blog/posts/installing-the-latest-syslog-ng-on-ubuntu-and-other-deb-distributions", file=sys.stderr)
        sys.exit(1)

    # Check if version is in known working versions
    if version_str not in KNOWN_WORKING_VERSIONS:
        # Get max known working version to check if newer
        max_known = max(version.parse(v) for v in KNOWN_WORKING_VERSIONS)

        if ver > max_known:
            # Newer version than tested - alert user
            msg = f"""
NOTICE: syslog-ng {version_str} is NEWER than tested versions
  Tested versions: {', '.join(KNOWN_WORKING_VERSIONS)}
  Found: {version_str}

This newer version has not been tested with patterndb-yaml yet.
It will likely work, but please report any issues at:
  https://github.com/JeffreyUrban/patterndb-yaml/issues

IMPORTANT: Ensure you installed from official syslog-ng repos (NOT distro defaults).
Official repo setup:
  https://www.syslog-ng.com/community/b/blog/posts/installing-the-latest-syslog-ng-on-ubuntu-and-other-deb-distributions

Use --quiet to suppress this message.
"""
        elif ver >= version.parse(MIN_SYSLOG_NG_VERSION):
            # Between minimum and max known - probably okay
            msg = f"""
INFO: syslog-ng {version_str} has not been explicitly tested with patterndb-yaml
  Tested versions: {', '.join(KNOWN_WORKING_VERSIONS)}
  Found: {version_str}

This version will likely work if installed from official syslog-ng repos.

IMPORTANT: Distro-provided syslog-ng packages may be incompatible.
Ensure you installed from official repos:
  https://www.syslog-ng.com/community/b/blog/posts/installing-the-latest-syslog-ng-on-ubuntu-and-other-deb-distributions

Use --quiet to suppress this message.
"""

        if not quiet:
            print(msg, file=sys.stderr)
```

### CLI Integration

**Add flags to CLI:**
```python
@click.option(
    '--allow-version-mismatch',
    is_flag=True,
    help='Allow running with untested syslog-ng version (use at own risk)'
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    help='Suppress informational messages'
)
def main(allow_version_mismatch: bool, quiet: bool, ...):
    check_syslog_ng_version(allow_override=allow_version_mismatch, quiet=quiet)
    # ... rest of main
```

**Version check behavior:**
- Always fails on incompatible versions (4.3) - no override
- Always fails on versions < 4.10.1 (minimum)
- Shows NOTICE for newer untested versions (suppressible with --quiet)
- Shows INFO for versions between min and max (suppressible with --quiet)
- `--quiet` suppresses informational messages, not errors

### Benefits

- **Safety:** Ensures tested configuration in production
- **Flexibility:** Advanced users can override for newer versions
- **Debugging:** Clear error messages when version incompatibilities occur
- **CI alignment:** Runtime version matches CI-tested version
- **User awareness:** Users know when they're in unsupported territory

### CI Integration and Automatic Version Tracking

**Current CI behavior:**
- Installs latest syslog-ng from official repos (unpinned)
- Gets whatever version is current (4.10.1 as of 2024-11-30)

**Proposed automatic version tracking mechanism:**

#### Option 1: Semi-automatic with PR automation (Recommended)

**GitHub Actions workflow (`check-syslog-ng-version.yml`):**
```yaml
name: Check syslog-ng Version

on:
  schedule:
    - cron: '0 9 * * 1'  # Weekly on Monday at 9am UTC
  workflow_dispatch:  # Manual trigger

jobs:
  check-version:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Install latest syslog-ng
        run: |
          wget -qO - https://ose-repo.syslog-ng.com/apt/syslog-ng-ose-pub.asc | sudo gpg --dearmor -o /etc/apt/keyrings/syslog-ng-ose.gpg
          echo "deb [signed-by=/etc/apt/keyrings/syslog-ng-ose.gpg] https://ose-repo.syslog-ng.com/apt/ stable ubuntu-noble" | sudo tee /etc/apt/sources.list.d/syslog-ng-ose.list
          sudo apt-get update
          sudo apt-get install -y syslog-ng-core

      - name: Get installed version
        id: version
        run: |
          VERSION=$(syslog-ng --version | grep -oP 'syslog-ng \d+ \(\K[0-9.]+')
          echo "version=$VERSION" >> $GITHUB_OUTPUT
          echo "Found syslog-ng version: $VERSION"

      - name: Check if version is already supported
        id: check
        run: |
          VERSION="${{ steps.version.outputs.version }}"
          if grep -q "\"$VERSION\"" src/patterndb_yaml/version_check.py; then
            echo "supported=true" >> $GITHUB_OUTPUT
            echo "Version $VERSION already in KNOWN_WORKING_VERSIONS"
          else
            echo "supported=false" >> $GITHUB_OUTPUT
            echo "Version $VERSION is NEW - needs testing"
          fi

      - name: Run full test suite
        if: steps.check.outputs.supported == 'false'
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
          pytest --cov=src/patterndb_yaml

      - name: Update version list
        if: steps.check.outputs.supported == 'false'
        run: |
          VERSION="${{ steps.version.outputs.version }}"
          DATE=$(date +%Y-%m-%d)

          # Add version to KNOWN_WORKING_VERSIONS list
          sed -i "/KNOWN_WORKING_VERSIONS = \[/a\\    \"$VERSION\",  # Tested in CI on $DATE" src/patterndb_yaml/version_check.py

      - name: Create Pull Request
        if: steps.check.outputs.supported == 'false'
        uses: peter-evans/create-pull-request@v5
        with:
          commit-message: "Add syslog-ng ${{ steps.version.outputs.version }} to known working versions"
          title: "Add syslog-ng ${{ steps.version.outputs.version }} to known working versions"
          body: |
            Automatic version tracking detected new syslog-ng version from official repos.

            - **Version:** ${{ steps.version.outputs.version }}
            - **Tested:** All tests passed in CI
            - **Date:** $(date +%Y-%m-%d)

            This PR adds the new version to `KNOWN_WORKING_VERSIONS` list.

            Review and merge to approve this version for production use.
          branch: auto/syslog-ng-${{ steps.version.outputs.version }}
          delete-branch: true
```

**Benefits:**
- ✅ Automatic weekly checks for new versions
- ✅ Runs full test suite before adding to list
- ✅ Creates PR for human review before merging
- ✅ Maintains audit trail of when versions were tested
- ✅ Manual approval step ensures safety

**Implementation location:**
- File: `src/patterndb_yaml/version_check.py`
- Workflow: `.github/workflows/check-syslog-ng-version.yml`

#### Option 2: Fully automatic (Not recommended - less safe)

- Auto-merge PR if tests pass
- No human review step
- Risk: untested breaking changes could slip through

**Recommendation:** Use Option 1 (semi-automatic) for safety while reducing manual effort.

**Maintenance:**
1. GitHub Actions runs weekly
2. Detects new syslog-ng version from official repos
3. Runs full test suite
4. Creates PR if tests pass
5. Human reviews and merges PR
6. Version automatically added to supported list

---

## What We DON'T Need (Clarification)

### pdbtool
**pdbtool** is a separate utility for:
- Testing patterndb XML files
- Converting pattern databases
- Merging pattern databases

**We don't use pdbtool because:**
- We run syslog-ng itself as a subprocess
- syslog-ng's db-parser() does the actual pattern matching
- We generate the XML programmatically in Python

**Note:** pdbtool is included in both `syslog-ng-core` and `syslog-ng`, but we don't invoke it.

---

## Recommendations by Platform

| Platform | Primary Method | Installation | Handles syslog-ng? | Notes |
|----------|---------------|--------------|-------------------|-------|
| **macOS** | Homebrew | `brew install patterndb-yaml` | ✅ Automatic | Recommended |
| **Linux (any)** | Homebrew | `brew install patterndb-yaml` | ✅ Automatic | Recommended |
| **Linux** | Snap | `snap install patterndb-yaml` | ✅ Automatic | Worth investigating |
| **Linux** | AppImage | Download single file | ✅ Bundled | Worth investigating |
| **Linux (Debian/Ubuntu)** | apt + pipx | Manual multi-step | ⚠️ Manual | Requires careful docs |
| **Linux (RHEL/Fedora)** | dnf + pipx | Manual multi-step | ⚠️ Manual | Requires careful docs |
| **Windows** | WSL2 | Follow Linux instructions | Via WSL2 | Nice-to-have only |
| **CI/CD** | Official repos | Direct install | ⚠️ Manual | Version pinning required |

### Priority Order

1. **Homebrew (macOS + Linux)** - ✅ Ready to implement
   - Works now, just needs `depends_on "syslog-ng"` in formula
   - Cross-platform (macOS and Linux)
   - Zero user configuration

2. **Snap (Linux)** - 🔍 Investigate further
   - Could provide automatic syslog-ng bundling on Linux
   - Single command installation
   - Needs research on confinement issues with subprocess

3. **AppImage (Linux)** - 🔍 Investigate further
   - Complete bundling solution
   - No package manager required
   - Larger file size but truly portable

4. **Native packages (apt/dnf)** - ⚠️ Usable but problematic
   - Requires careful documentation
   - Users must remember official repos
   - Multi-step process error-prone

5. **Windows** - ❌ Low priority
   - WSL2 works but adds complexity
   - Native Windows support deferred

---

## Final Implementation Decision

**Approved installation methods:**

1. **Homebrew (Recommended)** - macOS + Linux
   - Primary installation method
   - Automatic syslog-ng dependency management
   - ~1 hour implementation effort

2. **pip/pipx (Alternative)** - All platforms
   - For users who prefer pip or need library access
   - Requires manual syslog-ng installation from official repos
   - Runtime version checking with helpful error messages
   - ~2 hours implementation effort (version checking + docs)

**Deferred for future consideration:**
- Snap packaging (Linux)
- AppImage (Linux)
- Native .deb/.rpm packages
- Docker images

---

## Implementation Plan

### Phase 1: Immediate Implementation (Current Priority)

#### 1.1 Homebrew Formula Update (~1 hour)
**Location:** `homebrew-patterndb-yaml` repository

**Changes required:**
```ruby
# In Formula/patterndb-yaml.rb
depends_on "syslog-ng"  # Add this line after license declaration
```

**Testing:**
```bash
# Local testing
brew install --build-from-source ./Formula/patterndb-yaml.rb
brew list syslog-ng  # Verify syslog-ng installed
syslog-ng --version  # Verify version
```

**Deliverables:**
- [ ] Update formula with `depends_on "syslog-ng"`
- [ ] Test local installation
- [ ] Push to homebrew-patterndb-yaml repo
- [ ] Update README.md to emphasize Homebrew as primary method

#### 1.2 Version Checking Implementation (~2 hours)
**Location:** `src/patterndb_yaml/` (new module or in CLI)

**Components:**
1. **Version requirements** (conservative approach):
   ```python
   # Minimum tested version (no assumptions below this)
   MIN_SYSLOG_NG_VERSION = "4.10.1"

   # Known working versions (tested in development/CI)
   # CI installs latest from official repos (currently 4.10.1 as of 2024-11)
   KNOWN_WORKING_VERSIONS = [
       "4.10.1",  # Latest from official repos as of 2024-11-30, tested in CI
   ]

   # Known incompatible versions (hard failures in CI)
   KNOWN_INCOMPATIBLE_VERSIONS = [
       "4.3",  # Distro default, incompatible - failed in CI
   ]
   ```

2. **Version checker function**:
   - Check syslog-ng binary exists
   - Parse version from `syslog-ng --version` (format: "syslog-ng 4 (4.10.1)")
   - **Check for known incompatible versions (hard failure, cannot override)**
   - Check minimum version requirement (>= 4.10.1, hard failure)
   - Warn if not in KNOWN_WORKING_VERSIONS but >= minimum (informational)
   - Provide helpful error with official repo setup instructions

3. **CLI flag**:
   - Add `--allow-version-mismatch` flag
   - Bypasses version warnings for advanced users
   - Still enforces minimum version check

**Error message content:**
- Current version vs vetted versions
- Link to official syslog-ng installation guide
- Copy-paste commands for Ubuntu/Debian repo setup
- Instruction to use `--allow-version-mismatch` flag

**Deliverables:**
- [ ] Create `src/patterndb_yaml/version_check.py` module
- [ ] Integrate into CLI entry point
- [ ] Add `--allow-version-mismatch` flag
- [ ] Write unit tests for version parsing and checking
- [ ] Create `.github/workflows/check-syslog-ng-version.yml` for automation
- [ ] Document in README.md

**Automatic version tracking:**
- [ ] Set up weekly GitHub Actions workflow
- [ ] Configure version detection and testing
- [ ] Enable automatic PR creation for new versions
- [ ] Document review process for version PRs

#### 1.3 Documentation Updates (~1 hour)
**Files to update:**
- `README.md`: Emphasize Homebrew as primary, pip/pipx as alternative
- `SYSLOG_NG_INSTALLATION.md`: Update with official repo instructions
- Add version compatibility section

**Content:**
- Homebrew installation (recommended)
- pip/pipx installation with official repo setup
- Version compatibility notes
- Troubleshooting common issues

**Deliverables:**
- [ ] Update README.md installation section
- [ ] Update SYSLOG_NG_INSTALLATION.md
- [ ] Add version compatibility documentation
- [ ] Add troubleshooting section

### Phase 2: Future Enhancements (Deferred)

**Only if demand warrants:**
1. **Snap package** (~3-5 hours)
   - If Homebrew adoption low on Linux
   - Need to test confinement/subprocess compatibility

2. **AppImage** (~5-8 hours)
   - For edge cases (air-gapped, unusual distros)
   - Supplementary distribution method

3. **Native packages** (.deb/.rpm)
   - If project gains significant Linux server adoption
   - Requires ongoing maintenance

---

## Why Not Bundle syslog-ng Binary?

**Could we include syslog-ng in the Python wheel?**

**Technical analysis:**
- **Size:** syslog-ng binary + core modules = ~20-30MB
- **Dependencies:** Requires system libraries (glib, pcre2, openssl)
- **Platform variations:** Need separate binaries for:
  - macOS Intel (x86_64)
  - macOS ARM (aarch64)
  - Linux x86_64 (multiple libc versions)
  - Linux aarch64
  - Windows (different architecture entirely)

**Licensing:**
- syslog-ng: LGPL-2.1-or-later and GPL-2.0-or-later
- LGPL requires allowing users to replace the library
- Complexity in compliance for bundled binaries

**Maintenance:**
- Would need to compile syslog-ng for each platform/architecture
- Keep up with syslog-ng security updates
- Handle library compatibility issues

**Verdict:** **Not recommended**
- Official packages are well-maintained
- System package managers handle dependencies better
- Licensing compliance is complex
- Maintenance burden too high

**Source:** [Bundling binary tools in Python wheels](https://simonwillison.net/2022/May/23/bundling-binary-tools-in-python-wheels/)

---

## Alternative Considered: Pure Python Pattern Matching

**Could we replace syslog-ng entirely with pure Python?**

**Option:** Use Drain3 or similar log parsing library.

**Pros:**
- No system dependencies
- Works everywhere Python works
- Bundleable in wheel
- Potentially simpler for users

**Cons:**
- **Fundamentally changes the project**: We're currently a wrapper around syslog-ng's patterndb
- **Different pattern syntax**: Not compatible with existing syslog-ng patterns
- **Loses performance**: Python vs C implementation
- **Loses established tooling**: syslog-ng patterndb is mature and well-documented
- **Major rewrite required**

**Verdict:** **Out of scope**
- Would be a different project entirely
- Core value proposition is making syslog-ng patterndb more accessible via YAML
- If we wanted pure Python, should start a new project

**Source:** [Drain3 - Log template miner](https://github.com/logpai/Drain3)

---

## Conclusion

**What we need:**
- The `syslog-ng` binary (runs as subprocess, see `src/patterndb_yaml/pattern_filter.py:90`)
- With `db-parser()` module (built-in to all packages)
- From official syslog-ng repositories (distro defaults have incompatibility issues)

**Approved implementation (Phase 1):**

1. **Homebrew (Primary method)** - macOS + Linux
   - Add `depends_on "syslog-ng"` to formula (~1 hour)
   - Automatic dependency management
   - Zero user configuration
   - Recommended for all users

2. **pip/pipx (Alternative method)** - All platforms
   - Runtime version checking (~2 hours implementation)
   - Helpful error messages with official repo setup instructions
   - `--allow-version-mismatch` flag for advanced users
   - Known working versions list (currently: "4.10.1")
   - Automatic weekly testing of new versions via GitHub Actions

**Deferred for future:**
- Snap packaging (Linux) - ~3-5 hours if demand warrants
- AppImage (Linux) - ~5-8 hours for supplementary distribution
- Native .deb/.rpm packages - if significant Linux server adoption
- Windows native support - WSL2 works, low priority

**Total immediate effort:** ~4 hours
- Homebrew formula update: ~1 hour
- Version checking implementation: ~2 hours
- Documentation updates: ~1 hour

**Key benefits:**
- ✅ Minimal implementation effort (4 hours total)
- ✅ Excellent user experience via Homebrew
- ✅ Safety via version checking for pip/pipx users
- ✅ Clear migration path from distro packages to official repos
- ✅ Flexibility for advanced users with override flag
- ✅ Keeps options open for Linux-specific formats if needed later

---

## References

### syslog-ng Documentation
- [syslog-ng db-parser documentation](https://www.syslog-ng.com/technical-documents/doc/syslog-ng-open-source-edition/3.21/administration-guide/db-parser-process-message-content-with-a-pattern-database-patterndb/)
- [Installing syslog-ng on Ubuntu](https://www.syslog-ng.com/community/b/blog/posts/installing-the-latest-syslog-ng-on-ubuntu-and-other-deb-distributions)
- [Syslog-ng in Homebrew announcement](https://www.syslog-ng.com/community/b/blog/posts/syslog-ng-is-now-available-in-homebrew)

### Packaging Resources
- [Debian syslog-ng-core package](https://packages.debian.org/sid/syslog-ng-core)
- [Homebrew syslog-ng Formula](https://formulae.brew.sh/formula/syslog-ng)
- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Bundling binary tools in Python wheels](https://simonwillison.net/2022/May/23/bundling-binary-tools-in-python-wheels/)
- [PEP 725 - External Dependencies](https://peps.python.org/pep-0725/)

### Linux Distribution Formats
- [Snapcraft Documentation](https://snapcraft.io/docs)
- [Flatpak Dependencies](https://docs.flatpak.org/en/latest/dependencies.html)
- [Flatpak Single-file Bundles](https://docs.flatpak.org/en/latest/single-file-bundles.html)
- [AppImage Full Bundle](https://appimage-builder.readthedocs.io/en/latest/advanced/full_bundle.html)
- [AppImage Packaging Native Binaries](https://docs.appimage.org/packaging-guide/from-source/native-binaries.html)
- [AppImage Concepts](https://docs.appimage.org/introduction/concepts.html)
