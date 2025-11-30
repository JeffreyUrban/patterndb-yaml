# Testing Strategy

## Test Pyramid and Coverage Approach

### Prefer Integration Tests for CLI Entry Points

**Key principle**: Integration tests provide better coverage for command-line entry points than mocking.

**Why mocking main() functions is brittle**:
- pytest-cov instrumentation modifies code execution paths
- @patch decorators may not apply correctly in CI environments
- Module-level imports are cached differently across test execution contexts
- Test collection/execution order affects mock application
- Mocks can drift from real behavior over time

**When to use integration tests vs unit tests**:

**Use integration tests for**:
- CLI entry points (main functions)
- End-to-end workflows
- Command execution paths
- Features that integrate multiple components

**Use unit tests for**:
- Individual classes and methods
- Pure functions with no external dependencies
- Algorithm validation
- Edge case handling in isolated components

**Example**: `pattern_filter.main()` testing
- ❌ **Avoid**: Mocking Path, stdin, and PatternMatcher to test main()
- ✅ **Prefer**: CLI integration tests (`test_cli.py`) that execute actual commands

Integration tests for CLI provide:
- Real command execution end-to-end
- No dependency on complex mock chains
- Consistent behavior across environments
- Better detection of integration issues

## Test Data Philosophy

**All tests use synthetic data** - no real user data

**Rationale**:
- **Reproducibility**: Synthetic patterns are deterministic
- **Clarity**: Test intent is obvious from data generation
- **Compactness**: Minimal test data for specific scenarios
- **Privacy**: No risk of exposing sensitive information

## Test Organization

### Unit Tests

**tests/test_pattern_filter.py**:
- PatternMatcher class initialization and cleanup
- Pattern matching behavior
- Process management
- Error handling in isolated methods

**tests/test_pattern_generator.py**:
- Pattern generation logic
- XML output formatting
- Rule validation

**tests/test_patterndb_yaml.py**:
- Core normalization engine
- Sequence processing
- Statistics tracking
- Rule loading and validation

### Integration Tests

**tests/test_cli.py**:
- Command-line interface end-to-end
- stdin/stdout handling
- File processing
- Option parsing and validation
- Error reporting

**docs/** (Sybil tests):
- Documentation examples
- User-facing API validation
- Tutorial verification

### Test Execution

**All tests use in-memory I/O** - StringIO for output, no file I/O in unit tests where possible

**Test markers**:
- `@pytest.mark.unit` - Fast, isolated tests
- `@pytest.mark.integration` - End-to-end tests
- `@pytest.mark.slow` - Performance or long-running tests

## When to Skip Tests

**Skip tests that**:
- Require unreliable mocking of complex execution paths
- Duplicate coverage provided by integration tests
- Fail inconsistently due to environment differences

**Mark skipped tests clearly**:
```python
@pytest.mark.skip(reason="Functionality covered by CLI integration tests in test_cli.py")
```
