# Design Decisions

Why patterndb-yaml works the way it does.

## Core Principles

### 1. Streaming First

**Decision**: Process logs line-by-line with constant memory, never loading entire files.

**Why**:
- Real-world logs can be gigabytes or terabytes
- Need to work with infinite streams (`tail -f`, network streams)
- Memory-constrained environments (containers, edge devices)
- Simplicity - easier to understand and debug

**Impact**:
- ✅ Handles files of any size with constant memory (~20-50 MB)
- ✅ Works with infinite streams and real-time processing
- ✅ Low latency - process lines as they arrive
- ⚠️ Cannot do multi-pass analysis or global optimizations
- ⚠️ Cannot look ahead or behind in the stream

**Alternative considered**: Load entire file, build index, enable multi-pass processing.
- **Rejected**: Memory usage would scale with file size, incompatible with streaming.

### 2. Unix Philosophy

**Decision**: Do one thing well - normalize log formats. Delegate everything else.

**Why**: There are already excellent tools for:
- Log collection: `fluentd`, `logstash`, `filebeat`
- Log analysis: `grep`, `awk`, `sed`, `jq`
- Log storage: `elasticsearch`, `splunk`, `loki`
- Log visualization: `kibana`, `grafana`
- Diff and comparison: `diff`, `comm`, `vimdiff`

patterndb-yaml focuses on what they don't do: **structural normalization** - transforming heterogeneous log formats into a canonical form for comparison.

**Impact**:
- ✅ Simple, focused tool that composes with others
- ✅ Composes well with existing Unix tools
- ✅ Easier to understand and maintain
- ✅ Follows "filter" pattern (stdin → stdout, stderr for diagnostics)
- ❌ Won't add features better served by other tools (analytics, storage, visualization)

**Example composition**:
```bash
# Normalize logs from multiple sources, compare, find differences
patterndb-yaml --rules rules.yaml prod.log > prod-norm.log
patterndb-yaml --rules rules.yaml staging.log > staging-norm.log
diff prod-norm.log staging-norm.log
```

### 3. Pattern Priority Over Performance

**Decision**: Sequential pattern matching (first-match-wins) instead of compiled automaton.

**Why**:
- Predictable behavior - pattern order is explicit and controllable
- Simple mental model - users understand "first match wins"
- Easy debugging - trace which pattern matched and why
- Dynamic updates - change rules without recompiling
- Fast enough - 10k-100k lines/sec sufficient for most use cases

**Impact**:
- ✅ Clear, understandable matching behavior
- ✅ Explicit control over pattern priority
- ✅ Easy to debug with `--explain` mode
- ⚠️ O(rules) matching time instead of theoretical O(1)

**Alternative considered**: Compile all patterns into single finite automaton.
- **Rejected**: Complex implementation, hard to debug, loses pattern priority control.

### 4. YAML for Humans, XML for Machines

**Decision**: Users write YAML rules, internally generate syslog-ng XML.

**Why**:
- YAML is human-readable and easy to edit
- syslog-ng XML format is proven and battle-tested
- Leverage syslog-ng's optimized C pattern matcher
- Best of both worlds: usability + performance

**Impact**:
- ✅ User-friendly rule authoring (YAML)
- ✅ Fast pattern matching (syslog-ng C implementation)
- ✅ Version control friendly (text-based YAML)
- ⚠️ Dependency on syslog-ng pattern database format
- ⚠️ Translation layer adds startup overhead

## Feature Decisions

### ✅ Included: LRU Caching

**Feature**: Cache normalized results for recently-seen lines (65,536 entry LRU cache).

**Why**:
- Real-world logs often have repetitive content (health checks, periodic status)
- Identical lines don't need re-processing
- Bounded cache size prevents unbounded memory growth
- 65,536 entries = 6.4 MB max, large enough for most patterns

**Alternatives considered**:
- No caching: Simpler, but slower for repetitive logs
- Unbounded cache: Fast, but memory grows without bound
- Smaller cache (1k-10k entries): Lower memory, but lower hit rate

**Decision**: 65,536 entry LRU cache balances memory and hit rate effectively.

**Impact**:
- ✅ Significant speedup for logs with repetitive patterns (30-70% hit rate)
- ✅ O(1) lookup for cached lines
- ✅ Bounded memory (6.4 MB max)
- ⚠️ No benefit for logs with all unique lines

### ✅ Included: Multi-Line Sequences

**Feature**: Buffer and group multi-line log entries (e.g., stack traces).

**Why**:
- Real-world logs have multi-line entries (exceptions, stack traces, multi-line messages)
- Atomicity - related lines should be output together
- Normalization applies to entire sequence, not individual lines

**How it works**:
```yaml
rules:
  - name: exception
    pattern: [...]
    output: "[EXCEPTION:{message}]"
    sequence:
      followers:
        - pattern: [...]
          output: "  {trace_line}"
```

**Decision**: Explicit sequence configuration in rules file.

**Impact**:
- ✅ Handles stack traces, multi-line errors correctly
- ✅ Preserves atomicity of related lines
- ✅ User controls what constitutes a sequence
- ⚠️ Sequences buffered in memory until complete

### ✅ Included: Statistics Output

**Feature**: Report lines processed, matched, and match rate on stderr.

**Why**:
- Users need to know if patterns are working (high match rate = good coverage)
- Low match rate indicates missing patterns
- Helps validate rules files
- Separate from data (stdout) following Unix principles

**Formats**:
```bash
# Table format (default, human-readable)
patterndb-yaml --rules rules.yaml app.log
# → stderr shows formatted table

# JSON format (machine-readable)
patterndb-yaml --rules rules.yaml --stats-format json app.log 2> stats.json
```

**Decision**: Always output statistics unless `--quiet` specified.

**Impact**:
- ✅ Users get feedback on pattern coverage
- ✅ Easy to validate rules files
- ✅ Machine-readable JSON option
- ⚠️ Stderr output may clutter logs (use `--quiet` to suppress)

### ✅ Included: Explain Mode

**Feature**: Show detailed explanations of pattern matching decisions (`--explain`).

**Why**:
- Debugging - understand why patterns match or don't match
- Rule development - test patterns before deployment
- Troubleshooting - diagnose low match rates

**Output**:
```
EXPLAIN: [Line 1] Matched rule 'nginx_access'
EXPLAIN: [Line 2] No pattern matched - passed through
EXPLAIN: [Line 3] Matched rule 'app_error'
```

**Decision**: Optional flag, disabled by default (verbose output).

**Impact**:
- ✅ Invaluable for debugging pattern issues
- ✅ Helps users understand matching behavior
- ⚠️ Verbose output not suitable for production
- ⚠️ Performance overhead from logging

### ❌ Excluded: In-Tool Analytics

**Feature**: Built-in log analysis (counting, aggregation, filtering).

**Why excluded**:
- Unix tools already do this better (`grep`, `awk`, `uniq`, `sort`, `wc`)
- Adding analytics would bloat the tool
- Violates Unix philosophy (do one thing well)

**Alternative**:
```bash
# Count normalized events
patterndb-yaml --rules rules.yaml --quiet app.log | sort | uniq -c | sort -rn

# Filter for errors only
patterndb-yaml --rules rules.yaml --quiet app.log | grep '\[ERROR\]'

# Count by event type
patterndb-yaml --rules rules.yaml --quiet app.log | cut -d: -f1 | sort | uniq -c
```

**Decision**: Focus on normalization, delegate analysis to existing tools.

### ❌ Excluded: Built-In Comparison

**Feature**: Built-in diff/comparison of normalized logs.

**Why excluded**:
- `diff`, `comm`, `vimdiff` already exist and work well
- Users have preferred diff tools
- Adds complexity without clear benefit

**Alternative**:
```bash
# Use standard Unix diff
diff <(patterndb-yaml --rules rules.yaml --quiet prod.log) \
     <(patterndb-yaml --rules rules.yaml --quiet staging.log)
```

**Decision**: Output normalized logs, let users choose comparison tool.

### ❌ Excluded: Format Auto-Detection

**Feature**: Automatically detect log format without rules file.

**Why excluded**:
- Ambiguous - same format can have different semantics
- Unreliable - may mis-classify logs
- Normalization requires semantic understanding, not just syntax
- Users know their log formats better than heuristics

**Alternative**:
```yaml
# Explicit rules are clear and reliable
rules:
  - name: app_format_v1
    pattern: [...]
    output: "[...]"
```

**Decision**: Require explicit rules file - clarity over convenience.

### ❌ Excluded: Regex-Based Patterns

**Feature**: Use regex patterns instead of component-based patterns.

**Why excluded**:
- Component-based patterns are more structured and maintainable
- Regex hard to read and debug (write-only code)
- Component approach enables field extraction with clear semantics
- syslog-ng pattern database uses components, not regex

**Example comparison**:
```yaml
# Regex approach (harder to maintain)
pattern: "^(\S+) \[(\w+)\] (.+)$"

# Component approach (clear structure)
pattern:
  - field: timestamp
  - text: " ["
  - field: level
  - text: "] "
  - field: message
```

**Decision**: Component-based patterns for clarity and maintainability.

## Memory Management

### Constant Memory Streaming

**Decision**: Never load more than one line into memory at a time (except sequences).

**Why**:
- Handles any file size
- Works with infinite streams
- Predictable memory usage

**Implementation**:
```python
def process(stream, output):
    for line in stream:  # One line at a time
        normalized = normalize(line)
        output.write(normalized + "\n")
```

**Memory breakdown**:
```
Base overhead:     ~10-50 MB (Python + syslog-ng)
Rules:            ~1 KB × num_rules
LRU cache:        ~100 bytes × 65,536 = 6.4 MB max
Sequence buffer:  Variable (typically < 1 MB)
Total:            ~20-60 MB typical
```

**Impact**:
- ✅ Predictable memory usage
- ✅ Scales to any file size
- ⚠️ Sequence buffering can grow with sequence length

### LRU Cache Size: 65,536 Entries

**Decision**: Fixed cache size of 65,536 entries (2^16).

**Why**:
- Power of 2 for efficient hash table implementation
- ~6.4 MB memory (100 bytes per entry)
- Large enough to capture most repetitive patterns
- Small enough to stay in CPU cache for fast lookups

**Alternatives considered**:
- 4,096 entries: Lower memory (400 KB), but lower hit rate
- 1,048,576 entries: Higher hit rate, but 100 MB memory
- Unbounded: Best hit rate, but memory grows without bound

**Decision**: 65,536 balances memory and effectiveness.

### Temporary File Management

**Decision**: Auto-generate and auto-cleanup temporary XML files.

**Why**:
- syslog-ng requires XML file (not in-memory)
- Users shouldn't manage temporary files manually
- Clean up even on crashes (`atexit` handler)

**Implementation**:
```python
xml_tempfile = tempfile.NamedTemporaryFile(
    mode="w",
    suffix=".xml",
    prefix="patterndb_",
    delete=False
)
atexit.register(cleanup_tempfile)
```

**Impact**:
- ✅ No manual cleanup required
- ✅ Cleaned up on normal exit and crashes
- ⚠️ Temporary files in system temp directory

## CLI Design

### Why Flags Over Positional Args?

**Decision**: All options are flags (`--rules`, `--quiet`), not positional.

**Why**:
- Self-documenting - clear what each parameter does
- Optional parameters easy to add later
- Better shell completion support
- Follows modern CLI conventions (typer, click)

**Example**:
```bash
# Clear what each option does
patterndb-yaml --rules rules.yaml --quiet input.log

# vs positional (unclear)
patterndb-yaml rules.yaml input.log quiet  # What does each arg mean?
```

### Why Stderr for UI, Stdout for Data?

**Decision**: Data to stdout, all UI/diagnostics to stderr.

**Why**:
- Follows Unix filter pattern
- Enables composition in pipelines
- Users can redirect data and logs independently

**Example**:
```bash
# Redirect data and stats separately
patterndb-yaml --rules rules.yaml app.log > normalized.log 2> stats.txt

# Use in pipeline (stats don't pollute pipeline)
cat app.log | patterndb-yaml --rules rules.yaml --quiet | grep ERROR
```

### Why No Config Files?

**Decision**: No `.patterndb-yamlrc` or config files.

**Why**:
- Tool typically used in one-off commands and pipelines
- Shell aliases work fine for common patterns:
  ```bash
  alias norm='patterndb-yaml --rules my-rules.yaml --quiet'
  ```
- Avoids "spooky action at a distance" (hidden config affecting behavior)
- Simplifies mental model - behavior fully specified in command

**Impact**:
- ✅ Explicit, predictable behavior
- ✅ No hidden configuration affecting results
- ⚠️ Long command lines for complex options (mitigated with shell aliases)

### Why Progress Bar Optional?

**Decision**: Progress indicator with `--progress` flag, not automatic.

**Why**:
- Interferes with piped output
- Not useful for small files
- Overhead not worth it for fast processing

**Implementation**: Detects if output is piped, disables automatically.

```bash
# Manual progress
patterndb-yaml --rules rules.yaml --progress large.log > output.log

# In pipeline - progress would interfere
cat large.log | patterndb-yaml --rules rules.yaml | grep ERROR
```

## Library vs CLI

### Why Both?

**Decision**: Provide both Python library and CLI tool.

**Why**:
- **CLI**: Most users want command-line tool for ad-hoc normalization
- **Library**: Some users need Python integration (Flask apps, data pipelines)
- Same core implementation, minimal extra code
- Separation of concerns (core logic vs UI)

**Architecture**:
```
src/patterndb_yaml/
  patterndb_yaml.py     # Core library (no CLI dependencies)
  cli.py                # CLI wrapper (uses library)
```

**Benefit**: Users can start with CLI, graduate to library if needed.

**Library usage**:
```python
from patterndb_yaml import PatterndbYaml
from pathlib import Path

processor = PatterndbYaml(rules_path=Path("rules.yaml"))
processor.process(input_stream, output_stream)
```

**CLI usage**:
```bash
patterndb-yaml --rules rules.yaml input.log
```

## Error Handling Philosophy

### Fail Fast vs Graceful Degradation

**Decision**: Different strategies for different error types.

**Fail fast** (startup errors):
- Invalid YAML syntax → immediate error with line number
- Rules file not found → immediate error with path
- Invalid pattern syntax → immediate error with rule name

**Graceful degradation** (runtime):
- Line doesn't match any pattern → pass through unchanged
- Output template references missing field → pass through unchanged
- ANSI stripping fails → process line as-is

**Why**:
- Configuration errors should be caught early (fail fast)
- Data errors shouldn't halt processing (graceful)
- Best effort processing for partial results

**Impact**:
- ✅ Clear errors for configuration problems
- ✅ Processing continues despite malformed input lines
- ✅ Statistics show match rate (indicates pattern coverage)

## Pattern Design Choices

### Why Component-Based Patterns?

**Decision**: Structured components (text, field, alternatives) instead of regex.

**Comparison**:
```yaml
# Component-based (chosen)
pattern:
  - field: timestamp
  - text: " ["
  - field: level
  - text: "] "
  - field: message

# Regex-based (rejected)
pattern: "^(\\S+) \\[([A-Z]+)\\] (.+)$"
```

**Why components**:
- More readable and maintainable
- Clear field extraction semantics
- Easier to debug (explain mode shows which component failed)
- Matches syslog-ng pattern database format

**Impact**:
- ✅ Easier to write and maintain
- ✅ Self-documenting structure
- ⚠️ More verbose than regex

### Why First-Match-Wins?

**Decision**: Stop trying patterns after first successful match.

**Why**:
- Predictable behavior - order in rules file is priority
- Efficient - don't waste time matching remaining patterns
- User controls priority explicitly

**Alternative considered**: Try all patterns, use best match.
- **Problem**: How to define "best"? Complexity without clear benefit.

**Impact**:
- ✅ Simple, understandable behavior
- ✅ Efficient (early exit)
- ⚠️ Rule order matters (specific before general)

## Next Steps

- **[Algorithm Details](algorithm.md)** - How it's implemented
- **[Performance Guide](../guides/performance.md)** - Optimize for your use case
- **[Contributing](contributing.md)** - Help improve patterndb-yaml
