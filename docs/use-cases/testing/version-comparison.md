# Testing: Application Version Comparison

## Overview

When testing a new version of an application, you need to verify it behaves the same as the old version. Log formats often change between versions (timestamps, log levels, formatting), making direct comparison impossible. Normalizing logs from both versions reveals actual behavioral differences.

## Core Problem Statement

"Application logs vary in format between versions, hiding whether the underlying behavior has changed." Direct diff comparison shows thousands of cosmetic differences, obscuring the handful of real behavioral changes that matter.

## Example Scenario

You're upgrading an e-commerce application from v2.3 to v2.4. The new version has reformatted logs:

- Old: `[INFO] 2024-01-15 10:23:45 - Order #1234 processed`
- New: `2024-01-15T10:23:45.123Z [info] Order ID=1234 status=processed`

The message is the same, but the format changed. You need to verify that v2.4 processes the same orders in the same sequence as v2.3.

## Input Data

???+ note "v2.3 Log (old version)"
    ```text
    --8<-- "use-cases/testing/fixtures/app-v2.3.log"
    ```

    Old log format with bracketed log levels and simple timestamps.

???+ note "v2.4 Log (new version)"
    ```text
    --8<-- "use-cases/testing/fixtures/app-v2.4.log"
    ```

    New log format with ISO timestamps and structured fields.

## Normalization Rules

Create rules that extract the semantic content, ignoring format differences:

???+ note "Normalization Rules"
    ```yaml
    --8<-- "use-cases/testing/fixtures/version-comparison-rules.yaml"
    ```

    Rules normalize both formats to consistent `[action:details]` format.

## Implementation

=== "CLI"

    ```bash
    # Normalize v2.3 logs
    patterndb-yaml --rules version-comparison-rules.yaml app-v2.3.log \
        --quiet > normalized-v2.3.log

    # Normalize v2.4 logs
    patterndb-yaml --rules version-comparison-rules.yaml app-v2.4.log \
        --quiet > normalized-v2.4.log

    # Compare normalized outputs
    diff normalized-v2.3.log normalized-v2.4.log
    ```

=== "Python"

    ```python
    from patterndb_yaml import PatterndbYaml
    from pathlib import Path
    import subprocess

    # Normalize both versions
    processor = PatterndbYaml(rules_path=Path("version-comparison-rules.yaml"))

    with open("app-v2.3.log") as f:
        with open("normalized-v2.3.log", "w") as out:
            processor.process(f, out)

    with open("app-v2.4.log") as f:
        with open("normalized-v2.4.log", "w") as out:
            processor.process(f, out)

    # Compare normalized logs
    result = subprocess.run(
        ["diff", "normalized-v2.3.log", "normalized-v2.4.log"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✓ Versions behave identically")
    else:
        print("✗ Behavioral differences detected:")
        print(result.stdout)
    ```

## Expected Output

???+ success "Normalized Logs (both versions)"
    ```text
    --8<-- "use-cases/testing/fixtures/version-comparison-normalized.log"
    ```

    Both versions produce identical normalized output, confirming same behavior.

## Practical Workflows

### 1. Automated Regression Testing

Integrate into CI/CD to automatically verify new versions:

```bash
#!/bin/bash
# Run test suite against both versions
docker run app:v2.3 run-tests > v2.3-test.log
docker run app:v2.4 run-tests > v2.4-test.log

# Normalize and compare
patterndb-yaml --rules test-rules.yaml v2.3-test.log --quiet > norm-v2.3.log
patterndb-yaml --rules test-rules.yaml v2.4-test.log --quiet > norm-v2.4.log

# Fail if behavior changed
if ! diff -q norm-v2.3.log norm-v2.4.log; then
    echo "ERROR: Behavioral regression detected"
    diff norm-v2.3.log norm-v2.4.log
    exit 1
fi
```

### 2. Upgrade Validation in Staging

Before production deployment, validate in staging:

```bash
# Capture baseline from current version in staging
patterndb-yaml --rules production-rules.yaml staging-current.log \
    --quiet > baseline.log

# Deploy new version and capture logs
patterndb-yaml --rules production-rules.yaml staging-new.log \
    --quiet > candidate.log

# Review differences
diff baseline.log candidate.log | less
```

### 3. A/B Testing Verification

Verify A and B variants behave identically except for intended changes:

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path

processor = PatterndbYaml(rules_path=Path("ab-test-rules.yaml"))

# Normalize both variants
for variant in ['a', 'b']:
    with open(f"variant-{variant}.log") as f:
        with open(f"normalized-{variant}.log", "w") as out:
            processor.process(f, out)

# Compare (should be identical except for feature-flag-specific behavior)
# ...
```

### 4. Multi-Version Compatibility Testing

Test that multiple versions can coexist (e.g., during rolling deployment):

```bash
# Collect logs from all running versions during rollout
for version in v2.2 v2.3 v2.4; do
    kubectl logs -l version=$version > logs-$version.log
    patterndb-yaml --rules compat-rules.yaml logs-$version.log \
        --quiet > normalized-$version.log
done

# Verify all versions handle same requests consistently
diff normalized-v2.2.log normalized-v2.3.log
diff normalized-v2.3.log normalized-v2.4.log
```

## Key Benefits

- **Focus on behavior, not format**: Ignore cosmetic log changes
- **Catch regressions early**: Detect unintended behavioral changes before production
- **Reduce test maintenance**: Rules adapt to format changes automatically
- **Confident upgrades**: Verify new versions work as expected

## Related Topics

- [Rules](../../features/rules/rules.md) - Pattern matching and normalization
- [Statistics](../../features/stats/stats.md) - Measure match coverage
- [Explain Mode](../../features/explain/explain.md) - Debug pattern matching
