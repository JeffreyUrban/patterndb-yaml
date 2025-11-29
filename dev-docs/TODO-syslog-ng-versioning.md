# TODO: syslog-ng Version Management Strategy

## Current Situation

**Problem**: Our application currently hardcodes `@version: 4.10` in the syslog-ng configuration, but the installed version may vary depending on the environment.

**Observed behavior**:
- Ubuntu 24.04 default repos: syslog-ng 4.3
- Official syslog-ng repo: Latest stable version (TBD - awaiting CI results)
- Local development: Version varies by OS and installation method

**Current approach**: We've added the official syslog-ng repository to CI to get the latest stable version instead of Ubuntu's older 4.3.

## What We Actually Need from syslog-ng

Our usage is minimal - we only use these features:
1. **pipe source/destination** - Read from/write to named pipes (FIFOs)
2. **rewrite (set)** - Set PROGRAM field to "claude"
3. **db-parser** - Pattern matching against patterndb XML
4. **template** - Format output MESSAGE

**All of these are available in `syslog-ng-core`** - the minimal package.

**Package differences**:
- **syslog-ng-core**: Core daemon with standard plugins (includes db-parser) - **This is all we need**
- **syslog-ng**: Metapackage that pulls in all available plugins and modules (SQL, NoSQL, etc.)

**Recommendation**: Use `syslog-ng-core` for minimal installation footprint.

## Strategic Questions to Answer

### 1. Version Detection vs Configuration

**Option A: Dynamic version detection**
- Detect installed syslog-ng version at runtime
- Generate config with matching `@version` directive
- **Pros**: Works with any syslog-ng version
- **Cons**: Adds complexity, requires version parsing

**Option B: Require minimum version**
- Document minimum required version (e.g., 4.10+)
- Fail with clear error if version too old
- **Pros**: Simpler, predictable behavior
- **Cons**: May exclude users with older systems

**Option C: Test against multiple versions**
- CI matrix testing with different syslog-ng versions
- Document compatibility range
- **Pros**: Know what works, can support range
- **Cons**: CI complexity, maintenance burden

### 2. Installation Control

**Where should we control syslog-ng version?**

**CI/CD**:
- ✅ Already using official repo for latest stable
- Should we pin to specific version or track latest stable?
- Should we test multiple versions in matrix?

**Documentation**:
- Installation instructions for users
- Should we recommend official repo or allow system packages?
- Version requirements and compatibility notes

**Code**:
- Version detection and validation
- Feature detection vs version checking
- Graceful degradation for missing features

### 3. Configuration Compatibility

**Current issue**: `@version` directive must match or be lower than installed version

**Options**:
1. **Detect version and generate appropriate config**
   ```python
   version = detect_syslog_ng_version()
   config = f"@version: {version}\n..."
   ```

2. **Use conservative version**
   - Use lowest supported version (e.g., 4.3)
   - Only use features available in that version
   - Trade features for compatibility

3. **Feature-based configuration**
   - Detect available features rather than version
   - Generate config based on capabilities
   - Most robust but most complex

## Immediate Actions Needed

1. **Wait for CI results** to see what version the official repo provides
2. **Document minimum version requirement** once we confirm what works
3. **Add version detection** to PatternMatcher for better error messages
4. **Decide on version strategy** based on CI results and user needs

## Implementation Options

### Option 1: Dynamic Version Detection (Recommended)

```python
class PatternMatcher:
    def __init__(self, pdb_path: Path):
        self.pdb_path = pdb_path
        self.syslog_ng_version = self._detect_version()
        self._setup()

    def _detect_version(self) -> str:
        """Detect installed syslog-ng version."""
        result = subprocess.run(
            ["syslog-ng", "--version"],
            capture_output=True,
            text=True,
        )
        # Parse version from output
        # Return version string like "4.10"

    def _setup(self) -> None:
        # Use self.syslog_ng_version in config
        config = f"@version: {self.syslog_ng_version}\n..."
```

**Pros**:
- Works with any version automatically
- Clear error if syslog-ng not installed
- Can log version for debugging

**Cons**:
- More complex
- Need to parse version output
- Version detection could fail

### Option 2: Minimum Version Check

```python
MIN_SYSLOG_NG_VERSION = "4.3"

def _check_version(self) -> None:
    """Verify syslog-ng meets minimum version."""
    version = self._detect_version()
    if version < MIN_SYSLOG_NG_VERSION:
        raise RuntimeError(
            f"syslog-ng {MIN_SYSLOG_NG_VERSION}+ required, found {version}"
        )
```

**Pros**:
- Simple to implement
- Clear error messages
- Guarantees features available

**Cons**:
- Still excludes some users
- Requires keeping MIN_VERSION updated
- Manual testing of each version

### Option 3: CI Version Matrix

Add to `.github/workflows/test.yml`:

```yaml
strategy:
  matrix:
    python-version: ["3.9", "3.14"]
    syslog-ng-version: ["4.3", "4.10", "latest"]
```

**Pros**:
- Know exactly what versions work
- Catch version-specific issues
- Can document compatibility range

**Cons**:
- Significant CI complexity
- Longer CI times
- How to install specific versions?

## Questions for Discussion

1. **What syslog-ng features do we actually need?**
   - Are we using anything specific to newer versions?
   - Can we work with older versions like 4.3?

2. **Who are our users?**
   - System administrators with existing syslog-ng?
   - Users installing fresh for this tool?
   - Docker/container users?

3. **What's our support policy?**
   - Support latest N versions?
   - Support versions available in LTS distros?
   - Recommend installation method?

4. **How important is version flexibility vs simplicity?**
   - Is dynamic detection worth the complexity?
   - Or should we just document "install from official repo"?

## Related Files

- `src/patterndb_yaml/pattern_filter.py` - PatternMatcher class with hardcoded version
- `.github/workflows/test.yml` - CI with official syslog-ng repo
- `.github/workflows/quality.yml` - CI with official syslog-ng repo
- `dev-docs/TODO-restore-syslog-ng.md` - Investigation of CI hanging issues

## Next Steps

1. ✅ Install from official repo in CI (completed)
2. ⏳ Wait for CI results to see actual version
3. ⏳ Decide on versioning strategy based on needs
4. ⏳ Implement chosen approach
5. ⏳ Update documentation with version requirements
6. ⏳ Remove debugging output once confirmed working
