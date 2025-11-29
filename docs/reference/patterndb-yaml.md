# PatterndbYaml API

API reference for the `PatterndbYaml` class - the core log normalization processor.

## Overview

The `PatterndbYaml` class provides the core log normalization functionality. It:

- Loads YAML rule definitions
- Processes input streams line-by-line with constant memory
- Matches patterns and extracts fields
- Applies output templates to normalize logs
- Tracks statistics (lines processed, matched, match rate)
- Supports multi-line sequences (stack traces, etc.)

## Key Features

- **Streaming architecture**: Processes logs line-by-line, handles files of any size
- **Constant memory**: ~20-50 MB regardless of input file size
- **LRU caching**: 65,536 entry cache for repeated lines (significant speedup)
- **Multi-line sequences**: Buffer and group related lines (exceptions, stack traces)
- **Statistics tracking**: Monitor pattern coverage and matching effectiveness
- **Explain mode**: Debug pattern matching with detailed explanations

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

## Advanced Features

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
    with open(log_file) as infile, open(f"{log_file}.normalized", "w") as outfile:
        processor.process(infile, outfile)

    stats = processor.get_stats()
    print(f"{log_file}: {stats['match_rate']:.1%} match rate")
```

**Why reuse**: Processor initialization (loading rules, generating patterns) has overhead. Reusing the instance avoids repeated initialization.

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

## Performance Considerations

### Memory Usage

- **Constant memory**: Memory usage independent of file size
- **Typical usage**: 20-50 MB for most rules files
- **Rule of thumb**: Can process gigabyte files on megabytes of memory

**Memory components**:
```
Base overhead:       ~10-50 MB (Python + syslog-ng)
Rules:              ~1 KB per rule
LRU cache:          ~6.4 MB (65,536 entries)
Sequence buffer:    Variable (typically < 1 MB)
```

### Processing Speed

- **Throughput**: Typically 10k-100k lines/sec (depends on pattern complexity)
- **Cache benefit**: Repeated identical lines processed in O(1) time
- **Optimization**: Put common patterns first in rules file

**Note**: Do not create new `PatterndbYaml` instance per file - reuse the same instance.

```python
# SLOW - creates processor repeatedly
for log_file in files:
    processor = PatterndbYaml(rules_path=Path("rules.yaml"))  # Slow!
    processor.process(...)

# FAST - reuses processor
processor = PatterndbYaml(rules_path=Path("rules.yaml"))  # Once
for log_file in files:
    processor.process(...)  # Reuse
```

### Cache Performance

Monitor cache effectiveness:

```python
processor = PatterndbYaml(rules_path=Path("rules.yaml"))

# After processing...
cache_info = processor.norm_engine.normalize_cached.cache_info()

print(f"Cache hits: {cache_info.hits}")
print(f"Cache misses: {cache_info.misses}")
print(f"Hit rate: {cache_info.hits / (cache_info.hits + cache_info.misses):.1%}")
```

High cache hit rate (> 50%) indicates significant speedup from caching.

## Error Handling

### Initialization Errors

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import sys

try:
    processor = PatterndbYaml(rules_path=Path("rules.yaml"))
except FileNotFoundError as e:
    print(f"Rules file not found: {e}", file=sys.stderr)
    sys.exit(1)
except RuntimeError as e:
    print(f"Failed to initialize: {e}", file=sys.stderr)
    sys.exit(2)
```

**Common errors**:
- `FileNotFoundError`: Rules file doesn't exist
- `RuntimeError`: Invalid YAML syntax or pattern errors

### Processing Errors

```python
try:
    with open("input.log") as infile, open("output.log", "w") as outfile:
        processor.process(infile, outfile)
except IOError as e:
    print(f"I/O error: {e}", file=sys.stderr)
    sys.exit(1)
```

**Graceful degradation**:
- Lines that don't match any pattern → passed through unchanged
- Processing continues despite malformed lines
- Check `match_rate` statistic to detect coverage issues

## Integration Examples

### pytest Integration

```python
import pytest
from patterndb_yaml import PatterndbYaml
from pathlib import Path
from io import StringIO

@pytest.fixture
def processor():
    """Shared processor for tests"""
    return PatterndbYaml(rules_path=Path("test-rules.yaml"))

def test_normalization(processor):
    """Test log normalization"""
    input_data = StringIO("2024-11-15 10:00:01 [INFO] User login\n")
    output_data = StringIO()

    processor.process(input_data, output_data)

    output_data.seek(0)
    result = output_data.read().strip()
    assert result == "[INFO:login]"

def test_match_rate(processor):
    """Test pattern coverage"""
    input_data = StringIO("""
    2024-11-15 10:00:01 [INFO] User login
    2024-11-15 10:00:02 [ERROR] Database error
    """)

    output = StringIO()
    processor.process(input_data, output)

    stats = processor.get_stats()
    assert stats['match_rate'] == 100.0
```

### Flask Integration

```python
from flask import Flask, request, jsonify
from patterndb_yaml import PatterndbYaml
from pathlib import Path
from io import StringIO

app = Flask(__name__)

# Create processor at startup (reuse across requests)
processor = PatterndbYaml(rules_path=Path("api-rules.yaml"))

@app.route('/normalize', methods=['POST'])
def normalize_logs():
    """API endpoint to normalize log data"""
    log_data = request.data.decode('utf-8')

    # Normalize
    input_stream = StringIO(log_data)
    output_stream = StringIO()
    processor.process(input_stream, output_stream)

    # Return result
    output_stream.seek(0)
    normalized = output_stream.read()

    return jsonify({
        'normalized': normalized,
        'stats': processor.get_stats()
    })
```

### Pandas Integration

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
from io import StringIO
import pandas as pd
import re

processor = PatterndbYaml(rules_path=Path("rules.yaml"))

def normalize_to_dataframe(log_file):
    """Normalize log file and convert to DataFrame"""
    with open(log_file) as f:
        output = StringIO()
        processor.process(f, output)
        output.seek(0)

        # Parse normalized output into structured data
        data = []
        for line in output:
            line = line.strip()
            if not line:
                continue

            # Example: [GET:/api/users/123,status:200]
            match = re.match(r'\[(\w+):([^,]+),status:(\d+)\]', line)
            if match:
                method, path, status = match.groups()
                data.append({
                    'method': method,
                    'path': path,
                    'status': int(status)
                })

        return pd.DataFrame(data)

# Create DataFrame
df = normalize_to_dataframe("api.log")

# Analyze with pandas
print(df['method'].value_counts())
print(df['status'].value_counts())
```

## See Also

- [Library Usage Guide](library.md) - Comprehensive library usage examples
- [CLI Reference](cli.md) - Command-line interface
- [Algorithm Details](../about/algorithm.md) - How the algorithm works
- [Performance Guide](../guides/performance.md) - Optimization tips
