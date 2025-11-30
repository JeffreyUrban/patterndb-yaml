# Test Coverage

## Overview

Comprehensive test suite for patterndb-yaml. Tests are organized into three categories:

1. **Unit Tests**: Targeted tests for specific components, classes, and methods
2. **Integration Tests**: End-to-end CLI and workflow testing
3. **Documentation Tests**: Sybil tests validating examples in documentation

All tests use **pytest exclusively** (not unittest).

## Test Philosophy

- **Prefer integration tests for CLI**: See [TESTING_STRATEGY.md](TESTING_STRATEGY.md) for rationale
- **Comprehensive coverage**: Exercise all code paths and edge cases
- **Synthetic test data**: All tests use generated data, no real user data
- **Invariant checking**: Verify algorithm guarantees hold under all conditions
- **Clear test names**: Describe what's being tested and expected behavior
- **Skip unreliable tests**: Tests that fail inconsistently or duplicate integration coverage should be skipped

## 1. Unit Tests

### 1.1 Core Normalization Engine

**File**: `tests/test_patterndb_yaml_advanced.py`
- PatterndbYaml class initialization
- Process method with various input scenarios
- Statistics tracking and reporting
- Error handling for missing/invalid rules

**File**: `tests/test_normalization_engine.py`
- Line-by-line normalization logic
- Pattern matching behavior
- Sequence processing
- Statistics accumulation

**File**: `tests/test_normalization_transforms.py`
- Output transformation logic
- Field substitution
- Template rendering

### 1.2 Pattern Filter

**File**: `tests/test_pattern_filter.py`
- PatternMatcher class initialization and cleanup
- Pattern matching behavior
- Process management with syslog-ng
- Error handling
- **Note**: main() function tests skipped - covered by CLI integration tests (see TESTING_STRATEGY.md)

### 1.3 Pattern Generator

**File**: `tests/test_pattern_generator.py`
- Pattern generation from YAML rules
- XML output formatting
- Rule validation
- Edge cases in pattern compilation

### 1.4 CLI Module

**File**: `tests/test_main.py`
- CLI argument parsing
- Command dispatch logic
- Error handling

### 1.5 Edge Cases

**File**: `tests/test_edge_cases.py`
- Empty input handling
- Malformed input
- Boundary conditions
- Special characters

## 2. Integration Tests

### 2.1 CLI End-to-End

**File**: `tests/test_cli.py`
- Command-line interface with stdin/stdout
- File processing
- Progress reporting
- Statistics output (text and JSON)
- Error reporting
- Help and version flags

**File**: `tests/test_cli_additional_coverage.py`
- Additional CLI scenarios
- Edge cases in command processing
- Stats format variations

**File**: `tests/test_cli_coverage.py`
- JSON stats formatting
- Quiet mode
- stdin input handling

**File**: `tests/test_cli_stats.py`
- Statistics calculation
- Output format variations

**File**: `tests/test_cli_error_paths.py`
- Error handling in CLI
- Invalid input scenarios
- Exception handling

**File**: `tests/test_cli_missing_paths.py`
- Missing file handling
- Invalid path scenarios

### 2.2 Application Integration

**File**: `tests/test_integration.py`
- End-to-end workflow scenarios
- Multiple file processing
- Real-world usage patterns

**File**: `tests/test_integration_application.py`
- Application log processing
- Multi-format log handling

**File**: `tests/test_integration_webserver.py`
- Web server log processing
- Access log normalization

## 3. Documentation Tests

### 3.1 Sybil Tests

**Files**: `docs/**/*.md`
- Documentation code examples
- User-facing API validation
- Tutorial verification
- Ensures docs stay synchronized with code

**Configuration**: `tests/test_docs_validation.py`
- Sybil configuration for markdown parsing
- Python code block execution
- Expected output validation

### 3.2 MkDocs Build

**File**: `tests/test_mkdocs_build.py`
- Documentation build validation
- Ensures docs can be generated without errors

## 4. Test Fixtures and Utilities

### 4.1 Common Fixtures

**File**: `tests/conftest.py`
- Shared pytest fixtures
- Temporary file/directory setup
- Mock data generators
- Test utilities

### 4.2 Test Utilities

**File**: `tests/test_utils.py`
- Helper functions for tests
- Data generation utilities
- Assertion helpers

### 4.3 Coverage Gap Testing

**File**: `tests/test_coverage_gaps.py`
- Targeted tests for uncovered code paths
- Edge cases identified by coverage analysis

## 5. Test Execution Strategy

### 5.1 Test Markers

```python
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests for individual components",
    "integration: Integration tests for multiple components",
    "slow: Slow tests (skipped by default)",
]
```

### 5.2 Running Tests

```bash
# Run all tests
pytest

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only fast tests (exclude slow)
pytest -m "not slow"

# Run specific test file
pytest tests/test_cli.py

# Run with coverage
pytest --cov=patterndb_yaml --cov-report=html

# Run with coverage report to terminal
pytest --cov=patterndb_yaml --cov-report=term

# Verbose output
pytest -v

# Show print statements
pytest -s

# Run specific test
pytest tests/test_cli.py::test_cli_help -v
```

## 6. Coverage Goals and Current Status

### Current Metrics (as of 2025-11-30)

- **Total Tests**: 289 tests (2 skipped)
- **Overall Coverage**: 85%
- **Test Execution Time**: ~74 seconds

### Per-Module Coverage

| Module | Statements | Coverage | Status |
|--------|-----------|----------|---------|
| `__init__.py` | 6 | 100% | ✅ Excellent |
| `__main__.py` | 1 | 100% | ✅ Excellent |
| `_version.py` | 13 | 100% | ✅ Excellent |
| `normalization_transforms.py` | 19 | 100% | ✅ Excellent |
| `pattern_filter.py` | 91 | 94% | ✅ Excellent |
| `normalization_engine.py` | 116 | 92% | ✅ Excellent |
| `patterndb_yaml.py` | 188 | 92% | ✅ Excellent |
| `pattern_generator.py` | 238 | 75% | ⚠️ Good |
| `cli.py` | 101 | 73% | ⚠️ Good |
| **TOTAL** | **773** | **85%** | ✅ **Good** |

### Coverage Targets

**Minimum coverage targets**:
- Overall: 85%+ ✅ **Currently met**
- Core algorithm (`patterndb_yaml.py`, `normalization_engine.py`): 90%+ ✅ **Currently met (92%)**
- Critical transforms (`normalization_transforms.py`): 100% ✅ **Currently met**

**What to test**:
- ✅ All public methods
- ✅ All error conditions
- ✅ All edge cases
- ✅ Algorithm invariants
- ✅ Determinism

**What not to test**:
- ❌ CLI formatting details (tested via integration)
- ❌ External dependencies (mocked or integration tested)
- ❌ Implementation details (test behavior, not internals)
- ❌ Main entry points with complex mocking (use CLI integration tests instead)

### Areas for Improvement

1. **CLI Module (73%)**: Additional error path testing
2. **Pattern Generator (75%)**: Edge cases in XML generation

These are non-critical areas where coverage is good but could be improved. The core algorithm and critical paths have excellent coverage.

## 7. Test Organization Best Practices

### Unit vs Integration Testing

See [TESTING_STRATEGY.md](TESTING_STRATEGY.md) for detailed guidance on:
- When to use integration tests vs unit tests
- Why mocking CLI entry points is brittle
- How to handle unreliable tests

**Key principle**: Prefer CLI integration tests for command-line entry points over mocking main() functions.

### Test Markers Usage

```python
@pytest.mark.unit
class TestPatternMatcher:
    """Unit tests for PatternMatcher class."""

@pytest.mark.integration
def test_cli_with_stdin():
    """Integration test for CLI with stdin input."""
```

### Skipping Unreliable Tests

```python
@pytest.mark.skip(
    reason="Mocking main() is unreliable in CI - covered by CLI integration tests"
)
def test_main_function():
    """This test is skipped - see TESTING_STRATEGY.md."""
```

## See Also

- [TESTING_STRATEGY.md](TESTING_STRATEGY.md) - Testing philosophy and best practices
