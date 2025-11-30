# syslog-ng Installation Guide

`patterndb-yaml` requires `syslog-ng` to be installed on your system for pattern matching functionality. This guide covers installation across different platforms.

## Quick Reference

| Platform | Recommended Method | Handles syslog-ng? |
|----------|-------------------|-------------------|
| **macOS** | `brew install patterndb-yaml` | ✅ Automatic |
| **Linux (Debian/Ubuntu)** | Manual install + `pipx install patterndb-yaml` | ⚠️ Manual |
| **Linux (RHEL/Fedora)** | Manual install + `pipx install patterndb-yaml` | ⚠️ Manual |
| **Windows** | Not currently supported | ❌ |

---

## macOS Installation

### Option 1: Homebrew (Recommended)

```bash
brew tap JeffreyUrban/patterndb-yaml
brew install patterndb-yaml
```

**What this does:**
- Automatically installs `syslog-ng` as a dependency
- Installs `patterndb-yaml` CLI tool
- Manages all dependencies via Homebrew

The Homebrew formula includes `depends_on "syslog-ng"`, which ensures syslog-ng is automatically installed and updated alongside patterndb-yaml.

**Verify installation:**
```bash
patterndb-yaml --version
syslog-ng --version
```

### Option 2: Manual Installation

If you prefer manual installation:

```bash
# Install syslog-ng first
brew install syslog-ng

# Then install patterndb-yaml via pipx
pipx install patterndb-yaml
```

---

## Linux Installation

### Debian/Ubuntu

**Step 1: Install syslog-ng from official repository**

```bash
# Add syslog-ng GPG key
wget -qO - https://ose-repo.syslog-ng.com/apt/syslog-ng-ose-pub.asc | \
  sudo gpg --dearmor -o /etc/apt/keyrings/syslog-ng-ose.gpg

# Add repository (adjust for your Ubuntu version)
echo "deb [signed-by=/etc/apt/keyrings/syslog-ng-ose.gpg] https://ose-repo.syslog-ng.com/apt/ stable ubuntu-noble" | \
  sudo tee /etc/apt/sources.list.d/syslog-ng-ose.list

# Update and install
sudo apt-get update
sudo apt-get install -y syslog-ng-core
```

**Step 2: Install patterndb-yaml**

```bash
# Using pipx (recommended)
pipx install patterndb-yaml

# Or using pip
pip install patterndb-yaml
```

**Verify installation:**
```bash
patterndb-yaml --version
syslog-ng --version
```

**Available Ubuntu/Debian versions:**
- ubuntu-noble (24.04 LTS)
- ubuntu-jammy (22.04 LTS)
- ubuntu-focal (20.04 LTS)
- debian-bookworm
- debian-bullseye

### RHEL/Fedora/CentOS

**Step 1: Install syslog-ng from official DNF repository**

```bash
# Add repository
sudo dnf install -y 'dnf-command(config-manager)'
sudo dnf config-manager --add-repo https://ose-repo.syslog-ng.com/yum/nightly/rhel9/

# Import GPG key
sudo rpm --import https://ose-repo.syslog-ng.com/yum/nightly/rhel9/repodata/repomd.xml.key

# Install
sudo dnf install -y syslog-ng
```

**Step 2: Install patterndb-yaml**

```bash
# Using pipx (recommended)
pipx install patterndb-yaml

# Or using pip
pip install patterndb-yaml
```

### Alternative: Distribution Repositories

Most Linux distributions include syslog-ng in their official repositories, though versions may be older:

```bash
# Debian/Ubuntu
sudo apt-get install syslog-ng

# Fedora/RHEL
sudo dnf install syslog-ng

# Arch Linux
sudo pacman -S syslog-ng
```

---

## Windows Installation

**Status:** Windows support is currently limited.

- **syslog-ng Agent for Windows** is available only in the commercial Premium Edition
- The open-source syslog-ng OSE does not officially support Windows
- `patterndb-yaml` is not currently tested on Windows

**Alternative approaches:**
1. Use **Windows Subsystem for Linux (WSL2)** and follow Linux installation instructions
2. Use a Linux virtual machine or container
3. Wait for Windows support (tracking issue: TBD)

---

## Verifying Installation

After installation, verify both components work:

```bash
# Check patterndb-yaml
patterndb-yaml --version

# Check syslog-ng
syslog-ng --version

# Test with a simple example
echo '[INFO] Test message' | patterndb-yaml --rules examples/normalization_rules.yaml
```

---

## Troubleshooting

### "syslog-ng: command not found"

**macOS (Homebrew):**
```bash
brew install syslog-ng
```

**Linux:**
```bash
# Check if installed
which syslog-ng

# If not installed, follow platform-specific instructions above
```

### "pdbtool: command not found"

The `pdbtool` command is included with syslog-ng. If missing:

```bash
# macOS
brew reinstall syslog-ng

# Linux (Debian/Ubuntu)
sudo apt-get install --reinstall syslog-ng-core

# Linux (RHEL/Fedora)
sudo dnf reinstall syslog-ng
```

### Version Compatibility

`patterndb-yaml` requires:
- **syslog-ng**: 3.35+ (recommended: 3.38+)
- **Python**: 3.9+

Check versions:
```bash
syslog-ng --version | head -1
python --version
```

---

## Updating

### macOS (Homebrew)

```bash
brew upgrade patterndb-yaml
```

This automatically updates both patterndb-yaml and syslog-ng if needed.

### Linux

```bash
# Update syslog-ng
sudo apt-get update && sudo apt-get upgrade syslog-ng-core  # Debian/Ubuntu
sudo dnf upgrade syslog-ng                                   # RHEL/Fedora

# Update patterndb-yaml
pipx upgrade patterndb-yaml  # If installed via pipx
pip install --upgrade patterndb-yaml  # If installed via pip
```

---

## References

### Official Documentation
- [syslog-ng Pattern Database Documentation](https://syslog-ng.github.io/admin-guide/120_Parser/006_db_parser/004_The_syslog-ng_patterndb_format/README)
- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)

### Platform-Specific
- [syslog-ng on Homebrew](https://formulae.brew.sh/formula/syslog-ng)
- [Installing syslog-ng on Ubuntu](https://www.syslog-ng.com/community/b/blog/posts/installing-the-latest-syslog-ng-on-ubuntu-and-other-deb-distributions)
- [syslog-ng APT Repository](https://ose-repo.syslog-ng.com/apt/)

### Homebrew Dependencies
- [syslog-ng Homebrew Formula](https://formulae.brew.sh/formula/syslog-ng)
- [Formula Cookbook - Dependencies](https://docs.brew.sh/Formula-Cookbook#specifying-other-formulae-as-dependencies)
