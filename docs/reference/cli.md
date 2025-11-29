# CLI Reference

Complete reference for the `patterndb-yaml` command-line interface.

## Command Syntax

```bash
patterndb-yaml [OPTIONS] [INPUT_FILE]
```

## Basic Usage

```bash
# placeholder
patterndb-yaml placeholder
```

## Options Reference

### Core Options

#### `--placeholder, -b`
**Type**: placeholder
**Default**: placeholder

placeholder.

```bash
patterndb-yaml --placeholder
```

### Display Options

#### `--quiet, -q`
**Type**: Boolean
**Default**: False

Suppress statistics output to stderr.

```bash
patterndb-yaml --quiet input.log
```

#### `--progress, -p`
**Type**: Boolean
**Default**: False

Show progress indicator (auto-disabled for pipes).

```bash
patterndb-yaml --progress large-file.log
```

#### `--stats-format`
**Type**: String (table | json)
**Default**: table

Statistics output format: 'table' (Rich table) or 'json' (machine-readable).

```bash
patterndb-yaml --stats-format json input.log
```

#### `--explain`
**Type**: Boolean
**Default**: False

Show explanations to stderr for why placeholder.

Outputs diagnostic messages showing placeholder decisions:
- When placeholder
- Which placeholder

```bash
# See all placeholder decisions
patterndb-yaml --explain input.log 2> explain.log

# Debug with quiet mode (only explanations, no stats)
patterndb-yaml --explain --quiet input.log

# Validate placeholder
patterndb-yaml --explain --placeholder input.log 2>&1 | grep EXPLAIN
```

Example output:
```
EXPLAIN: placeholder
```

See [Explain Mode](../features/explain/explain.md) for detailed usage.

### Version Information

#### `--version`
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

### Mutually Exclusive Options

- `--placeholder` and `--placeholder`: Use one or the other
- `--placeholder` requires `--placeholder`

## Examples

### placeholder

```bash
# placeholder
patterndb-yaml placeholder.log > output.log
```

## Statistics Output

### Table Format (Default)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Metric                   ┃  Value ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ placeholder                     │   placeholder │
└──────────────────────────┴────────┘
```

### JSON Format

```json
{
  "statistics": {
    "placeholder": placeholder
  }
}
```

## Exit Codes

- **0**: Success
- **1**: Error (invalid arguments, file not found, processing error)

## See Also

- [PatterndbYaml API](patterndb-yaml.md) - Core placeholder class
- [Basic Concepts](../getting-started/basic-concepts.md) - Understanding how patterndb-yaml works
