# DevOps: CI/CD Build Reproducibility

## Overview

Reproducible builds are critical for supply chain security and debugging. Build logs contain ephemeral data (timestamps, PIDs, temp paths) that obscure whether builds are truly identical. Normalizing logs reveals real differences while ignoring noise.

## Core Problem Statement

"Build logs vary with every execution due to ephemeral details, making it impossible to verify builds are reproducible." You need to distinguish between cosmetic differences (timestamps, process IDs) and substantive changes (dependency versions, compiler settings, build artifacts).

## Example Scenario

Your CI/CD pipeline runs builds on every commit. You want to verify that:

- Rebuilding the same commit produces identical outputs
- Different commits with actual changes are detected
- Build environment changes (compiler updates, dependency changes) are caught

## Input Data

???+ note "Build 1 (14:32)"
    ```text
    --8<-- "use-cases/devops/fixtures/build1.log"
    ```

    First build with specific timestamp, PID, and temp directory.

???+ note "Build 2 (15:47)"
    ```text
    --8<-- "use-cases/devops/fixtures/build2.log"
    ```

    Second build of same code - different timestamp, PID, temp directory, but same dependencies and output.

???+ note "Build 3 (16:22)"
    ```text
    --8<-- "use-cases/devops/fixtures/build3.log"
    ```

    Third build with updated dependency (libssl 3.0.7) - should be detected as different.

## Normalization Rules

Create rules that preserve meaningful data while filtering ephemeral details:

???+ note "Build Normalization Rules"
    ```yaml
    --8<-- "use-cases/devops/fixtures/build-reproducibility-rules.yaml"
    ```

    Rules extract and preserve: compiler version, dependency versions, compiled files, and binary hash.
    Rules ignore: timestamps, PIDs, temp paths, and timing measurements.

## Implementation

=== "CLI"

    ```bash
    # Normalize all three builds
    patterndb-yaml --rules build-reproducibility-rules.yaml build1.log \
        --quiet > normalized-build1.log

    patterndb-yaml --rules build-reproducibility-rules.yaml build2.log \
        --quiet > normalized-build2.log

    patterndb-yaml --rules build-reproducibility-rules.yaml build3.log \
        --quiet > normalized-build3.log

    # Compare builds 1 and 2 (should be identical)
    if diff -q normalized-build1.log normalized-build2.log; then
        echo "✓ Builds 1 and 2 are reproducible"
    fi

    # Compare builds 2 and 3 (should differ)
    if ! diff -q normalized-build2.log normalized-build3.log; then
        echo "✗ Build 3 has changes:"
        diff normalized-build2.log normalized-build3.log
    fi
    ```

=== "Python"

    ```python
    from patterndb_yaml import PatterndbYaml
    from pathlib import Path
    import subprocess

    # Normalize all three builds
    processor = PatterndbYaml(
        rules_path=Path("build-reproducibility-rules.yaml")
    )

    for build_num in [1, 2, 3]:
        with open(f"build{build_num}.log") as f:
            with open(f"normalized-build{build_num}.log", "w") as out:
                processor.process(f, out)

    # Compare builds 1 and 2
    result = subprocess.run(
        ["diff", "-q", "normalized-build1.log", "normalized-build2.log"],
        capture_output=True
    )

    if result.returncode == 0:
        print("✓ Builds 1 and 2 are reproducible")
    else:
        print("✗ Builds differ unexpectedly")

    # Compare builds 2 and 3
    result = subprocess.run(
        ["diff", "normalized-build2.log", "normalized-build3.log"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("✗ Build 3 has changes:")
        print(result.stdout)
    ```

## Expected Output

???+ success "Builds 1 and 2 (Identical - Reproducible)"
    ```text
    --8<-- "use-cases/devops/fixtures/build-reproducibility-normalized.log"
    ```

    Builds 1 and 2 produce identical normalized output, confirming reproducibility.

???+ warning "Build 3 (Different - Dependency Update)"
    ```text
    --8<-- "use-cases/devops/fixtures/build-reproducibility-changed.log"
    ```

    Build 3 shows different dependency version (libssl 3.0.7) and different binary hash.

## Practical Workflows

### 1. CI/CD Reproducibility Verification

Automatically verify builds are reproducible in your pipeline:

```bash
#!/bin/bash
# Build twice from same commit
git checkout $COMMIT_SHA
docker build -t app:build1 . 2>&1 | tee build1.log
docker build -t app:build2 . 2>&1 | tee build2.log

# Normalize both builds
patterndb-yaml --rules build-rules.yaml build1.log --quiet > norm1.log
patterndb-yaml --rules build-rules.yaml build2.log --quiet > norm2.log

# Verify reproducibility
if ! diff -q norm1.log norm2.log; then
    echo "ERROR: Build is not reproducible"
    diff norm1.log norm2.log
    exit 1
fi

echo "✓ Build is reproducible"
```

### 2. Dependency Change Detection

Detect when dependencies change between builds:

```bash
# Normalize baseline build
patterndb-yaml --rules build-rules.yaml baseline-build.log \
    --quiet > baseline-norm.log

# Normalize current build
patterndb-yaml --rules build-rules.yaml current-build.log \
    --quiet > current-norm.log

# Extract and compare dependencies
grep '^\[dependency:' baseline-norm.log | sort > baseline-deps.txt
grep '^\[dependency:' current-norm.log | sort > current-deps.txt

if ! diff -q baseline-deps.txt current-deps.txt; then
    echo "Dependency changes detected:"
    diff baseline-deps.txt current-deps.txt
fi
```

### 3. Build Artifact Verification

Verify build artifacts match across environments:

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import re

processor = PatterndbYaml(rules_path=Path("build-rules.yaml"))

# Normalize builds from dev, staging, and prod environments
for env in ['dev', 'staging', 'prod']:
    with open(f"{env}-build.log") as f:
        with open(f"{env}-normalized.log", "w") as out:
            processor.process(f, out)

# Extract binary hashes
def get_binary_hash(normalized_log):
    with open(normalized_log) as f:
        for line in f:
            if match := re.match(r'\[binary-hash:(.*)\]', line):
                return match.group(1)
    return None

dev_hash = get_binary_hash("dev-normalized.log")
staging_hash = get_binary_hash("staging-normalized.log")
prod_hash = get_binary_hash("prod-normalized.log")

if dev_hash == staging_hash == prod_hash:
    print(f"✓ All environments produced identical binary: {dev_hash}")
else:
    print("✗ Binary hash mismatch across environments")
    print(f"  Dev:     {dev_hash}")
    print(f"  Staging: {staging_hash}")
    print(f"  Prod:    {prod_hash}")
```

### 4. Historical Build Comparison

Compare current builds against historical baselines:

```bash
# Archive normalized build as baseline
patterndb-yaml --rules build-rules.yaml build.log --quiet > baseline.log
git add baseline.log
git commit -m "Archive build baseline"

# Later, compare new builds against baseline
patterndb-yaml --rules build-rules.yaml new-build.log --quiet > new-norm.log

# Show what changed
echo "Changes since baseline:"
diff baseline.log new-norm.log | grep '^[<>]' | while read line; do
    case "$line" in
        \<*) echo "  Removed: ${line:2}" ;;
        \>*) echo "  Added:   ${line:2}" ;;
    esac
done
```

### 5. Supply Chain Verification

Verify builds in supply chain match expectations:

```bash
#!/bin/bash
# Normalize vendor-provided build log
patterndb-yaml --rules build-rules.yaml vendor-build.log \
    --quiet > vendor-norm.log

# Normalize your own rebuild
patterndb-yaml --rules build-rules.yaml local-build.log \
    --quiet > local-norm.log

# Extract and compare critical fields
for field in compiler dependency binary-hash; do
    echo "Comparing $field..."
    grep "^\[$field:" vendor-norm.log | sort > vendor-$field.txt
    grep "^\[$field:" local-norm.log | sort > local-$field.txt

    if ! diff -q vendor-$field.txt local-$field.txt; then
        echo "⚠ $field mismatch:"
        diff vendor-$field.txt local-$field.txt
    else
        echo "✓ $field matches"
    fi
done
```

## Key Benefits

- **Verify reproducibility**: Confirm identical commits produce identical builds
- **Detect real changes**: Distinguish dependency updates from noise
- **Supply chain security**: Verify vendor builds match your rebuilds
- **Debug build issues**: Compare successful vs. failed builds meaningfully
- **Environment parity**: Ensure dev/staging/prod build consistently

## Related Topics

- [Rules](../../features/rules/rules.md) - Pattern matching and normalization
- [Statistics](../../features/stats/stats.md) - Measure match coverage
- [Explain Mode](../../features/explain/explain.md) - Debug pattern matching
