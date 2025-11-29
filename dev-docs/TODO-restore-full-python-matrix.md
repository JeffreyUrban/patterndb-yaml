# TODO: Restore Full Python Version Matrix Before Release

## Current State (Development)

For development velocity, testing only **boundary versions**:
- Python 3.9 (minimum supported - most restrictive)
- Python 3.14 (latest - catches new features/deprecations)

**Time savings:** ~67% reduction (6 jobs → 2 jobs)

**Location:** `.github/workflows/test.yml` line 16-17

```yaml
strategy:
  matrix:
    python-version: ["3.9", "3.14"]
```

---

## Before v0.1.0 Release

**Restore full matrix to test all supported versions:**

```yaml
strategy:
  matrix:
    python-version: ["3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]
```

---

## Why This Works

**Middle versions rarely have unique issues because:**
- Most compatibility issues show up at boundaries (oldest/newest)
- Python maintains strong backward compatibility
- Standard library changes are incremental

**Testing 3.9 catches:**
- Missing features (3.10+ additions)
- Type hint syntax (3.10+ union syntax)
- Deprecated features still needed

**Testing 3.14 catches:**
- New deprecation warnings
- Future compatibility issues
- Latest stdlib changes

---

## Verification Checklist (Before Release)

- [ ] Update python-version matrix to full list
- [ ] Push and verify all 6 versions pass tests
- [ ] Check coverage meets threshold on all versions
- [ ] Review any version-specific test skips/xfails
- [ ] Verify no deprecation warnings on Python 3.14
- [ ] Document supported versions in README.md
- [ ] Update pyproject.toml if version support changed:
  ```toml
  requires-python = ">=3.9"
  classifiers = [
      "Programming Language :: Python :: 3.9",
      "Programming Language :: Python :: 3.10",
      # ... all versions
  ]
  ```

---

## Optional: Keep Reduced Matrix Longer

If you want to keep the reduced matrix past initial release:

**Consider:**
- Many projects only test min + max + current stable
- Example: Test 3.9, 3.13, 3.14 (oldest, stable, latest)
- Expand to full matrix only when issues arise

**Trade-off:**
- Faster CI during active development
- Potentially miss version-specific edge cases
- Acceptable for early releases, restore for production maturity
