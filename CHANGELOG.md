# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-30

### Initial Release

First release of patterndb-yaml - YAML-based pattern matching with multi-line capabilities for log normalization using syslog-ng patterndb.

#### Features

**Core Functionality:**
- YAML-based pattern rule definitions for log normalization
- Pattern matching powered by syslog-ng's efficient C implementation
- Field extraction with named capture groups
- Multi-line log sequence handling with state management
- Pattern transformation and output formatting
- Support for alternatives, options, and custom parsers
- Unicode character support with automatic escaping

**Features:**
- Process logs from files or stdin
- Multiple output modes (quiet, explain, progress)
- Statistics reporting (table and JSON formats)
- XML patterndb generation for use with syslog-ng
- Version checking for syslog-ng compatibility
- Support for Python 3.9-3.14

Special thanks to the Python community and the developers of the excellent tools that made this project possible.

---

## Release Process

Releases are automated via GitHub Actions when a version tag is pushed:

1. Update CHANGELOG.md with release notes
2. Create and push Git tag: `git tag v0.1.0 && git push origin v0.1.0`
3. GitHub Actions automatically:
   - Creates GitHub Release
   - Publishes to PyPI (when configured)
4. Version number is automatically derived from Git tag

[0.1.0]: https://github.com/JeffreyUrban/patterndb-yaml/releases/tag/v0.1.0
