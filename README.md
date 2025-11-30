# patterndb-yaml

> ## ⚠️ Early Development - Not Ready for Use
>
> **This project is under active development and is not ready for production use.**
>
> - APIs may change without notice
> - Documentation is incomplete
> - No releases published yet
> - Not accepting contributions at this time
>
> **Star/watch the repo to be notified when the first release is available.**

**YAML-based pattern matching with multi-line capabilities for log normalization using syslog-ng patterndb**

[![PyPI version](https://img.shields.io/pypi/v/patterndb-yaml.svg)](https://pypi.org/project/patterndb-yaml/)
[![Tests](https://github.com/JeffreyUrban/patterndb-yaml/actions/workflows/test.yml/badge.svg)](https://github.com/JeffreyUrban/patterndb-yaml/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/JeffreyUrban/patterndb-yaml/branch/main/graph/badge.svg)](https://codecov.io/gh/JeffreyUrban/patterndb-yaml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Documentation](https://img.shields.io/readthedocs/patterndb-yaml)](https://patterndb-yaml.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What is patterndb-yaml?

`patterndb-yaml` brings intuitive YAML pattern definitions to [syslog-ng's proven patterndb engine](https://www.syslog-ng.com/technical-documents/doc/syslog-ng-open-source-edition/3.38/administration-guide/56#TOPIC-1829130). Instead of writing complex XML patterns, you define rules in readable YAML and let patterndb-yaml handle the translation to syslog-ng's efficient pattern matcher.

This makes it easier to normalize heterogeneous logs - transforming different log formats into standardized output for comparison, analysis, or filtering.

## Features

- **YAML rules** - Readable pattern definitions instead of syslog-ng XML
- **Field extraction** - Pull specific data (table names, IDs, etc.) from matched lines
- **Pattern matching** - Powered by syslog-ng's efficient C implementation
- **Multi-line sequences** - Handle log entries spanning multiple lines
- **Explain mode** - Debug which patterns matched and why
- **CLI and Python API** - Use as a command-line tool or library

## Installation

**Requirements:** Python 3.9+, syslog-ng 3.35+

> **📋 Note:** `patterndb-yaml` requires `syslog-ng` to be installed. See [SYSLOG_NG_INSTALLATION.md](SYSLOG_NG_INSTALLATION.md) for detailed platform-specific instructions.

### Via Homebrew (macOS) - Recommended

```bash
brew tap JeffreyUrban/patterndb-yaml && brew install patterndb-yaml
```

**Automatically installs syslog-ng** as a dependency. Homebrew manages all dependencies and provides easy updates via `brew upgrade`.

### Via pipx (Linux)

```bash
# First, install syslog-ng for your distribution
# See SYSLOG_NG_INSTALLATION.md for platform-specific instructions

# Then install patterndb-yaml
pipx install patterndb-yaml
```

[pipx](https://pipx.pypa.io/) installs in an isolated environment with global CLI access. Update with `pipx upgrade patterndb-yaml`.

### Via pip

```bash
pip install patterndb-yaml
```

Use `pip` if you want to use patterndb-yaml as a library in your Python projects.

**Note:** You must install syslog-ng separately. See [SYSLOG_NG_INSTALLATION.md](SYSLOG_NG_INSTALLATION.md).

### From Source

```bash
# Development installation
git clone https://github.com/JeffreyUrban/patterndb-yaml
cd patterndb-yaml
pip install -e ".[dev]"
```

### Windows

Windows is not currently supported. Consider using WSL2 (Windows Subsystem for Linux) and following the Linux installation instructions.

## Quick Start

### Command Line

Create a YAML rules file (`rules.yaml`):

```yaml
rules:
  - name: log_info
    pattern:
      - text: "["
      - text: "INFO"
      - text: "] "
      - field: message
    output: "[info:{message}]"

  - name: log_error
    pattern:
      - text: "["
      - text: "ERROR"
      - text: "] "
      - field: message
    output: "[error:{message}]"
```

Process your logs:

```bash
# Process from stdin
cat app.log | patterndb-yaml --rules rules.yaml

# Process a file
patterndb-yaml --rules rules.yaml --input app.log

# Get statistics
patterndb-yaml --rules rules.yaml --input app.log --stats
```

### Python API

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path

# Initialize with rules
processor = PatterndbYaml(rules_path=Path("rules.yaml"))

# Process logs
with open("app.log") as infile, open("clean.log", "w") as outfile:
    processor.process(infile, outfile)

# Get statistics
stats = processor.get_stats()
print(f"Matched {stats['lines_matched']} of {stats['lines_processed']} lines")
print(f"Match rate: {stats['match_rate']:.1%}")
```

## Use Cases

- **Log Normalization** - Transform heterogeneous log formats into standardized output
- **Data Extraction** - Pull structured data from unstructured log lines
- **Log Filtering** - Identify and process specific log patterns
- **Format Standardization** - Convert legacy log formats to modern structured formats
- **Compliance** - Normalize logs for security analysis and auditing

## How It Works

`patterndb-yaml` uses syslog-ng's patterndb engine for efficient pattern matching:

1. **YAML → XML** - Converts your readable YAML rules into syslog-ng's XML patterndb format
2. **Pattern Matching** - Uses syslog-ng's C implementation for fast, memory-efficient matching
3. **Field Extraction** - Pulls named fields from matched patterns
4. **Output Transformation** - Applies output templates to normalize log format

The system processes logs line-by-line with constant memory usage, making it suitable for large files and streaming data.

## Documentation

**[Read the full documentation at patterndb-yaml.readthedocs.io](https://patterndb-yaml.readthedocs.io/)**

Key sections:
- **Getting Started** - Installation and quick start guide
- **Use Cases** - Real-world examples across different domains
- **Guides** - Pattern design, performance tips, common patterns
- **Reference** - Complete CLI and Python API documentation

## Development

```bash
# Clone repository
git clone https://github.com/JeffreyUrban/patterndb-yaml.git
cd patterndb-yaml

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=patterndb_yaml --cov-report=html

# Build documentation
cd docs && mkdocs build
```

## Performance

- **Time complexity:** O(n) where n is number of log lines
- **Space complexity:** O(1) constant memory for processing
- **Throughput:** Processes logs line-by-line with streaming support
- **Memory:** Minimal memory footprint, suitable for large files

Performance is determined by syslog-ng's patterndb engine, which uses efficient C implementations for pattern matching.

## License

MIT License - See [LICENSE](LICENSE) file for details

## Author

Jeffrey Urban

---

**[Star on GitHub](https://github.com/JeffreyUrban/patterndb-yaml)** | **[Report Issues](https://github.com/JeffreyUrban/patterndb-yaml/issues)** | **[Documentation](https://patterndb-yaml.readthedocs.io/)**
