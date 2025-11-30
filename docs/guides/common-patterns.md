# Common Patterns

Quick reference for common patterndb-yaml use cases and patterns. Each pattern includes copy-paste ready commands.

## Pattern Reference

| Pattern | Use Case | When to Use |
|---------|----------|-------------|
| **Timestamp Extraction** | Ignore timestamps, keep events | Comparing logs with different timestamps |
| **HTTP Request Normalization** | Standardize API logs | Multiple web servers/formats |
| **Database Query Normalization** | Compare database operations | Migration testing, query analysis |
| **Error Pattern Matching** | Extract error types | Error aggregation, monitoring |
| **Multi-line Stack Traces** | Group exception traces | Error analysis, debugging |

## Timestamp Patterns

### Pattern 1: Ignore ISO Timestamps

**Scenario**: Logs have ISO 8601 timestamps you want to ignore

```yaml
rules:
  - name: iso_timestamp_log
    pattern:
      - field: timestamp  # Extract but don't use
      - text: " "
      - field: level
      - text: " "
      - field: message
    output: "[{level}] {message}"
```

**Input**:
```
2024-11-15T10:00:01.123Z INFO User login successful
2024-11-15T10:00:02.456Z ERROR Database connection failed
```

**Output**:
```
[INFO] User login successful
[ERROR] Database connection failed
```

**When to use**: Comparing behavior across different time periods

### Pattern 2: Multiple Timestamp Formats

**Scenario**: Different systems use different timestamp formats

```yaml
rules:
  - name: iso_format
    pattern:
      - field: timestamp
      - text: " "
      - field: message
    output: "{message}"

  - name: unix_format
    pattern:
      - text: "["
      - field: timestamp
      - text: "] "
      - field: message
    output: "{message}"
```

**When to use**: Aggregating logs from heterogeneous systems

## HTTP Request Patterns

### Pattern 3: Nginx Access Logs

**Scenario**: Normalize nginx access logs

```yaml
rules:
  - name: nginx_access
    pattern:
      - field: ip
      - text: " - - ["
      - field: timestamp
      - text: '] "'
      - field: method
      - text: " "
      - field: path
      - text: " HTTP/"
      - field: version
      - text: '" '
      - field: status
      - text: " "
      - field: bytes
    output: "[{method}:{path},status:{status}]"
```

**Input**:
```
192.168.1.100 - - [15/Nov/2024:10:00:01 +0000]
  "GET /api/users/123 HTTP/1.1" 200 1234
```

**Output**:
```
[GET:/api/users/123,status:200]
```

### Pattern 4: Multiple HTTP Log Formats

**Scenario**: Normalize logs from different web servers

```yaml
rules:
  # Apache Common Log Format
  - name: apache_access
    pattern:
      - field: ip
      - text: " - - ["
      - field: timestamp
      - text: '] "'
      - field: method
      - text: " "
      - field: path
      - text: ' "'
      - field: status
    output: "[{method}:{path},status:{status}]"

  # Application log format
  - name: app_request
    pattern:
      - field: timestamp
      - text: " [REQUEST] "
      - field: method
      - text: " "
      - field: path
      - text: " -> "
      - field: status
    output: "[{method}:{path},status:{status}]"
```

**When to use**: Comparing application behavior across different deployment environments

## Database Query Patterns

### Pattern 5: SQL Query Normalization

**Scenario**: Extract table and operation, ignore query details

```yaml
rules:
  - name: select_query
    pattern:
      - field: timestamp
      - text: " Query: SELECT "
      - field: columns
      - text: " FROM "
      - field: table
      - text: " "
      - field: rest
    output: "[SELECT:{table}]"

  - name: insert_query
    pattern:
      - field: timestamp
      - text: " Query: INSERT INTO "
      - field: table
      - text: " "
      - field: rest
    output: "[INSERT:{table}]"

  - name: update_query
    pattern:
      - field: timestamp
      - text: " Query: UPDATE "
      - field: table
      - text: " "
      - field: rest
    output: "[UPDATE:{table}]"
```

**When to use**: Database migration validation, query pattern analysis

## Error Patterns

### Pattern 6: Extract Error Types

**Scenario**: Categorize errors by type

```yaml
rules:
  - name: connection_error
    pattern:
      - field: timestamp
      - text: " ERROR: Connection "
      - field: details
    output: "[ERROR:CONNECTION]"

  - name: timeout_error
    pattern:
      - field: timestamp
      - text: " ERROR: "
      - field: operation
      - text: " timeout"
    output: "[ERROR:TIMEOUT]"

  - name: auth_error
    pattern:
      - field: timestamp
      - text: " ERROR: Authentication failed"
    output: "[ERROR:AUTH]"
```

**When to use**: Error aggregation, monitoring, alerting

### Pattern 7: Log Level Alternatives

**Scenario**: Match multiple log levels

```yaml
rules:
  - name: log_message
    pattern:
      - field: timestamp
      - text: " ["
      - alternatives:
          - [{ text: "INFO" }]
          - [{ text: "WARN" }]
          - [{ text: "ERROR" }]
          - [{ text: "DEBUG" }]
      - text: "] "
      - field: message
    output: "[{message}]"
```

**When to use**: Ignoring log levels to focus on message content

## Field Extraction Patterns

### Pattern 8: Extract Numeric IDs

**Scenario**: Extract user IDs, order IDs, etc.

```yaml
rules:
  - name: user_action
    pattern:
      - field: timestamp
      - text: " User "
      - field: user_id
        parser: NUMBER  # Only matches digits
      - text: " "
      - field: action
    output: "[USER_ACTION:{action}]"
```

**Input**:
```
2024-11-15 10:00:01 User 12345 logged in
```

**Output**:
```
[USER_ACTION:logged in]
```

**When to use**: Extracting IDs without including them in normalized output

### Pattern 9: Extract Until Delimiter

**Scenario**: Extract variable-length fields

```yaml
rules:
  - name: key_value
    pattern:
      - field: timestamp
      - text: " "
      - field: key
      - text: "="
      - field: value
      - text: " "
      - field: rest
    output: "[{key}={value}]"
```

**When to use**: Parsing key=value log formats

## Pattern Selection Guide

**Choose based on your goal**:

| Goal | Pattern Type | Example |
|------|--------------|---------|
| Compare behavior | Ignore timestamps, IDs | Database migration validation |
| Aggregate errors | Extract error types | Monitoring dashboards |
| Analyze traffic | Extract HTTP methods/paths | API usage analysis |
| Correlate events | Extract correlation IDs | Distributed tracing |

## Real-World Workflow Examples

### Workflow 1: Compare Production vs Staging

```bash
# Normalize both environments
patterndb-yaml --rules app-rules.yaml --quiet prod.log > prod-norm.log
patterndb-yaml --rules app-rules.yaml --quiet staging.log > staging-norm.log

# Find differences
diff prod-norm.log staging-norm.log

# Count event types
sort prod-norm.log | uniq -c | sort -rn > prod-events.txt
sort staging-norm.log | uniq -c | sort -rn > staging-events.txt
```

### Workflow 2: Monitor Match Coverage

```bash
# Process logs and get statistics
patterndb-yaml --rules rules.yaml --stats-format json app.log 2> stats.json

# Check match rate
match_rate=$(jq '.match_rate' stats.json)

# Alert if coverage drops
if (( $(echo "$match_rate < 95" | bc -l) )); then
    echo "WARNING: Match rate dropped to $match_rate%"
    # Send alert
fi
```

### Workflow 3: Aggregate Errors Across Services

```bash
# Normalize all service logs
for service in api web worker; do
    patterndb-yaml --rules error-rules.yaml \
        --quiet "${service}.log" > "${service}-errors.log"
done

# Combine and count errors by type
cat *-errors.log | sort | uniq -c | sort -rn
```

### Workflow 4: Database Query Analysis

```bash
# Extract query patterns
patterndb-yaml --rules db-rules.yaml --quiet queries.log > query-patterns.log

# Find most common operations
grep -o '\[.*:.*\]' query-patterns.log | sort | uniq -c | sort -rn | head -10

# Find slow queries (if duration is preserved)
grep 'duration:' query-patterns.log | sort -t: -k2 -rn | head -10
```

## Tips for Writing Patterns

1. **Start specific, then generalize**: Write patterns for specific log lines first, then make them more general

2. **Test incrementally**: Add one pattern at a time and verify it matches correctly

3. **Use explain mode**: `--explain` shows which patterns match and why

4. **Order matters**: Put most specific patterns first, general patterns last

5. **Group related patterns**: Keep patterns for the same log format together

## See Also

- [Rules Documentation](../features/rules/rules.md) - Complete pattern syntax
- [Use Cases](../use-cases/index.md) - Real-world examples
- [Troubleshooting](./troubleshooting.md) - Solving common issues
- [Performance Guide](./performance.md) - Optimization tips
