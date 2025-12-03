# PatterndbYaml API

API reference for the `PatterndbYaml` class - the core log normalization processor.

## Overview

The `PatterndbYaml` class provides log normalization using YAML-defined rules and syslog-ng's pattern matching engine. It processes input streams line-by-line with constant memory, supporting files of any size.

## Class Reference

::: patterndb_yaml.patterndb_yaml.PatterndbYaml
    options:
      show_source: false
      show_root_heading: true
      heading_level: 3

## Basic Usage

### Simple Processing

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path

# Create processor
processor = PatterndbYaml(rules_path=Path("rules.yaml"))

# Process a file
with open("input.log") as infile, open("output.log", "w") as outfile:
    processor.process(infile, outfile)

# Get statistics
stats = processor.get_stats()
print(f"Matched {stats['lines_matched']} of {stats['lines_processed']} lines")
print(f"Match rate: {stats['match_rate']:.1%}")
```

### In-Memory Processing with StringIO

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
from io import StringIO

processor = PatterndbYaml(rules_path=Path("rules.yaml"))

# Process string data
input_data = StringIO("""
2024-11-15 10:00:01 [INFO] User login successful
2024-11-15 10:00:02 [ERROR] Database connection failed
""")

output_data = StringIO()
processor.process(input_data, output_data)

# Get normalized output
output_data.seek(0)
normalized = output_data.read()
print(normalized)
```

### Batch Processing with normalize_lines()

For efficient processing of lines already in memory, use `normalize_lines()` to avoid StringIO overhead:

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path

processor = PatterndbYaml(rules_path=Path("rules.yaml"))

# Process a list of lines directly
lines = [
    "2024-11-15 10:00:01 [INFO] User login successful",
    "2024-11-15 10:00:02 [ERROR] Database connection failed",
    "2024-11-15 10:00:03 [INFO] User logout",
]

# Normalize in one batch - returns list of normalized lines
normalized_lines = processor.normalize_lines(lines)

for original, normalized in zip(lines, normalized_lines):
    print(f"Original: {original}")
    print(f"Normalized: {normalized}\n")
```

**Benefits over StringIO**:

- **No string concatenation overhead** - processes lines directly without join/split operations
- **Simpler code** - direct list input and output
- **Better for testing** - easier to work with lists in unit tests

**When to use**:

- Processing lines from `file.readlines()` or `splitlines()`
- Batch processing in memory (API endpoints, testing)
- When you need random access to results

**When to use `process()` instead**:

- Streaming large files (constant memory usage)
- Processing stdin/stdout
- Files that don't fit in memory

### Explain Mode for Debugging

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path

# Enable explain mode to see matching decisions
processor = PatterndbYaml(
    rules_path=Path("rules.yaml"),
    explain=True  # Outputs explanations to stderr
)

with open("test.log") as infile, open("output.log", "w") as outfile:
    processor.process(infile, outfile)

# stderr will show:
# EXPLAIN: [Line 1] Matched rule 'nginx_access'
# EXPLAIN: [Line 2] No pattern matched - passed through
# EXPLAIN: [Line 3] Matched rule 'app_error'
```

## Features

### Progress Tracking

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path

processor = PatterndbYaml(rules_path=Path("rules.yaml"))

def progress_callback(current, total):
    """Called periodically during processing"""
    if total > 0:
        percent = (current / total) * 100
        print(f"Progress: {current}/{total} ({percent:.1f}%)", end='\r')

# Process with progress updates
with open("large.log") as infile, open("output.log", "w") as outfile:
    processor.process(infile, outfile, progress_callback=progress_callback)

print("\nDone!")
```

### Reusing Processor Instance

**Important**: Create processor once, reuse for multiple files.

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path

# Create processor once
processor = PatterndbYaml(rules_path=Path("rules.yaml"))

# Process multiple files
for log_file in ["server1.log", "server2.log", "server3.log"]:
    with open(log_file) as infile, \
            open(f"{log_file}.normalized", "w") as outfile:
        processor.process(infile, outfile)

    stats = processor.get_stats()
    print(f"{log_file}: {stats['match_rate']:.1%} match rate")
```

**Why reuse**: Processor initialization (loading rules, generating patterns) has overhead. Reusing the instance avoids repeated initialization.

### Batch Processing with Sequences

`normalize_lines()` supports multi-line sequences just like `process()`:

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path

processor = PatterndbYaml(rules_path=Path("rules.yaml"))

# Lines with multi-line sequences (e.g., Q&A format)
lines = [
    "Q: What is the server status?",
    "A: All systems operational",
    "Q: Any errors in the log?",
    "A: No errors found",
]

# Sequences are automatically detected and buffered
normalized = processor.normalize_lines(lines)

# Each sequence (Q + A) is kept together in output
for line in normalized:
    print(line)
```

**Sequence behavior**:

- Leader lines start buffering a sequence
- Follower lines are added to the buffer
- Sequences flush automatically when:
    - A non-follower line is encountered
    - End of input is reached
    - A new sequence leader starts

**State isolation**: Each call to `normalize_lines()` is independent - sequences don't carry over between calls.

### Flushing Sequences

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path

processor = PatterndbYaml(rules_path=Path("rules.yaml"))

with open("input.log") as infile, open("output.log", "w") as outfile:
    processor.process(infile, outfile)

    # Ensure any buffered sequences are written
    processor.flush(outfile)
```

**Note**: `process()` automatically flushes at end of input. Manual flushing only needed for custom streaming scenarios.

### Stream Processing

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import sys

processor = PatterndbYaml(rules_path=Path("rules.yaml"))

# Process stdin to stdout (Unix filter style)
processor.process(sys.stdin, sys.stdout)
```

Usage:
```bash
# In pipeline
tail -f /var/log/app.log | python normalize_stream.py | grep ERROR
```

## Statistics

### get_stats()

Returns processing statistics:

```python
stats = processor.get_stats()

print(f"Lines processed: {stats['lines_processed']}")
print(f"Lines matched: {stats['lines_matched']}")
print(f"Match rate: {stats['match_rate']:.1%}")
```

**Return value**:
```python
{
    'lines_processed': 1000,    # Total lines read
    'lines_matched': 950,       # Lines that matched a pattern
    'match_rate': 95.0          # Percentage (0-100)
}
```

**Interpreting match rate**:
- **100%**: Perfect - all lines matched patterns
- **95-99%**: Good - most lines covered, a few edge cases
- **80-94%**: Fair - some missing patterns
- **< 80%**: Poor - many missing patterns or wrong rules file

**Low match rate indicates**:
- Missing patterns for some log formats
- Log format changed (need new patterns)
- Using wrong rules file for this log


## See Also

- [CLI Reference](cli.md) - Command-line interface
- [Rules Documentation](../features/rules/rules.md) - Pattern syntax and examples
- [Performance Guide](../guides/performance.md) - Optimization strategies
