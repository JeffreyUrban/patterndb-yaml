# Installation

`patterndb-yaml` can be installed via Homebrew, pipx, pip, or from source.

## Requirements

- **Python 3.9 or higher** (for pip/pipx installations)
- **Homebrew** (for macOS/Linux Homebrew installation)
- **syslog-ng-core** (for pattern matching engine)

!!! todo "syslog-ng Setup"
    Installation and configuration instructions for syslog-ng-core will be added in a future release.

`patterndb-yaml` works on Linux, macOS, and Windows.

## Via Homebrew (macOS/Linux)

```bash
brew tap jeffreyurban/patterndb-yaml
brew install patterndb-yaml
```

Homebrew manages the Python dependency and provides easy updates via `brew upgrade`.

## Via pipx (Cross-platform)

```bash
pipx install patterndb-yaml
```

[pipx](https://pipx.pypa.io/) installs in an isolated environment with global CLI access. Works on macOS, Linux, and Windows. Update with `pipx upgrade patterndb-yaml`.

## Via pip

```bash
pip install patterndb-yaml
```

Use `pip` if you want to use patterndb-yaml as a library in your Python projects.

## Via Source

For development or the latest unreleased features:

```bash
git clone https://github.com/JeffreyUrban/patterndb-yaml.git
cd patterndb-yaml
pip install .
```

This installs `patterndb-yaml` and its dependencies:

- **typer** - CLI framework
- **rich** - Terminal formatting and progress display
- **pyyaml** - YAML parsing

## Development Installation

For contributing or modifying `patterndb-yaml`, install in editable mode with development dependencies:

```bash
git clone https://github.com/JeffreyUrban/patterndb-yaml.git
cd patterndb-yaml
pip install -e ".[dev]"
```

Development dependencies include:

- **pytest** - Test framework
- **pytest-cov** - Code coverage
- **ruff** - Linting and formatting
- **mypy** - Type checking
- **types-pyyaml** - Type stubs for YAML
- **pre-commit** - Git hooks for code quality

## Platform-Specific Notes

### Linux

Recommended installation methods:

- **Homebrew**: `brew tap jeffreyurban/patterndb-yaml && brew install patterndb-yaml`
- **pipx**: `pipx install patterndb-yaml`
- **pip**: `pip install patterndb-yaml`

!!! tip "Virtual Environments"
    If using pip directly, consider using a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install patterndb-yaml
    ```

### macOS

Recommended installation methods:

- **Homebrew**: `brew tap jeffreyurban/patterndb-yaml && brew install patterndb-yaml` (recommended)
- **pipx**: `pipx install patterndb-yaml`
- **pip**: `pip install patterndb-yaml`

### Windows

Recommended installation methods:

- **pipx**: `pipx install patterndb-yaml` (recommended)
- **pip**: `pip install patterndb-yaml`

The `patterndb-yaml` command will be available in your terminal after installation.

## Verify Installation

After installation, verify `patterndb-yaml` is working:

```bash
patterndb-yaml --version
patterndb-yaml --help
```

Try a quick test with the `--generate-xml` option:

```bash
echo "rules: []" | patterndb-yaml --rules /dev/stdin --generate-xml
```

This should output valid syslog-ng XML pattern database markup.

## Upgrading

### Homebrew

```bash
brew upgrade patterndb-yaml
```

### pipx

```bash
pipx upgrade patterndb-yaml
```

### pip

```bash
pip install --upgrade patterndb-yaml
```

### Source Installation

```bash
cd patterndb-yaml
git pull
pip install --upgrade .
```

For development installations:

```bash
cd patterndb-yaml
git pull
pip install --upgrade -e ".[dev]"
```

## Uninstalling

### Homebrew

```bash
brew uninstall patterndb-yaml
```

### pipx

```bash
pipx uninstall patterndb-yaml
```

### pip

```bash
pip uninstall patterndb-yaml
```

## Troubleshooting

### Command Not Found

If `patterndb-yaml` command is not found after installation:

1. **Check pip installed in the right location:**
   ```bash
   pip show patterndb-yaml
   ```

2. **Verify Python scripts directory is in PATH:**
   ```bash
   python -m site --user-base
   ```
   Add `<user-base>/bin` to your PATH if needed.

3. **Use Python module syntax:**
   ```bash
   python -m patterndb-yaml --help
   ```

### Import Errors

If you see import errors, ensure dependencies are installed:

```bash
pip install typer rich
```

Or reinstall with dependencies:

```bash
pip install --force-reinstall .
```

### Permission Errors

If you encounter permission errors, install for your user only:

```bash
pip install --user .
```

Or use a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install .
```

## Next Steps

- [Quick Start Guide](quick-start.md) - Learn basic usage
- [Basic Concepts](basic-concepts.md) - Understand how `patterndb-yaml` works
- [CLI Reference](../reference/cli.md) - Complete command-line options
