# patterndb-yaml

**YAML-based pattern matching for log normalization using syslog-ng patterndb**

## Overview

`patterndb-yaml` brings intuitive YAML pattern definitions to [syslog-ng's proven patterndb engine](https://www.syslog-ng.com/technical-documents/doc/syslog-ng-open-source-edition/3.38/administration-guide/56#TOPIC-1829130). Instead of writing complex XML patterns, you define rules in readable YAML and let patterndb-yaml handle the translation to syslog-ng's battle-tested pattern matcher.

This makes it easy to normalize heterogeneous logs - transforming different log formats into standardized output for comparison, analysis, or filtering.

## Features

- **YAML rules** - Readable pattern definitions instead of syslog-ng XML
- **Field extraction** - Pull specific data (table names, IDs, etc.) from matched lines
- **Pattern matching** - Powered by syslog-ng's efficient C implementation
- **Multi-line sequences** - Handle log entries spanning multiple lines
- **Explain mode** - Debug which patterns matched and why
- **CLI and Python API** - Use as a command-line tool or library

## Getting Started

- [Installation](getting-started/installation.md) - Install patterndb-yaml
- [Quick Start](getting-started/quick-start.md) - Normalize your first log file
- [Basic Concepts](getting-started/basic-concepts.md) - Understand patterns and rules
