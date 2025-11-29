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

    ```python
    from patterndb_yaml import PatterndbYaml
    from pathlib import Path
    import subprocess

    processor = PatterndbYaml(rules_path=Path("golden-master-rules.yaml"))

    # Capture and normalize golden master
    result = subprocess.run(
        ["run-legacy-system", "--input", "test-data.json"],
        capture_output=True,
        text=True
    )

    from io import StringIO
    legacy_input = StringIO(result.stdout)
    golden_output = StringIO()
    processor.process(legacy_input, golden_output)

    # Save golden master
    with open("golden-master.txt", "w") as f:
        f.write(golden_output.getvalue())

    print("Golden master captured")
    print(f"  Events: {len(golden_output.getvalue().splitlines())}")

    # After refactoring, test new system
    result = subprocess.run(
        ["run-refactored-system", "--input", "test-data.json"],
        capture_output=True,
        text=True
    )

    refactored_input = StringIO(result.stdout)
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

### 2. Iterative Refactoring

Test each refactoring step against golden master:

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import subprocess
import sys

processor = PatterndbYaml(rules_path=Path("golden-master-rules.yaml"))

# Load all golden master files
golden_masters = {}
for golden_file in Path("golden").glob("*.txt"):
    with open(golden_file) as f:
        golden_masters[golden_file.stem] = set(f.read().strip().split('\n'))

print(f"Loaded {len(golden_masters)} golden master test cases\n")

# Run refactored system against all test cases
failures = []
for test_case in Path("tests/data").glob("*.json"):
    test_name = test_case.stem

    # Run refactored system
    result = subprocess.run(
        ["run-refactored-system", "--input", str(test_case)],
        capture_output=True,
        text=True
    )

    # Normalize output
    from io import StringIO
    output = StringIO()
    processor.process(StringIO(result.stdout), output)
    refactored_events = set(output.getvalue().strip().split('\n'))

    # Compare with golden master
    golden_events = golden_masters[test_name]

    if refactored_events == golden_events:
        print(f"✓ {test_name}")
    else:
        print(f"✗ {test_name}")
        failures.append(test_name)

        # Show differences
        missing = golden_events - refactored_events
        added = refactored_events - golden_events

        if missing:
            print(f"    Missing: {len(missing)} events")
        if added:
            print(f"    Added: {len(added)} events")

# Summary
passed = len(golden_masters) - len(failures)
total = len(golden_masters)
print(f"\nResults: {passed}/{total} passed")

if failures:
    print("\nFailed test cases:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
```

### 3. Approval Testing Workflow

Human-in-the-loop approval for behavior changes:

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import subprocess
import difflib

processor = PatterndbYaml(rules_path=Path("golden-master-rules.yaml"))

def normalize_output(raw_output):
    """Normalize system output"""
    from io import StringIO
    output = StringIO()
    processor.process(StringIO(raw_output), output)
    return sorted(output.getvalue().strip().split('\n'))

# Run test
result = subprocess.run(
    ["run-refactored-system", "--input", "tests/complex-order.json"],
    capture_output=True,
    text=True
)

refactored = normalize_output(result.stdout)

# Load golden master
golden_file = Path("golden/complex-order.txt")
with open(golden_file) as f:
    golden = sorted(f.read().strip().split('\n'))

# Compare
if refactored == golden:
    print("✓ Output matches golden master")
else:
    print("⚠ Output differs from golden master\n")

    # Show diff
    diff = difflib.unified_diff(
        golden,
        refactored,
        fromfile="golden master",
        tofile="refactored output",
        lineterm=""
    )

    print('\n'.join(diff))

    # Prompt for approval
    print("\nOptions:")
    print("  [a] Approve new output (update golden master)")
    print("  [r] Reject (fix refactoring)")
    print("  [v] View details")

    choice = input("\nChoice: ").lower()

    if choice == 'a':
        # Update golden master
        with open(golden_file, "w") as f:
            f.write('\n'.join(refactored) + '\n')
        print("✓ Golden master updated")
    elif choice == 'r':
        print("✗ Please fix refactoring to match golden master")
        exit(1)
    elif choice == 'v':
        print("\nDetailed differences:")
        for line in difflib.context_diff(golden, refactored):
            print(line)
```

### 4. Coverage Analysis

Verify golden master covers all code paths:

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
from collections import Counter
import subprocess

processor = PatterndbYaml(rules_path=Path("golden-master-rules.yaml"))

# Expected event types from code review
EXPECTED_EVENTS = {
    'CUSTOMER', 'DISCOUNT', 'SUBTOTAL', 'TAX', 'TOTAL',
    'PAYMENT', 'INVENTORY', 'SHIPPING', 'ORDER_COMPLETE', 'EMAIL'
}

# Run all test cases and collect events
all_events = Counter()

for test_case in Path("tests/data").glob("*.json"):
    result = subprocess.run(
        ["run-refactored-system", "--input", str(test_case)],
        capture_output=True,
        text=True
    )

    from io import StringIO
    output = StringIO()
    processor.process(StringIO(result.stdout), output)

    for line in output.getvalue().split('\n'):
        if line.strip():
            # Extract event type
            event_type = line.split(':')[0].strip('[')
            all_events[event_type] += 1

# Analyze coverage
print("Golden Master Coverage Analysis:\n")
print(f"{'Event Type':<20} {'Count':<10}")
print("-" * 30)

for event in sorted(EXPECTED_EVENTS):
    count = all_events.get(event, 0)
    status = "✓" if count > 0 else "✗"
    print(f"{status} {event:<18} {count:<10}")

# Find unexpected events
unexpected = set(all_events.keys()) - EXPECTED_EVENTS
if unexpected:
    print("\nUnexpected events:")
    for event in sorted(unexpected):
        print(f"  + {event} ({all_events[event]} times)")

# Coverage summary
covered = len([e for e in EXPECTED_EVENTS if all_events[e] > 0])
total = len(EXPECTED_EVENTS)
print(f"\nCoverage: {covered}/{total} event types ({covered/total*100:.0f}%)")
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
- **Characterize legacy code**: Document current behavior as executable specification
- **Catch regressions**: Detect unintended changes immediately
- **Approval testing**: Human-in-the-loop for intentional behavior changes
- **Incremental improvement**: Refactor with confidence, one step at a time

## Related Topics

- [Rules](../../features/rules/rules.md) - Pattern matching and normalization
- [Statistics](../../features/stats/stats.md) - Measure match coverage
- [Explain Mode](../../features/explain/explain.md) - Debug pattern matching
