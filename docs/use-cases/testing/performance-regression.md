# Testing: Performance Regression Detection

## Overview

Performance regressions are difficult to detect because absolute timing varies with load, hardware, and environment. Performance logs contain noisy data (timestamps, absolute durations) that obscures meaningful patterns. Normalizing performance metrics reveals structural changes (cache misses, query counts) that indicate regressions independent of environment.

## Core Problem Statement

"Absolute performance metrics vary too much to detect regressions reliably." A 50ms operation might be fast on one machine and slow on another. You need to identify structural inefficiencies (cache misses, excessive queries) that indicate real performance problems regardless of absolute timing.

## Example Scenario

Your application has two versions:

- **Baseline**: Efficient caching, minimal database queries
- **Regression**: Introduced caching bug causing cache misses and query explosion

Absolute timing varies (3ms vs 42ms for user_lookup), but the structural problem is clear: cache misses increased from 0 to 4-5, database queries increased from 0-1 to 5-6.

## Input Data

???+ note "Baseline Performance (Good)"
    ```text
    --8<-- "use-cases/testing/fixtures/perf-baseline.log"
    ```

    Baseline version with efficient caching (0 cache misses) and minimal queries.

???+ note "Regression Version (Bad)"
    ```text
    --8<-- "use-cases/testing/fixtures/perf-regression.log"
    ```

    Regression version with cache misses and query explosion on multiple operations.

## Normalization Rules

Create rules that extract structural performance indicators:

???+ note "Performance Regression Rules"
    ```yaml
    --8<-- "use-cases/testing/fixtures/perf-rules.yaml"
    ```

    Rules preserve: operation name, cache misses, database query counts.
    Rules ignore: timestamps, absolute durations (environment-dependent).

## Implementation

=== "CLI"

    ```bash
    # Normalize both versions
    patterndb-yaml --rules perf-rules.yaml baseline.log \
        --quiet > baseline-norm.log

    patterndb-yaml --rules perf-rules.yaml regression.log \
        --quiet > regression-norm.log

    # Compare structural metrics
    echo "Baseline cache misses:"
    grep -o 'cache_misses=[0-9]*' baseline-norm.log | \
        awk -F= '{sum+=$2} END {print sum}'

    echo "Regression cache misses:"
    grep -o 'cache_misses=[0-9]*' regression-norm.log | \
        awk -F= '{sum+=$2} END {print sum}'

    # Find operations with increased queries
    echo "\nOperations with increased DB queries:"
    join -t: <(grep -o 'PERF:[^,]*,.*db_queries=[0-9]*' baseline-norm.log | sort) \
             <(grep -o 'PERF:[^,]*,.*db_queries=[0-9]*' regression-norm.log | sort) | \
        awk -F, '{
            split($3, b, "="); split($6, r, "=");
            if (r[2] > b[2]) print $1 ": " b[2] " → " r[2] " queries"
        }'
    ```

=== "Python"

    ```python
    from patterndb_yaml import PatterndbYaml
    from pathlib import Path
    from collections import defaultdict
    import re

    # Normalize both versions
    processor = PatterndbYaml(rules_path=Path("perf-rules.yaml"))

    def extract_metrics(log_file):
        """Extract performance metrics from log"""
        with open(log_file) as f:
            from io import StringIO
            output = StringIO()
            processor.process(f, output)
            output.seek(0)

            metrics = defaultdict(lambda: {'cache_misses': [], 'db_queries': []})

            for line in output:
                if match := re.match(
                    r'\[PERF:([^,]+),cache_misses=(\d+),db_queries=(\d+)\]',
                    line.strip()
                ):
                    op, cache_misses, db_queries = match.groups()
                    metrics[op]['cache_misses'].append(int(cache_misses))
                    metrics[op]['db_queries'].append(int(db_queries))

            return metrics

    baseline = extract_metrics("baseline.log")
    regression = extract_metrics("regression.log")

    # Analyze regressions
    print("Performance Regression Analysis:\n")

    all_ops = set(baseline.keys()) | set(regression.keys())
    regressions_found = False

    for op in sorted(all_ops):
        base_cache = baseline.get(op, {}).get('cache_misses', [0])
        reg_cache = regression.get(op, {}).get('cache_misses', [0])

        base_queries = baseline.get(op, {}).get('db_queries', [0])
        reg_queries = regression.get(op, {}).get('db_queries', [0])

        # Calculate averages
        avg_base_cache = sum(base_cache) / len(base_cache)
        avg_reg_cache = sum(reg_cache) / len(reg_cache)

        avg_base_queries = sum(base_queries) / len(base_queries)
        avg_reg_queries = sum(reg_queries) / len(reg_queries)

        # Detect regressions
        cache_regressed = avg_reg_cache > avg_base_cache
        queries_regressed = avg_reg_queries > avg_base_queries

        if cache_regressed or queries_regressed:
            regressions_found = True
            print(f"⚠ {op}:")

            if cache_regressed:
                print(f"    Cache misses: {avg_base_cache:.1f} → {avg_reg_cache:.1f} "
                      f"(+{avg_reg_cache - avg_base_cache:.1f})")

            if queries_regressed:
                print(f"    DB queries: {avg_base_queries:.1f} → {avg_reg_queries:.1f} "
                      f"(+{avg_reg_queries - avg_base_queries:.1f})")
            print()

    if not regressions_found:
        print("✓ No performance regressions detected")
    ```

## Expected Output

???+ note "Baseline (Normalized)"
    ```text
    --8<-- "use-cases/testing/fixtures/perf-baseline-normalized.log"
    ```

    Baseline shows efficient operations with minimal cache misses and queries.

???+ warning "Regression (Normalized)"
    ```text
    --8<-- "use-cases/testing/fixtures/perf-regression-normalized.log"
    ```

    Regression shows:
    - **user_lookup**: 0→5 cache misses, 0-1→5-6 queries
    - **payment_process**: 0→3 cache misses, 2→8 queries
    - **inventory_check**: 0→12 cache misses, 1→15 queries

## Practical Workflows

### 1. CI/CD Performance Gates

Fail builds if performance metrics regress:

```bash
#!/bin/bash
# Run performance tests
run-perf-tests --baseline > baseline-perf.log
run-perf-tests --current > current-perf.log

# Normalize metrics
patterndb-yaml --rules perf-rules.yaml baseline-perf.log --quiet > base-norm.log
patterndb-yaml --rules perf-rules.yaml current-perf.log --quiet > curr-norm.log

# Calculate total cache misses
baseline_misses=$(grep -o 'cache_misses=[0-9]*' base-norm.log | \
    awk -F= '{sum+=$2} END {print sum}')
current_misses=$(grep -o 'cache_misses=[0-9]*' curr-norm.log | \
    awk -F= '{sum+=$2} END {print sum}')

# Calculate total queries
baseline_queries=$(grep -o 'db_queries=[0-9]*' base-norm.log | \
    awk -F= '{sum+=$2} END {print sum}')
current_queries=$(grep -o 'db_queries=[0-9]*' curr-norm.log | \
    awk -F= '{sum+=$2} END {print sum}')

# Check thresholds
echo "Performance Metrics:"
echo "  Cache misses: $baseline_misses → $current_misses"
echo "  DB queries: $baseline_queries → $current_queries"

if [ "$current_misses" -gt "$baseline_misses" ]; then
    echo "ERROR: Cache efficiency regressed"
    exit 1
fi

if [ "$current_queries" -gt "$baseline_queries" ]; then
    echo "ERROR: Database query count increased"
    exit 1
fi

echo "✓ Performance metrics acceptable"
```

### 2. Operation-Level Regression Detection

Detect which specific operations regressed:

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import re

processor = PatterndbYaml(rules_path=Path("perf-rules.yaml"))

def get_operation_metrics(log_file):
    """Extract metrics grouped by operation"""
    with open(log_file) as f:
        from io import StringIO
        output = StringIO()
        processor.process(f, output)
        output.seek(0)

        ops = {}
        for line in output:
            if match := re.match(
                r'\[PERF:([^,]+),cache_misses=(\d+),db_queries=(\d+)\]',
                line.strip()
            ):
                op, misses, queries = match.groups()
                if op not in ops:
                    ops[op] = {
                        'cache_misses': int(misses),
                        'db_queries': int(queries),
                        'samples': 1
                    }
                else:
                    # Average with previous samples
                    ops[op]['cache_misses'] = (
                        (ops[op]['cache_misses'] * ops[op]['samples'] + int(misses)) /
                        (ops[op]['samples'] + 1)
                    )
                    ops[op]['db_queries'] = (
                        (ops[op]['db_queries'] * ops[op]['samples'] + int(queries)) /
                        (ops[op]['samples'] + 1)
                    )
                    ops[op]['samples'] += 1

        return ops

baseline_ops = get_operation_metrics("baseline-perf.log")
current_ops = get_operation_metrics("current-perf.log")

# Compare operations
print("Operation-Level Performance Analysis:\n")

for op in sorted(set(baseline_ops.keys()) | set(current_ops.keys())):
    if op not in baseline_ops:
        print(f"+ {op}: NEW OPERATION")
        continue

    if op not in current_ops:
        print(f"- {op}: REMOVED OPERATION")
        continue

    base = baseline_ops[op]
    curr = current_ops[op]

    # Check for regressions (>10% increase)
    cache_regression = (curr['cache_misses'] - base['cache_misses']) / max(base['cache_misses'], 1)
    query_regression = (curr['db_queries'] - base['db_queries']) / max(base['db_queries'], 1)

    if cache_regression > 0.1 or query_regression > 0.1:
        print(f"⚠ {op}:")
        if cache_regression > 0.1:
            print(f"    Cache: {base['cache_misses']:.1f} → {curr['cache_misses']:.1f} "
                  f"({cache_regression*100:+.0f}%)")
        if query_regression > 0.1:
            print(f"    Queries: {base['db_queries']:.1f} → {curr['db_queries']:.1f} "
                  f"({query_regression*100:+.0f}%)")
    else:
        print(f"✓ {op}: No regression")
```

### 3. Historical Trend Analysis

Track performance metrics over time:

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import re
from datetime import datetime

processor = PatterndbYaml(rules_path=Path("perf-rules.yaml"))

# Process performance logs from multiple builds
builds = {
    "2024-11-01": "perf-2024-11-01.log",
    "2024-11-08": "perf-2024-11-08.log",
    "2024-11-15": "perf-2024-11-15.log",
}

history = {}
for date, log_file in sorted(builds.items()):
    with open(log_file) as f:
        from io import StringIO
        output = StringIO()
        processor.process(f, output)
        output.seek(0)

        total_misses = 0
        total_queries = 0

        for line in output:
            if match := re.search(r'cache_misses=(\d+)', line):
                total_misses += int(match.group(1))
            if match := re.search(r'db_queries=(\d+)', line):
                total_queries += int(match.group(1))

        history[date] = {
            'cache_misses': total_misses,
            'db_queries': total_queries
        }

# Display trend
print("Performance Trend Analysis:\n")
print("Date       | Cache Misses | DB Queries")
print("-----------|--------------|-----------")

for date in sorted(history.keys()):
    metrics = history[date]
    print(f"{date} |      {metrics['cache_misses']:6d} |   {metrics['db_queries']:7d}")

# Detect trends
dates = sorted(history.keys())
if len(dates) >= 2:
    first = history[dates[0]]
    latest = history[dates[-1]]

    cache_trend = ((latest['cache_misses'] - first['cache_misses']) /
                   max(first['cache_misses'], 1) * 100)
    query_trend = ((latest['db_queries'] - first['db_queries']) /
                   max(first['db_queries'], 1) * 100)

    print(f"\nTrend ({dates[0]} → {dates[-1]}):")
    print(f"  Cache misses: {cache_trend:+.0f}%")
    print(f"  DB queries: {query_trend:+.0f}%")
```

### 4. Load Test Comparison

Compare performance under load:

```bash
# Run load tests at different scales
for concurrency in 10 50 100; do
    echo "Testing with $concurrency concurrent users..."
    run-load-test --users=$concurrency > load-${concurrency}.log

    # Normalize and analyze
    patterndb-yaml --rules perf-rules.yaml load-${concurrency}.log \
        --quiet > load-${concurrency}-norm.log

    # Calculate metrics
    total_misses=$(grep -o 'cache_misses=[0-9]*' load-${concurrency}-norm.log | \
        awk -F= '{sum+=$2} END {print sum}')

    total_queries=$(grep -o 'db_queries=[0-9]*' load-${concurrency}-norm.log | \
        awk -F= '{sum+=$2} END {print sum}')

    operations=$(grep '^\[PERF:' load-${concurrency}-norm.log | wc -l)

    echo "  Operations: $operations"
    echo "  Avg cache misses per op: $(echo "scale=2; $total_misses / $operations" | bc)"
    echo "  Avg queries per op: $(echo "scale=2; $total_queries / $operations" | bc)"
    echo
done
```

### 5. A/B Performance Comparison

Compare performance between variants:

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import re

processor = PatterndbYaml(rules_path=Path("perf-rules.yaml"))

variants = {'variant-a': 'perf-a.log', 'variant-b': 'perf-b.log'}

results = {}
for variant, log_file in variants.items():
    with open(log_file) as f:
        from io import StringIO
        output = StringIO()
        processor.process(f, output)
        output.seek(0)

        cache_misses_by_op = {}
        queries_by_op = {}

        for line in output:
            if match := re.match(
                r'\[PERF:([^,]+),cache_misses=(\d+),db_queries=(\d+)\]',
                line.strip()
            ):
                op, misses, queries = match.groups()
                cache_misses_by_op[op] = cache_misses_by_op.get(op, 0) + int(misses)
                queries_by_op[op] = queries_by_op.get(op, 0) + int(queries)

        results[variant] = {
            'cache_misses': cache_misses_by_op,
            'queries': queries_by_op
        }

# Compare variants
print("A/B Performance Comparison:\n")

all_ops = set(results['variant-a']['cache_misses'].keys()) | \
          set(results['variant-b']['cache_misses'].keys())

for op in sorted(all_ops):
    a_misses = results['variant-a']['cache_misses'].get(op, 0)
    b_misses = results['variant-b']['cache_misses'].get(op, 0)

    a_queries = results['variant-a']['queries'].get(op, 0)
    b_queries = results['variant-b']['queries'].get(op, 0)

    if a_misses != b_misses or a_queries != b_queries:
        print(f"{op}:")
        print(f"  Cache misses: A={a_misses}, B={b_misses}")
        print(f"  DB queries: A={a_queries}, B={b_queries}")

        if b_misses < a_misses:
            print("  → Variant B has better caching")
        if b_queries < a_queries:
            print("  → Variant B has fewer queries")
```

## Key Benefits

- **Detect structural issues**: Find cache and query problems independent of timing
- **Environment-independent**: Compare across different hardware/load conditions
- **Automated gates**: Fail CI/CD builds on performance regressions
- **Root cause analysis**: Identify which operations regressed
- **Historical tracking**: Monitor performance trends over time

## Related Topics

- [Rules](../../features/rules/rules.md) - Pattern matching and normalization
- [Statistics](../../features/stats/stats.md) - Measure match coverage
- [Explain Mode](../../features/explain/explain.md) - Debug pattern matching
