# Library Usage

Guide to using patterndb-yaml as a Python library in your applications.

## Installation

```bash
pip install patterndb-yaml
```

## Quick Start

### Basic Usage

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path

# Create processor with rules
processor = PatterndbYaml(rules_path=Path("rules.yaml"))

# Process a file
with open("input.log") as infile, open("output.log", "w") as outfile:
    processor.process(infile, outfile)
```

### Using StringIO for In-Memory Processing

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
from io import StringIO

processor = PatterndbYaml(rules_path=Path("rules.yaml"))

# Process string data
input_data = StringIO("""
2024-11-15 10:00:01 [INFO] GET /api/users/123 - 200 OK (5ms)
2024-11-15 10:00:02 POST /api/orders -> Status: 201 Created, Duration: 12ms
""")

output_data = StringIO()
processor.process(input_data, output_data)

# Get normalized output
output_data.seek(0)
normalized = output_data.read()
print(normalized)
```

## Core API

### PatterndbYaml

The main normalization class. See [PatterndbYaml API](patterndb-yaml.md) for complete reference.

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path

# Initialize with rules file
processor = PatterndbYaml(
    rules_path=Path("rules.yaml"),
    explain=False  # Set True to print explanation messages to stderr
)

# Process logs
processor.process(input_stream, output_stream)

# Get statistics
stats = processor.get_stats()
print(f"Matched {stats['lines_matched']} of {stats['lines_processed']} lines")
```

### Parameters

**`rules_path: Path`** (required)
Path to YAML file containing normalization rules.

**`explain: bool`** (optional, default=False)
If True, print explanation messages to stderr showing which rules matched and why.

### Methods

**`process(input_stream, output_stream, progress_callback=None)`**

Process input stream and write normalized output.

**Arguments**:
- `input_stream`: Text or binary input stream (file, StringIO, etc.)
- `output_stream`: Text or binary output stream
- `progress_callback`: Optional function `(current: int, total: int) -> None` for progress updates

**`get_stats() -> dict`**

Get processing statistics.

**Returns**: Dictionary with:
```python
{
    'lines_processed': 100,    # Total lines read
    'lines_matched': 95,       # Lines that matched a pattern
    'match_rate': 95.0         # Percentage (0-100)
}
```

## Complete Library Workflow

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
from io import StringIO

# Initialize
processor = PatterndbYaml(
    rules_path=Path("migration-rules.yaml"),
    explain=True  # Debug mode
)

# Process log file
with open("mysql.log") as input_file:
    output = StringIO()
    processor.process(input_file, output)

    # Get normalized lines
    output.seek(0)
    normalized_lines = [line.strip() for line in output if line.strip()]

# Check statistics
stats = processor.get_stats()
print(f"Processed {stats['lines_processed']} lines")
print(f"Matched {stats['lines_matched']} lines ({stats['match_rate']:.1f}%)")

# Use normalized data
for line in normalized_lines:
    # Process normalized log entries
    if line.startswith("[SELECT:"):
        print(f"Found SELECT: {line}")
```

## Advanced Features

### Comparing Multiple Log Files

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
from io import StringIO

processor = PatterndbYaml(rules_path=Path("rules.yaml"))

def normalize_file(filename):
    """Normalize a log file and return lines as set"""
    with open(filename) as f:
        output = StringIO()
        processor.process(f, output)
        output.seek(0)
        return set(line.strip() for line in output if line.strip())

# Normalize both files
prod_lines = normalize_file("production.log")
staging_lines = normalize_file("staging.log")

# Find differences
only_in_prod = prod_lines - staging_lines
only_in_staging = staging_lines - prod_lines

if only_in_prod or only_in_staging:
    print("Behavioral differences detected!")
    if only_in_prod:
        print("\nOnly in production:")
        for line in sorted(only_in_prod):
            print(f"  {line}")
    if only_in_staging:
        print("\nOnly in staging:")
        for line in sorted(only_in_staging):
            print(f"  {line}")
else:
    print("✓ Environments behave identically")
```

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
with open("large-file.log") as infile, open("output.log", "w") as outfile:
    processor.process(infile, outfile, progress_callback=progress_callback)

print("\nDone!")
```

## Integration Examples

### Flask Application

```python
from flask import Flask, request, jsonify
from patterndb_yaml import PatterndbYaml
from pathlib import Path
from io import StringIO

app = Flask(__name__)
processor = PatterndbYaml(rules_path=Path("api-rules.yaml"))

@app.route('/normalize', methods=['POST'])
def normalize_logs():
    """API endpoint to normalize log data"""
    log_data = request.data.decode('utf-8')

    # Normalize
    input_stream = StringIO(log_data)
    output_stream = StringIO()
    processor.process(input_stream, output_stream)

    # Return normalized data
    output_stream.seek(0)
    normalized = output_stream.read()

    return jsonify({
        'normalized': normalized,
        'stats': processor.get_stats()
    })
```

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

def test_api_normalization(processor):
    """Test API log normalization"""
    input_data = StringIO("2024-11-15 10:00:01 [INFO] GET /api/users/123 - 200 OK (5ms)\n")
    output_data = StringIO()

    processor.process(input_data, output_data)

    output_data.seek(0)
    result = output_data.read().strip()

    assert result == "[GET:/api/users/123,status:200]"

def test_match_rate(processor):
    """Test that all expected patterns match"""
    test_logs = StringIO("""
    2024-11-15 10:00:01 [INFO] GET /api/users/123 - 200 OK (5ms)
    2024-11-15 10:00:02 POST /api/orders -> Status: 201 Created, Duration: 12ms
    """)

    output = StringIO()
    processor.process(test_logs, output)

    stats = processor.get_stats()
    assert stats['match_rate'] == 100.0, "All test logs should match patterns"
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
    """Normalize log file and convert to pandas DataFrame"""
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

# Create DataFrame from normalized logs
df = normalize_to_dataframe("api.log")

# Analyze with pandas
print("Requests by method:")
print(df['method'].value_counts())

print("\nRequests by status code:")
print(df['status'].value_counts())

print("\nMost accessed paths:")
print(df['path'].value_counts().head(10))
```

## Error Handling

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path
import sys

try:
    processor = PatterndbYaml(rules_path=Path("rules.yaml"))
except FileNotFoundError:
    print("Rules file not found", file=sys.stderr)
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"Invalid YAML in rules file: {e}", file=sys.stderr)
    sys.exit(2)

try:
    with open("input.log") as infile, open("output.log", "w") as outfile:
        processor.process(infile, outfile)
except FileNotFoundError:
    print("Input file not found", file=sys.stderr)
    sys.exit(1)
except IOError as e:
    print(f"I/O error: {e}", file=sys.stderr)
    sys.exit(1)
```

## Performance Tips

1. **Reuse processor instances**: Create once, use many times
   ```python
   # Good: Create once
   processor = PatterndbYaml(rules_path=Path("rules.yaml"))
   for log_file in log_files:
       with open(log_file) as f:
           processor.process(f, output)

   # Bad: Create repeatedly
   for log_file in log_files:
       processor = PatterndbYaml(rules_path=Path("rules.yaml"))  # Slow!
       with open(log_file) as f:
           processor.process(f, output)
   ```

2. **Stream large files**: Don't read entire file into memory
   ```python
   # Good: Stream processing
   with open("large.log") as infile:
       processor.process(infile, outfile)

   # Bad: Load into memory
   data = open("large.log").read()  # Memory intensive!
   processor.process(StringIO(data), outfile)
   ```

3. **Use binary mode for large files**: Slightly faster for large files
   ```python
   with open("large.log", "rb") as infile, open("output.log", "wb") as outfile:
       processor.process(infile, outfile)
   ```

## See Also

- [PatterndbYaml API](patterndb-yaml.md) - Complete API reference
- [CLI Reference](cli.md) - Command-line usage
- [Rules Documentation](../features/rules/rules.md) - YAML rule format
- [Use Cases](../use-cases/index.md) - Real-world examples
