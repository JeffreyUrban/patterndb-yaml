# Packaging Analysis: Handling syslog-ng Dependency

Analysis of how to handle the syslog-ng dependency across different packaging methods for `patterndb-yaml`.

## Key Finding: pdbtool is in syslog-ng-core

**We only need `syslog-ng-core`** - this includes `pdbtool` which is what patterndb-yaml uses for pattern matching. The full `syslog-ng` package includes many additional modules (MQTT, Kafka, SNMP, etc.) that we don't need.

**Source:** [pdbtool manual - Debian](https://manpages.debian.org/testing/syslog-ng-core/pdbtool.1.en.html), [Debian syslog-ng-core package](https://packages.debian.org/sid/syslog-ng-core)

## Current Situation

**syslog-ng package size and dependencies:**
- **Size:** 122.9MB (4,032 files on macOS Homebrew)
- **Dependencies:** 21 required packages including gRPC, Kafka, MQTT, MongoDB, RabbitMQ, Redis, SNMP, Protobuf
- **Reality:** Most of these are for advanced syslog-ng features we don't use

## Packaging Method Analysis

### 1. Homebrew (macOS) ✅ Works Well

**Current approach:**
```ruby
depends_on "syslog-ng"
```

**Issue:** Homebrew doesn't have a separate `syslog-ng-core` package - only the full `syslog-ng` formula.

**Recommendation:** **Keep as-is** - use `depends_on "syslog-ng"`
- Homebrew handles dependency management automatically
- Users get automatic updates
- Size isn't critical on macOS systems
- Alternative formula for just core components would be maintenance burden

**Pros:**
- Zero user effort
- Automatic updates
- Well-tested

**Cons:**
- Installs unnecessary modules
- 122MB for what we need ~20MB for

---

### 2. pip/pipx (All platforms) ❌ Cannot Handle System Dependencies

**Reality:** pip/pipx **cannot install system packages** like syslog-ng.

**Options:**

#### Option A: Runtime Check + Helpful Error (Recommended)
Detect syslog-ng at runtime and provide installation instructions:

```python
import shutil
import sys
import platform

def check_syslog_ng():
    """Check if syslog-ng is available, provide helpful error if not."""
    if not shutil.which("pdbtool"):
        system = platform.system()

        if system == "Darwin":  # macOS
            msg = """
syslog-ng is required but not installed.

Install via Homebrew:
    brew install syslog-ng

Or install patterndb-yaml via Homebrew to handle dependencies automatically:
    brew install jeffreyurban/patterndb-yaml/patterndb-yaml
"""
        elif system == "Linux":
            msg = """
syslog-ng-core is required but not installed.

For Debian/Ubuntu:
    wget -qO - https://ose-repo.syslog-ng.com/apt/syslog-ng-ose-pub.asc | \\
      sudo gpg --dearmor -o /etc/apt/keyrings/syslog-ng-ose.gpg
    echo "deb [signed-by=/etc/apt/keyrings/syslog-ng-ose.gpg] \\
      https://ose-repo.syslog-ng.com/apt/ stable ubuntu-noble" | \\
      sudo tee /etc/apt/sources.list.d/syslog-ng-ose.list
    sudo apt-get update && sudo apt-get install syslog-ng-core

For RHEL/Fedora:
    sudo dnf install syslog-ng

See: https://github.com/JeffreyUrban/patterndb-yaml/blob/main/SYSLOG_NG_INSTALLATION.md
"""
        else:  # Windows or unknown
            msg = """
syslog-ng is required but not installed.

Windows is not currently supported. Consider using WSL2:
    https://learn.microsoft.com/en-us/windows/wsl/install
"""

        print(msg, file=sys.stderr)
        sys.exit(1)
```

**Pros:**
- Clear, actionable error messages
- Platform-specific guidance
- No false expectations

**Cons:**
- User must manually install syslog-ng
- Extra step in installation process

#### Option B: Pure Python Alternative
Replace syslog-ng with a pure Python pattern matcher like Drain3.

**Pros:**
- No system dependencies
- Works everywhere Python works
- Bundleable in wheel

**Cons:**
- **Major architectural change** - would need to reimplement pattern matching
- Different pattern syntax (not compatible with existing syslog-ng patterns)
- Loses performance benefit of C implementation
- Significant development effort

**Verdict:** Not recommended unless we want to change the project's core value proposition

---

### 3. Docker/Container 🎯 Best for Cross-Platform

**Approach:** Pre-built container with syslog-ng-core included

```dockerfile
FROM python:3.9-slim

# Install syslog-ng-core
RUN apt-get update && apt-get install -y \
    wget gnupg2 \
    && wget -qO - https://ose-repo.syslog-ng.com/apt/syslog-ng-ose-pub.asc | \
       gpg --dearmor -o /etc/apt/keyrings/syslog-ng-ose.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/syslog-ng-ose.gpg] \
       https://ose-repo.syslog-ng.com/apt/ stable ubuntu-noble" | \
       tee /etc/apt/sources.list.d/syslog-ng-ose.list \
    && apt-get update \
    && apt-get install -y syslog-ng-core \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install patterndb-yaml
RUN pip install patterndb-yaml

ENTRYPOINT ["patterndb-yaml"]
```

**Usage:**
```bash
# Pull and run
docker run -i jeffreyurban/patterndb-yaml:latest --rules rules.yaml < input.log

# Or with docker-compose for log processing pipeline
docker-compose up
```

**Pros:**
- Consistent environment everywhere
- syslog-ng-core included automatically
- Reproducible builds
- Works on Windows (via Docker Desktop)
- Can publish to Docker Hub for easy distribution

**Cons:**
- Requires Docker installed
- Larger download (but only once)
- Overhead of container runtime

**Recommendation:** **Add this as an official distribution method** - it solves the Windows problem and provides consistency.

---

### 4. System Package Managers (Future Consideration)

#### Debian/Ubuntu (.deb)

Create a `.deb` package with `syslog-ng-core` as a dependency:

```
Package: patterndb-yaml
Depends: python3 (>= 3.9), syslog-ng-core (>= 3.35)
```

When installed via `apt install patterndb-yaml`, it automatically pulls in syslog-ng-core.

**Pros:**
- Automatic dependency resolution
- Native package management
- Clean uninstallation

**Cons:**
- Requires packaging for each distro
- Need to maintain package repositories
- Overhead of package maintenance

#### RPM (RHEL/Fedora)

Similar to .deb, create RPM with dependency:

```
Requires: python3 >= 3.9
Requires: syslog-ng >= 3.35
```

---

### 5. Conda/Mamba (Data Science Users)

Conda can handle system dependencies through conda-forge:

```yaml
# environment.yml
name: patterndb-yaml
channels:
  - conda-forge
dependencies:
  - python>=3.9
  - syslog-ng  # If available on conda-forge
  - pip
  - pip:
    - patterndb-yaml
```

**Status:** Need to check if syslog-ng is available on conda-forge.

---

## Recommendations by User Environment

| User Environment | Recommended Method | How syslog-ng is Handled |
|-----------------|-------------------|--------------------------|
| **macOS developer** | Homebrew | Automatic via `depends_on` |
| **Linux server admin** | pip + manual syslog-ng | Runtime check with helpful error |
| **CI/CD pipeline** | Docker | Pre-installed in image |
| **Windows user** | Docker + WSL2 | Pre-installed in image |
| **Data scientist** | Conda (if available) | Conda dependency |
| **Enterprise Linux** | RPM/DEB package | Package manager dependency |

## Implementation Priority

### Phase 1: Immediate (Current Release)
1. ✅ Homebrew: Add `depends_on "syslog-ng"` to formula
2. ✅ pip/pipx: Add runtime check with platform-specific error messages
3. ✅ Update README with clear installation requirements

### Phase 2: Next Release
1. Create official Docker image with syslog-ng-core
2. Publish to Docker Hub
3. Add Docker documentation

### Phase 3: Future
1. Consider conda-forge package if there's demand
2. Evaluate creating native .deb/.rpm packages
3. Investigate bundling minimal pdbtool (if licensing permits)

## Alternative Approach: Bundle pdbtool Binary?

**Question:** Could we extract and bundle just `pdbtool` instead of requiring full syslog-ng?

**Analysis:**
- **Size:** pdbtool binary is small (~few MB)
- **Dependencies:** Requires glib, pcre2, and a few other libs
- **Licensing:** LGPL-2.1-or-later (would need to comply with LGPL requirements)
- **Platform variations:** Would need separate binaries for:
  - macOS (Intel + ARM)
  - Linux (various distros/architectures)
  - Windows (if possible)

**Verdict:** **Not recommended**
- LGPL compliance complexity (must allow users to replace library)
- Maintenance burden of multiple platform binaries
- Still needs system library dependencies (glib, pcre2)
- Official packages are well-maintained and tested

**Source:** [Bundling binary tools in Python wheels](https://simonwillison.net/2022/May/23/bundling-binary-tools-in-python-wheels/)

## Conclusion

**Recommended approach per installation method:**

1. **Homebrew:** Use `depends_on "syslog-ng"` (automatic, zero user effort)
2. **pip/pipx:** Runtime check + helpful error message pointing to installation guide
3. **Docker:** Create official image with syslog-ng-core pre-installed (solves Windows + CI/CD)
4. **Documentation:** Clear installation requirements in README

This provides the best balance of:
- User experience (Homebrew users get zero-config)
- Cross-platform support (Docker for Windows/CI)
- Transparency (pip users know what's needed)
- Maintenance burden (leverage existing package managers)

## References

- [syslog-ng-core Debian package](https://packages.debian.org/sid/syslog-ng-core)
- [pdbtool manual](https://manpages.debian.org/testing/syslog-ng-core/pdbtool.1.en.html)
- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Bundling binary tools in Python wheels](https://simonwillison.net/2022/May/23/bundling-binary-tools-in-python-wheels/)
- [PEP 725 - External Dependencies](https://peps.python.org/pep-0725/)
