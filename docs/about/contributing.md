# Contributing to patterndb-yaml

Thank you for your interest in contributing to patterndb-yaml! This guide will help you get started.

## Ways to Contribute

### 1. Report Issues

Found a bug or have a feature request?

**Before creating an issue**:
- Search existing issues to avoid duplicates
- Check if it's already fixed in the main branch
- Gather relevant information (see below)

**What to include**:
```markdown
**Description**: Brief description of the issue

**Command used**:
```bash
patterndb-yaml --rules rules.yaml --explain input.log
```

**Sample input** (first 20 lines):
```
[paste sample here]
```

**Expected behavior**: What you expected to happen

**Actual behavior**: What actually happened

**Environment**:
- patterndb-yaml version: `patterndb-yaml --version`
- Python version: `python --version`
- OS: macOS/Linux/Windows
```

### 2. Improve Documentation

Documentation improvements are always welcome!

**Types of documentation contributions**:
- Fix typos or unclear explanations
- Add examples for common use cases
- Improve existing guides
- Add new use case examples
- Clarify error messages

**Where documentation lives**:
- `docs/` - User-facing documentation (MkDocs)
- `README.md` - Project overview
- Code docstrings - API documentation

**Testing documentation changes**:
```bash
# Install dependencies
pip install -e ".[docs]"

# Serve documentation locally
mkdocs serve

# View at http://127.0.0.1:8000
```

### 3. Submit Code Changes

#### Getting Started

**Fork and clone**:
```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/patterndb-yaml.git
cd patterndb-yaml
```

**Set up development environment**:
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

**Run tests**:
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_integration.py

# Run with coverage
pytest --cov=src --cov-report=html
```

#### Code Standards

**Python code requirements**:

1. **Type hints** for all function signatures:
   ```python
   def process(self, stream: TextIO, output: TextIO) -> None:
       """Process input stream and write normalized output."""
       pass
   ```

2. **Docstrings** for public functions/classes:
   ```python
   def normalize(line: str) -> str:
       """
       Normalize a single log line according to pattern rules.

       Args:
           line: Raw log line to normalize

       Returns:
           Normalized log line or original if no pattern matches
       """
       pass
   ```

3. **Named constants** instead of magic numbers:
   ```python
   # Good
   DEFAULT_SOMETHING_SIZE = 10
   something_size = DEFAULT_SOMETHING_SIZE

   # Bad
   something_size = 10  # What does 10 mean?
   ```

4. **Code formatting**:
   ```bash
   # Format code (runs automatically via pre-commit)
   ruff format .

   # Check for issues
   ruff check .
   ```

5. **Type checking**:
   ```bash
   # Run type checker
   mypy src/
   ```

#### Testing Requirements

**All code changes must include tests.**

**Test categories**:
- **Unit tests**: Test individual functions/classes
- **Integration tests**: Test component interactions
- **Feature tests**: Test complete features with fixtures

**Writing tests**:
```python
import pytest
from patterndb_yaml import PatterndbYaml
from pathlib import Path
from io import StringIO

def test_pattern_matching():
    """Test that patterns match correctly."""
    processor = PatterndbYaml(rules_path=Path("tests/fixtures/rules.yaml"))

    # Test input
    input_data = StringIO("2024-11-15 10:00:01 [INFO] User login\\n")
    output_data = StringIO()

    # Process and collect output
    processor.process(input_data, output_data)

    # Verify
    output_data.seek(0)
    result = output_data.read().strip()
    assert result == "[INFO:login]"
```

**Running specific tests**:
```bash
# Run by name pattern
pytest -k "test_normalization"

# Run specific file
pytest tests/test_integration.py

# Run with verbose output
pytest -v

# Run and stop at first failure
pytest -x
```

#### Submitting Pull Requests

**Before submitting**:

1. **Create a branch**:
   ```bash
   git checkout -b feature/my-improvement
   ```

2. **Make your changes**:
   - Write code
   - Add tests
   - Update documentation
   - Ensure all tests pass

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

   **Good commit messages**:
   - Start with verb (Add, Fix, Update, Remove)
   - Keep first line under 50 characters
   - Add detailed description if needed

   **Examples**:
   ```
   Add support for custom delimiters

   - Add --delimiter option to CLI
   - Support custom field delimiters in patterns
   - Add tests for delimiter functionality
   - Update documentation with examples
   ```

4. **Push and create PR**:
   ```bash
   git push origin feature/my-improvement
   ```

   Then create a Pull Request on GitHub.

**PR description should include**:
- What problem does this solve?
- How does it solve it?
- Any breaking changes?
- Related issues (closes #123)

**PR checklist**:
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] Type hints added
- [ ] Docstrings added
- [ ] Pre-commit hooks pass
- [ ] No merge conflicts

## Development Workflow

### Project Structure

```
patterndb-yaml/
├── src/patterndb_yaml/   # Source code
│   ├── __init__.py
│   ├── cli.py            # CLI interface (Typer)
│   ├── patterndb_yaml.py # Core normalization logic
│   ├── normalization_engine.py
│   ├── pattern_generator.py
│   └── ...
├── tests/                # Test files
│   ├── test_integration.py
│   ├── test_cli.py
│   ├── test_oracle.py
│   └── fixtures/         # Test data files
├── docs/                 # Documentation (MkDocs)
│   ├── guides/
│   ├── features/
│   └── use-cases/
├── pyproject.toml        # Project configuration
└── README.md
```

### Running Quality Checks

**Before committing** (automatic via pre-commit):
```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type check
mypy src/

# Run tests
pytest
```

**All checks together**:
```bash
# Run pre-commit on all files
pre-commit run --all-files
```

### Building Documentation

**Local preview**:
```bash
# Install docs dependencies
pip install -e ".[docs]"

# Serve documentation
mkdocs serve

# Open http://127.0.0.1:8000
```

**Build static site**:
```bash
mkdocs build
# Output in site/
```

### Debugging

**Enable debug logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Use pytest debugger**:
```bash
# Drop into debugger on failure
pytest --pdb

# Start debugger at specific test
pytest tests/test_file.py::test_function --pdb
```

**Profile performance**:
```bash
# Time a command
time patterndb-yaml large-file.log > /dev/null

# Profile with cProfile
python -m cProfile -s cumulative -m patterndb-yaml large-file.log
```

## Feature Development Guidelines

### Understanding syslog-ng Integration

patterndb-yaml translates YAML rules to [syslog-ng's pattern database format](https://syslog-ng.github.io/admin-guide/120_Parser/006_db_parser/004_The_syslog-ng_patterndb_format/README). syslog-ng provides many pattern parsers that can be used in field extraction.

**Available parsers**: See [Pattern parsers of syslog-ng OSE](https://syslog-ng.github.io/admin-guide/120_Parser/006_db_parser/003_Creating_pattern_databases/001_Pattern_parsers)

**Note**: patterndb-yaml may not yet support all available syslog-ng parsers.

**Contributing parser support**: Check the syslog-ng Pattern parsers page for additional parser types to consider adding.

When adding parser support, ensure:

1. The YAML syntax is intuitive
2. The generated XML correctly uses the syslog-ng parser
3. Tests validate the parser works correctly
4. Documentation includes examples

### Adding a New Feature

**Process**:

1. **Discuss first**: Open an issue to discuss the feature
2. **Design**: Write design doc if complex
3. **Implement**: Write code + tests
4. **Document**: Add to user documentation
5. **Submit**: Create PR

**Example: Adding a new CLI option**

1. **Add to CLI** (`src/patterndb_yaml/cli.py`):
   ```python
   @app.command()
   def main(
       # ... existing options ...
       case_sensitive: bool = typer.Option(
           True,
           "--case-sensitive/--case-insensitive",
           help="Enable or disable case-sensitive matching"
       ),
   ):
       # Pass to PatterndbYaml
       processor = PatterndbYaml(
           rules_path=rules,
           case_sensitive=case_sensitive
       )
   ```

2. **Add to core** (`src/patterndb_yaml/patterndb_yaml.py`):
   ```python
   def __init__(
       self,
       rules_path: Path,
       explain: bool = False,
       case_sensitive: bool = True
   ):
       self.case_sensitive = case_sensitive
       # Implementation
   ```

3. **Add tests**:
   ```python
   def test_case_insensitive_matching():
       processor = PatterndbYaml(
           rules_path=Path("rules.yaml"),
           case_sensitive=False
       )
       # Test that "ERROR" matches "error"
   ```

4. **Add documentation**:
   - Update `docs/reference/cli.md` with new option
   - Add example in `docs/guides/common-patterns.md`
   - Document in API reference (`docs/reference/patterndb-yaml.md`)

### Code Review Process

**What reviewers look for**:

- Does code work correctly?
- Are tests comprehensive?
- Is code readable and maintainable?
- Is documentation clear?
- Are edge cases handled?

**Responding to feedback**:
- Be open to suggestions
- Ask questions if unclear
- Make requested changes
- Push updates to same branch

## Common Development Tasks

### Adding a Test

```bash
# Create test file
touch tests/test_new_feature.py

# Write test
cat > tests/test_new_feature.py << 'EOF'
import pytest
from patterndb_yaml import PatterndbYaml

def test_new_feature():
    """Test the new feature."""
    processor = PatterndbYaml(
        rules_path=Path("tests/fixtures/rules.yaml"),
        new_option=True
    )
    # Test code here
EOF

# Run the new test
pytest tests/test_new_feature.py -v
```

### Adding Documentation

```bash
# Create new doc page
mkdir -p docs/features/my-feature
touch docs/features/my-feature/my-feature.md

# Add to navigation (mkdocs.yml)
# Edit nav: section

# Preview
mkdocs serve
```

### Updating Dependencies

```bash
# Update specific package
pip install --upgrade package-name

# Update all dev dependencies
pip install --upgrade -e ".[dev]"

# Regenerate lockfile (if using)
pip freeze > requirements.txt
```

## Getting Help

### Resources

- **Documentation**: https://patterndb-yaml.readthedocs.io/
- **Issue Tracker**: https://github.com/JeffreyUrban/patterndb-yaml/issues
- **Discussions**: Use issue tracker for now (Discussions not yet enabled)

### Ask Questions

**Where to ask**:
- GitHub Discussions for general questions
- GitHub Issues for bugs/features
- PR comments for code-specific questions

**How to ask**:
- Be specific about what you're trying to do
- Include code snippets or examples
- Show what you've already tried

## Code of Conduct

**Be respectful and inclusive**:
- Welcome newcomers
- Be patient with questions
- Provide constructive feedback
- Focus on the code, not the person

**Unacceptable behavior**:
- Harassment or discrimination
- Trolling or insulting comments
- Publishing private information
- Other unprofessional conduct

## License

By contributing to patterndb-yaml, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors are recognized in:
- GitHub contributors page
- Release notes for significant contributions
- Documentation credits for major doc improvements

Thank you for contributing to patterndb-yaml! 🎉
