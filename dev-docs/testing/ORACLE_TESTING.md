# Oracle Testing Framework

## Overview

This document describes the enhanced oracle-based testing framework for patterndb-yaml. The oracle provides ground truth for validating the correctness of the optimized implementation.

## Oracle Implementation

### Location
`tests/oracle.py` - Reference implementation with comprehensive tracking

### Key Features

The oracle provides:

1. **Correctness validation**: Simple algorithm that is obviously correct
2. **Precomputed results**: All test cases analyzed in advance for fast test execution

### Data Structures

#### placeholder

#### `OracleResult`
Complete analysis of placeholder:
- `input_lines`: Original input
- `output_lines`: Expected output

### Oracle Algorithm

The oracle uses a simple brute-force approach:

```python
placeholder
```

**Key properties**:
- placeholder

## Test Fixtures

### Organization

Fixtures stored in `tests/fixtures/`:

- `handcrafted_cases.json` - test cases with known placeholder
- `edge_cases.json` - boundary condition tests
- `random_cases.json` - randomly generated with various properties
- `all_cases.json` - Combined fixture set

### Generation

Run `tests/generate_fixtures.py` to regenerate all fixtures:

```bash
cd tests
python generate_fixtures.py
```

This:
1. Generates random placeholder
2. Creates handcrafted test cases for known placeholder
3. Runs oracle analysis on all cases
4. Saves comprehensive JSON fixtures with all analysis data

**When to regenerate**:
- When oracle algorithm changes
- When adding new test patterns
- When fixing oracle bugs
- Before major releases

### Fixture Contents

Each fixture contains:

```json
{
  "name": "test_case_name",
  "description": "Human-readable description",
  "generator": {"type": "random|handcrafted|edge_case", ...},
  "placeholder": placeholder,
}
```

### Fixture Coverage

**placeholder**: placeholder

## Test Suite

### Location
`tests/test_comprehensive.py` - Main oracle-based test suite

### Test Classes

#### `TestHandcraftedCases`
- Tests known placeholder with predictable behavior
- Verifies output
- Validates placeholder

#### `TestEdgeCases`
- Empty input, boundary conditions
- placeholder

#### `TestRandomCases`
- Random placeholder with precomputed oracle results

#### `TestInvariantsWithOracle`
- placeholder

#### `TestFixtureQuality`
- Verifies all fixtures loaded correctly
- Validates fixture structure
- Checks coverage of edge cases

### Running Tests

```bash
# All comprehensive tests
pytest tests/test_comprehensive.py -v

# Specific test class
pytest tests/test_comprehensive.py::TestHandcraftedCases -v

# Specific fixture
pytest tests/test_comprehensive.py -k "placeholder" -v

# With coverage
pytest tests/test_comprehensive.py --cov=patterndb-yaml --cov-report=html
```

## Benefits of Oracle Approach

### 1. Correctness Guarantee
- Oracle implementation is simple enough to verify by inspection
- Brute force eliminates clever optimizations that could have bugs
- Ground truth for validating optimized implementation

### 2. Comprehensive Test Data
- Precomputed test cases cover wide range of scenarios
- Each case includes detailed expected results at multiple levels:
  - Final output (end-to-end validation)
  - Per-placeholder processing (detailed behavior validation)
  - Placeholder (algorithm internals validation)

### 3. Fast Test Execution
- Oracle runs once during fixture generation (slow O(placeholder) acceptable)
- Tests run against precomputed results (fast)
- No need to re-run oracle during development

### 4. Debugging Support
- Line-by-line processing info helps debug failures
- Sequence occurrence tracking shows placeholder
- Clear reason codes explain placeholder

### 5. Regression Prevention
- Fixtures capture current correct behavior
- Any change that breaks tests requires explanation
- Easy to add new fixtures for discovered edge cases

## Oracle vs Implementation

### What Oracle Tracks (but implementation doesn't need to)

The oracle tracks comprehensive metadata for testing purposes:
- placeholder

The actual implementation only needs:
- placeholder

### Overlap Rule

Both oracle and implementation enforce the same rule:

**placeholder**

## Maintenance

### Adding New Test Cases

1. Add pattern to `tests/generate_fixtures.py`:
   - Handcrafted: Add to `generate_handcrafted_fixtures()`
   - Random: Add configuration to `generate_random_fixtures()`
   - Edge case: Add to `generate_edge_case_fixtures()`

2. Regenerate fixtures:
   ```bash
   python tests/generate_fixtures.py
   ```

3. Run tests to verify:
   ```bash
   pytest tests/test_comprehensive.py -v
   ```

### Updating Oracle Algorithm

If oracle algorithm changes:

1. Update `placeholder()` in `tests/oracle.py`
2. Regenerate all fixtures: `python tests/generate_fixtures.py`
3. Review changes to fixture outputs (git diff)
4. Verify changes are correct
5. Commit updated fixtures

### Verifying Oracle Correctness

The oracle itself should be simple enough to verify by inspection. Key invariants:

- ✓ placeholder

## Statistics

Current test coverage (from fixture generation):

```
Total fixtures: placeholder
  Handcrafted: placeholder
  Edge cases: placeholder
  Random: placeholder
```

This comprehensive test suite provides high confidence in algorithm correctness across a wide variety of inputs and conditions.
