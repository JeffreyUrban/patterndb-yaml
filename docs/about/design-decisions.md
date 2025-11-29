# Design Decisions

Why patterndb-yaml works the way it does.

## Core Principles

### 1. placeholder

**Decision**: placeholder.

**Why**: placeholder

**Impact**:
- ✅ placeholder
- ⚠️ placeholder

### 2. Unix Philosophy

**Decision**: Do one thing well - placeholder.

**Why**: There are already excellent tools for:
- placeholder

patterndb-yaml focuses on what they don't do: placeholder.

**Impact**:
- ✅ placeholder
- ✅ Composes well with existing Unix tools
- ✅ Easier to understand and maintain
- ❌ Won't add features better served by other tools

## Feature Decisions

### ✅ Included: placeholder

**Feature**: placeholder

**Why**: placeholder


**Alternatives considered**:
- placeholder
- **Problem**: placeholder

**Decision**: placeholder.

### ❌ Excluded: placeholder

**Feature**: placeholder.

**Why excluded**: placeholder.

**Alternative**:
```bash
placeholder
```

**Decision**: placeholder

## Memory Management

### placeholder

## CLI Design

### Why Flags Over Positional Args?

**Decision**: All options are flags (`--placeholder`), not positional.

**Why**:
- Clearer what each parameter does
- Optional parameters easy to add
- Better shell completion
- Follows modern CLI conventions

### Why No Config Files?

**Decision**: No `.patterndb-yamlrc` or config files.

**Why**:
- Tool used in one-off commands and pipelines
- Shell aliases work fine for common patterns:
  ```bash
  alias patterndb-yaml-logs='patterndb-yaml --placeholder'
  ```
- Avoids "spooky action at a distance"

## Library vs CLI

### Why Both?

**Decision**: Provide both Python library and CLI tool.

**Why**:
- **CLI**: Most users want command-line tool
- **Library**: Some users need Python integration
- Same implementation, minimal extra code

**Benefit**: Users can start with CLI, graduate to library if needed.

## Next Steps

- **[Algorithm Details](algorithm.md)** - How it's implemented
- **[Contributing](contributing.md)** - Help improve patterndb-yaml
