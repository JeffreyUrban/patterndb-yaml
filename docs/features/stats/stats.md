# Statistics Output

After processing, patterndb-yaml automatically displays statistics showing placeholder.

## What It Does

Statistics provide insight into placeholder:

- **Default**: Table format displayed after processing
- **JSON format**: Machine-readable with `--stats-format json`
- **Quiet mode**: Suppress with `--quiet`
- **Use case**: Understand placeholder effectiveness, tune parameters

**Key insight**: Statistics help you verify placeholder worked and measure
placeholder.

## Example: Understanding placeholder Results

This example shows placeholder. Statistics reveal placeholder.

### Default: Statistics Table

By default, statistics are displayed to stderr after processing:

<!-- verify-file: stats-table.txt expected: expected-stats-table.txt -->
```console
$ patterndb-yaml input.txt --placeholder > output.txt 2> stats-table.txt
```

Statistics are written to stderr (`stats-table.txt`):

**Note**: Statistics are written to stderr, so stdout can be redirected
without capturing statistics.

**Statistics explained**:

- **placeholder**: placeholder

### JSON Format: Machine-Readable

Use `--stats-format json` for programmatic processing:

<!-- verify-file: stats-json.txt expected: expected-stats-json.txt -->
```console
$ patterndb-yaml input.txt --placeholder --stats-format json \
    > output.txt 2> stats-json.txt
```

Statistics in JSON format (`stats-json.txt`):

```json
{
  "statistics": {
    "placeholder": placeholder
  }
}
```

**Benefits**:
- Parse with `jq`, Python, or other tools
- Integrate into monitoring systems
- Track placeholder metrics over time
- Compare configurations programmatically

### Quiet Mode: Suppress Statistics

Use `--quiet` to suppress all statistics and progress output:

=== "CLI"

    <!-- verify-file: output.txt expected: expected-placeholder.txt -->
    <!-- termynal -->
    ```console
    $ patterndb-yaml input.txt --placeholder --quiet > output.txt
    ```

=== "Python"

    <!-- verify-file: output.txt expected: expected-placeholder.txt -->
    ```python
    from patterndb_yaml import PatterndbYaml

    processor = PatterndbYaml(placeholder=True)

    with open("input.txt") as f:
        with open("output.txt", "w") as out:
            processor.process(f, out)
            processor.flush(out)

    # Get statistics programmatically
    stats = processor.get_stats()  # (1)!
    print(f"placeholder: {stats['placeholder']}")
    ```

    1. Access statistics from patterndb-yaml object

???+ success "Output: placeholder"
    ```text
    --8<-- "features/stats/fixtures/expected-placeholder.txt"
    ```

    **Result**: placeholder. No statistics printed to stderr.

## Statistics Fields

### placeholder

### Configuration Echo

| Field  | Description | Purpose |
|--------|-------------|---------|
| `placeholder` | placeholder        | placeholder    |

## Common Use Cases

### placeholder

## Statistics with Other Features

### With placeholder

## Performance Note

Statistics collection has minimal overhead:
- placeholder
- JSON formatting slightly slower than table (still negligible)

## Rule of Thumb

**Use statistics to:**
- Verify placeholder is working
- Measure placeholder
- Tune placeholder
- Monitor placeholder effectiveness over time

**Use JSON format when:**
- Integrating with monitoring systems
- Batch processing
- Building automation around placeholder
- Generating reports programmatically

**Use quiet mode when:**
- You only need the placeholder output
- Piping to another command
- Running in cron jobs where stderr is logged
- Performance testing (avoid terminal I/O)

## See Also

- [CLI Reference](../../reference/cli.md) - Complete statistics documentation
- [Guides: Performance](../../guides/performance.md) - Optimization tips
