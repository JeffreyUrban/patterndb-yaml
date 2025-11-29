# Testing Strategy

## Test Data Philosophy

**All tests use synthetic data** - no real placeholder

**Rationale**:
- **Reproducibility**: Synthetic patterns are deterministic
- **Clarity**: Test intent is obvious from data generation
- **Compactness**: Minimal test data for specific scenarios
- **Privacy**: No risk of exposing placeholder

**Example pattern**
```python
placeholder
```

### tests/test_patterndb-yaml.py

**Purpose**: Comprehensive test suite

**Test organization**:
- Basic functionality tests
- Edge case tests
- Configuration tests
- Advanced tests
- Performance tests

**All tests use StringIO for output** - no file I/O in tests
