# Design Decisions

Why patterndb-yaml works the way it does.

## Core Principles

### 1. YAML Rules, syslog-ng Engine

**Decision**: Users write YAML rules, patterndb-yaml translates to syslog-ng XML.

**Why**:

- YAML is human-readable and easy to edit
- [syslog-ng's patterndb](https://www.syslog-ng.com/technical-documents/doc/syslog-ng-open-source-edition/3.38/administration-guide/56#TOPIC-1829130) is proven robust
- Leverage syslog-ng's efficient radix tree pattern matching
- Best of both worlds: usability + performance

### 2. Streaming Architecture

**Decision**: Process logs line-by-line with constant memory, never loading entire files.

**Why**:

- Supports files of any size
- Works with infinite streams (`tail -f`, network streams)
- Low latency - process lines as they arrive
- Simple implementation

**Trade-offs**: Cannot do multi-pass analysis or look ahead/behind in stream

### 3. Unix Philosophy

**Decision**: Do one thing well - normalize log formats. Compose with existing tools.

**Why**: Excellent tools already exist for log collection (fluentd, logstash), analysis (grep, awk, jq), storage (elasticsearch, loki), visualization (kibana, grafana), and comparison (diff, vimdiff).

patterndb-yaml focuses on **structural normalization** - transforming heterogeneous log formats into a canonical form for comparison.

**Example**:
```bash
# Normalize and compare
diff <(patterndb-yaml --rules rules.yaml --quiet prod.log) \
     <(patterndb-yaml --rules rules.yaml --quiet staging.log)
```

## Feature Decisions

### LRU Caching (65,536 entries)

Caches normalized results for identical lines (O(1) lookups). Effective for logs with repetitive content like health checks or status messages. Bounded cache prevents unbounded memory growth.

## What's Excluded

**No built-in analytics** - Use Unix tools (grep, awk, sort, uniq, wc) for counting, aggregation, and filtering.

**No built-in comparison** - Use standard diff tools (diff, comm, vimdiff) on normalized output.

**No format auto-detection** - Require explicit rules for clarity and reliability. Same format can have different semantics.

**No regex patterns** - Component-based patterns (text, field, alternatives) are more intuitive and support syslog-ng's approach.

**No config files** - Behavior is fully specified in command. Use shell aliases for common patterns.

## CLI Design

**stdout for data, stderr for UI** - Follows Unix filter pattern, enables clean pipeline composition

**Optional progress** - `--progress` flag available, off by default to avoid interfering with pipes

## Error Handling

**Fail fast on configuration errors** - Invalid YAML, missing rules file, or bad pattern syntax causes immediate error

**Graceful degradation on data errors** - Unmatched lines pass through unchanged. Best effort processing for partial results.

## See Also

- **[Algorithm Details](algorithm.md)** - Technical implementation
- **[Performance Guide](../guides/performance.md)** - Optimization strategies
- **[Basic Concepts](../getting-started/basic-concepts.md)** - User-focused overview
