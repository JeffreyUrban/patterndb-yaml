# Quick Start

Get started with `patterndb-yaml` in 5 minutes.

## Prerequisites

!!! warning "syslog-ng Required"
    `patterndb-yaml` requires syslog-ng to be installed. See the [Installation Guide](installation.md) for detailed setup instructions.

## Installation

**Recommended (automatically installs syslog-ng):**
```bash
brew tap jeffreyurban/patterndb-yaml
brew install patterndb-yaml
```

**Alternative (requires manual syslog-ng installation):**
```bash
# First install syslog-ng (see Installation Guide), then:
pip install patterndb-yaml
```

## Your First Normalization

Let's normalize some web server logs with different formats.

### 1. Create Sample Logs

Create a file `web.log` with mixed log formats:

```bash
cat > web.log << 'EOF'
2024-11-15 10:00:01 [INFO] GET /api/users/123 - 200 OK (5ms)
2024-11-15 10:00:02 POST /api/orders -> Status: 201 Created, Duration: 12ms
2024-11-15 10:00:03 [INFO] GET /api/orders/5001 - 200 OK (3ms)
2024-11-15 10:00:04 PUT /api/orders/5001 -> Status: 200 OK, Duration: 8ms
EOF
```

Two different formats, but the same operations.

### 2. Create Normalization Rules

Create `rules.yaml` to match both formats:

```yaml
rules:
  # Format 1: [INFO] METHOD /path - STATUS (duration)
  - name: format1_request
    pattern:
      - field: timestamp
      - text: " [INFO] "
      - field: method
      - text: " "
      - field: path
      - text: " - "
      - field: status_code
      - text: " "
      - field: status_text
      - text: " ("
      - field: duration
      - text: ")"
    output: "[{method}:{path},status:{status_code}]"

  # Format 2: METHOD /path -> Status: CODE TEXT, Duration: Xms
  - name: format2_request
    pattern:
      - field: timestamp
      - text: " "
      - field: method
      - text: " "
      - field: path
      - text: " -> Status: "
      - field: status_code
      - text: " "
      - field: status_text
      - text: ", Duration: "
      - field: duration
    output: "[{method}:{path},status:{status_code}]"
```

### 3. Run Normalization

```bash
$ patterndb-yaml --rules rules.yaml web.log --quiet
[GET:/api/users/123,status:200]
[POST:/api/orders,status:201]
[GET:/api/orders/5001,status:200]
[PUT:/api/orders/5001,status:200]
```

All logs now use the same format! The normalized output shows:
- HTTP method
- API endpoint path
- Status code

**Dynamic data like timestamps and durations are ignored**, leaving only the behavior.

## See What Matched

Use `--explain` mode to understand which patterns matched:

```bash
$ patterndb-yaml --rules rules.yaml web.log --explain 2>&1 | head -10
EXPLAIN: Line 1: Matched rule 'format1_request'
[GET:/api/users/123,status:200]
EXPLAIN: Line 2: Matched rule 'format2_request'
[POST:/api/orders,status:201]
EXPLAIN: Line 3: Matched rule 'format1_request'
[GET:/api/orders/5001,status:200]
EXPLAIN: Line 4: Matched rule 'format2_request'
[PUT:/api/orders/5001,status:200]
```

Shows which rule matched each line.

## Get Statistics

Run without `--quiet` to see match statistics:

```bash
$ patterndb-yaml --rules rules.yaml web.log
[GET:/api/users/123,status:200]
[POST:/api/orders,status:201]
[GET:/api/orders/5001,status:200]
[PUT:/api/orders/5001,status:200]

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric             ┃ Value ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Lines processed    │     4 │
│ Lines matched      │     4 │
│ Match rate         │  100% │
└────────────────────┴───────┘
```

100% match rate means all lines were normalized.

## Using in Scripts

Redirect output to a file for comparison:

```bash
# Normalize production logs
patterndb-yaml --rules rules.yaml production.log --quiet > prod-normalized.log

# Normalize staging logs
patterndb-yaml --rules rules.yaml staging.log --quiet > staging-normalized.log

# Compare behavior
diff prod-normalized.log staging-normalized.log
```

If environments behave identically, `diff` shows no differences!

## Next Steps

- **[Basic Concepts](basic-concepts.md)** - Understand how patterndb-yaml works
- **[Common Patterns](../guides/common-patterns.md)** - Copy-paste ready examples
- **[Troubleshooting](../guides/troubleshooting.md)** - Solutions to common problems
- **[Use Cases](../use-cases/index.md)** - Real-world examples
- **[CLI Reference](../reference/cli.md)** - Complete command-line options
