# Operations: Multi-Environment Validation

## Overview

Applications deployed across dev, staging, and production environments should behave consistently despite different configurations. Environment-specific details (hostnames, credentials, debug logging) make direct log comparison impossible. Normalizing logs reveals whether core behavior matches across environments.

## Core Problem Statement

"Environment configurations differ, making it impossible to verify application behavior is consistent." Each environment has unique hostnames, database endpoints, session IDs, and logging levels, but the core business logic should be identical.

## Example Scenario

Your e-commerce application runs in three environments:

- **Dev**: Localhost with debug logging enabled
- **Staging**: Internal staging infrastructure with standard logging
- **Production**: Production infrastructure with minimal logging

You need to verify that an order flow (login → create order → process payment → ship) works identically across all environments.

## Input Data

???+ note "Development Environment"
    ```text
    --8<-- "use-cases/operations/fixtures/dev.log"
    ```

    Development logs include DEBUG-level output, localhost hostnames, and local database connections.

???+ note "Staging Environment"
    ```text
    --8<-- "use-cases/operations/fixtures/staging.log"
    ```

    Staging logs use INFO-level only, staging hostnames, and staging infrastructure.

???+ note "Production Environment"
    ```text
    --8<-- "use-cases/operations/fixtures/prod.log"
    ```

    Production logs use INFO-level, production hostnames with availability zones, and production database endpoints.

## Normalization Rules

Create rules that extract business logic while ignoring environment-specific details:

???+ note "Multi-Environment Normalization Rules"
    ```yaml
    --8<-- "use-cases/operations/fixtures/multi-env-rules.yaml"
    ```

    Rules preserve: business events (orders, payments, shipping), user identifiers.
    Rules ignore: hostnames, database endpoints, session IDs, timestamps, DEBUG-level logs.

## Implementation

=== "CLI"

    ```bash
    # Normalize logs from all three environments
    patterndb-yaml --rules multi-env-rules.yaml dev.log \
        --quiet > normalized-dev.log

    patterndb-yaml --rules multi-env-rules.yaml staging.log \
        --quiet > normalized-staging.log

    patterndb-yaml --rules multi-env-rules.yaml prod.log \
        --quiet > normalized-prod.log

    # Extract core business logic (INFO-level events only)
    grep -v '^\[query-executed\]\|\[cache-miss\]\|\[email-queued\]' \
        normalized-dev.log > dev-core.log

    # Compare core behavior
    if diff -q dev-core.log normalized-staging.log && \
       diff -q normalized-staging.log normalized-prod.log; then
        echo "✓ All environments behave identically"
    else
        echo "✗ Environment behavior differs"
        diff dev-core.log normalized-staging.log
        diff normalized-staging.log normalized-prod.log
    fi
    ```

=== "Python"

    ```python
    from patterndb_yaml import PatterndbYaml
    from pathlib import Path
    import subprocess

    # Normalize all three environments
    processor = PatterndbYaml(rules_path=Path("multi-env-rules.yaml"))

    environments = ['dev', 'staging', 'prod']
    for env in environments:
        with open(f"{env}.log") as f:
            with open(f"normalized-{env}.log", "w") as out:
                processor.process(f, out)

    # Extract core business events (filter debug events)
    debug_events = {'[query-executed]', '[cache-miss]', '[email-queued]'}

    def extract_core_events(log_path):
        with open(log_path) as f:
            return [line.strip() for line in f
                    if line.strip() not in debug_events]

    dev_core = extract_core_events("normalized-dev.log")
    staging_core = extract_core_events("normalized-staging.log")
    prod_core = extract_core_events("normalized-prod.log")

    # Compare
    if dev_core == staging_core == prod_core:
        print("✓ All environments behave identically")
        print("\nCore business flow:")
        for event in dev_core:
            print(f"  {event}")
    else:
        print("✗ Environment behavior differs")
        if dev_core != staging_core:
            print("\nDev vs Staging differences:")
            print(f"  Dev only: {set(dev_core) - set(staging_core)}")
            print(f"  Staging only: {set(staging_core) - set(dev_core)}")
        if staging_core != prod_core:
            print("\nStaging vs Prod differences:")
            print(f"  Staging only: {set(staging_core) - set(prod_core)}")
            print(f"  Prod only: {set(prod_core) - set(staging_core)}")
    ```

## Expected Output

???+ success "Core Business Logic (All Environments)"
    ```text
    --8<-- "use-cases/operations/fixtures/multi-env-normalized.log"
    ```

    All environments produce identical normalized output for core business events.

Note: Development environment includes additional debug events (`[query-executed]`, `[cache-miss]`, `[email-queued]`) that are filtered out when comparing core business logic.

## Practical Workflows

### 1. Deployment Validation

Verify new deployments match expected behavior:

```bash
#!/bin/bash
# Capture baseline from production
kubectl logs -l app=myapp -n production --tail=1000 > prod-baseline.log
patterndb-yaml --rules env-rules.yaml prod-baseline.log --quiet > prod-norm.log

# Deploy to staging and capture logs
kubectl logs -l app=myapp -n staging --tail=1000 > staging-test.log
patterndb-yaml --rules env-rules.yaml staging-test.log \
    --quiet > staging-norm.log

# Compare core events
if diff <(grep '^\[order\|payment\|ship' prod-norm.log | sort) \
        <(grep '^\[order\|payment\|ship' staging-norm.log | sort); then
    echo "✓ Staging matches production behavior"
    echo "Safe to promote to production"
else
    echo "✗ Staging behavior differs from production"
    echo "Review changes before promoting"
fi
```

### 2. Configuration Drift Detection

Detect when environments drift in behavior:

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
from collections import Counter

processor = PatterndbYaml(rules_path=Path("env-rules.yaml"))

# Normalize logs from each environment
def get_event_distribution(log_file):
    """Extract normalized events and count their frequency"""
    with open(log_file) as f:
        from io import StringIO
        output = StringIO()
        processor.process(f, output)
        output.seek(0)
        events = [line.strip() for line in output if line.strip()]
        return Counter(events)

prod_events = get_event_distribution("prod.log")
staging_events = get_event_distribution("staging.log")

# Compare event distributions
for event in set(prod_events.keys()) | set(staging_events.keys()):
    prod_count = prod_events.get(event, 0)
    staging_count = staging_events.get(event, 0)

    # Allow 10% variance
    variance = abs(prod_count - staging_count) / \
        max(prod_count, staging_count, 1)
    if variance > 0.10:
        print(f"⚠ Event frequency differs: {event}")
        print(f"  Production: {prod_count}, Staging: {staging_count}")
```

### 3. Feature Flag Verification

Verify feature flags work correctly across environments:

```bash
# Normalize logs with feature flag enabled in dev
patterndb-yaml --rules env-rules.yaml dev-flag-on.log \
    --quiet > dev-flag-norm.log

# Normalize logs with feature flag enabled in staging
patterndb-yaml --rules env-rules.yaml staging-flag-on.log \
    --quiet > staging-flag-norm.log

# Compare to ensure feature behaves identically
diff dev-flag-norm.log staging-flag-norm.log || {
    echo "⚠ Feature flag behavior differs between environments"
    diff dev-flag-norm.log staging-flag-norm.log
}
```

### 4. Load Testing Validation

Verify load test in staging matches production patterns:

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path

processor = PatterndbYaml(rules_path=Path("env-rules.yaml"))

# Normalize production baseline
with open("prod-normal-load.log") as f:
    with open("prod-norm.log", "w") as out:
        processor.process(f, out)

# Normalize staging load test
with open("staging-load-test.log") as f:
    with open("staging-norm.log", "w") as out:
        processor.process(f, out)

# Extract event sequences
def extract_sequences(log_file, user_field="user"):
    """Group events by user to extract workflows"""
    sequences = {}
    with open(log_file) as f:
        for line in f:
            if user_field in line:
                # Extract user ID and event
                # Format: [event:data,user:123]
                import re
                if match := re.search(r'\[([^:]+):.*?user:(\d+)', line):
                    event, user_id = match.groups()
                    sequences.setdefault(user_id, []).append(event)
    return sequences

prod_sequences = extract_sequences("prod-norm.log")
staging_sequences = extract_sequences("staging-norm.log")

# Compare workflow patterns
prod_workflows = set(tuple(seq) for seq in prod_sequences.values())
staging_workflows = set(tuple(seq) for seq in staging_sequences.values())

if staging_workflows.issubset(prod_workflows):
    print("✓ Staging load test exhibits production workflows")
else:
    print("⚠ Staging has unexpected workflows:")
    for workflow in staging_workflows - prod_workflows:
        print(f"  {' → '.join(workflow)}")
```

### 5. Smoke Test Across Environments

Run same smoke test in all environments and verify identical behavior:

```bash
#!/bin/bash
# Run smoke test in each environment
for env in dev staging prod; do
    echo "Running smoke test in $env..."
    case $env in
        dev)     ENDPOINT="http://localhost:8080" ;;
        staging) ENDPOINT="https://staging.example.com" ;;
        prod)    ENDPOINT="https://api.example.com" ;;
    esac

    # Run test suite
    ./run-smoke-test.sh "$ENDPOINT" 2>&1 | tee "$env-smoke.log"

    # Normalize logs
    patterndb-yaml --rules env-rules.yaml "$env-smoke.log" \
        --quiet > "$env-smoke-norm.log"
done

# Compare all environments
if diff -q dev-smoke-norm.log staging-smoke-norm.log && \
   diff -q staging-smoke-norm.log prod-smoke-norm.log; then
    echo "✓ Smoke test passed identically in all environments"
else
    echo "✗ Smoke test results differ across environments"
    for env1 in dev staging; do
        for env2 in staging prod; do
            if [ "$env1" != "$env2" ]; then
                echo "\n$env1 vs $env2:"
                diff "$env1-smoke-norm.log" "$env2-smoke-norm.log" | head -20
            fi
        done
    done
fi
```

## Key Benefits

- **Verify environment parity**: Ensure dev, staging, and prod behave identically
- **Catch configuration drift**: Detect when environments diverge
- **Validate deployments**: Confirm new releases work correctly before production
- **Debug environment issues**: Understand differences between environments
- **Test with confidence**: Verify load tests and feature flags across environments

## Related Topics

- [Rules](../../features/rules/rules.md) - Pattern matching and normalization
- [Statistics](../../features/stats/stats.md) - Measure match coverage
- [Explain Mode](../../features/explain/explain.md) - Debug pattern matching
