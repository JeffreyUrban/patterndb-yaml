# How patterndb-yaml Works

A detailed look at the algorithm behind log normalization.

## Core Algorithm

patterndb-yaml uses a **hybrid pattern matching approach** combining YAML-defined rules with syslog-ng's proven pattern matching engine. The algorithm processes logs line-by-line with constant memory usage, making it suitable for files of any size.

### High-Level Architecture

```
Input Stream
     ↓
┌────────────────────────────────────────────┐
│  1. Load Rules & Generate Patterns        │
│     - Parse YAML rules                     │
│     - Generate syslog-ng XML patterns      │
│     - Initialize pattern matcher           │
└────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────┐
│  2. Line-by-Line Processing                │
│     For each input line:                   │
│       a. Strip ANSI codes                  │
│       b. Check LRU cache (65k entries)     │
│       c. If cached → use cached result     │
│       d. If not cached → match patterns    │
└────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────┐
│  3. Pattern Matching                       │
│     Try each rule in order until match:    │
│       - Match text components exactly      │
│       - Extract field values               │
│       - Handle alternatives                │
│     First match wins (stop trying)         │
└────────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────────┐
│  4. Sequence Processing                    │
│     If normalized line is sequence leader: │
│       - Buffer line                        │
│       - Collect follower lines             │
│       - Flush on sequence end              │
│     Else:                                  │
│       - Output immediately                 │
└────────────────────────────────────────────┘
     ↓
Output Stream
```

### The Process

1. **Initialization Phase**
   - Load YAML rules file
   - Generate syslog-ng XML patterns from YAML rules
   - Create temporary XML file (auto-cleaned on exit)
   - Initialize pattern matcher with generated XML
   - Build rule lookup table for fast access
   - Initialize LRU cache (65,536 entry capacity)
   - Load multi-line sequence configurations

2. **Processing Phase** (for each input line)
   - Read line from input stream
   - Strip ANSI escape codes (terminal colors, formatting)
   - Check LRU cache: if line seen before, use cached result (O(1))
   - If not cached: match against patterns sequentially
   - Extract fields from matched pattern
   - Apply output template with extracted fields
   - Handle multi-line sequence buffering if needed
   - Write to output stream
   - Update statistics (lines processed, matched)

3. **Finalization Phase**
   - Flush any buffered multi-line sequences
   - Output statistics (lines processed, match rate)
   - Clean up temporary files

## Key Concepts

### Pattern Matching

**Sequential First-Match-Wins**:
```python
for rule in rules:  # Try each rule in order
    if pattern_matches(line, rule.pattern):
        return apply_template(rule.output, extracted_fields)
# If no pattern matched, return line unchanged
```

**Component Types**:

1. **text** - Exact string match
   ```yaml
   - text: " [INFO] "
   # Line must contain exactly " [INFO] " at this position
   ```

2. **serialized** - Match special characters (tabs, newlines, etc.)
   ```yaml
   - serialized: "\t"
   # Matches a tab character
   ```

3. **field** - Extract variable content
   ```yaml
   - field: username
   # Extracts text into 'username' field for use in output template
   ```

4. **alternatives** - Match any of several options
   ```yaml
   - alternatives:
       - [{ text: "GET" }]
       - [{ text: "POST" }]
       - [{ text: "PUT" }]
   # Matches any HTTP method
   ```

**Field Extraction Behavior**:

Fields extract text until:
- The next pattern component (text, serialized, etc.)
- End of line (if no delimiter specified)
- NUMBER parser matches digits only

Example:
```yaml
pattern:
  - text: "User: "
  - field: username      # Extracts until next component
  - text: " logged in"   # Delimiter that stops extraction
```

Input: `User: alice logged in`
- Extracts: `username = "alice"`

### ANSI Code Handling

Terminal colors and formatting are automatically stripped before matching:

```python
# Before matching, strip ANSI codes
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
clean_line = ANSI_RE.sub("", line)
```

This ensures patterns match correctly even when input contains colored output.

### LRU Caching

**Purpose**: Avoid re-processing identical repeated lines (common in logs).

**Implementation**:
```python
from functools import lru_cache

@lru_cache(maxsize=65536)  # Cache up to 65,536 unique lines
def normalize_cached(line: str) -> str:
    return normalize(line)
```

**Cache Benefits**:
- O(1) lookup for repeated lines
- Automatic eviction (LRU - Least Recently Used)
- Significant speedup for logs with repetitive content

**Cache Effectiveness**:
```
High cache hit rate:  Health checks, periodic status messages
Low cache hit rate:   Unique transaction IDs, varying timestamps
```

### Multi-Line Sequences

Some log entries span multiple lines (e.g., stack traces). The sequence processor handles these:

**Sequence Structure**:
```yaml
rules:
  - name: exception_with_trace
    pattern: [...]  # Leader pattern
    output: "[EXCEPTION:{message}]"
    sequence:
      followers:
        - pattern: [...]  # Follower pattern 1
          output: "  {trace_line}"
        - pattern: [...]  # Follower pattern 2
          output: "  {trace_line}"
```

**Sequence Processing**:
1. Detect sequence leader (match + has 'sequence' config)
2. Buffer leader line
3. For subsequent lines:
   - If matches follower pattern → buffer
   - If doesn't match follower → flush buffer, process new line
4. On end of input → flush any remaining buffer

**Buffer Management**:
- Sequences buffered in memory until complete
- No arbitrary length limit (trust input structure)
- Flushed as complete units to maintain atomicity

## Memory Efficiency

### Streaming Architecture

**Line-by-line processing** - never loads entire file into memory:

```python
def process(stream, output):
    for line in stream:  # Process one line at a time
        normalized = normalize(line)
        output.write(normalized + "\n")
```

**Memory footprint is constant**:
- 10 MB file → ~20-50 MB memory
- 10 GB file → ~20-50 MB memory (same!)

### Memory Components

```
Total Memory = Base + Rules + Cache + Buffer

Base overhead:    ~10-50 MB
  - Python runtime
  - syslog-ng pattern matcher
  - Module imports

Rule storage:     ~1 KB × num_rules
  - Pattern definitions
  - Output templates
  - Lookup tables

LRU cache:       ~100 bytes × 65,536
  - Cached normalized lines
  - ~6.4 MB maximum

Sequence buffer: Variable
  - Active multi-line sequences
  - Usually < 1 MB
  - Scales with sequence length
```

### Temporary Files

**XML Pattern File**:
- Generated from YAML rules at startup
- Stored in system temp directory
- Automatically deleted on process exit
- Cleaned up even on crashes (atexit handler)

```python
xml_tempfile = tempfile.NamedTemporaryFile(
    mode="w",
    suffix=".xml",
    prefix="patterndb_",
    delete=False
)
atexit.register(cleanup_tempfile)
```

## Performance Characteristics

### Time Complexity

**Per-line processing**:
- **Best case**: O(1) - Cache hit (line seen before)
- **Average case**: O(R) - First rule matches (R = number of rules)
- **Worst case**: O(R × P) - Try all rules (P = avg pattern length)

**Full file processing**:
- **Total time**: O(N × R × P) where N = number of lines
- **Amortized**: Often better due to caching (repeated lines)

**Optimizations**:
1. **First-match-wins**: Stop checking patterns after match
2. **LRU cache**: O(1) for repeated lines
3. **Precompiled regex**: ANSI stripping uses compiled pattern
4. **Rule ordering**: Common patterns first reduce average case

### Space Complexity

**Algorithm space complexity**: O(R + C)
- R = rules (pattern definitions)
- C = cache entries (bounded at 65,536)
- **Independent of input size** (streaming)

**Practical memory usage**:
```
Small rules file (10 rules):     ~20 MB total
Medium rules file (100 rules):   ~25 MB total
Large rules file (1000 rules):   ~40 MB total
```

Memory does **not** grow with:
- Input file size
- Number of lines processed
- Line length (lines processed individually)

### I/O Characteristics

**Sequential reads only**:
- No seeking or random access
- Efficient for large files
- Works with pipes and streams

**Minimal buffering**:
- Process immediately as lines arrive
- Low latency for real-time processing
- Suitable for `tail -f` streaming

## Algorithm Correctness

### Pattern Matching Order

**Critical property**: First matching rule wins.

This means **rule order matters**:

```yaml
# WRONG ORDER - specific pattern never reached
rules:
  - name: general
    pattern:
      - field: timestamp
      - text: " ERROR "
      - field: message
    output: "[ERROR]"

  - name: specific  # Never matched! (general pattern catches it first)
    pattern:
      - field: timestamp
      - text: " ERROR Connection failed"
      - field: details
    output: "[ERROR:CONNECTION]"
```

```yaml
# CORRECT ORDER - specific before general
rules:
  - name: specific
    pattern:
      - field: timestamp
      - text: " ERROR Connection failed"
      - field: details
    output: "[ERROR:CONNECTION]"

  - name: general
    pattern:
      - field: timestamp
      - text: " ERROR "
      - field: message
    output: "[ERROR]"
```

### Field Extraction Semantics

**Greedy extraction**: Fields consume text until delimiter or end of line.

```yaml
pattern:
  - text: "User: "
  - field: username  # Extracts: "alice logged"
  - text: " in"
```

Input: `User: alice logged in`
- Without delimiter between components, `username` extracts too much!

**Fixed with delimiter**:
```yaml
pattern:
  - text: "User: "
  - field: username
  - text: " logged in"  # Delimiter stops extraction at "alice"
```

### NUMBER Parser

**Special parser for numeric fields**:

```yaml
pattern:
  - text: "Count: "
  - field: count
    parser: NUMBER  # Matches only digits
  - text: " items"
```

**Behavior**:
- Matches: `Count: 42 items` → `count = "42"`
- Fails: `Count: N/A items` (N/A not numeric)

## Oracle Compatibility

patterndb-yaml's algorithm is validated against an **oracle implementation** - a simple, obviously-correct reference implementation used for testing.

**Oracle testing approach**:
1. Implement simple, correct algorithm (even if slow)
2. Generate test cases covering edge cases
3. Verify production implementation matches oracle exactly
4. Property-based testing for comprehensive coverage

**What oracle testing validates**:
- Pattern matching correctness
- Field extraction accuracy
- Edge cases (empty lines, special characters)
- Multi-line sequence handling
- Output template formatting

All edge cases and complex scenarios are verified to match oracle behavior exactly.

See [Testing Strategy](../../dev-docs/testing/TESTING_STRATEGY.md) for details.

## Implementation Details

### Hybrid Architecture

**Why combine YAML and syslog-ng?**

1. **YAML for rules**: User-friendly, readable, version-controllable
2. **syslog-ng for matching**: Fast, proven, battle-tested C implementation
3. **Python for orchestration**: Flexible, rich ecosystem

**Pattern Generation Pipeline**:
```
YAML Rules → Pattern Generator → syslog-ng XML → Pattern Matcher
                (Python)                              (C library)
```

### Pattern Matcher Integration

**PatternMatcher class** (wraps syslog-ng):
- Loads compiled XML patterns
- Provides `match(line)` method
- Returns matched rule name + extracted fields
- Optimized C implementation for speed

**Field Encoding**:
Matched patterns return encoded MESSAGE:
```
[rule_name]|field1=value1|field2=value2|
```

This is parsed to extract:
- Which rule matched
- Field values for template substitution

### Error Handling

**Graceful degradation**:
- If no pattern matches → pass line through unchanged
- If output template has missing field → pass line through
- If YAML is invalid → fail fast with clear error

**Statistics tracking**:
```python
stats = {
    'lines_processed': 1000,
    'lines_matched': 950,
    'match_rate': 95.0  # 95% of lines matched a pattern
}
```

Low match rates indicate missing patterns for some log formats.

## Design Trade-offs

### Chosen: Sequential Pattern Matching

**Alternative considered**: Build finite automaton from all patterns.

**Why sequential**:
- Simple to understand and debug
- Fast enough for typical use cases (10k-100k lines/sec)
- Preserves rule priority (first match wins)
- Easy to modify rules without recompilation

**Cost**: O(rules) per line instead of O(1) theoretical best case.

### Chosen: Line-by-Line Streaming

**Alternative considered**: Load entire file, build index, batch process.

**Why streaming**:
- Constant memory regardless of file size
- Works with infinite streams (`tail -f`)
- Lower latency (process as data arrives)
- Simple implementation

**Cost**: Cannot do multi-pass analysis or global optimizations.

### Chosen: LRU Cache (65,536 entries)

**Why 65,536**:
- Balance between memory (6.4 MB) and coverage
- Power of 2 for efficient hash table
- Large enough for most repetitive patterns
- Small enough to stay in CPU cache

**Alternative considered**: Unbounded cache (would grow with unique lines).

## Next Steps

- **[Design Decisions](design-decisions.md)** - Why these specific choices were made
- **[Performance Guide](../guides/performance.md)** - Optimize for your use case
- **[Basic Concepts](../getting-started/basic-concepts.md)** - User-focused concepts
- **[Troubleshooting](../guides/troubleshooting.md)** - Solving common problems
