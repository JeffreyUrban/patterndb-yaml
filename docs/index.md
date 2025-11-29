# patterndb-yaml

**Normalize heterogeneous logs using YAML-defined patterns**

## Overview

`patterndb-yaml` is a command-line tool and Python library for normalizing log files using pattern matching rules. It helps you compare logs from different systems, filter noise, and detect behavioral differences by transforming diverse log formats into standardized output.

## What Problem Does It Solve?

When comparing logs from different systems or versions, you face challenges:

- **Different formats**: MySQL logs look different from PostgreSQL logs
- **Dynamic data**: Timestamps, IDs, and durations change on every run
- **Noise**: Irrelevant details obscure what you're trying to compare

`patterndb-yaml` solves this by:

1. **Matching** log lines against YAML-defined patterns
2. **Extracting** relevant fields (table names, operations, etc.)
3. **Normalizing** output to a standard format

**Result**: You can compare what the systems **do**, not how they **log**.

## Features

- **YAML-based rules**: Define patterns in readable YAML, not complex regex
- **Field extraction**: Pull out specific data from matched lines
- **Multi-line support**: Handle log entries spanning multiple lines
- **Explain mode**: See which patterns matched and why
- **Statistics**: Track match rates and coverage
- **Library and CLI**: Use as a command-line tool or Python library

## Quick Example

Given these different log formats:

```text
2024-11-15 10:00:01 [MySQL] Query: SELECT * FROM users | Duration: 0.5ms
2024-11-15 10:00:01 [PostgreSQL] duration: 0.5ms  statement: SELECT * FROM users
```

Define a pattern that matches both:

```yaml
rules:
  - name: mysql_select
    pattern:
      - field: timestamp
      - text: " [MySQL] Query: SELECT "
      - field: columns
      - text: " FROM "
      - field: table
    output: "[SELECT:{table}]"

  - name: postgres_select
    pattern:
      - field: timestamp
      - text: " [PostgreSQL] duration: "
      - field: duration
      - text: "  statement: SELECT "
      - field: columns
      - text: " FROM "
      - field: table
    output: "[SELECT:{table}]"
```

Both logs normalize to:

```text
[SELECT:users]
```

Now you can compare behavior across databases!

## Getting Started

- [Installation](getting-started/installation.md) - Install patterndb-yaml
- [Quick Start](getting-started/quick-start.md) - Get started in 5 minutes
- [Basic Concepts](getting-started/basic-concepts.md) - Understand how patterndb-yaml works

## Use Cases

See how `patterndb-yaml` solves real problems:

- **[Testing](use-cases/index.md#testing)** - Verify behavior, detect regressions, ensure quality
- **[DevOps](use-cases/index.md#devops)** - Build reliability, deployment validation
- **[Operations](use-cases/index.md#operations)** - Monitor, troubleshoot, validate deployments
- **[Security](use-cases/index.md#security)** - Aggregate logs, detect attacks, compliance
- **[Data](use-cases/index.md#data)** - Migrations, transformations, data quality

## Documentation Sections

### Guides

Practical guides for common scenarios:

- [Common Patterns](guides/common-patterns.md) - Copy-paste ready examples
- [Troubleshooting](guides/troubleshooting.md) - Solutions to common problems
- [Performance](guides/performance.md) - Optimization tips

### Reference

Complete technical documentation:

- [CLI Reference](reference/cli.md) - Command-line options
- [Python API](reference/library.md) - Using as a library
- [PatterndbYaml Class](reference/patterndb-yaml.md) - Core API reference

### Features

Deep dives into specific features:

- [Rules](features/rules/rules.md) - Pattern matching and normalization
- [Statistics](features/stats/stats.md) - Match coverage and metrics
- [Explain Mode](features/explain/explain.md) - Debug pattern matching

### About

Design and development:

- [How It Works](about/algorithm.md) - Algorithm details
- [Design Decisions](about/design-decisions.md) - Why patterndb-yaml works this way
- [Contributing](about/contributing.md) - Help improve patterndb-yaml
