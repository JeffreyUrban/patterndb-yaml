# Generate syslog-ng XML

The `--generate-xml` flag converts YAML normalization rules into syslog-ng's native XML pattern database format.

## What It Does

Generate XML enables interoperability with syslog-ng:

- **Export to syslog-ng**: Convert YAML rules to XML pattern database format
- **Migration path**: Move existing syslog-ng XML patterns to YAML
- **Validation**: Verify YAML rules generate valid syslog-ng patterns
- **Use case**: Deploy normalization rules to syslog-ng infrastructure

**Key insight**: Write rules once in YAML, use them in both patterndb-yaml and syslog-ng.

## Example: Exporting Rules to syslog-ng Format

This example shows converting SSH authentication rules from YAML to syslog-ng XML.

???+ note "Input: YAML rules"
    ```yaml
    --8<-- "features/generate-xml/fixtures/rules.yaml"
    ```

    Simple SSH authentication rules matching successful and failed logins.

### Generating XML

Use `--generate-xml` to convert YAML rules to syslog-ng XML format:

=== "CLI"

    <!-- verify-file: output.xml expected: expected-output.xml -->
    <!-- termynal -->
    ```console
    $ patterndb-yaml --rules rules.yaml --generate-xml > output.xml
    ```

=== "Python"

    <!-- verify-file: output.xml expected: expected-output.xml -->
    ```python
    from patterndb_yaml.pattern_generator import generate_from_yaml
    from pathlib import Path
    import yaml

    # Load YAML rules
    with open("rules.yaml") as f:
        rules_data = yaml.safe_load(f)

    # Generate XML
    xml_content = generate_from_yaml(rules_data)

    # Write to file
    with open("output.xml", "w") as f:
        f.write(xml_content)
    ```

???+ success "Output: syslog-ng XML pattern database"
    ```xml
    --8<-- "features/generate-xml/fixtures/expected-output.xml"
    ```

**XML structure**:

- `<patterndb>`: Root element with version metadata
- `<ruleset>`: Container for related rules
- `<rule>`: Individual pattern matching rule
  - `<patterns>`: syslog-ng pattern syntax (ESTRING, etc.)
  - `<values>`: Output MESSAGE value
- Field extraction uses syslog-ng parser syntax (`@ESTRING:field:delimiter@`)

## XML Generation Details

### Pattern Conversion

YAML patterns are converted to syslog-ng parser syntax:

| YAML Pattern | syslog-ng XML |
|-------------|---------------|
| `text: "literal"` | `literal` (plain text) |
| `field: name` with following text | `@ESTRING:name:delimiter@` |
| `field: name` at end of line | `@ESTRING:name:$@` (until end) |
| `parser: NUMBER` | `@NUMBER@` parser |

### Field Delimiter Inference

The YAML-to-XML converter automatically infers field delimiters:

```yaml
# YAML
pattern:
  - text: "User "
  - field: username
  - text: " logged in"

# Generated XML
^User @ESTRING:username: logged in@
#       ^field starts    ^delimiter inferred from next element
```

### Output Format

The generated `MESSAGE` value combines the rule name and extracted fields:

```yaml
# YAML
output: "[ssh-login:user={user}]"

# Generated XML (syslog-ng format)
[ssh_login_success]|user=$user|
```

## Common Use Cases

### Deploying to syslog-ng

Generate XML and deploy to syslog-ng pattern database:

```bash
# Generate XML from YAML rules
patterndb-yaml --rules normalization.yaml --generate-xml > patterns.xml

# Deploy to syslog-ng
sudo cp patterns.xml /var/lib/syslog-ng/patterndb/custom.pdb

# Test pattern database
pdbtool match -p /var/lib/syslog-ng/patterndb/custom.pdb \
  -M "Accepted publickey for admin from 192.168.1.100"

# Reload syslog-ng
sudo systemctl reload syslog-ng
```

### Validating YAML Rules

Verify YAML rules generate valid syslog-ng patterns:

```bash
# Generate XML
patterndb-yaml --rules rules.yaml --generate-xml > patterns.xml

# Validate with syslog-ng's pdbtool
pdbtool test /var/lib/syslog-ng/patterndb/patterns.xml

# Check for errors
echo $?  # 0 = valid, non-zero = errors
```

### Converting Existing XML to YAML

While patterndb-yaml doesn't provide XML→YAML conversion, you can:

1. **Manually convert** patterns to YAML format
2. **Generate XML** from YAML to verify equivalence
3. **Compare** with original using diff tools

```bash
# Generate XML from your YAML conversion
patterndb-yaml --rules converted.yaml --generate-xml > new.xml

# Compare with original
diff -u original.xml new.xml
```

### CI/CD Integration

Automate XML generation in build pipelines:

```yaml
# .github/workflows/build.yml
- name: Generate syslog-ng patterns
  run: |
    patterndb-yaml --rules normalization.yaml --generate-xml \
      > dist/patterns.xml

- name: Validate patterns
  run: |
    pdbtool test dist/patterns.xml

- name: Upload artifact
  uses: actions/upload-artifact@v3
  with:
    name: syslog-ng-patterns
    path: dist/patterns.xml
```

## Limitations

### Pattern Syntax Differences

Some YAML features may not translate perfectly to syslog-ng XML:

- **Transformations**: YAML field transformations (like `strip_ansi`) are not supported in syslog-ng patterns
- **Sequences**: Multi-line sequences are a patterndb-yaml feature, not available in syslog-ng
- **Alternatives**: YAML alternatives generate separate XML rules

### Output Format

The generated XML uses a specific MESSAGE format optimized for diff comparison:

```
[rule_name]|field1=$field1|field2=$field2|
```

This format differs from the YAML `output` field but preserves all extracted fields.

## Performance Note

XML generation is fast:

- Runs at YAML parse speed (no input processing)
- Suitable for build-time generation
- No runtime overhead (generate once, deploy)

## Rule of Thumb

**Use --generate-xml when:**

- Deploying rules to syslog-ng infrastructure
- Validating YAML rules with syslog-ng tools
- Migrating from YAML to syslog-ng XML
- Integrating with existing syslog-ng deployments

**Don't use --generate-xml when:**

- Processing logs with patterndb-yaml (use normal mode)
- YAML transformations or sequences are required (not supported in XML)
- Output format must match YAML `output` field exactly

## See Also

- [Writing Rules](../rules/rules.md) - Writing normalization rules in YAML
- [syslog-ng Pattern Database](https://www.syslog-ng.com/technical-documents/doc/syslog-ng-open-source-edition/3.38/administration-guide/11#TOPIC-1829071) - Official syslog-ng pattern database documentation
- [Quick Start](../../getting-started/quick-start.md) - Basic usage with YAML rules
