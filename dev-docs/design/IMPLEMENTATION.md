# Implementation Overview

## Unix Filter Principles

1. **Data to stdout, UI to stderr**: Clean output data goes to stdout, all formatting (statistics, progress) goes to stderr
2. **Composable**: Works in pipelines with other Unix tools
3. **Streaming**: Processes input line-by-line with bounded memory
4. **No side effects**: Pure filter behavior - read stdin, write stdout

---

## Architecture

### Component Structure

```
src/patterndb-yaml/
    patterndb-yaml.py    # Core algorithm (PatterndbYaml class)
    cli.py             # CLI interface with typer + rich
    __init__.py        # Package exports
    __main__.py        # Module entry point
```

**Separation of Concerns**:
- `patterndb-yaml.py`: Pure Python logic, no CLI dependencies
- `cli.py`: User interface, progress display, TODO
- Clear API boundary allows embedding in other applications

---

## Testing

**Test Framework**: pytest exclusively

**Test Categories**:
- Unit tests: Core algorithm components
- Integration tests: End-to-end workflows
- Property tests: Edge cases and invariants
- Fixture tests: Reproducible test cases

**Test Coverage**: See [TEST_COVERAGE.md](../testing/TEST_COVERAGE.md) for comprehensive test documentation

---

## API for Embedding

The `PatterndbYaml` class can be used in other Python applications:

```python
from patterndb-yaml.patterndb-yaml import PatterndbYaml
import sys

# Create patterndb-yaml
processor = PatterndbYaml(TODO)
```
