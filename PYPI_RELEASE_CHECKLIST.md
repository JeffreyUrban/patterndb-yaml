# PyPI Release Checklist

Checklist for preparing the first PyPI release of patterndb-yaml.

## Pre-Release Requirements

### Code Quality
- [ ] All tests passing in CI
- [ ] Test coverage >= 80% (current requirement)
- [ ] No critical linting errors
- [ ] Type checking passes (mypy)
- [ ] No security vulnerabilities

### Documentation
- [ ] README.md is complete and accurate
  - [ ] Remove "Early Development" warning
  - [ ] Installation instructions correct
  - [ ] Quick start examples work
  - [ ] Links are valid
- [ ] LICENSE file present and correct (MIT)
- [ ] CHANGELOG.md has initial release notes
- [ ] API documentation complete (if applicable)
- [ ] Examples directory has working examples

### Package Configuration
- [ ] pyproject.toml complete
  - [ ] Name: `patterndb_yaml` (correct)
  - [ ] Description accurate
  - [ ] Keywords appropriate
  - [ ] Classifiers correct
  - [ ] Dependencies complete
  - [ ] Python version requirement (>=3.9)
  - [ ] Entry point (`patterndb-yaml` CLI) works
- [ ] hatch-vcs version management configured
- [ ] Git tag for version created

### Functionality
- [ ] CLI works as documented
  - [ ] `patterndb-yaml --version` shows version
  - [ ] `patterndb-yaml --help` shows help
  - [ ] Basic pattern matching works
  - [ ] Multi-line patterns work
  - [ ] Stats output works
  - [ ] Explain mode works
- [ ] Python API works
  - [ ] Can import `from patterndb_yaml import PatterndbYaml`
  - [ ] Basic usage works as documented
- [ ] syslog-ng dependency handled
  - [ ] Clear error if syslog-ng not found
  - [ ] Version checking works (if implemented)

### Repository State
- [ ] Main branch is stable
- [ ] No uncommitted changes
- [ ] All PRs merged
- [ ] Git tags follow semantic versioning (v0.1.0, v1.0.0, etc.)

## Release Process

### 1. Finalize Version
- [ ] Decide version number (suggest: 0.1.0 for initial release)
- [ ] Update CHANGELOG.md with release date
- [ ] Commit final changes

### 2. Create Git Tag
```bash
git tag -a v0.1.0 -m "Initial release v0.1.0"
git push origin v0.1.0
```

### 3. Build Package
```bash
# Install build tools
pip install --upgrade build twine

# Build distribution
python -m build

# Check build
ls dist/
# Should see: patterndb_yaml-0.1.0.tar.gz and patterndb_yaml-0.1.0-py3-none-any.whl
```

### 4. Test Package Locally
```bash
# Create test environment
python -m venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install from built wheel
pip install dist/patterndb_yaml-0.1.0-py3-none-any.whl

# Test CLI
patterndb-yaml --version
patterndb-yaml --help

# Test basic functionality
# (commands from README Quick Start)

# Deactivate
deactivate
rm -rf test-env
```

### 5. Upload to TestPyPI (Optional but Recommended)
```bash
# Upload to TestPyPI first to catch issues
twine upload --repository testpypi dist/*

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    patterndb-yaml==0.1.0

# Test that it works
patterndb-yaml --version
```

### 6. Upload to PyPI
```bash
# Upload to real PyPI
twine upload dist/*

# Verify on PyPI
# Visit: https://pypi.org/project/patterndb-yaml/
```

### 7. Update Homebrew Formula
Once PyPI release is live:
- [ ] Update homebrew-patterndb-yaml formula with new version
- [ ] Update SHA256 hash from PyPI tarball
- [ ] Add `depends_on "syslog-ng"` if not already present
- [ ] Test Homebrew installation

### 8. Announce Release
- [ ] Create GitHub release from tag
- [ ] Update README.md to remove "Early Development" warning
- [ ] Announce on relevant channels (if applicable)

## Post-Release

- [ ] Monitor GitHub issues for installation problems
- [ ] Check PyPI download stats
- [ ] Update documentation if issues found
- [ ] Plan next release based on feedback

## Current Status Check

Run these commands to check current status:

```bash
# Check tests
pytest --cov=src/patterndb_yaml --cov-report=term

# Check linting
ruff check .

# Check type checking
mypy src/patterndb_yaml

# Check if package builds
python -m build --wheel --sdist

# Check package metadata
twine check dist/*
```

## Critical Blockers

Issues that MUST be resolved before release:

1. **syslog-ng dependency handling:**
   - Users must be able to install from pip without Homebrew
   - Clear error message if syslog-ng not found
   - Documentation on how to install syslog-ng

2. **README warning removal:**
   - Must update to indicate ready for use
   - Keep clear about external syslog-ng requirement

3. **Working examples:**
   - At least one complete example in `examples/` directory
   - Example rules file that works

4. **Version tag:**
   - Must have at least one git tag for hatch-vcs to work
   - Recommend starting with v0.1.0 or v1.0.0

## Notes

- pyproject.toml uses hatch-vcs for version management (gets version from git tags)
- First release requires at least one git tag
- TestPyPI is useful for catching packaging issues before real release
- Homebrew formula must point to PyPI tarball, not GitHub

## Version Numbering

**Suggest starting with v0.1.0:**
- Signals "beta" / "not yet stable"
- Room to iterate based on user feedback
- Can go to v1.0.0 when stable

**Or start with v1.0.0 if:**
- You're confident in API stability
- Ready to commit to semver
- Documentation complete
- Well tested

## Dependencies Note

Remember: pip/pipx installation will NOT install syslog-ng. Users must:
1. Install syslog-ng separately (from official repos)
2. Then install patterndb-yaml

Homebrew installation WILL install syslog-ng automatically (once `depends_on` added).
