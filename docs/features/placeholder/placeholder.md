# ⚠️ Template doc: Testing disabled ⚠️

# Annotations

The `--placeholder` flag placeholder.

## What It Does

placeholder

**Key insight**: placeholder.

## Example: placeholder

This example shows placeholder.

???+ note "Input: placeholder"
    ```text hl_lines="1-2"
    --8<-- "features/placeholder/fixtures/input.txt"
    ```

    **First occurrence** (lines 1-2): Line placeholder
    **placeholder** (line 3): placeholder

### With placeholder: placeholder

With `--placeholder`, placeholder.

=== "CLI"

    <!-- verify-file: output-placeholder.txt expected: expected-placeholder.txt -->
    <!-- termynal -->
    ```console
    $ patterndb-yaml input.txt --placeholder \
        > output-placeholder.txt
    ```

=== "Python"

    <!-- verify-file: output-placeholder.txt expected: expected-placeholder.txt -->
    ```python
    from patterndb_yaml import PatterndbYaml

    processor = PatterndbYaml(
        placeholder=True  # (1)!
    )

    with open("input.txt") as f:
        with open("output-placeholder.txt", "w") as out:
            processor.process(f, out)
            processor.flush(out)
    ```

## How It Works

### placeholder


### Available Variables

placeholder

## Common Use Cases

### placeholder

## Combining with Other Features

### placeholder

## Performance Note

placeholder

## Rule of Thumb

**placeholder**

## See Also

- [CLI Reference](../../reference/cli.md) - Complete annotation documentation
- [Common Patterns](../../guides/common-patterns.md) - Annotation examples
