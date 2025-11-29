# Testing: Golden Master Testing

## Overview

Golden Master Testing (also called Characterization Testing) captures the current behavior of legacy code as a baseline, enabling safe refactoring. The challenge is that output formats, timestamps, and generated IDs change even when behavior is identical. Normalizing outputs lets you compare behavior while ignoring cosmetic differences.

## Core Problem Statement

"Legacy code has no tests, but you need to refactor it safely." Direct output comparison fails because timestamps, transaction IDs, and formatting differ between runs. You need to verify that refactored code produces the same business logic results as the original.

## Example Scenario

Your e-commerce order processing system is a legacy monolith with verbose, inconsistent logging. You're refactoring it to use structured logging and modern patterns. To verify the refactoring preserves behavior:

1. Capture output from legacy system (the "golden master")
2. Run same inputs through refactored system
3. Normalize both outputs
4. Verify they match

## Input Data

???+ note "Legacy System Output"
    ```text
    --8<-- "use-cases/testing/fixtures/legacy-output.log"
    ```

    Legacy system with verbose prose-style logging, commas in numbers, mixed formats.

???+ note "Refactored System Output"
    ```text
    --8<-- "use-cases/testing/fixtures/refactored-output.log"
    ```

    Refactored system with structured logging, ISO timestamps, consistent key=value format.

## Normalization Rules

Create rules that extract business logic while ignoring format differences:

???+ note "Golden Master Normalization Rules"
    ```yaml
    --8<-- "use-cases/testing/fixtures/golden-master-rules.yaml"
    ```

    Rules preserve: business events, customer data, order amounts, inventory changes.
    Rules ignore: timestamps, transaction IDs, server names, processing times, number formatting.

## Implementation

=== "CLI"

    ```bash
    # Capture golden master from legacy system
    run-legacy-system --input test-data.json > legacy-golden.log

    # Save normalized golden master
    patterndb-yaml --rules golden-master-rules.yaml legacy-golden.log \
        --quiet > golden-master.txt

    # After refactoring, test new system
    run-refactored-system --input test-data.json > refactored-output.log

    # Normalize refactored output
    patterndb-yaml --rules golden-master-rules.yaml refactored-output.log \
        --quiet > refactored-normalized.txt

    # Compare
    if diff -q golden-master.txt refactored-normalized.txt; then
        echo "✓ Refactoring preserves behavior"
    else
        echo "✗ Behavioral differences detected:"
        diff golden-master.txt refactored-normalized.txt
    fi
    ```

=== "Python"

    <!-- verify-file: output.txt expected: golden-output-1.txt -->
    ```python
    import sys
    from patterndb_yaml import PatterndbYaml
    from pathlib import Path
    from io import StringIO

    # Redirect stdout to file for testing
    _original_stdout = sys.stdout
    output_file = open("output.txt", "w")
    sys.stdout = output_file

    processor = PatterndbYaml(rules_path=Path("golden-master-rules.yaml"))

    # Process legacy output
    with open("legacy-output.log") as f:
        legacy_input = StringIO(f.read())
        golden_output = StringIO()
        processor.process(legacy_input, golden_output)

    print("Golden master captured")
    print(f"  Events: {len(golden_output.getvalue().splitlines())}")

    # Process refactored output
    with open("refactored-output.log") as f:
        refactored_input = StringIO(f.read())
        refactored_output = StringIO()
        processor.process(refactored_input, refactored_output)

    # Compare
    golden_lines = sorted(golden_output.getvalue().strip().split('\n'))
    refactored_lines = sorted(refactored_output.getvalue().strip().split('\n'))

    if golden_lines == refactored_lines:
        print("\n✓ Refactoring preserves behavior")
    else:
        print("\n✗ Behavioral differences detected:")

        # Find differences
        golden_set = set(golden_lines)
        refactored_set = set(refactored_lines)

        missing = golden_set - refactored_set
        added = refactored_set - golden_set

        if missing:
            print("\nMissing in refactored (regressions):")
            for line in sorted(missing):
                print(f"  - {line}")

        if added:
            print("\nAdded in refactored (new behavior):")
            for line in sorted(added):
                print(f"  + {line}")

    # Restore stdout and close output file
    sys.stdout = _original_stdout
    output_file.close()
    ```

## Expected Output

???+ success "Normalized Output (Both Systems)"
    ```text
    --8<-- "use-cases/testing/fixtures/golden-master-normalized.log"
    ```

    Both legacy and refactored systems produce identical normalized behavior.

Note: Minor formatting differences (e.g., "1,111.10" vs "1111.10") are normalized away, focusing on business logic equivalence.

## Practical Workflows

### 1. Initial Golden Master Creation

Capture comprehensive golden master from production:

```bash
#!/bin/bash
# Run comprehensive test suite against legacy system
echo "Capturing golden master from legacy system..."

for test_case in tests/data/*.json; do
    echo "  Processing $(basename $test_case)..."

    # Run legacy system
    run-legacy-system --input "$test_case" > \
        "output/legacy-$(basename $test_case .json).log"

    # Normalize
    patterndb-yaml --rules golden-master-rules.yaml \
        "output/legacy-$(basename $test_case .json).log" \
        --quiet > "golden/$(basename $test_case .json).txt"
done

echo "Golden master created for $(ls tests/data/*.json | wc -l) test cases"
```

```

### 5. Regression Detection

Detect unintended behavior changes:

```bash
#!/bin/bash
# Continuous testing against golden master

echo "Running regression tests..."

# Track results
passed=0
failed=0

for test_case in tests/data/*.json; do
    name=$(basename "$test_case" .json)

    # Run refactored system
    run-refactored-system --input "$test_case" > output/current-$name.log 2>&1

    # Normalize
    patterndb-yaml --rules golden-master-rules.yaml \
        output/current-$name.log --quiet > output/current-$name.txt

    # Compare with golden master
    if diff -q golden/$name.txt output/current-$name.txt > /dev/null; then
        echo "  ✓ $name"
        ((passed++))
    else
        echo "  ✗ $name - REGRESSION DETECTED"
        ((failed++))

        # Save diff for review
        diff golden/$name.txt output/current-$name.txt > output/diff-$name.txt
    fi
done

# Report
echo ""
echo "Results: $passed passed, $failed failed"

if [ $failed -gt 0 ]; then
    echo ""
    echo "Regressions detected in:"
    ls output/diff-*.txt 2>/dev/null | while read diff_file; do
        name=$(basename "$diff_file" | sed 's/diff-\(.*\)\.txt/\1/')
        echo "  - $name (see output/diff-$name.txt)"
    done
    exit 1
fi

echo "✓ All regression tests passed"
```

## Key Benefits

- **Safe refactoring**: Verify behavior preservation without existing tests
- **Characterize legacy code**: Document current behavior as executable
  specification
- **Catch regressions**: Detect unintended changes immediately
- **Approval testing**: Human-in-the-loop for intentional behavior changes
- **Incremental improvement**: Refactor with confidence, one step at a time

## Related Topics

- [Rules](../../features/rules/rules.md) - Pattern matching and normalization
- [Statistics](../../features/stats/stats.md) - Measure match coverage
- [Explain Mode](../../features/explain/explain.md) - Debug pattern matching
