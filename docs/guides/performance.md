# Performance Guide

Understand patterndb-yaml's performance characteristics and optimize for your use case.

## Quick Performance Facts

| Characteristic       | Description |
|----------------------|-------------|
| **Throughput**       | Varies by pattern complexity (typically 10k-100k lines/sec)        |
| **Memory**           | Constant regardless of input size (streaming architecture)        |
| **Disk I/O**         | Sequential reads only (no random access)        |
| **Space complexity** | O(rules + cache_entries) - independent of input size        |
| **Time complexity**  | O(rules × pattern_length) per line worst case, O(1) for cached lines        |

## Performance Characteristics

### Throughput

**Throughput varies by pattern complexity** - simpler patterns match faster, complex patterns with many alternatives or fields are slower.

**Factors affecting speed** (relative impact):

1. **Number of rules**: Each line is checked against rules sequentially until a match is found
2. **Pattern complexity**: Patterns with many components or alternatives take longer to match
3. **Match position**: If common patterns are first, most lines match quickly
4. **Cache hit rate**: Repeated identical lines are served from cache (65,536 entry LRU cache)
5. **Field extraction**: Patterns with many fields require more processing

**Measure your throughput**:
```bash
# Generate test data (1 million lines)
for i in {1..1000000}; do echo "2024-11-15 10:00:$i [INFO] User action: login"; done > test.log

# Benchmark
time patterndb-yaml --rules rules.yaml --quiet test.log > /dev/null
```

Use the `time` command to measure actual performance on your hardware and data.

### Memory Usage

patterndb-yaml uses **constant memory** regardless of input file size:

```
Total memory = Base overhead + Rule definitions + LRU cache + Sequence buffer

Base overhead:         ~10-50 MB (Python runtime + syslog-ng pattern matcher)
Rule definitions:      ~1 KB per rule (depends on pattern complexity)
LRU cache:            ~100 bytes × 65,536 entries = ~6.4 MB max
Sequence buffer:      Variable (typically < 1 MB, depends on sequence length)
```

**Memory-efficient architecture**:
- **Line-by-line streaming**: Processes one line at a time, no need to load entire file
- **Bounded cache**: LRU cache limited to 65,536 entries (oldest evicted when full)
- **Temporary file cleanup**: Intermediate XML files automatically cleaned up

**Example**: Processing a 10 GB log file uses the same memory as processing a 10 KB file.

### CPU Usage

**Algorithm complexity**: O(R × P) per line
- R = number of rules
- P = average pattern length (components in pattern)

**Best case**: O(1) for cached repeated lines (LRU cache hit)

**Average case**: O(R) when first rule matches quickly

**Worst case**: O(R × P) when line doesn't match any pattern (tries all rules)

**CPU-intensive operations** (ordered by typical impact):
1. **Pattern matching**: String comparisons for each text/serialized component
2. **ANSI code stripping**: Regex applied to every line (precompiled for speed)
3. **Field extraction**: Variable-length field capture
4. **Output formatting**: String template substitution with extracted fields
5. **Cache lookup**: Dictionary lookup for repeated lines (very fast)

## Optimization Strategies

### 1. Order Rules by Frequency

**Problem**: Common log patterns placed late in rules file cause all lines to check many patterns before matching.

**Solution**: Put most frequent patterns first in your rules file.

**Example**:
```yaml
rules:
  # Most common - 80% of lines (put first!)
  - name: info_log
    pattern:
      - field: timestamp
      - text: " [INFO] "
      - field: message
    output: "[INFO]"

  # Less common - 15% of lines
  - name: warn_log
    pattern:
      - field: timestamp
      - text: " [WARN] "
      - field: message
    output: "[WARN]"

  # Rare - 5% of lines (put last)
  - name: error_log
    pattern:
      - field: timestamp
      - text: " [ERROR] "
      - field: message
    output: "[ERROR]"
```

**Why this helps**: First match wins - 80% of lines match immediately without checking other rules.

**Measure impact**:
```bash
# Before reordering
time patterndb-yaml --rules rules-unordered.yaml --quiet app.log > /dev/null

# After reordering
time patterndb-yaml --rules rules-ordered.yaml --quiet app.log > /dev/null
```

**Expected improvement**: 20-50% speedup for logs with concentrated patterns.

### 2. Simplify Complex Patterns

**Problem**: Patterns with many alternatives or deeply nested components slow down matching.

**Solution**: Use field extraction instead of enumerating all alternatives.

**Before** (slow - 6 alternatives):
```yaml
pattern:
  - field: timestamp
  - text: " Level: "
  - alternatives:
      - [{ text: "TRACE" }]
      - [{ text: "DEBUG" }]
      - [{ text: "INFO" }]
      - [{ text: "WARN" }]
      - [{ text: "ERROR" }]
      - [{ text: "FATAL" }]
  - text: " "
  - field: message
```

**After** (fast - single field extraction):
```yaml
pattern:
  - field: timestamp
  - text: " Level: "
  - field: level
  - text: " "
  - field: message
```

**Performance impact**: 3-5× faster pattern matching.

### 3. Leverage the LRU Cache

**Problem**: Many log systems produce repeated identical lines (e.g., periodic health checks).

**Solution**: Ensure repeated lines are truly identical so the cache can serve them.

**Cache characteristics**:
- Size: 65,536 entries
- Algorithm: LRU (Least Recently Used eviction)
- Hit rate: Typically 30-70% for real-world logs with repetition

**Example logs with high cache hit rates**:
```
# Health checks (identical, repeated every 10 seconds)
2024-11-15 10:00:00 [INFO] Health check: OK
2024-11-15 10:00:10 [INFO] Health check: OK
2024-11-15 10:00:20 [INFO] Health check: OK
```

**Monitor cache effectiveness**:
```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path

processor = PatterndbYaml(rules_path=Path("rules.yaml"))
# After processing...
cache_info = processor.norm_engine.normalize_cached.cache_info()
print(f"Cache hits: {cache_info.hits}")
print(f"Cache misses: {cache_info.misses}")
print(f"Hit rate: {cache_info.hits / (cache_info.hits + cache_info.misses):.1%}")
```

### 4. Use Specific Patterns

**Problem**: Very general patterns match many lines, forcing later patterns to never be reached.

**Solution**: Make patterns as specific as possible while still matching intended lines.

**Too general**:
```yaml
pattern:
  - field: timestamp
  - text: " "
  - field: message
# Matches EVERYTHING with a timestamp - other patterns never reached!
```

**Better**:
```yaml
pattern:
  - field: timestamp
  - text: " [INFO] "  # Specific to INFO level
  - field: message
```

## Real-World Optimization Examples

### Scenario 1: Processing Large Files (> 1 GB)

**Problem**: Need to normalize large log files efficiently.

**Approach**:
```bash
# Use quiet mode to avoid stderr overhead
patterndb-yaml --rules rules.yaml --quiet large.log > normalized.log

# For very large files, show progress
patterndb-yaml --rules rules.yaml --quiet --progress huge.log > normalized.log
```

**Why**:
- `--quiet`: Eliminates statistics table rendering overhead
- `--progress`: Shows progress without slowing processing significantly
- Streaming architecture handles any file size

**Characteristics**:
- Memory: Constant (~20-50 MB regardless of file size)
- Processing: Linear time O(lines)
- Throughput: Typically 20k-50k lines/second on modern hardware

### Scenario 2: High-Frequency Real-Time Processing

**Problem**: Need to normalize streaming logs in real-time (e.g., tail -f).

**Approach**:
```bash
# Stream processing
tail -f /var/log/app.log | patterndb-yaml --rules rules.yaml --quiet

# With real-time monitoring
tail -f /var/log/app.log | patterndb-yaml --rules rules.yaml --quiet | \
    grep '\[ERROR\]' | \
    while read line; do
        # Alert on errors
        echo "$line" | mail -s "Error Alert" ops@example.com
    done
```

**Why**:
- Line-by-line processing introduces minimal latency (< 1ms per line)
- No buffering delays
- Cache helps with repeated log patterns

**Characteristics**:
- Latency: < 1 ms per line on modern hardware
- Memory: Constant
- Throughput: Limited by input rate, not processing speed

### Scenario 3: Batch Processing Multiple Files

**Problem**: Need to normalize many log files from different servers.

**Approach**:
```bash
# Serial processing
for log in /var/logs/server*.log; do
    patterndb-yaml --rules rules.yaml --quiet "$log" > "normalized_$(basename $log)"
done

# Parallel processing (4 at a time)
ls /var/logs/server*.log | xargs -P 4 -I {} sh -c \
    'patterndb-yaml --rules rules.yaml --quiet "{}" > "normalized_$(basename {})"'
```

**Why**:
- Each process is independent (no shared state)
- Parallel processing utilizes multiple CPU cores
- Memory usage: (base overhead) × (number of parallel processes)

**Characteristics**:
- Speedup: Near-linear with number of cores (if I/O not bottleneck)
- Memory: 20-50 MB per process

## Performance Monitoring

### Track Statistics

Use `--stats-format json` to monitor performance metrics:

```bash
patterndb-yaml --rules rules.yaml --stats-format json large.log 2> stats.json
```

Output:
```json
{
  "lines_processed": 1000000,
  "lines_matched": 950000,
  "match_rate": 95.0
}
```

**Key metrics**:
- `lines_processed`: Total throughput indicator
- `match_rate`: Pattern coverage - low rates indicate missing patterns

### Benchmark Your Data

**Create a baseline**:
```bash
#!/bin/bash
# benchmark.sh - Measure normalization performance

LOG_FILE=$1
RULES_FILE=${2:-rules.yaml}

echo "Benchmarking: $LOG_FILE"
echo "Rules: $RULES_FILE"
echo ""

# Count lines
LINES=$(wc -l < "$LOG_FILE")
echo "Input lines: $LINES"
echo ""

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

Usage:
```bash
chmod +x benchmark.sh
./benchmark.sh app.log
```

### Profile with Different Configurations

**Test multiple configurations**:
```bash
#!/bin/bash
# Compare different rule orderings

echo "Testing original rule order..."
time patterndb-yaml --rules rules-original.yaml --quiet test.log > /dev/null

echo ""
echo "Testing optimized rule order (common patterns first)..."
time patterndb-yaml --rules rules-optimized.yaml --quiet test.log > /dev/null
```

## Troubleshooting Performance Issues

### Slow Processing

**Diagnosis**:
1. Check number of rules: `grep -c "^  - name:" rules.yaml`
2. Identify complex patterns with many alternatives or components
3. Check match rate: Low match rates mean many patterns tried per line

**Solutions**:
- **Reduce rules**: Combine similar patterns where possible
- **Simplify patterns**: Replace alternatives with field extraction
- **Reorder rules**: Put common patterns first
- **Check for regex**: NUMBER parser is slower than simple text matching

### High Memory Usage

**Diagnosis**:
1. Check for sequence buffering: Long multi-line sequences consume memory
2. Monitor actual memory: `ps aux | grep patterndb-yaml`
3. Check if running multiple instances

**Solutions**:
- **Limit sequence length**: Keep multi-line sequences short
- **Reduce parallel processes**: If running in parallel, reduce concurrency
- **Clear cache between batches**: Restart process between large batches

### Low Match Rate

**Diagnosis**:
```bash
# Find unmatched lines
patterndb-yaml --rules rules.yaml --explain test.log 2>&1 | grep "No pattern matched"
```

**Solutions**:
- **Add missing patterns**: See [Common Patterns](./common-patterns.md)
- **Check whitespace**: Patterns must match whitespace exactly
- **Verify pattern order**: Specific patterns before general ones

See [Troubleshooting Guide](./troubleshooting.md) for detailed diagnosis.

## Best Practices

1. **Start simple**: Use default configuration first, optimize only if needed
2. **Measure first**: Benchmark before optimizing - don't guess
3. **Order by frequency**: Put most common patterns first in rules file
4. **Simplify alternatives**: Use field extraction instead of enumerating values
5. **Leverage caching**: Ensure repeated lines are identical for cache hits
6. **Stream when possible**: Use stdin/stdout for pipeline integration
7. **Quiet mode for performance**: Use `--quiet` to eliminate display overhead
8. **Profile with real data**: Test with actual production logs, not synthetic data

## Performance Checklist

Before processing large datasets:

- [ ] Tested configuration on representative sample (1000-10000 lines)
- [ ] Verified match rate > 95% (add missing patterns if needed)
- [ ] Ordered rules by frequency (common patterns first)
- [ ] Simplified complex patterns with many alternatives
- [ ] Benchmarked throughput on sample data
- [ ] Estimated total processing time: (total_lines ÷ sample_throughput)
- [ ] Verified sufficient disk space for output
- [ ] Considered parallel processing for multiple files

## Advanced: Measuring Pattern Complexity

**Pattern complexity score** = components + (2 × alternatives) + (0.5 × fields)

**Example 1** (simple, score = 4):
```yaml
pattern:
  - field: timestamp        # 0.5
  - text: " [INFO] "        # 1
  - field: message          # 0.5
# Score: 2 components + 1 field = 2.5
```

**Example 2** (complex, score = 14):
```yaml
pattern:
  - field: timestamp                    # 0.5
  - text: " ["                          # 1
  - alternatives:                       # 2 × 6 = 12
      - [{ text: "TRACE" }]
      - [{ text: "DEBUG" }]
      - [{ text: "INFO" }]
      - [{ text: "WARN" }]
      - [{ text: "ERROR" }]
      - [{ text: "FATAL" }]
  - text: "] "                          # 1
  - field: message                      # 0.5
# Score: 3 components + 12 (alternatives) + 1 field = 15
```

**Optimization target**: Keep patterns below complexity score of 10 where possible.

## See Also

- [Algorithm Details](../about/algorithm.md) - How patterndb-yaml works internally
- [CLI Reference](../reference/cli.md) - All performance-related options
- [Troubleshooting](./troubleshooting.md) - Solving performance problems
- [Common Patterns](./common-patterns.md) - Efficient pattern examples
