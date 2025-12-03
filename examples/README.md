# Examples

This directory contains example rules files for patterndb-yaml.

## Files

### `rules.yaml`

Simple starter rules for basic log normalization. Demonstrates:

- Basic pattern matching
- Field extraction
- Output templates

Good for:
- Getting started
- Testing examples from documentation
- Learning pattern syntax

Example usage:
```python
from pathlib import Path
from patterndb_yaml import PatterndbYaml

processor = PatterndbYaml(rules_path=Path("examples/rules.yaml"))
lines = ["ERROR: Connection failed", "INFO: Retrying"]
normalized = processor.normalize_lines(lines)
```

### `normalization_rules.yaml`

Advanced rules used by the patterndb-yaml project itself. Demonstrates:

- Complex pattern alternatives
- Multi-line sequences
- Character sets
- Serialized Unicode characters
- Named options

Good for:
- Learning advanced patterns
- Real-world usage examples
- Understanding project internals

## See Also

- [Rules Documentation](../docs/features/rules/rules.md) - Complete pattern syntax reference
- [Quick Start](../docs/getting-started/quick-start.md) - Getting started guide
