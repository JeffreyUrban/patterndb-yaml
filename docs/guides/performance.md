# Performance Guide

Optimize patterndb-yaml for your use case by understanding its architecture and syslog-ng's pattern matching engine.

## Architecture

`patterndb-yaml` uses [syslog-ng's patterndb engine](https://www.syslog-ng.com/technical-documents/doc/syslog-ng-open-source-edition/3.38/administration-guide/56#TOPIC-1829130) for pattern matching. Understanding this helps optimize performance.

### Pattern Matching Algorithm

syslog-ng uses a **radix tree** (longest prefix match) for pattern matching:

- **Character-by-character matching** from the beginning of messages
- **Tree structure** organizes patterns alphabetically
- **Performance scales independently** of the number of patterns
- **Efficient subset evaluation** - only relevant branches checked at each position

See ['How pattern matching works` in the syslog-ng documentation](https://syslog-ng.github.io/admin-guide/120_Parser/006_db_parser/000_Classifying_log_messages/001_How_pattern_matching_works) for details on the radix tree approach.

### Memory Architecture

`patterndb-yaml` processes logs line-by-line without loading entire files:

**Memory components**:

- **Python runtime** + syslog-ng pattern matcher (base overhead)
- **Rule definitions** (scales with number/complexity of patterns)
- **LRU cache** (65,536 entry limit for repeated lines)
- **Sequence buffer** (holds multi-line sequences in progress)

Large files can be processed with constant memory due to streaming.

## Optimization Strategies

### 1. Order Rules by Frequency

Put frequently-matched patterns first in your rules file.

**Why**: patterndb-yaml tries rules sequentially until a match is found (first match wins).

**Example**:
```yaml
rules:
  # Most common pattern first
  - name: info_log
    pattern:
      - field: timestamp
      - text: " [INFO] "
      - field: message
    output: "[INFO]"

  # Less common patterns after
  - name: error_log
    pattern:
      - field: timestamp
      - text: " [ERROR] "
      - field: message
    output: "[ERROR]"
```

**Measure impact**:
```bash
time patterndb-yaml --rules rules.yaml --quiet app.log > /dev/null
```

### 2. Use Specific Patterns

Avoid overly-general patterns that match everything:

**Too general**:
```yaml
pattern:
  - field: timestamp
  - text: " "
  - field: message
# Matches everything with a timestamp!
```

**Better**:
```yaml
pattern:
  - field: timestamp
  - text: " [INFO] "  # Specific to INFO level
  - field: message
```

## Real-World Scenarios

### Large File Processing

**Approach**:
```bash
# Quiet mode for batch processing
patterndb-yaml --rules rules.yaml --quiet large.log > normalized.log

# Show progress for very large files
patterndb-yaml --rules rules.yaml --progress huge.log > normalized.log
```

**Why**:

- `--quiet`: Eliminates statistics display overhead
- `--progress`: Provides feedback without significant slowdown
- Streaming handles files of any size

### Real-Time Stream Processing

**Approach**:
```bash
# Stream processing
tail -f /var/log/app.log | patterndb-yaml --rules rules.yaml --quiet

# With filtering
tail -f /var/log/app.log | \
    patterndb-yaml --rules rules.yaml --quiet | grep '\[ERROR\]'
```

**Why**:

- Line-by-line processing minimizes latency
- No buffering delays
- Cache benefits repeated patterns

### Batch Processing Multiple Files

**Approach**:
```bash
# Serial processing
for log in logs/*.log; do
    patterndb-yaml --rules rules.yaml --quiet "$log" > \
        "normalized_$(basename $log)"
done

# Parallel processing (4 at a time)
ls logs/*.log | xargs -P 4 -I {} sh -c \
    'patterndb-yaml --rules rules.yaml --quiet "{}" > \
     "normalized_$(basename {})"'
```

**Why**:

- Each process is independent (no shared state)
- Parallel processing utilizes multiple cores
- Linear memory scaling with number of processes

## Performance Monitoring

### Track Statistics

```bash
patterndb-yaml --rules rules.yaml --stats-format json large.log 2> stats.json
```

Output:
```json
{
  "lines_processed": 1000000,
  "lines_matched": 950000,
  "match_rate": 0.95
}
```

**Key metrics**:

- `lines_processed`: Total throughput
- `match_rate`: Pattern coverage (low values indicate missing patterns)

### Benchmark Your Data

```bash
#!/bin/bash
LOG_FILE=$1
RULES_FILE=${2:-rules.yaml}

echo "Benchmarking: $LOG_FILE with $RULES_FILE"

# Count lines
LINES=$(wc -l < "$LOG_FILE")
echo "Input lines: $LINES"

# Measure time
START=$(date +%s.%N)
patterndb-yaml --rules "$RULES_FILE" --quiet "$LOG_FILE" > /dev/null
END=$(date +%s.%N)

# Calculate throughput
ELAPSED=$(echo "$END - $START" | bc)
THROUGHPUT=$(echo "scale=0; $LINES / $ELAPSED" | bc)

echo "Elapsed: ${ELAPSED}s"
echo "Throughput: ${THROUGHPUT} lines/sec"
```

## Troubleshooting

### Low Match Rate

**Diagnosis**:
```bash
# Find unmatched lines
patterndb-yaml --rules rules.yaml --explain test.log 2>&1 | \
    grep "No pattern matched"
```

**Solutions**:

- Add missing patterns for unmatched log formats
- Check whitespace (patterns must match exactly)
- Verify pattern order (specific before general)

### High Memory Usage

**Diagnosis**:

- Check for long multi-line sequences (consume buffer memory)
- Monitor with: `ps aux | grep patterndb-yaml`
- Check if running multiple instances

**Solutions**:

- Keep sequences short where possible
- Reduce parallel process count
- Restart between large batches to clear cache

## Best Practices

1. **Measure first** - Benchmark with real data before optimizing
2. **Order by frequency** - Common patterns first
3. **Simplify alternatives** - Use field extraction when possible
4. **Profile with real data** - Test with production logs
5. **Use quiet mode** - `--quiet` for batch processing
6. **Monitor match rate** - Low rates indicate missing patterns

## See Also

- [syslog-ng Pattern Database Documentation](https://syslog-ng.github.io/admin-guide/120_Parser/006_db_parser/004_The_syslog-ng_patterndb_format/README) - Details on the radix tree algorithm
- [Algorithm Details](../about/algorithm.md) - How patterndb-yaml works internally
- [Troubleshooting](./troubleshooting.md) - Solving performance problems
- [Common Patterns](./common-patterns.md) - Efficient pattern examples
