# Explain Mode

The `--explain` flag outputs diagnostic messages to stderr showing how lines are being processed.
This helps you understand the normalization decisions being made in real-time.

## What It Does

Explain mode adds diagnostic messages to stderr:

- **Normal mode**: Normalization happens silently
- **With explain**: Messages show pattern matching, field extraction, transformations, and sequence processing
- **Use case**: Debugging patterns, understanding transformations, troubleshooting unexpected output

**Key insight**: Explanations go to stderr, so stdout remains clean for piping normalized output.

## Example: Understanding Pattern Matching

### Without Explain: Silent Processing

Without `--explain`, normalization happens without feedback.

=== "CLI"

    <!-- verify-file: output.txt expected: expected-output.txt -->
    <!-- termynal -->
    ```console
    $ patterndb-yaml --rules rules.yaml input.txt \
        > output.txt
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
    ```

You see the normalized output but don't know what happened internally.

### With Explain: Documented Decisions

With `--explain`, stderr shows why each line was processed the way it was:

=== "CLI"

    <!-- verify-file: explain.txt expected: expected-explain.txt -->
    <!-- termynal -->
    ```console
    $ patterndb-yaml --rules rules.yaml input.txt --explain \
        > output.txt 2> explain.txt
    ```

    Explanation output (`explain.txt`):
    ```text
    --8<-- "features/explain/fixtures/expected-explain.txt"
    ```

=== "Python"

    <!-- verify-file: explain.txt expected: expected-explain.txt -->
    ```python
    from patterndb_yaml import PatterndbYaml
    from pathlib import Path

    processor = PatterndbYaml(
        rules_path=Path("rules.yaml"),
        explain=True  # Explanations go to stderr
    )

    with open("input.txt") as f:
        with open("output.txt", "w") as out:
            processor.process(f, out)
    ```

## Explanation Message Types

### 1. Pattern Matching

Shows whether a line matched a normalization rule:

```
EXPLAIN: [Line 42] Matched rule 'dialog_question'
EXPLAIN: [Line 43] No pattern matched (passed through unchanged)
```

**Why useful**: Quickly see if your patterns are working.

### 2. Field Extraction

Shows extracted field values from matched patterns:

```
EXPLAIN: [Line 42] Extracted fields: content='What is your name?', number='1'
```

**Why useful**: Debug field patterns and delimiters.

### 3. Field Transformations

Shows transformations applied to field values:

```bash
patterndb-yaml --rules rules.yaml input.txt --explain 2> explain.txt
cat explain.txt
```

Example output:
```
EXPLAIN: [Line 42] Applied transform 'strip_ansi' to field
  'content': '\x1b[1mBold\x1b[0m' → 'Bold'
EXPLAIN: [Line 42] Applied transform 'normalize_spinner' to
  field 'prompt': '✻' → '*'
```

**Why useful**: See exactly how values are being modified.

### 4. Sequence Processing

Shows multi-line sequence buffering:

```
EXPLAIN: [Line 10] Started buffering sequence 'dialog_question'
  (leader line)
EXPLAIN: [Line 11] Added follower to sequence 'dialog_question'
  (buffer: 2 lines)
EXPLAIN: [Line 12] Added follower to sequence 'dialog_question'
  (buffer: 3 lines)
EXPLAIN: [Line 13] Line is not a follower - ending sequence
  'dialog_question'
EXPLAIN: [Line 13] Flushed sequence 'dialog_question'
  (3 lines buffered)
```

**Why useful**: Multi-line sequences are complex; see when buffering
starts/ends.

### 5. Output Formatting

Shows the final normalized output:

```
EXPLAIN: [Line 42] Output: [dialog-question:What is your name?]
```

### 6. Error Cases

Shows configuration or processing errors:

```
EXPLAIN: [Line 42] Rule 'unknown_rule' not found in
  configuration (returned encoded message)
EXPLAIN: [Line 43] Template error - missing field 'nonexistent'
  (returned encoded message)
```

**Why useful**: Helps debug configuration issues.

## Message Format

All explain messages follow a consistent format:

```
EXPLAIN: [Line N] <message>
```

- **Prefix**: `EXPLAIN:` for easy grep filtering
- **Line number**: `[Line N]` correlates with input line
- **Message**: Human-readable description of the operation

## Common Use Cases

### Debugging Pattern Rules

See if your patterns are matching:

```bash
patterndb-yaml --rules rules.yaml input.txt --explain 2>&1 \
  | grep "Matched rule"
```

### Validating Field Extraction

Check that fields are extracted correctly:

```bash
patterndb-yaml --rules rules.yaml input.txt --explain 2>&1 \
  | grep "Extracted fields"
```

### Understanding Transformations

See how transformations modify values:

```bash
patterndb-yaml --rules rules.yaml input.txt --explain 2>&1 \
  | grep "Applied transform"
```

### Debugging Sequences

Track multi-line sequence processing:

```bash
patterndb-yaml --rules rules.yaml input.txt --explain 2>&1 | grep "sequence"
```

## Combining with Other Features

### With Progress

```bash
# Real-time explanations with progress indicator
patterndb-yaml --rules rules.yaml large.log --explain --progress
```

### Separate Output Streams

```bash
# Normalized output to file, explanations to terminal
patterndb-yaml --rules rules.yaml log.txt --explain \
  > normalized.log

# Both to separate files
patterndb-yaml --rules rules.yaml log.txt --explain \
  > normalized.log 2> explain.log

# Combined for line-by-line analysis
patterndb-yaml --rules rules.yaml log.txt --explain 2>&1 \
  | less
```

### Filter Specific Lines

```bash
# Show only processing for line 42
patterndb-yaml --rules rules.yaml log.txt --explain 2>&1 \
  | grep "Line 42"

# Show only lines that didn't match
patterndb-yaml --rules rules.yaml log.txt --explain 2>&1 \
  | grep "No pattern matched"
```

## Python API

Enable explain mode programmatically:

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path

# Enable explain mode
processor = PatterndbYaml(
    rules_path=Path("rules.yaml"),
    explain=True  # Explanations go to stderr
)

with open("input.txt") as f:
    with open("output.txt", "w") as out:
        processor.process(f, out)
```

Explanations are written to `sys.stderr` automatically.

## Performance Note

Explain mode has minimal overhead:

- Simple conditional check before printing
- Messages only written when explain is enabled
- No impact on normalization performance
- Stderr output is buffered (efficient)

## Rule of Thumb

**Use explain mode when you need to understand** the normalization process:

- **Initial setup**: Validate patterns are working correctly
- **Debugging**: Understand why a line didn't match or was transformed incorrectly
- **Pattern development**: Test and refine normalization rules
- **Troubleshooting**: Diagnose unexpected output
- **Learning**: Understand how the normalization algorithm works on your data

**Don't use in production** unless actively debugging—the extra output
can clutter logs and reduce readability.

## See Also

- [Pattern Rules](../../getting-started/basic-concepts.md#pattern-rules) - How to write normalization patterns
- [Field Transformations](../../getting-started/basic-concepts.md#transformations) - Available transformation functions
- [Troubleshooting](../../guides/troubleshooting.md) - Common issues and solutions
