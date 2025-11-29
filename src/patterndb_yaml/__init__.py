"""
patterndb-yaml: Transform and normalize log data using pattern-based rules.

A Python library and CLI tool for log normalization using YAML-based pattern
definitions. Leverages syslog-ng's pattern matching engine for high-performance
log parsing and transformation.

Key features:
- Define patterns and transformations in simple YAML format
- Automatic syslog-ng pattern database (XML) generation
- Field extraction and value transformations
- Support for sequence detection and stateful processing
- Rich CLI with progress tracking and statistics
"""

from .patterndb_yaml import PatterndbYaml

# Version is managed by hatch-vcs and set during build
try:
    from ._version import __version__
except ImportError:
    # Fallback for development installs without build
    __version__ = "0.0.0.dev0+unknown"

__all__ = ["PatterndbYaml", "__version__"]
