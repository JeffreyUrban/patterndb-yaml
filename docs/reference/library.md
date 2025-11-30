# Library Usage

Using patterndb-yaml as a Python library.

## Installation

```bash
pip install patterndb-yaml
```

## Quick Start

```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path

# Create processor
processor = PatterndbYaml(rules_path=Path("rules.yaml"))

# Process logs
with open("input.log") as infile, open("output.log", "w") as outfile:
    processor.process(infile, outfile)

# Get statistics
stats = processor.get_stats()
print(f"Match rate: {stats['match_rate']:.1%}")
```

## See Also

- [PatterndbYaml API](patterndb-yaml.md) - Complete API reference
- [CLI Reference](cli.md) - Command-line interface
- [Rules Documentation](../features/rules/rules.md) - Pattern syntax
