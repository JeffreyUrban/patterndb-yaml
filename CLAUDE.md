# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working with this repository.

## Working with a Template-Based Project

**CRITICAL: This project uses a custom template designed to be release-ready from day one.**

### Template Philosophy

The template provides **complete, working infrastructure**:
- README with badges (PyPI, Tests, Coverage, etc.) - keep ALL badges even if they show "no release"
- CI/CD workflows fully configured
- Documentation structure with examples
- Test framework with fixtures
- All quality checks (coverage, type checking, linting)

### What to DO:
1. **Fill in template content** - Replace "placeholder" text with real project-specific content
2. **Follow template structure** - When creating new docs/tests, use existing templates as examples
3. **Keep all infrastructure** - README badges, CI workflows, doc structure stay intact
4. **Adapt, don't delete** - Modify template examples to fit this project, don't start from scratch

### What NOT to do:
- ❌ Delete README badges because "they don't work yet"
- ❌ Remove CI/CD workflows because "we're not ready"
- ❌ Delete template documentation and start over
- ❌ Remove quality checks because "coverage is too low"
- ❌ Strip out infrastructure "until we need it"

### Progressive Development Pattern:
- Template docs marked with `# ⚠️ Template doc: Testing disabled ⚠️` are automatically skipped in tests
- **Remove the warning heading when doc is ready** - testing automatically enables
- Coverage threshold starts low (30%), should be increased as code matures
- All template infrastructure stays in place, just incomplete content gets filled in

### Examples of Correct Approach:

**Wrong:**
```markdown
Let me remove these badges since PyPI doesn't exist yet...
Let me delete this template doc and write a new one...
This CI workflow is too complex, let me simplify it...
```

**Right:**
```markdown
Let me fill in this template doc with real content for this project...
Let me use this existing doc as a template for the new feature doc...
Let me add real test data to these template fixtures...
```

### Remember:
The user has invested significant effort designing a complete template. **Respect that work** by filling it in, not replacing it. When in doubt, ask before deleting ANY template infrastructure.

The project is new, all code is new and we need to vet and fix all code for errors and issues that come up.
There are no 'pre-existing issues'. Avoid overriding any quality checks. When type checking, avoid the `Any` type.

Documentation should include code and CLI commands and those should be tested. These are part of the test suite.

## Critical Rules

**NEVER mention version numbers** (v0.x, v1.x, etc.) unless they have been explicitly agreed upon and documented in planning. Use:
- **"Stage X"** for implementation phases (e.g., "Stage 3: Pattern Libraries")
- **"Current implementation"** for what exists now
- **"Planned features"** or **"Future features"** for what's coming
- **"Milestone"** for completed work

**DO NOT** add version numbers to:
- Documentation
- Code comments
- Commit messages
- Planning documents
- Unless the user has explicitly specified and approved a versioning scheme and specific versions

## Quick Links

**User Documentation:**
- **[README.md](./README.md)** - Project overview and installation

**Design Documentation:**
- **[dev-docs/design/IMPLEMENTATION.md](./dev-docs/design/IMPLEMENTATION.md)** - Implementation overview and design decisions
- **[dev-docs/design/ALGORITHM_DESIGN.md](./dev-docs/design/ALGORITHM_DESIGN.md)** - Detailed algorithm design
- **[dev-docs/design/DESIGN_RATIONALE.md](./dev-docs/design/DESIGN_RATIONALE.md)** - Design rationale and trade-offs

**Planning Documentation:**
- **[dev-docs/planning/PLANNING.md](./dev-docs/planning/PLANNING.md)** - Roadmap and feature planning

**Testing Documentation:**
- **[dev-docs/testing/TESTING_STRATEGY.md](./dev-docs/testing/TESTING_STRATEGY.md)** - Test strategy and organization
- **[dev-docs/testing/TEST_COVERAGE.md](./dev-docs/testing/TEST_COVERAGE.md)** - Test coverage plan
- **[dev-docs/testing/ORACLE_TESTING.md](./dev-docs/testing/ORACLE_TESTING.md)** - Oracle-based testing approach

**Code Quality:**

- **Type hints required** for function signatures
- **Docstrings required** for public functions/classes
- **Avoid magic numbers** - use named constants

## Modern Tools & Techniques Philosophy

**Approach:** Favor modern, mature tools over legacy approaches. Not bleeding edge, but proven improvements.

**When relevant, consider these modern alternatives:**

**Python libraries** (consider when use case arises):

- **CLI tools:** `typer` (type-based, modern) over `argparse`/`click` ✓ Project standard
- **Terminal output:** `rich` for beautiful CLI output, progress bars, tables

## Code Standards

**Python:**

- Type hints required for function signatures
- Docstrings for public functions/classes
- **Avoid magic numbers** - use named constants
    - Example: `MY_CONSTANT = 0.5` instead of hardcoded `0.5`

### Writing Code That Passes Quality Checks First Time

**This project has strict quality checks. Write code that passes from the start to avoid rework.**

#### Type Checking (mypy --strict)

**Always:**
- Add type hints to ALL function parameters and return values
- Use `Optional[Type]` for values that can be `None`
- Never use `Any` type
- Import types from `typing` for Python 3.9 compatibility:
  ```python
  from typing import Optional, Union  # Not using `Type | None` syntax
  ```

**Common Issues:**
```python
# ❌ Wrong - missing return type
def process(data):
    return data

# ✅ Right
def process(data: str) -> str:
    return data

# ❌ Wrong - Any type
def handle(obj: Any) -> None:
    ...

# ✅ Right - specific type
def handle(obj: dict[str, str]) -> None:
    ...
```

#### Line Length (100 chars max)

**Check before committing:**
- Code lines: 100 characters maximum
- Docstring lines: 80 characters maximum (markdown in docs)
- Use implicit line continuation in parentheses:
  ```python
  # ✅ Right
  result = some_function(
      long_parameter_name,
      another_parameter,
  )
  ```

#### Formatting (ruff format)

**Let ruff handle it:**
- Run `ruff format .` before committing
- Or rely on pre-commit hooks
- **Don't fight the formatter** - accept its style

#### Imports (ruff check)

**Order:**
1. Standard library imports
2. Third-party imports
3. Local imports

```python
# ✅ Right
import sys
from pathlib import Path

import yaml

from .module import function
```

#### Docstrings

**Required for public functions/classes:**
```python
def public_function(param: str) -> bool:
    """
    One-line summary ending with period.

    Longer description if needed.

    Args:
        param: Description of parameter

    Returns:
        Description of return value
    """
```

**Pre-commit will enforce:**
- Trailing whitespace removal
- End-of-file newlines
- YAML syntax validity
- Mixed line endings

**Pro tip:** Run `pre-commit run --all-files` before pushing to catch issues early.

## Documentation Standards

**Three Types of Documentation:**

1. **Planning Documentation** (temporary) - Design explorations, implementation plans, "Next Steps", "TODO"
2. **Progress Documentation** (temporary) - "What We've Built", implementation status
3. **Work Product Documentation** (permanent) - Current implementation, usage, architecture decisions

**Key Principles:**

- Work is not complete until documentation is production-ready
- Planning/progress docs are valuable during development - **delete or archive after completion**
- Work product docs describe current reality, not plans or history
- Put function details in docstrings, not external docs
- Reference code locations, don't duplicate values or implementation
- Preserve design rationales when converting planning → work product docs
- **Clean up as you go**: Delete TODO documents once resolved, update permanent docs instead

**Documentation Cleanup:**

When work is complete, **remove temporary documentation**:
- ❌ **Delete** TODO documents that describe completed work
- ✅ **Update** permanent documentation (design docs, implementation guides) with useful information
- ✅ **Update** CLAUDE.md if there are lessons learned for future work
- Don't leave the project littered with obsolete TODO files

**Before creating directory structures:** Discuss scope and organization with user

### Documentation-Driven Engineering

**CRITICAL: Before implementing, understand and document requirements first!**

This project follows a documentation-driven approach. When working on features or fixing issues:

1. **Clarify requirements** through discussion with the user
2. **Document the design** in the appropriate work product documentation
3. **Reference the documentation** during implementation
4. **Update documentation** as design evolves

**Documentation Organization:**

Documentation is organized by audience and purpose:

1. **User Documentation** (`dev-docs/user/`):
   - Usage guides, examples, and user-facing features
   - **Update when**: Adding features, changing CLI, updating examples
   - **Audience**: End users of patterndb-yaml

2. **Design Documentation** (`dev-docs/design/`):
   - Technical architecture, algorithms, implementation details
   - **Update when**: Changing algorithms, adding design decisions, modifying architecture
   - **Audience**: Developers, contributors, technical reviewers

3. **Planning Documentation** (`dev-docs/planning/`):
   - Roadmaps, feature plans, implementation stages
   - **Update when**: Completing milestones, planning new stages, updating roadmap
   - **Audience**: Project maintainers, contributors

4. **Testing Documentation** (`dev-docs/testing/`):
   - Test strategy, coverage plans, testing approaches
   - **Update when**: Adding test categories, changing coverage targets, new testing approaches
   - **Audience**: Developers, QA, contributors

**Documentation Maintenance Rules:**

When working on different scopes of work, maintain corresponding documentation:

| Work Scope | Documentation to Update |
|------------|------------------------|
| **Adding/changing features** | `dev-docs/design/IMPLEMENTATION.md`, `dev-docs/user/EXAMPLES.md` |
| **Modifying algorithm** | `dev-docs/design/ALGORITHM_DESIGN.md`, `dev-docs/design/IMPLEMENTATION.md` |
| **Adding tests** | `dev-docs/testing/TESTING_STRATEGY.md` |
| **CLI changes** | `README.md`, `dev-docs/user/EXAMPLES.md` |
| **Completing milestones** | `dev-docs/planning/PLANNING.md` |
| **Design decisions** | `dev-docs/design/DESIGN_RATIONALE.md` |

**Implementation Workflow:**

When implementing or fixing features:

1. **Identify scope**: Determine which documentation category applies
2. **Read relevant docs**: Reference appropriate design/planning docs
3. **Ask for clarification** if requirements are unclear or incomplete
4. **Update documentation FIRST**: Document design changes before implementing
5. **Implement** according to documented design
6. **Update related docs**: Ensure all affected documentation is updated
7. **Verify** implementation matches documentation

**DO NOT:**
- Implement based on assumptions without documented requirements
- Add implementation details to @CLAUDE.md (they belong in @docs/IMPLEMENTATION.md)
- Skip documentation updates when design changes
- Document violations of requirements as "limitations" or "TODO" items
- **Make unsubstantiated causal claims** - only state what is observed, not assumed causes

### Feature and Use Case Documentation Pattern

**Locations**:
- Features: `docs/features/[feature-name]/[feature-name].md`
- Use cases: `docs/use-cases/[use-case-name]/[use-case-name].md`

**Purpose**: User-facing documentation for features and use cases with executable examples.

**Template**: Follow the pattern in `docs/features/placeholder/placeholder.md`

**Key Requirements:**

1. **Tabbed CLI/Python Examples** - Show CLI and Python side-by-side, NOT in separate sections:
   ```markdown
   === "CLI"
       <!-- verify-file: output.txt expected: expected-output.txt -->
       <!-- termynal -->
       ```console
       $ patterndb-yaml --rules rules.yaml input.txt > output.txt
       ```

   === "Python"
       <!-- verify-file: output.txt expected: expected-output.txt -->
       ```python
       from patterndb_yaml import PatterndbYaml
       from pathlib import Path

       processor = PatterndbYaml(rules_path=Path("rules.yaml"))

       with open("input.txt") as f:
           with open("output.txt", "w") as out:
               processor.process(f, out)
       ```
   ```

2. **Output to Files** - Code blocks should write output to files, NOT display output inline:
   - ✅ Right: `patterndb-yaml ... > output.txt`
   - ❌ Wrong: `patterndb-yaml ...` (showing output in same block)

3. **Display Output from Fixtures** - Use admonitions with file inclusion:
   ```markdown
   ???+ success "Output: Description"
       ```text
       --8<-- "features/explain/fixtures/expected-output.txt"
       ```
   ```

4. **Test Markers** - Include verify-file markers for executable testing:
   ```markdown
   <!-- verify-file: output.txt expected: expected-output.txt -->
   ```

5. **Annotations for Key Concepts** - Use numbered annotations in code:
   ```python
   processor = PatterndbYaml(
       rules_path=Path("rules.yaml"),
       explain=True  # (1)!
   )
   ```

   Then add explanations after the code block:
   ```markdown
   1. Explanations are written to stderr automatically
   ```

6. **Simplified, Realistic Examples** - Focus on the feature being documented:
   - Don't overcomplicate with multiple features
   - Use realistic but simple input/output
   - Highlight what makes this feature useful

7. **Template Headers** - Template docs (not yet written) have:
   ```markdown
   # ⚠️ Template doc: Testing disabled ⚠️
   ```

**Structure (Features):**
- **What It Does** - Brief overview
- **Examples** - Tabbed CLI/Python blocks demonstrating the feature
- **Common Use Cases** - Practical applications
- **See Also** - Links to related features/docs

**Structure (Use Cases):**
- Use case-specific sections (varies by use case)
- Follow same formatting patterns (tabs, file output, fixtures, etc.)
- Examples should demonstrate the use case scenario

**DON'T:**
- Create separate "Python API" sections (use tabs instead)
- Show output inline in code blocks (write to files, display separately)
- Duplicate CLI/Python examples (use tabs to show both approaches)
- Write documentation for features not yet implemented (use template marker)

**Example violations:**

*Requirement violation:*
```
Requirement: "Keep the most recent value"
Wrong: Implement to keep old value, add TODO to fix later
Right: Ask for clarification if unclear, implement correctly
```

*Unsubstantiated causal claim:*
```
Wrong: "Substring matching causes performance degradation"
  (we observed slow performance AND learned of a requirement - no causal link established)
Right: "Full-line matching required per user specification. Performance issue under investigation."
```

**Evidence-Based Documentation:**
- Distinguish between **observed facts** and **inferred causes**
- Use precise language: "observed", "measured", "specified by user" vs "causes", "due to", "because"
- When debugging, document what was tried and what was observed, not assumed root causes
- If stating a cause, cite the evidence or mark as hypothesis

**When Asked to Justify Decisions:**
- If the user asks why you made a decision or assumption, search documentation and code comments for supporting evidence
- Present the evidence with specific references (file paths and line numbers where applicable)
- If no supporting evidence is found, acknowledge the assumption and ask for clarification
- Example: "I assumed X based on the comment at normalization_engine.py:117 which states '...'"

## Testing

This project uses **pytest exclusively** (not unittest).

**Core Principles:**

1. **Use pytest markers** - `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
2. Reference `dev-docs/testing/TESTING_STRATEGY.md` and `dev-docs/testing/TEST_COVERAGE.md` to understand test organization and coverage
3. When tests fail, determine if the change is a fix (regenerate tests) or a regression (fix the code)

### Testable Documentation and Specification Tests

**This project uses documentation as specification through executable examples.**

**Intentional Test Failures:**

Tests SHOULD fail when they document intended behavior that isn't yet implemented:

- **Purpose**: Serve as both specification and test for future implementation
- **Benefit**: Clear, executable documentation of what SHOULD happen
- **Identification**: Look for notes in documentation like "specified but not yet fully implemented"

**Example Pattern:**
```markdown
???+ success "Expected Output: Feature behavior (specification)"
    ```text
    --8<-- "features/example/fixtures/expected-output.txt"
    ```

    **Expected behavior**: Description of what should happen

    **Note**: This feature is specified but not yet fully implemented.
    Currently [describe actual behavior].
```

**When You See Failing Documentation Tests:**

1. **Check if intentional** - Look for specification notes in the documentation
2. **Intentional failures are CORRECT** - They document requirements, don't "fix" them
3. **Unintentional failures need fixing** - Missing files, wrong paths, etc. should be resolved

**DO NOT:**
- ❌ Remove or skip specification tests because they fail
- ❌ Change expected output to match current (incorrect) behavior
- ❌ Add workarounds to make specification tests pass when feature isn't implemented

**DO:**
- ✅ Keep specification tests that document intended behavior
- ✅ Add notes explaining the gap between expected and actual behavior
- ✅ Use these tests as implementation guides when building the feature

**Example pattern:**

A specification test might document intended behavior like:
- **Expected**: Feature produces specific output format
- **Actual**: Feature not yet implemented, different output
- **Status**: Intentional - documents the specification for implementation

When the feature is implemented, update the documentation to reflect completion.

## Common Task Checklists

### Creating New Features

1. Check `dev-docs/design/IMPLEMENTATION.md` for design alignment
2. **Write tests** (TDD or alongside implementation):
    - Create fixtures
    - Unit tests for pure functions
    - Mark with `@pytest.mark.unit`, `@pytest.mark.integration`, etc.
3. **Verify tests pass**: `pytest`
4. **Update documentation**:
    - `dev-docs/design/IMPLEMENTATION.md` - if changing architecture
    - `dev-docs/user/EXAMPLES.md` - if adding user-facing features
    - `dev-docs/testing/TESTING_STRATEGY.md` - if adding new test categories

**Testing is not optional** - All features require tests.

## Project Context for Claude Code

**Development Philosophy:**

- **Testing Required** - All code needs pytest tests

**Project-Specific Critical Rules:**

- **CRITICAL: Implement requirements correctly, don't document violations as limitations!**
  - When given a requirement (e.g., "keep the most recent value"), implement it correctly
  - Do NOT implement the opposite behavior and add a TODO noting it should be fixed later
  - If the requirement needs clarification or would require significant changes, ASK first

- **CRITICAL: Use proper solutions, not workarounds!**
  - When encountering issues (especially in CI/testing), investigate the root cause
  - Find the standard/best-practice solution for the problem
  - Examples of workarounds to AVOID:
    - Weakening test assertions to pass (e.g., changing "window-size" to "window")
    - Adding `# type: ignore` comments instead of fixing type issues
    - Disabling linters/checkers instead of fixing the underlying issue
  - Examples of proper solutions:
    - Setting environment variables for consistent behavior (e.g., `COLUMNS` for terminal width)
    - Using appropriate imports for Python version compatibility (e.g., `Optional` vs `|`)
    - Configuring tools correctly in config files
  - If unsure whether a solution is a workaround or proper fix, ASK the user

**Maintenance:**

- Upon confirming new code works correctly, remove outdated code and documentation
- Add and maintain test cases in @tests corresponding to issues found and fixes applied
