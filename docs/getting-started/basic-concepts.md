# Basic Concepts

Understand the core concepts behind `patterndb-yaml`.

## What is Log Normalization?

**Problem**: Different systems log the same events in different formats:

```text
MySQL: 2024-11-15 10:00:01 [MySQL] Query: SELECT * FROM users | Duration: 0.5ms
PostgreSQL: 2024-11-15 10:00:01 [PostgreSQL] duration: 0.5ms  statement: SELECT * FROM users
```

**Solution**: Extract what matters (the operation) and ignore what doesn't (timestamps, format):

```text
[SELECT:users]
```

This is **normalization** - transforming diverse formats into a standard representation.

## How patterndb-yaml Works

### 1. Define Patterns

You write YAML rules that describe how to match and normalize log lines:

```yaml
rules:
  - name: mysql_select
    pattern:
      - field: timestamp
      - text: " [MySQL] Query: SELECT * FROM "
      - field: table
    output: "[SELECT:{table}]"
```

### 2. Match Lines

`patterndb-yaml` reads each line and tries to match it against your patterns:

- **Pattern matches**: Extract fields, output normalized form
- **No pattern matches**: Line passes through unchanged

### 3. Extract Fields

Patterns define which parts to extract:

```yaml
pattern:
  - field: timestamp    # Extract but ignore
  - text: " [MySQL] "   # Must match exactly
  - field: table        # Extract for use in output
```

### 4. Generate Output

The `output` template uses extracted fields:

```yaml
output: "[SELECT:{table}]"
```

`{table}` is replaced with the extracted value.

## Key Components

### Patterns

A pattern is a sequence of components that must match in order:

- **`field`**: Extract a value (variable)
- **`text`**: Match exact text (constant)
- **`serialized`**: Match special characters
- **`alternatives`**: Match any of several options

Example pattern with all components:

```yaml
pattern:
  - field: timestamp
  - text: " ["
  - alternatives:
      - [{ text: "INFO" }]
      - [{ text: "WARN" }]
      - [{ text: "ERROR" }]
  - text: "] "
  - field: message
```

### Fields

Fields extract dynamic data from log lines:

```yaml
- field: timestamp    # Extracts "2024-11-15 10:00:01"
- field: method       # Extracts "GET"
- field: path         # Extracts "/api/users/123"
```

**Field parsers** can extract specific types:

```yaml
- field: count
  parser: NUMBER      # Extracts only digits
```

Without a parser, fields extract until the next pattern component.

### Output Templates

Output templates generate normalized lines using extracted fields:

```yaml
output: "[{method}:{path},status:{status_code}]"
```

- `{field_name}` - Replaced with extracted value
- Everything else is literal text

## Processing Flow

```
Input Line
   ↓
Try Pattern 1 → Match? → Extract Fields → Generate Output
   ↓ No
Try Pattern 2 → Match? → Extract Fields → Generate Output
   ↓ No
Try Pattern 3 → Match? → Extract Fields → Generate Output
   ↓ No
Pass Through Unchanged
```

**First match wins** - once a pattern matches, no other patterns are tried for that line.

## Memory Efficiency

`patterndb-yaml` processes logs **line-by-line** without loading the entire file into memory.

**Memory usage depends only on**:

- Number of rules
- Size of pattern/output definitions
- Multi-line sequence buffer size

This means you can process **gigabyte log files** with **megabytes of memory**.

## Multi-Line Support

Some log entries span multiple lines:

```text
2024-11-15 10:00:01 ERROR: Database connection failed
  at com.example.Database.connect(Database.java:42)
  at com.example.App.start(App.java:15)
```

`patterndb-yaml` can recognize and group these into single normalized outputs. See the [Rules documentation](../features/rules/rules.md#sequences-multi-line-pattern-matching) for details on sequence patterns.

## Statistics

`patterndb-yaml` tracks:

- **Lines processed**: Total lines read
- **Lines matched**: Lines matching a pattern
- **Match rate**: Percentage matched (100% ideal)

Low match rates indicate:
- Missing patterns for some log formats
- Unexpected log format changes
- Need to add more rules

## Next Steps

- **[Quick Start](quick-start.md)** - Try patterndb-yaml with simple examples
- **[Common Patterns](../guides/common-patterns.md)** - Copy-paste ready examples
- **[Use Cases](../use-cases/index.md)** - See real-world applications
- **[Rules Documentation](../features/rules/rules.md)** - Complete pattern syntax
- **[Algorithm Details](../about/algorithm.md)** - Deep dive into how it works
