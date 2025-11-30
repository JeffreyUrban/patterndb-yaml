# CLI Reference

Complete reference for the `patterndb-yaml` command-line interface.

## Command Syntax

```bash
patterndb-yaml [OPTIONS] [INPUT_FILE]
```

## Basic Usage

```bash
# Normalize a file
patterndb-yaml --rules rules.yaml input.log > output.log

# Read from stdin (in pipelines)
cat input.log | patterndb-yaml --rules rules.yaml > output.log

# Show progress for large files
patterndb-yaml --rules rules.yaml --progress large.log > output.log
```

## Arguments

### `INPUT_FILE` (optional)

**Type**: File path
**Default**: Reads from stdin if not specified

Input file to normalize. If not provided, reads from standard input.

```bash
# From file
patterndb-yaml --rules rules.yaml app.log

# From stdin
cat app.log | patterndb-yaml --rules rules.yaml

# From pipeline
tail -f app.log | patterndb-yaml --rules rules.yaml
```

## Options Reference

### Input Format

#### `--rules, -r` (required)

**Type**: File path
**Required**: Yes

Path to YAML file containing normalization rules.

```bash
patterndb-yaml --rules my-rules.yaml input.log
```

See [Rules documentation](../features/rules/rules.md) for YAML format.

### StdErr Control

These options control what appears on stderr (statistics, progress, explanations).

#### `--quiet, -q`

**Type**: Boolean
**Default**: False

Suppress statistics output to stderr. Only normalized lines go to stdout.

```bash
# With statistics (default)
patterndb-yaml --rules rules.yaml input.log > output.log
# stderr shows: Lines processed: 100, Lines matched: 95, Match rate: 95%

# Without statistics (quiet)
patterndb-yaml --quiet --rules rules.yaml input.log > output.log
# stderr shows: nothing
```

**Use when**: Integrating into scripts where stderr should be clean.

#### `--progress, -p`

**Type**: Boolean
**Default**: False

Show progress indicator for long-running processes. Automatically disabled when output is piped.

```bash
patterndb-yaml --progress --rules rules.yaml large-file.log > output.log
```

Shows:
```
Processing... ⠋ 1,234,567 lines
```

**Use when**: Processing large files where you want visual feedback.

#### `--stats-format`

**Type**: String (table | json)
**Default**: table

Statistics output format.

**table format** (default):
```bash
patterndb-yaml --rules rules.yaml --stats-format table input.log
```

```
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric             ┃ Value ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Lines processed    │   100 │
│ Lines matched      │    95 │
│ Match rate         │   95% │
└────────────────────┴───────┘
```

**json format**:
```bash
patterndb-yaml --rules rules.yaml --stats-format json input.log 2> stats.json
```

```json
{
  "lines_processed": 100,
  "lines_matched": 95,
  "match_rate": 95.0
}
```

**Use when**: Machine-readable format needed for automation.

#### `--explain, -e`

**Type**: Boolean
**Default**: False

Show explanations to stderr for why each line was matched or not matched.

Outputs diagnostic messages showing pattern matching decisions:
- Which rule matched each line
- Why a line didn't match any rules
- Field extraction details

```bash
# See all pattern matching decisions
patterndb-yaml --explain --rules rules.yaml input.log 2> explain.log

# Debug with quiet mode (only explanations, no stats)
patterndb-yaml --explain --quiet --rules rules.yaml input.log

# Validate rules
patterndb-yaml --explain --rules rules.yaml test.log 2>&1 | grep EXPLAIN
```

Example output:
```
EXPLAIN: Line 1: Matched rule 'mysql_select'
EXPLAIN: Line 2: Matched rule 'postgres_select'
EXPLAIN: Line 3: No pattern matched - passed through
```

See [Explain Mode](../features/explain/explain.md) for detailed usage.

### XML Generation

#### `--generate-xml`

**Type**: Boolean
**Default**: False

Generate syslog-ng patterndb XML from rules file and output to stdout. No log processing occurs.

```bash
patterndb-yaml --rules rules.yaml --generate-xml > output.xml
```

This converts your YAML rules into syslog-ng's XML patterndb format for use with syslog-ng. See [Generate XML](../features/generate-xml/generate-xml.md) for details.

**Use when**: Integrating with syslog-ng infrastructure.

### Version Information

#### `--version, -v`

**Type**: Boolean
**Default**: False

Show version and exit.

```bash
patterndb-yaml --version
```

Example output:
```
patterndb-yaml version 0.1.0
```

## Option Combinations

### Commonly Used Together

```bash
# Silent processing (scripts)
patterndb-yaml --quiet --rules rules.yaml input.log > output.log

# Debug mode (understanding what matched)
patterndb-yaml --explain --quiet --rules rules.yaml input.log \
    > output.log 2> explain.log

# Progress with JSON stats (monitoring)
patterndb-yaml --progress --stats-format json --rules rules.yaml \
    input.log > output.log 2> stats.json
```

### Mutually Exclusive Behaviors

- `--generate-xml` outputs XML and skips log processing (other options ignored)
- `--quiet` suppresses statistics but not `--explain` output

## Examples

### Normalize Production Logs

```bash
# Basic normalization
patterndb-yaml --rules prod-rules.yaml /var/log/app.log > normalized.log
```

### Compare Environments

```bash
# Normalize both
patterndb-yaml --rules rules.yaml --quiet prod.log > prod-norm.log
patterndb-yaml --rules rules.yaml --quiet staging.log > staging-norm.log

# Compare
diff prod-norm.log staging-norm.log
```

### Monitor Match Coverage

```bash
# Get JSON statistics
patterndb-yaml --rules rules.yaml --stats-format json app.log 2> stats.json

# Check match rate
jq '.match_rate' stats.json
```

### Debug Pattern Matching

```bash
# See which patterns match
patterndb-yaml --explain --rules rules.yaml test.log 2>&1 | grep "Matched rule"

# Find unmatched lines
patterndb-yaml --explain --rules rules.yaml test.log 2>&1 | \
    grep "No pattern matched"
```

### Stream Processing

```bash
# Real-time log normalization
tail -f /var/log/app.log | patterndb-yaml --rules rules.yaml --quiet
```

## Statistics Output

### Table Format (Default)

```
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric             ┃ Value ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Lines processed    │   500 │
│ Lines matched      │   475 │
│ Match rate         │   95% │
└────────────────────┴───────┘
```

### JSON Format

```json
{
  "lines_processed": 500,
  "lines_matched": 475,
  "match_rate": 95.0
}
```

## Exit Codes

- **0**: Success
- **1**: Error (invalid arguments, file not found, processing error)
- **2**: Invalid rules file (YAML syntax error, invalid pattern)

## See Also

- [Rules Documentation](../features/rules/rules.md) - YAML rule format
- [Library API](library.md) - Using as a Python library
- [Basic Concepts](../getting-started/basic-concepts.md) - Understanding how it works
