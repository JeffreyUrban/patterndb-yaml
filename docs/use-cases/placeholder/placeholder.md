# ⚠️ Template doc: Testing disabled ⚠️

# placeholder

placeholder.

## Input Data

???+ note "app.log"
    --8<-- "use-cases/placeholder/fixtures/app.log"
    ```

    placeholder.

## Output Data

???+ success "output.log"
    --8<-- "use-cases/placeholder/fixtures/expected-output.log"
    ```

    **Result**: placeholder

## Solution

=== "CLI"

    <!-- verify-file: output.log expected: expected-output.log -->
    <!-- termynal -->
    ```console
    $ patterndb-yaml app.log \
        --placeholder \
        --quiet > output.log
    ```

    **Options:**

      show_source: false
      show_root_heading: true
      heading_level: 3

=== "Python"

    <!-- verify-file: output.log expected: expected-output.log -->
    ```python
    from patterndb_yaml import PatterndbYaml

    processor = PatterndbYaml(
        placeholder=True,  # (1)!
    )

    with open("app.log") as f:
        with open("output.log", "w") as out:
            processor.process(f, out)
            processor.flush(out)
    ```

    1. placeholder

## How It Works

placeholder

## Benefits

**placeholder**: placeholder

## Real-World Usage

```bash
placeholder
```

## See Also
