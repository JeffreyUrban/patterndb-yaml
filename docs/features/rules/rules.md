# Rules

YAML-based normalization rules provide an intuitive way to define pattern matching and transformation logic. Rules leverage syslog-ng's high-performance patterndb engine while offering a more organized and readable format than XML, plus multi-line sequence capabilities.

## What It Does

Rules enable pattern-based log normalization with a user-friendly interface:

- **Intuitive YAML syntax**: Define patterns in readable, structured format
- **High-performance matching**: Powered by syslog-ng's proven patterndb engine
- **Field extraction**: Capture variable data from log lines
- **Output formatting**: Transform matched lines to consistent format
- **Multi-line sequences**: Group related lines together (unique to patterndb-yaml)
- **Use case**: Normalize heterogeneous logs for analysis, diff comparison, or monitoring

**Key insight**: Write rules once in YAML, get syslog-ng's performance plus enhanced capabilities.

## Pattern Matching Engine

Under the hood, patterndb-yaml uses [syslog-ng's patterndb](https://www.syslog-ng.com/technical-documents/doc/syslog-ng-open-source-edition/3.38/administration-guide/11) as its matching engine. When you provide YAML rules, patterndb-yaml:

1. Converts your YAML to syslog-ng's XML pattern database format
2. Loads the patterns into syslog-ng's high-performance matching engine
3. Applies patterns to normalize your logs

Benefits:

- **High-performance matching**: Leverages syslog-ng's optimized engine
- **Proven reliability**: Pattern matching used in production worldwide
- **Enhanced capabilities**: Multi-line sequences and simplified YAML syntax

## Writing Normalization Rules

### Basic Rule Structure

A normalization rule has three required components:

1. **`name`**: Unique identifier for the rule
2. **`pattern`**: Match criteria (text literals and field captures)
3. **`output`**: Normalized output format template

```yaml
rules:
  - name: rule_identifier        # 1. Unique rule name
    pattern:                      # 2. Match criteria
      - text: "fixed string"      #   Literal text to match
      - field: variable_data      #   Variable data to capture
    output: "[tag:{field}]"       # 3. Normalized output format
```

### Example: Simple Text Matching

Match log lines by fixed text patterns:

???+ note "Input: Application logs with severity levels"
    ```text
    --8<-- "features/rules/fixtures/simple-input.txt"
    ```

    Log lines with different severity levels in square brackets.

???+ note "Rules: Match severity levels"
    ```yaml
    --8<-- "features/rules/fixtures/simple-rules.yaml"
    ```

    Four rules matching INFO, ERROR, WARN, and DEBUG severity levels.

=== "CLI"

    <!-- verify-file: output.txt expected: simple-output.txt -->
    <!-- termynal -->
    ```console
    $ patterndb-yaml --rules simple-rules.yaml simple-input.txt \
        --quiet > output.txt
    ```

=== "Python"

    <!-- verify-file: output.txt expected: simple-output.txt -->
    ```python
    from patterndb_yaml import PatterndbYaml
    from pathlib import Path

    processor = PatterndbYaml(rules_path=Path("simple-rules.yaml"))

    with open("simple-input.txt") as f:
        with open("output.txt", "w") as out:
            processor.process(f, out)
    ```

???+ success "Output: Normalized severity levels"
    ```text
    --8<-- "features/rules/fixtures/simple-output.txt"
    ```

    Each log line is normalized to a consistent format with severity tag.

**How it works**:

1. Each rule's `pattern` is tested against the input line
2. When a pattern matches, the rule's `output` format is used
3. The `{message}` placeholder is replaced with the captured field value

### Example: Field Extraction

Extract multiple fields from structured log lines:

???+ note "Input: Login events"
    ```text
    --8<-- "features/rules/fixtures/advanced-input.txt"
    ```

    User login events with usernames and IP addresses.

???+ note "Rules: Extract username and IP"
    ```yaml
    --8<-- "features/rules/fixtures/advanced-rules.yaml"
    ```

    Rules that extract `username` and `ip_address` fields from login events.

=== "CLI"

    <!-- verify-file: output.txt expected: advanced-output.txt -->
    <!-- termynal -->
    ```console
    $ patterndb-yaml --rules advanced-rules.yaml advanced-input.txt \
        --quiet > output.txt
    ```

=== "Python"

    <!-- verify-file: output.txt expected: advanced-output.txt -->
    ```python
    from patterndb_yaml import PatterndbYaml
    from pathlib import Path

    processor = PatterndbYaml(rules_path=Path("advanced-rules.yaml"))

    with open("advanced-input.txt") as f:
        with open("output.txt", "w") as out:
            processor.process(f, out)
    ```

???+ success "Output: Normalized with extracted fields"
    ```text
    --8<-- "features/rules/fixtures/advanced-output.txt"
    ```

    Username and IP address extracted and formatted consistently.

**How field extraction works**:

1. Pattern components are matched in order
2. `text` components match literal strings
3. `field` components capture variable data between text delimiters
4. Captured fields are available in the `output` format string

## Pattern Components

### Text Matching

Match literal text exactly:

```yaml
pattern:
  - text: "User "
  - text: "logged in"
```

**Characteristics**:

- Case-sensitive matching
- ANSI escape codes are automatically stripped before matching
- Whitespace matters (must match exactly)

### Field Extraction

Capture variable data:

```yaml
pattern:
  - field: username      # Captures until next delimiter
  - text: " from "       # Delimiter
  - field: ip_address    # Captures until end of line
```

**Field behavior**:

- Fields capture text between delimiters
- Last field in pattern captures until end of line
- Field names must be valid YAML identifiers

### Numbered Fields

Extract numeric values:

```yaml
pattern:
  - text: "Port "
  - field: port_number
    parser: NUMBER       # Only matches digits
```

**Number parser**:

- Matches one or more digits (`0-9`)
- Useful for ports, IDs, counts, etc.
- Fails to match if non-digit characters are encountered

## Output Formatting

The `output` field defines the normalized format:

```yaml
output: "[event-type:field1={field1},field2={field2}]"
```

**Placeholders**:

- `{fieldname}`: Replaced with extracted field value
- Literal text: Appears as-is in output
- Format is completely customizable

**Common patterns**:
```yaml
# Tagged format
output: "[tag:data={data}]"

# Key-value format
output: "event=login user={user} ip={ip}"

# JSON-like format
output: '{"event":"login","user":"{user}"}'

# Simplified format
output: "{user}@{host}"
```

## Rule Matching Behavior

### Match Order

Rules are tested in the order they appear in the YAML file:

```yaml
rules:
  - name: specific_rule      # Tested first
    pattern:
      - text: "WARN: deprecated"
    output: "[deprecated-warning]"

  - name: general_rule       # Tested second
    pattern:
      - text: "WARN: "
    output: "[warning]"
```

**Best practice**: Put more specific rules before general rules.

### Unmatched Lines

Lines that don't match any rule are passed through unchanged:

```text
# Input
Matched log line
Random unstructured text
Another matched line

# Output (with one rule matching "Matched")
[matched]
Random unstructured text      ← Passed through
[matched]
```

### Match Statistics

Use statistics to see match effectiveness:

```
Normalization Statistics
┌─────────────────┬────────┐
│ Lines Processed │  1,000 │
│ Lines Matched   │    847 │
│ Match Rate      │  84.7% │
└─────────────────┴────────┘
```

Low match rates suggest missing rules for common patterns.

## Advanced Features

### Alternatives

Match any of several options:

```yaml
pattern:
  - text: "Status: "
  - alternatives:
      - - text: "OK"
      - - text: "SUCCESS"
      - - text: "PASSED"
  - field: details
```

Matches "Status: OK", "Status: SUCCESS", or "Status: PASSED".

### Transformations

Transform field values before output:

```yaml
rules:
  - name: clean_ansi
    pattern:
      - text: "Output: "
      - field: message
    output: "[clean:{message}]"
    transformations:
      message: strip_ansi    # Remove ANSI escape codes
```

**Available transformations**:

- `strip_ansi`: Remove ANSI color/formatting codes

### Sequences: Multi-Line Pattern Matching

Sequences allow you to group related lines together for atomic processing. This is particularly useful for multi-line log entries like dialogs, stack traces, or multi-part messages.

A sequence consists of:

- **Leader pattern**: The first line that starts the sequence
- **Follower patterns**: Subsequent lines that belong to the sequence
- **Buffering behavior**: All sequence lines are buffered and output together

#### Example: Dialog Question-Answer Pairs

This example demonstrates how follower patterns can match lines based on their
position relative to a leader line. Notice that both answer lines (following
questions) and non-answer lines start with `- `, but only the answers are
matched because they follow a question leader.

???+ note "Input: Interactive dialog logs"
    ```text
    --8<-- "features/rules/fixtures/sequence-input.txt"
    ```

    Lines 2, 4-5, 7, and 11 start with `- ` and follow `[Q]` questions.
    Line 9 also starts with `- ` but does NOT follow a question.

???+ note "Rules: Match question-answer sequences"
    ```yaml
    --8<-- "features/rules/fixtures/sequence-rules.yaml"
    ```

    The follower pattern matches lines starting with `- `, but only when they
    follow a `[Q]` leader line. This positional matching is key: the same
    pattern (`- ...`) is treated differently based on context.

=== "CLI"

    ```bash
    patterndb-yaml --rules sequence-rules.yaml sequence-input.txt \
        --quiet > output.txt
    ```

=== "Python"

    <!-- verify-file: output.txt expected: sequence-output.txt -->
    ```python
    from patterndb_yaml import PatterndbYaml
    from pathlib import Path

    processor = PatterndbYaml(rules_path=Path("sequence-rules.yaml"))

    with open("sequence-input.txt") as f:
        with open("output.txt", "w") as out:
            processor.process(f, out)
    ```

???+ success "Expected Output: Grouped sequences (specification)"
    ```text
    --8<-- "features/rules/fixtures/sequence-output.txt"
    ```

    **Expected behavior**: Questions normalized, follower answers normalized
    and buffered with each question group.

    **Note**: Full sequence normalization (normalizing follower patterns) is
    specified but not yet fully implemented. Currently followers are buffered
    but passed through unchanged.

**How sequences work**:

1. **Leader line** matches and starts buffering
2. **Follower lines** are buffered (added to the sequence)
3. **Non-follower line** ends the sequence
4. **All buffered lines** are output together atomically

This ensures related lines stay together even during streaming processing.

**When to use sequences**:

- Multi-line error messages or stack traces
- Question-answer pairs or dialogs
- Header-detail log entries
- Any related group of lines that should be processed atomically

## Common Patterns

### HTTP Logs

```yaml
rules:
  - name: http_request
    pattern:
      - field: method
      - text: " "
      - field: path
      - text: " HTTP/"
      - field: version
    output: "[http:{method},{path}]"
```

### Timestamps

```yaml
rules:
  - name: iso_timestamp_log
    pattern:
      - field: timestamp      # ISO 8601 timestamp
      - text: " "
      - field: message
    output: "[log:{message}]"  # Discard timestamp
```

### Key-Value Pairs

```yaml
rules:
  - name: kv_pair
    pattern:
      - field: key
      - text: "="
      - field: value
    output: "{key}={value}"   # Preserve format
```

### Error Messages

```yaml
rules:
  - name: exception
    pattern:
      - field: exception_type
      - text: ": "
      - field: error_message
    output: "[error:type={exception_type},msg={error_message}]"
```

## Rule Development Tips

### Start Simple

Begin with basic patterns and iterate:

1. **Identify common log formats** in your input
2. **Write simple rules** matching key patterns
3. **Test with real data** and check match rates
4. **Refine patterns** based on unmatched lines

### Use Explain Mode

Debug pattern matching with `--explain`:

```
EXPLAIN: [Line 42] Matched rule 'http_request'
EXPLAIN: [Line 42] Extracted fields: method='GET', path='/api/users'
EXPLAIN: [Line 42] Output: [http:GET,/api/users]
```

### Validate Output

Check that output format is consistent:

```bash
# All output should start with same tag format
patterndb-yaml --rules rules.yaml logs.txt | grep -v '^\['
# Should return no lines (all lines start with [tag])
```

## Performance Considerations

Rules are processed efficiently using syslog-ng's optimized engine:

- **Cached normalization**: Identical lines normalized once
- **Sequential matching**: First matching rule wins (no backtracking)
- **ANSI stripping**: Pre-compiled regex, minimal overhead
- **Mature engine**: Built on syslog-ng's established codebase

**Best practice**: Order rules from most specific to most general for optimal performance.

## Rule of Thumb

**Write rules that are:**

- **Specific enough** to match intended patterns accurately
- **General enough** to handle slight variations
- **Ordered** from specific to general
- **Tested** with real log data to verify match rates

**Avoid:**

- Overly broad patterns that match unintended lines
- Duplicate rules with overlapping patterns
- Complex patterns when simple ones suffice

## See Also

- [Explain Mode](../explain/explain.md) - Debug pattern matching
- [Statistics](../stats/stats.md) - Measure normalization effectiveness
- [Generate XML](../generate-xml/generate-xml.md) - Export rules to syslog-ng format
- [Quick Start](../../getting-started/quick-start.md) - Quick introduction to rules
- [syslog-ng Pattern Database Documentation](https://www.syslog-ng.com/technical-documents/doc/syslog-ng-open-source-edition/3.38/administration-guide/11) - Underlying pattern matching engine
