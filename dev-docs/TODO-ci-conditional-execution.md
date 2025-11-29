# TODO: Decide on CI Conditional Execution Strategy

## Problem

Some CI checks are expensive (time/compute). Should we skip them in certain scenarios?

## Option 1: Draft PR Detection

**Skip expensive checks on draft PRs:**

```yaml
# .github/workflows/test.yml
jobs:
  test:
    # Only run full test matrix on ready-for-review PRs
    if: github.event.pull_request.draft == false || github.event_name == 'push'
    runs-on: ubuntu-latest
    # ...
```

**Pros:**
- GitHub has built-in draft PR feature
- Clear signal: "not ready for full review"
- Developers mark PR as draft while iterating
- Easy to toggle: mark as "ready for review" to run full checks

**Cons:**
- Requires remembering to mark PR as draft
- Might miss issues until marked ready
- Only works for PRs, not direct pushes to branches

**Best for:**
- Teams with code review process
- Long-lived feature branches
- When PRs go through multiple iterations

---

## Option 2: Branch-Based Logic

**Skip expensive checks on development branches:**

```yaml
jobs:
  test:
    # Full checks only on main and release branches
    if: |
      github.ref == 'refs/heads/main' ||
      startsWith(github.ref, 'refs/heads/release/') ||
      github.event_name == 'pull_request'
    runs-on: ubuntu-latest
```

Or inverse - run light checks on feature branches:

```yaml
jobs:
  quick-test:
    # Quick checks on feature branches
    if: startsWith(github.ref, 'refs/heads/feature/')
    strategy:
      matrix:
        python-version: ["3.9", "3.14"]  # Only boundary versions

  full-test:
    # Full checks on main/PRs
    if: github.ref == 'refs/heads/main' || github.event_name == 'pull_request'
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]
```

**Pros:**
- Automatic based on branch naming convention
- No manual intervention needed
- Works for direct pushes (no PR required)
- Encourages branch naming discipline

**Cons:**
- Requires consistent branch naming (feature/*, release/*)
- Less explicit than draft PR status
- Might run expensive checks unnecessarily if not using PRs

**Best for:**
- Solo developers or small teams
- Direct push workflow (not PR-heavy)
- When using branch naming conventions

---

## Option 3: Hybrid Approach

**Combine both strategies:**

```yaml
jobs:
  test:
    # Skip if:
    # - It's a draft PR, OR
    # - It's a push to a feature branch (not main/release)
    if: |
      (github.event_name == 'pull_request' && github.event.pull_request.draft == false) ||
      (github.event_name == 'push' && (
        github.ref == 'refs/heads/main' ||
        startsWith(github.ref, 'refs/heads/release/')
      ))
    runs-on: ubuntu-latest
```

**Behavior:**
- Draft PRs: Skipped
- Ready PRs: Run full checks
- Pushes to main/release: Run full checks
- Pushes to feature branches: Skipped

**Pros:**
- Best of both worlds
- Flexible for different workflows
- Clear rules for when checks run

**Cons:**
- More complex logic
- Harder to understand at a glance

---

## Recommendation

**For this project, I recommend Option 1 (Draft PR Detection):**

**Reasoning:**
1. You're using PRs (PR #1 exists)
2. Draft feature is built into GitHub (no new process)
3. Explicit control: mark ready when YOU want full checks
4. Simple conditional logic
5. Works well with reduced Python matrix during development

**Workflow:**
1. Create PR in draft mode while developing
2. Push commits freely - only quick checks run (if any)
3. When ready for full validation: mark "Ready for review"
4. Full CI runs (all Python versions, full coverage, etc.)
5. Merge when green

**Alternative for Direct Pushes:**

If you prefer pushing directly to feature branches without PRs:
- Use Option 2 (branch-based)
- Establish naming: `feature/*`, `fix/*`, `docs/*`
- Full checks only run on `main` and `release/*`

---

## Implementation Decision Needed

**Questions to answer:**

1. **Do you primarily use PRs or direct pushes?**
   - PRs → Use draft PR detection (Option 1)
   - Direct pushes → Use branch logic (Option 2)

2. **Do you want CI to run on every push to feature branches?**
   - Yes, but light checks → Reduced Python matrix on all branches
   - No, only on PR/main → Conditional execution

3. **What's your branching strategy?**
   - Feature branches → main → release
   - Direct commits to main (not recommended for this project)

**Current setup assumption:**
- Using PRs (PR #1 exists)
- Feature branch: `feature/flags`
- Merging to `main` eventually

**Recommended next step:**
- Implement Option 1 (draft PR) for now
- Keep it simple during early development
- Can add branch logic later if needed

---

## No Action Needed If:

You're fine with current setup:
- All pushes run full CI
- Rely on reduced Python matrix for speed (already done)
- Accept CI runs on every push

This is perfectly valid! The other optimizations (concurrency cancellation, caching) already provide good speedup.
