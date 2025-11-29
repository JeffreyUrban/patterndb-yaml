# TODO: Update Template Repository with CI Optimizations

These improvements should be added to the template repository so all future projects get them automatically.

## 1. Concurrency Cancellation

**File:** `.github/workflows/test.yml` and `.github/workflows/quality.yml`

Add at top level of each workflow:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

**Benefit:** Cancels old CI runs when new commits are pushed. Saves minutes and speeds feedback.

**No downside:** This should stay forever.

---

## 2. Dependency Caching with uv

**File:** `.github/workflows/test.yml` and `.github/workflows/quality.yml`

Update the Python setup step:

```yaml
- name: Set up Python ${{ matrix.python-version }}
  uses: actions/setup-python@v5
  with:
    python-version: ${{ matrix.python-version }}
    cache: 'pip'
    cache-dependency-path: |
      **/pyproject.toml
      **/uv.lock
```

**Benefit:** Caches uv dependencies, saving 30-60 seconds per job.

**Note:** This works with uv - the cache key is based on lock file changes.

---

## 3. Coverage Upload on Oldest Python

**File:** `.github/workflows/test.yml`

Change coverage upload condition:

```yaml
- name: Upload coverage to Codecov
  if: matrix.python-version == '3.9'  # Changed from '3.14'
  uses: codecov/codecov-action@v4
```

**Rationale:**
- Upload from oldest supported Python (most restrictive)
- Ensures coverage metrics reflect minimum platform capabilities
- More stable baseline as newer Pythons add stdlib features

---

## Implementation Checklist

- [ ] Add concurrency cancellation to workflows
- [ ] Update caching to support uv
- [ ] Change coverage upload to oldest Python
- [ ] Test in template repository
- [ ] Update template documentation
- [ ] Apply to existing projects using template
