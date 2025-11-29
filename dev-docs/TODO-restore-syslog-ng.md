# TODO: Restore syslog-ng Installation in CI

## Current State

syslog-ng installation has been **temporarily disabled** in CI workflows.

**Observed behavior**:
- CI jobs hung for 47+ minutes with no logs available (runs 19784078615, 19784619558)
- Multiple consecutive runs exhibited the same hanging behavior
- Quality job (without syslog-ng installation step at that time) completed in 49 seconds
- Test jobs (with syslog-ng installation step) all hung

**Hypothesis confirmed**: The `sudo apt-get install -y syslog-ng` step is causing jobs to hang.
- Run 19784729004 with syslog-ng installation commented out: jobs completed in ~30 seconds
- Tests failed with `FileNotFoundError: 'syslog-ng'` because the engine needs it to run
- This confirms syslog-ng installation was the blocking step

**Root cause unknown**: Why `apt-get install syslog-ng` hangs is still unclear. Possible causes:
- Package repository issue
- Interactive prompts not suppressed
- GitHub Actions runner-specific issue
- Transient infrastructure problem

## When to Re-enable

Re-enable syslog-ng installation when:

1. **Tests actually use the engine** - When we write real tests that instantiate `PatterndbYaml` and call `.process()`
2. **Integration tests added** - Tests that verify end-to-end normalization with actual pattern matching
3. **Document tests complete** - When explain.md and other doc tests actually run the engine

## How to Re-enable

### Location

Both workflows need updating:
- `.github/workflows/test.yml` (lines 33-38)
- `.github/workflows/quality.yml` (lines 30-34)

### Uncomment these lines:

```yaml
- name: Install system dependencies
  run: |
    sudo apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y syslog-ng
```

### Why DEBIAN_FRONTEND=noninteractive?

Prevents apt from prompting for input during installation, which could cause hangs.

## Investigation Needed

If syslog-ng installation still hangs after re-enabling:

1. **Try alternative installation method**:
   ```yaml
   - name: Install syslog-ng
     run: |
       sudo apt-get update -qq
       sudo apt-get install -y --no-install-recommends syslog-ng-core
   ```

2. **Add timeout to installation step**:
   ```yaml
   - name: Install syslog-ng
     timeout-minutes: 5
     run: |
       sudo apt-get update
       sudo apt-get install -y syslog-ng
   ```

3. **Check GitHub Actions Ubuntu image issues**:
   - May be a transient issue with GitHub's Ubuntu runners
   - Check if specific package repositories are slow

4. **Consider alternatives**:
   - Use Docker container with syslog-ng pre-installed
   - Mock PatternMatcher for unit tests, only use real syslog-ng for integration tests
   - Install from different package source

## Related

- Issue was discovered when CI hung for 47+ minutes on PR #1
- Added job timeouts and concurrency cancellation as safeguards
- Tests currently pass without syslog-ng because they're all template placeholders
