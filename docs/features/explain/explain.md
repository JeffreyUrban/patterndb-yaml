# Explain Mode

The `--explain` flag outputs explanations to stderr showing why placeholder.
This helps you understand the placeholder decisions being made in real-time.

## What It Does

Explain mode adds diagnostic messages to stderr:

- **Normal mode**: Deduplication happens silently
- **With explain**: Messages show why placeholder
- **Use case**: Debugging placeholder, understanding placeholder, troubleshooting unexpected behavior

**Key insight**: Explanations go to stderr, so stdout remains clean for placeholder.

## Example: placeholder

placeholder

### Without Explain: placeholder

Without `--explain`, placeholder happens without feedback.

=== "CLI"

    <!-- verify-file: output.txt expected: expected-output.txt -->
    <!-- termynal -->
    ```console
    $ patterndb-yaml input.txt --placeholder > output.txt
    ```

=== "Python"

    <!-- verify-file: output.txt expected: expected-output.txt -->
    ```python
    from patterndb_yaml import PatterndbYaml

    processor = PatterndbYaml(
        placeholder=False  # (1)!
    )

    with open("input.txt") as f:
        with open("output.txt", "w") as out:
            processor.process(f, out)
            processor.flush(out)
    ```

    1. Default: no explanations

???+ success "Output: placeholder"
    ```text
    --8<-- "features/explain/fixtures/expected-output.txt"
    ```

    **Result**: placeholder.

### With Explain: Documented Decisions

With `--explain`, stderr shows why placeholder.

=== "CLI"

    <!-- verify-file: output.txt expected: expected-output.txt -->
    <!-- termynal -->
    ```console
    $ patterndb-yaml input.txt --placeholder \
        > output.txt 2> explain.txt
    ```

=== "Python"

    <!-- verify-file: output.txt expected: expected-output.txt -->
    ```python
    from patterndb_yaml import PatterndbYaml
    import sys

    processor = PatterndbYaml(
        placeholder=False,
        explain=True  # (1)!
    )

    with open("input.txt") as f:
        with open("output.txt", "w") as out:
            processor.process(f, out)
            processor.flush(out)
    ```

    1. Enable explain mode

???+ warning "Stdout: Deduplicated output"
    ```text
    --8<-- "features/explain/fixtures/expected-output.txt"
    ```

???+ info "Stderr: Explanation messages"
    ```text
    --8<-- "features/explain/fixtures/expected-explain.txt"
    ```

    **Result**: Stdout has placeholder, stderr shows placeholder.

## How It Works

### Explanation Format

Explain messages provide actionable information:

**placeholder**:

## Common Use Cases

### Debugging Why placeholder

### Validating placeholder

### Understanding placeholder

### Troubleshooting Unexpected Behavior

## Combining with Other Features

### With Progress

```bash
# Real-time explanations with progress indicator
patterndb-yaml large.log --explain --progress 2>&1 | tee diagnostics.txt
```

## Filtering Explain Output

### Extract Specific Information

```bash
# Only show placeholder
patterndb-yaml log.txt --explain 2>&1 | grep "placeholder"
```

### Separate Stdout and Stderr

```bash
# placeholder to file, explanations to terminal
patterndb-yaml log.txt --explain > clean.log

# Both to separate files
patterndb-yaml log.txt --explain > clean.log 2> explain.log

# Merge for analysis
patterndb-yaml log.txt --explain 2>&1 | grep "Line 42"
```

## Performance Note

Explain mode has minimal overhead:
- Simple conditional check before printing
- Messages only written when explain is enabled
- No impact on placeholder performance
- Stderr output is buffered (efficient)

## Rule of Thumb

**Use explain mode when you need to understand** the placeholder.

- **Initial setup**: Validate placeholder are working correctly
- **Debugging**: Understand why placeholder
- **Pattern development**: Test and refine placeholder
- **Troubleshooting**: Diagnose unexpected behavior
- **Learning**: Understand how the algorithm works on your data

**Don't use in production** unless actively debugging—the extra output
can clutter logs.

## See Also

- [CLI Reference](../../reference/cli.md) - Complete explain documentation
- [Troubleshooting](../../guides/troubleshooting.md) - Common issues and solutions
