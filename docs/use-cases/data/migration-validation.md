# Data: Database Migration Validation

## Overview

Database migrations (MySQL to PostgreSQL, schema changes, version upgrades) require verification that application behavior remains unchanged. Query logs differ in syntax, timing, and database-specific idioms. Normalizing query logs before and after migration reveals whether the application performs the same operations.

## Core Problem Statement

"Database migrations change query syntax and timing, making it impossible to verify application behavior is preserved." Each database has unique syntax (RETURNING vs LAST_INSERT_ID), timing characteristics, and log formats, but the core data operations should be identical.

## Example Scenario

Your e-commerce application is migrating from MySQL to PostgreSQL. The application handles user lookup, order creation, payment processing, and shipping. You need to verify that:

- Same queries execute in same sequence
- Database-specific idioms are equivalent (LAST_INSERT_ID vs RETURNING)
- No data operations were missed or added

## Input Data

???+ note "Before Migration (MySQL)"
    ```text
    --8<-- "use-cases/data/fixtures/queries-before.log"
    ```

    MySQL query log with `LAST_INSERT_ID()` for retrieving inserted IDs.

???+ note "After Migration (PostgreSQL)"
    ```text
    --8<-- "use-cases/data/fixtures/queries-after.log"
    ```

    PostgreSQL query log using `RETURNING id` instead of separate query.

## Normalization Rules

Create rules that normalize both MySQL and PostgreSQL query formats:

???+ note "Migration Validation Rules"
    ```yaml
    --8<-- "use-cases/data/fixtures/migration-rules.yaml"
    ```

    Rules preserve: operation type (SELECT/INSERT/UPDATE), target table.
    Rules ignore: query timing, column details, database-specific syntax differences.
    Special handling: LAST_INSERT_ID filtered as database-specific idiom.

## Implementation

=== "CLI"

    ```bash
    # Normalize MySQL query log
    patterndb-yaml --rules migration-rules.yaml queries-before.log \
        --quiet > normalized-before.log

    # Normalize PostgreSQL query log
    patterndb-yaml --rules migration-rules.yaml queries-after.log \
        --quiet > normalized-after.log

    # Filter database-specific queries
    grep -v '^\[LAST-INSERT-ID\]' normalized-before.log > before-core.log
    cp normalized-after.log after-core.log

    # Compare core operations
    if diff -q before-core.log after-core.log; then
        echo "✓ Migration preserves application behavior"
    else
        echo "✗ Behavioral differences detected:"
        diff before-core.log after-core.log
    fi

    # Verify query counts
    echo "\nQuery distribution before migration:"
    grep -o '^\[[^:]*' normalized-before.log | sort | uniq -c

    echo "\nQuery distribution after migration:"
    grep -o '^\[[^:]*' normalized-after.log | sort | uniq -c
    ```

=== "Python"

    ```python
    from patterndb_yaml import PatterndbYaml
    from pathlib import Path
    from collections import Counter
    import re

    # Normalize both query logs
    processor = PatterndbYaml(rules_path=Path("migration-rules.yaml"))

    def normalize_queries(log_file):
        """Normalize query log and return list of operations"""
        with open(log_file) as f:
            from io import StringIO
            output = StringIO()
            processor.process(f, output)
            output.seek(0)
            return [line.strip() for line in output if line.strip()]

    before_queries = normalize_queries("queries-before.log")
    after_queries = normalize_queries("queries-after.log")

    # Filter database-specific queries
    db_specific = {'[LAST-INSERT-ID]'}
    before_core = [q for q in before_queries if q not in db_specific]
    after_core = [q for q in after_queries if q not in db_specific]

    # Compare core operations
    if before_core == after_core:
        print("✓ Migration preserves application behavior")
        print(f"\nCore operations ({len(before_core)} queries):")
        for i, query in enumerate(before_core, 1):
            print(f"  {i}. {query}")
    else:
        print("✗ Behavioral differences detected\n")

        # Find differences
        before_set = set(before_core)
        after_set = set(after_core)

        missing = before_set - after_set
        added = after_set - before_set

        if missing:
            print("Missing operations after migration:")
            for q in missing:
                print(f"  - {q}")

        if added:
            print("\nNew operations after migration:")
            for q in added:
                print(f"  + {q}")

    # Compare query distributions
    print("\n" + "="*60)
    print("Query Distribution Analysis:\n")

    def get_distribution(queries):
        """Count query types"""
        types = [re.match(r'\[([^\]:]+)', q).group(1)
                 for q in queries if re.match(r'\[([^\]:]+)', q)]
        return Counter(types)

    before_dist = get_distribution(before_queries)
    after_dist = get_distribution(after_queries)

    print("Before Migration:")
    for qtype, count in sorted(before_dist.items()):
        print(f"  {qtype}: {count}")

    print("\nAfter Migration:")
    for qtype, count in sorted(after_dist.items()):
        print(f"  {qtype}: {count}")

    # Check for distribution changes
    all_types = set(before_dist.keys()) | set(after_dist.keys())
    changes = []
    for qtype in all_types:
        before_count = before_dist.get(qtype, 0)
        after_count = after_dist.get(qtype, 0)
        if before_count != after_count:
            changes.append((qtype, before_count, after_count))

    if changes:
        print("\n⚠ Query count differences:")
        for qtype, before, after in changes:
            print(f"  {qtype}: {before} → {after}")
    ```

## Expected Output

???+ success "Core Operations (After Filtering DB-Specific Queries)"
    ```text
    --8<-- "use-cases/data/fixtures/migration-normalized.log"
    ```

    Both MySQL and PostgreSQL produce identical normalized operations, confirming behavior preservation.

### Database-Specific Handling

- **MySQL**: Uses `SELECT LAST_INSERT_ID()` to retrieve auto-increment IDs
- **PostgreSQL**: Uses `RETURNING id` clause in INSERT statements
- **Normalization**: Both approaches serve same purpose, filtered during comparison

## Practical Workflows

### 1. Parallel Run Validation

Run old and new databases in parallel, compare query logs:

```bash
#!/bin/bash
# Capture production traffic on MySQL
tail -f /var/log/mysql/query.log | \
    patterndb-yaml --rules migration-rules.yaml --quiet > mysql-prod.log &

# Replay same traffic to PostgreSQL (using query replay tool)
tail -f /var/log/postgresql/query.log | \
    patterndb-yaml --rules migration-rules.yaml --quiet > postgres-test.log &

# Periodically compare
while true; do
    sleep 60
    echo "Comparing last 1000 queries..."

    tail -1000 mysql-prod.log | grep -v LAST-INSERT-ID | sort > mysql-recent.txt
    tail -1000 postgres-test.log | sort > postgres-recent.txt

    if diff -q mysql-recent.txt postgres-recent.txt; then
        echo "✓ PostgreSQL behavior matches MySQL"
    else
        echo "⚠ Differences detected:"
        diff mysql-recent.txt postgres-recent.txt | head -20
    fi
done
```

### 2. Load Test Comparison

Run same load test against both databases:

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
from collections import Counter

processor = PatterndbYaml(rules_path=Path("migration-rules.yaml"))

# Run load test and capture queries
# loadtest.py captures queries to mysql-loadtest.log and postgres-loadtest.log

def analyze_load_test(log_file, db_name):
    """Analyze query distribution from load test"""
    with open(log_file) as f:
        from io import StringIO
        output = StringIO()
        processor.process(f, output)
        output.seek(0)
        queries = [line.strip() for line in output if line.strip()]

    # Count by table
    table_ops = Counter()
    for query in queries:
        import re
        if match := re.match(r'\[(\w+):(\w+)\]', query):
            op, table = match.groups()
            table_ops[f"{table}:{op}"] += 1

    print(f"\n{db_name} Load Test Results:")
    print(f"  Total queries: {len(queries)}")
    print("\n  Operations by table:")
    for key, count in sorted(table_ops.items()):
        print(f"    {key}: {count}")

    return table_ops

mysql_ops = analyze_load_test("mysql-loadtest.log", "MySQL")
postgres_ops = analyze_load_test("postgres-loadtest.log", "PostgreSQL")

# Compare distributions
print("\nDistribution Comparison:")
all_ops = set(mysql_ops.keys()) | set(postgres_ops.keys())
for op in sorted(all_ops):
    mysql_count = mysql_ops.get(op, 0)
    postgres_count = postgres_ops.get(op, 0)

    # Allow 5% variance (due to timing/concurrency)
    variance = abs(mysql_count - postgres_count) / max(mysql_count, postgres_count, 1)

    status = "✓" if variance < 0.05 else "⚠"
    print(f"  {status} {op}: MySQL={mysql_count}, PostgreSQL={postgres_count}")
```

### 3. Migration Regression Detection

Detect if migration introduces new/missing queries:

```bash
# Capture baseline from production MySQL
patterndb-yaml --rules migration-rules.yaml mysql-baseline.log \
    --quiet | grep -v LAST-INSERT-ID | sort -u > baseline-queries.txt

# Capture from PostgreSQL after migration
patterndb-yaml --rules migration-rules.yaml postgres-migrated.log \
    --quiet | sort -u > migrated-queries.txt

# Find regressions
echo "Missing queries (possible regressions):"
comm -23 baseline-queries.txt migrated-queries.txt

echo "\nNew queries (possible issues):"
comm -13 baseline-queries.txt migrated-queries.txt

echo "\nCommon queries (preserved behavior):"
comm -12 baseline-queries.txt migrated-queries.txt | wc -l
```

### 4. Schema Change Validation

Verify schema changes don't alter query patterns:

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import re

processor = PatterndbYaml(rules_path=Path("migration-rules.yaml"))

# Compare before/after schema change
before_log = "queries-before-schema-change.log"
after_log = "queries-after-schema-change.log"

def extract_query_patterns(log_file):
    """Extract query patterns (table + operation)"""
    with open(log_file) as f:
        from io import StringIO
        output = StringIO()
        processor.process(f, output)
        output.seek(0)
        patterns = set()
        for line in output:
            line = line.strip()
            if match := re.match(r'\[(\w+):(\w+)\]', line):
                patterns.add(match.group(0))
        return patterns

before_patterns = extract_query_patterns(before_log)
after_patterns = extract_query_patterns(after_log)

# Check for new tables or operations
new_patterns = after_patterns - before_patterns
removed_patterns = before_patterns - after_patterns

if removed_patterns:
    print("⚠ Queries no longer executed:")
    for pattern in sorted(removed_patterns):
        print(f"  - {pattern}")

if new_patterns:
    print("\nNew query patterns detected:")
    for pattern in sorted(new_patterns):
        print(f"  + {pattern}")

if not new_patterns and not removed_patterns:
    print("✓ Schema change preserves all query patterns")
```

### 5. Cross-Database Performance Comparison

Compare performance characteristics:

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import re

# Note: This requires custom rules that preserve timing information
# For this example, we'll parse timing from raw logs

def extract_timings(raw_log_file, db_type):
    """Extract query timings from raw logs"""
    timings_by_table = {}

    with open(raw_log_file) as f:
        for line in f:
            # Extract table and duration
            if db_type == 'mysql':
                if match := re.search(r'UPDATE (\w+).*Duration: (\d+)ms', line):
                    table, duration = match.groups()
                    timings_by_table.setdefault(table, []).append(int(duration))
            elif db_type == 'postgres':
                if match := re.search(r'UPDATE (\w+).*duration: ([\d.]+) ms', line):
                    table, duration = match.groups()
                    timings_by_table.setdefault(table, []).append(float(duration))

    # Calculate averages
    avg_timings = {}
    for table, durations in timings_by_table.items():
        avg_timings[table] = sum(durations) / len(durations)

    return avg_timings

mysql_timings = extract_timings("mysql-queries.log", "mysql")
postgres_timings = extract_timings("postgres-queries.log", "postgres")

print("Performance Comparison (UPDATE queries):\n")
all_tables = set(mysql_timings.keys()) | set(postgres_timings.keys())

for table in sorted(all_tables):
    mysql_avg = mysql_timings.get(table, 0)
    postgres_avg = postgres_timings.get(table, 0)

    if mysql_avg and postgres_avg:
        ratio = postgres_avg / mysql_avg
        status = "🚀" if ratio < 1 else "🐌" if ratio > 1.5 else "≈"
        print(f"{status} {table}:")
        print(f"    MySQL: {mysql_avg:.2f}ms")
        print(f"    PostgreSQL: {postgres_avg:.2f}ms")
        print(f"    Ratio: {ratio:.2f}x")
```

## Key Benefits

- **Verify migration correctness**: Confirm new database performs same operations
- **Detect regressions**: Find missing or altered queries after migration
- **Cross-database validation**: Compare MySQL, PostgreSQL, Oracle, etc.
- **Schema change verification**: Ensure schema changes preserve behavior
- **Performance baseline**: Compare query patterns for performance analysis

## Related Topics

- [Rules](../../features/rules/rules.md) - Pattern matching and normalization
- [Statistics](../../features/stats/stats.md) - Measure match coverage
- [Explain Mode](../../features/explain/explain.md) - Debug pattern matching
