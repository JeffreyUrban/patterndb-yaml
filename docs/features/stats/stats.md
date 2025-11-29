# Statistics Output

After processing, patterndb-yaml automatically displays statistics showing how many lines were processed and matched.

## What It Does

Statistics provide insight into normalization effectiveness:

- **Default**: Table format displayed to stderr after processing
- **JSON format**: Machine-readable output with `--stats-format json`
- **Quiet mode**: Suppress all statistics with `--quiet`
- **Use case**: Verify rules are working, measure match rates, tune patterns

**Key insight**: Statistics help you verify normalization worked and identify lines that didn't match any patterns.

## Example: Understanding Normalization Results

This example shows log normalization with statistics. Statistics reveal how effectively the rules matched the input.

???+ note "Input: Application logs"
    ```text
    --8<-- "features/stats/fixtures/input.txt"
    ```

    Simple application logs with different severity levels (INFO, DEBUG, ERROR, WARN) and some unstructured lines.

???+ note "Rules: Log normalization"
    ```yaml
    --8<-- "features/stats/fixtures/rules.yaml"
    ```

    Rules to normalize log messages by severity level.

### Default: Statistics Table

By default, statistics are displayed to stderr after processing:

=== "CLI"

    <!-- verify-file: stats-table.txt expected: expected-stats-table.txt -->
    <!-- termynal -->
    ```console
    $ patterndb-yaml --rules rules.yaml input.txt \
        > output.txt 2> stats-table.txt
    ```

=== "Python"

    <!-- verify-file: stats-table.txt expected: expected-stats-table.txt -->
    ```python
    from patterndb_yaml import PatterndbYaml
    from pathlib import Path
    import sys
    from io import StringIO

    processor = PatterndbYaml(rules_path=Path("rules.yaml"))

    with open("input.txt") as f:
        with open("output.txt", "w") as out:
            processor.process(f, out)

    # Capture stats output to file
    from patterndb_yaml.cli import print_stats
    from rich.console import Console

    with open("stats-table.txt", "w") as stats_file:
        console = Console(
            file=stats_file,
            force_terminal=False,  # Disable all terminal features
            legacy_windows=False
        )
        # Temporarily replace the module console
        import patterndb_yaml.cli as cli_module
        old_console = cli_module.console
        cli_module.console = console
        try:
            print_stats(processor)
        finally:
            cli_module.console = old_console
    ```

???+ success "Statistics: Table format"
    ```text
    --8<-- "features/stats/fixtures/expected-stats-table.txt"
    ```

**Statistics explained**:

- **Lines Processed**: Total input lines read (10 lines)
- **Lines Matched**: Lines that matched a normalization rule (10 lines)
- **Match Rate**: Percentage of lines matched (100.0%)

**Note**: Statistics are written to stderr, so stdout can be redirected to a file without capturing statistics.

### JSON Format: Machine-Readable

Use `--stats-format json` for programmatic processing:

=== "CLI"

    <!-- verify-file: stats-json.txt expected: expected-stats-json.txt -->
    <!-- termynal -->
    ```console
    $ patterndb-yaml --rules rules.yaml input.txt \
        --stats-format json > output.txt 2> stats-json.txt
    ```

=== "Python"

    <!-- verify-file: stats-json.txt expected: expected-stats-json.txt -->
    ```python
    from patterndb_yaml import PatterndbYaml
    from pathlib import Path
    import json

    processor = PatterndbYaml(rules_path=Path("rules.yaml"))

    with open("input.txt") as f:
        with open("output.txt", "w") as out:
            processor.process(f, out)

    # Get statistics and write to file in JSON format
    stats = processor.get_stats()
    output = {
        "statistics": stats,
        "configuration": {
            "rules_path": str(processor.rules_path),
        },
    }

    with open("stats-json.txt", "w") as f:
        json.dump(output, f, indent=2)
    ```

???+ success "Statistics: JSON format"
    ```json
    --8<-- "features/stats/fixtures/expected-stats-json.txt"
    ```

**JSON structure**:

- **statistics**: Object containing metrics
  - `lines_processed`: Total lines read
  - `lines_matched`: Lines matching patterns
  - `match_rate`: Decimal match rate (1.0 = 100%)
- **configuration**: Echo of settings used
  - `rules_path`: Path to rules file

**Benefits**:

- Parse with `jq`, Python `json` module, or other tools
- Integrate into monitoring systems
- Track normalization metrics over time
- Compare rule configurations programmatically

### Quiet Mode: Suppress Statistics

Use `--quiet` to suppress all statistics output:

=== "CLI"

    <!-- verify-file: output.txt expected: expected-output.txt -->
    <!-- termynal -->
    ```console
    $ patterndb-yaml --rules rules.yaml input.txt --quiet > output.txt
    ```

=== "Python"

    <!-- verify-file: output.txt expected: expected-output.txt -->
    ```python
    from patterndb_yaml import PatterndbYaml
    from pathlib import Path

    processor = PatterndbYaml(rules_path=Path("rules.yaml"))

    with open("input.txt") as f:
        with open("output.txt", "w") as out:
            processor.process(f, out)

    # Get statistics programmatically (even in quiet mode)
    stats = processor.get_stats()  # (1)!
    print(f"Match rate: {stats['match_rate']:.1%}")
    ```

    1. Statistics are always available via `get_stats()`, even when not printed

???+ success "Output: Normalized logs"
    ```text
    --8<-- "features/stats/fixtures/expected-output.txt"
    ```

    **Result**: Only normalized output. No statistics printed to stderr.

## Statistics Fields

### Line Metrics

| Field | Description | Purpose |
|-------|-------------|---------|
| `lines_processed` | Total input lines read | Track processing volume |
| `lines_matched` | Lines matching any rule | Measure normalization coverage |
| `match_rate` | Percentage matched | Assess rule effectiveness |

### Configuration Echo

| Field | Description | Purpose |
|-------|-------------|---------|
| `rules_path` | Path to rules file (JSON only) | Verify correct configuration |

## Common Use Cases

### Tuning Normalization Rules

Compare match rates to identify missing patterns:

```bash
# Test rule changes
patterndb-yaml --rules rules-v1.yaml logs.txt > /dev/null
# Match Rate: 75.3%

patterndb-yaml --rules rules-v2.yaml logs.txt > /dev/null
# Match Rate: 94.7%  ← Better coverage!
```

### Monitoring Production Normalization

Track effectiveness over time using JSON format:

```bash
#!/bin/bash
# Normalize and collect metrics
patterndb-yaml --rules rules.yaml input.log \
  --stats-format json > normalized.log 2> metrics.json

# Extract match rate with jq
match_rate=$(jq -r '.statistics.match_rate' metrics.json)

# Alert if match rate drops
if (( $(echo "$match_rate < 0.9" | bc -l) )); then
  echo "Alert: Match rate dropped to ${match_rate}" \
    | mail -s "Low Match Rate" admin@example.com
fi
```

### Batch Processing with Statistics

Process multiple files and collect statistics:

```bash
for log in logs/*.txt; do
  echo "Processing $log..."
  patterndb-yaml --rules rules.yaml "$log" \
    --stats-format json > "normalized/$(basename "$log")" \
    2> "stats/$(basename "$log" .txt).json"
done

# Aggregate statistics
jq -s 'map(.statistics) | add' stats/*.json
```

## Statistics with Other Features

### With Explain Mode

Combine statistics with explain mode for detailed diagnostics:

```bash
patterndb-yaml --rules rules.yaml input.txt --explain \
  > output.txt 2> explain-and-stats.txt
```

The output will contain both explain messages and final statistics.

### With Progress Indicator

Show progress bar and statistics:

```bash
patterndb-yaml --rules rules.yaml large-file.log --progress \
  > output.log 2> stats.txt
```

Statistics appear after the progress bar completes.

## Performance Note

Statistics collection has minimal overhead:

- Incremental counters (no buffering)
- Match rate calculated only at end
- JSON formatting slightly slower than table (still negligible)

## Rule of Thumb

**Use default table format when:**

- Reviewing normalization results interactively
- Quick verification during rule development
- Human-readable output preferred

**Use JSON format when:**

- Integrating with monitoring systems
- Batch processing multiple files
- Building automation around normalization
- Generating reports programmatically
- Comparing configurations across runs

**Use quiet mode when:**

- Only the normalized output matters
- Piping to another command
- Running in cron jobs where stderr is logged
- Statistics retrieved programmatically via `get_stats()`

## See Also

- [Explain Mode](../explain/explain.md) - Understand why lines matched or didn't match
- [Writing Rules](../rules/rules.md) - How to write normalization patterns
- [CLI Reference](../../reference/cli.md) - Complete command-line options
