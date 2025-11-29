# patterndb-yaml

**YAML-driven syslog-ng patterndb wrapper with multi-line capabilities**

[![PyPI version](https://img.shields.io/pypi/v/patterndb-yaml.svg)](https://pypi.org/project/patterndb-yaml/)
[![Tests](https://github.com/JeffreyUrban/patterndb-yaml/actions/workflows/test.yml/badge.svg)](https://github.com/JeffreyUrban/patterndb-yaml/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/JeffreyUrban/patterndb-yaml/branch/main/graph/badge.svg)](https://codecov.io/gh/JeffreyUrban/patterndb-yaml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Documentation](https://img.shields.io/readthedocs/patterndb-yaml)](https://patterndb-yaml.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

### Via Homebrew (macOS/Linux)

```bash
brew tap JeffreyUrban/patterndb-yaml && brew install patterndb-yaml
```

Homebrew manages the Python dependency and provides easy updates via `brew upgrade`.

### Via pipx (Cross-platform)

```bash
pipx install patterndb-yaml
```

[pipx](https://pipx.pypa.io/) installs in an isolated environment with global CLI access. Works on macOS, Linux, and Windows. Update with `pipx upgrade patterndb-yaml`.

### Via pip

```bash
pip install patterndb-yaml
```

Use `pip` if you want to use patterndb-yaml as a library in your Python projects.

### From Source

```bash
# Development installation
git clone https://github.com/JeffreyUrban/patterndb-yaml
cd patterndb-yaml
pip install -e ".[dev]"
```

**Requirements:** Python 3.9+

## Quick Start

### Command Line

```bash
patterndb-yaml
```

### Python API

```python
from patterndb-yaml import PatterndbYaml

# Initialize with configuration
placeholder = PatterndbYaml(
    placeholder=placeholder
)

# Process stream
with open("app.log") as infile, open("clean.log", "w") as outfile:
    for line in infile:
        placeholder.placeholder(placeholder, outfile)
    placeholder.flush(outfile)
```

## Use Cases

- **placeholder** - placeholder

## How It Works

`patterndb-yaml` uses placeholder:

1. **placeholder** - placeholder

placeholder.

## Documentation

**[Read the full documentation at patterndb-yaml.readthedocs.io](https://patterndb-yaml.readthedocs.io/)**

Key sections:
- **Getting Started** - Installation and quick start guide
- **Use Cases** - Real-world examples across different domains
- **Guides** - placeholder selection, performance tips, common patterns
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
pytest --cov=patterndb-yaml --cov-report=html
```

## Performance

- **Time complexity:** O(placeholder)
- **Space complexity:** O(placeholder)
- **Throughput:** placeholder
- **Memory:** placeholder

## License

MIT License - See [LICENSE](LICENSE) file for details

## Author

Jeffrey Urban

---

**[Star on GitHub](https://github.com/JeffreyUrban/patterndb-yaml)** | **[Report Issues](https://github.com/JeffreyUrban/patterndb-yaml/issues)**
