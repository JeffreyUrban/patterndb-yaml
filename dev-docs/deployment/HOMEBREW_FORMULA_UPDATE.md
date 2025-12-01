# Homebrew Formula Update - Add syslog-ng Dependency

This document describes the update needed to the Homebrew formula to automatically install syslog-ng.

## Location

The formula is maintained in a separate repository:
**https://github.com/JeffreyUrban/homebrew-patterndb-yaml**

File: `Formula/patterndb-yaml.rb`

## Required Change

Add `syslog-ng` as a runtime dependency in the formula.

### Current Formula Structure

```ruby
class PatterndbYaml < Formula
  include Language::Python::Virtualenv

  desc "YAML-based pattern matching for log normalization using syslog-ng patterndb"
  homepage "https://github.com/JeffreyUrban/patterndb-yaml"
  url "https://files.pythonhosted.org/packages/.../patterndb_yaml-X.Y.Z.tar.gz"
  sha256 "..."
  license "MIT"

  # Python dependencies would be here...

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "patterndb-yaml", shell_output("#{bin}/patterndb-yaml --version")
  end
end
```

### Updated Formula (Add This Line)

Add the following line after the `license` line and before any resource declarations:

```ruby
class PatterndbYaml < Formula
  include Language::Python::Virtualenv

  desc "YAML-based pattern matching for log normalization using syslog-ng patterndb"
  homepage "https://github.com/JeffreyUrban/patterndb-yaml"
  url "https://files.pythonhosted.org/packages/.../patterndb_yaml-X.Y.Z.tar.gz"
  sha256 "..."
  license "MIT"

  depends_on "syslog-ng"  # ← ADD THIS LINE

  # Python dependencies...

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "patterndb-yaml", shell_output("#{bin}/patterndb-yaml --version")
    # Verify syslog-ng is available
    assert_match "syslog-ng", shell_output("syslog-ng --version")
  end
end
```

## What This Does

When users run `brew install patterndb-yaml`:

1. **Homebrew installs syslog-ng first** (if not already installed)
2. Then installs patterndb-yaml
3. **Both packages are linked** - if users uninstall patterndb-yaml but have other tools using syslog-ng, syslog-ng remains
4. **Automatic updates**: `brew upgrade patterndb-yaml` will also upgrade syslog-ng if needed

## Testing the Updated Formula

### Local Testing

```bash
# Clone the homebrew tap
git clone https://github.com/JeffreyUrban/homebrew-patterndb-yaml
cd homebrew-patterndb-yaml

# Edit Formula/patterndb-yaml.rb to add the dependency

# Test installation from local formula
brew install --build-from-source ./Formula/patterndb-yaml.rb

# Verify both are installed
brew list patterndb-yaml
brew list syslog-ng

# Test the CLI
patterndb-yaml --version
syslog-ng --version

# Run formula tests
brew test patterndb-yaml

# Uninstall for clean state
brew uninstall patterndb-yaml
```

### After Merging to Repository

```bash
# Update tap
brew update

# Install from tap
brew install jeffreyurban/patterndb-yaml/patterndb-yaml

# Verify installation
brew deps jeffreyurban/patterndb-yaml/patterndb-yaml
# Should show: syslog-ng
```

## Dependency Syntax Reference

### Basic Runtime Dependency (Default)
```ruby
depends_on "syslog-ng"
```

This is a runtime dependency - syslog-ng will be installed and must remain installed for patterndb-yaml to work.

### Alternative: Build-Only Dependency
```ruby
depends_on "syslog-ng" => :build
```

This would only install syslog-ng during build, then uninstall it. **Don't use this** - we need syslog-ng at runtime.

### Alternative: Optional Dependency
```ruby
depends_on "syslog-ng" => :optional
```

This makes syslog-ng optional. **Don't use this** - it's required for patterndb-yaml to function.

## Additional Enhancements (Optional)

### Enhanced Test Block

Consider adding a more comprehensive test:

```ruby
test do
  # Test CLI version
  assert_match "patterndb-yaml", shell_output("#{bin}/patterndb-yaml --version")

  # Verify syslog-ng is available
  assert_match "syslog-ng", shell_output("syslog-ng --version")

  # Test basic functionality
  (testpath/"rules.yaml").write <<~EOS
    rules:
      - name: test_rule
        pattern:
          - text: "test"
        output: "matched"
  EOS

  output = pipe_output("#{bin}/patterndb-yaml --rules #{testpath}/rules.yaml", "test message")
  assert_match "matched", output
end
```

## Automation Note

The formula update workflow (`.github/workflows/update-formula.yml` in the homebrew tap) will need to preserve the `depends_on "syslog-ng"` line when automatically updating versions.

Make sure the workflow doesn't overwrite the entire formula, but only updates:
- `url`
- `sha256`
- Version number in test block (if present)

## References

- [Homebrew Formula Cookbook - Dependencies](https://docs.brew.sh/Formula-Cookbook#specifying-other-formulae-as-dependencies)
- [syslog-ng Homebrew Formula](https://formulae.brew.sh/formula/syslog-ng)
- [Formula Cookbook - Testing](https://docs.brew.sh/Formula-Cookbook#add-a-test-to-the-formula)

## Timeline

1. **Before next release**: Update the formula in homebrew-patterndb-yaml repository
2. **Test locally**: Verify the dependency installation works
3. **Document in release notes**: Mention that Homebrew now auto-installs syslog-ng
4. **Update automation**: Ensure formula update workflow preserves the dependency
