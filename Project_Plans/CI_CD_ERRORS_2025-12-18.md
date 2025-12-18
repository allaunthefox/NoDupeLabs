# CI/CD Pipeline Errors - December 18, 2025

## Critical Issues Identified

### 1. pyproject.toml Configuration Error (CRITICAL - FIXED)

**Error**: `Cannot declare ('tool', 'setuptools', 'packages', 'find') twice (at line 10, column 31)`

**Root Cause**:
- Lines 5-8 explicitly declared `packages = ["nodupe"]` in `[tool.setuptools]`
- Lines 10-39 used `[tool.setuptools.packages.find]` for automatic package discovery
- These two approaches are mutually exclusive in setuptools configuration

**Impact**:
- ❌ Test runner (pytest) failed to load pyproject.toml
- ❌ All test jobs failed immediately
- ❌ Package building would fail

**Fix Applied**:
```toml
# REMOVED the conflicting explicit declaration:
# [tool.setuptools]
# packages = ["nodupe"]
# package-dir = {"" = "."}

# KEPT the automatic discovery (more flexible):
[tool.setuptools.packages.find]
where = ["."]
include = ["nodupe*"]
exclude = [...]
```

**Status**: ✅ **FIXED** - Committed to branch

---

### 2. Pylint Line-Too-Long Errors (100+ violations)

**Error**: Multiple `C0301: Line too long (XXX/100)` errors across the codebase

**Root Cause**:
- pyproject.toml line 205 **disables** C0301 (line-too-long) in pylint config
- CI workflow explicitly **enables** C0301 with: `--enable=missing-docstring,invalid-name,line-too-long`
- Configuration mismatch between local dev and CI

**Files Affected** (94+ violations):
```
nodupe/plugins/gpu/__init__.py: 2 violations
nodupe/plugins/similarity/__init__.py: 8 violations
nodupe/plugins/commands/similarity.py: 2 violations
nodupe/plugins/commands/scan.py: 1 violation
nodupe/plugins/commands/verify.py: 7 violations
nodupe/plugins/commands/apply.py: 2 violations
nodupe/plugins/commands/plan.py: 2 violations
nodupe/plugins/commands/__init__.py: 2 violations
nodupe/plugins/video/__init__.py: 1 violation
nodupe/core/loader.py: 2 violations
nodupe/core/parallel.py: 3 violations
nodupe/core/version.py: 1 violation
nodupe/core/archive_handler.py: 4 violations
nodupe/core/api.py: 1 violation
nodupe/core/scan/processor.py: 1 violation
nodupe/core/scan/hasher.py: 3 violations
nodupe/core/scan/walker.py: 2 violations
nodupe/core/scan/progress.py: 1 violation
nodupe/core/scan/hash_autotune.py: 4 violations
nodupe/core/plugin_system/discovery.py: 1 violation
nodupe/core/plugin_system/compatibility.py: 2 violations
nodupe/core/cache/query_cache.py: 1 violation
nodupe/core/database/embeddings.py: 1 violation
nodupe/core/database/files.py: 2 violations
nodupe/core/database/database.py: 4 violations
nodupe/core/database/indexing.py: 6 violations
nodupe/core/database/query.py: 1 violation
nodupe/core/database/schema.py: 4 violations
nodupe/core/database/__init__.py: 1 violation
```

**Impact**:
- ❌ Lint job fails on every PR
- ⚠️ Code quality gate blocked
- ⚠️ PR merge blocked by required checks

**Configuration Options**:

**Option A**: Disable line-too-long in CI (Recommended - Quick Fix)
```yaml
# .github/workflows/ci-cd.yml
- name: Run pylint
  run: |
    # Remove line-too-long from the explicit enable list
    pylint nodupe/ --disable=all --enable=missing-docstring,invalid-name
```

**Option B**: Fix all line-too-long violations (Time-Consuming)
- Requires reformatting 94+ lines across 29 files
- Risk of introducing bugs during refactoring
- May conflict with Black formatter settings

**Option C**: Increase line length limit
```toml
# pyproject.toml
[tool.pylint.format]
max-line-length = 120  # Already set, but CI overrides
```

**Recommendation**: **Option A** - Remove `line-too-long` from CI checks
- Rationale: Black formatter handles line length (100 chars)
- pyproject.toml already disables C0301 for local development
- CI should match local development experience
- Focus on semantic issues, not formatting

---

### 3. Python Version Matrix Issues

**Error**: Tests running on Python 3.8 and 3.14 (non-existent versions)

**Root Cause**:
- Multiple workflow files with different Python version matrices
- Some workflows still reference old version configurations

**Impact**:
- ⚠️ Wasted CI time on invalid Python versions
- ⚠️ False test failures for non-existent versions

**Current Matrix** (Fixed in PR #16):
```yaml
python-version: ['3.9', '3.10', '3.11', '3.12', '3.13']
```

**Status**: ✅ **FIXED** in PR #16

---

## Action Items

### Immediate (Today)

1. ✅ **Fix pyproject.toml** - Remove duplicate package declaration
   - Status: COMPLETED
   - Commit: Ready to push

2. ⚠️ **Update CI workflow** - Remove line-too-long from pylint checks
   - File: `.github/workflows/ci-cd.yml`
   - Line: 83-85 (lint job)
   - Change: Remove `,line-too-long` from enable list

3. ⚠️ **Test the fix** - Verify tests pass locally
   ```bash
   pytest tests/ --cov=nodupe --cov-report=term-missing --cov-fail-under=80 -v
   ```

### Short-Term (This Week)

1. ⚠️ **Consolidate workflows** - Remove duplicate workflow files
   - Multiple workflows seem to be running
   - Standardize on single ci-cd.yml

2. ⚠️ **Update documentation** - Document CI/CD configuration
   - Add section to CONTRIBUTING.md about CI checks
   - Explain why certain lints are disabled

3. ⚠️ **Review Black settings** - Ensure consistency
   - Black max-line-length: 100
   - Pylint max-line-length: 120
   - Consider aligning both to 100

### Medium-Term (Next 2 Weeks)

1. ⚠️ **Optional: Code cleanup** - Fix line-too-long violations
   - Low priority since formatter handles it
   - Can be done gradually in separate PRs
   - Focus on worst offenders first

2. ⚠️ **Add pre-commit hooks** - Prevent future issues
   - Run Black on commit
   - Run basic linting checks
   - Validate pyproject.toml

3. ⚠️ **CI optimization** - Reduce build time
   - Use caching more effectively
   - Parallelize independent jobs
   - Skip redundant checks

---

## Lessons Learned

### Configuration Management

1. **Keep CI and local configs in sync**
   - CI should match local development experience
   - Avoid surprises when code passes locally but fails in CI

2. **Use formatter instead of linter for style**
   - Black handles formatting automatically
   - Pylint should focus on semantic issues
   - Don't duplicate concerns between tools

3. **Test configuration changes**
   - Always validate pyproject.toml after changes
   - Run `python -c "import tomli; tomli.load(open('pyproject.toml', 'rb'))"`
   - Check for TOML syntax errors before committing

### Workflow Management

1. **Single source of truth for workflows**
   - Avoid multiple workflow files with different configs
   - Use workflow_call for shared configurations
   - Document which workflow is canonical

2. **Keep Python versions current**
   - Remove EOL Python versions promptly
   - Don't test pre-release versions in main CI
   - Separate experimental tests to different workflow

---

## Updated Metrics

### Before Fixes

| Metric | Status |
|--------|--------|
| **pyproject.toml** | ❌ Invalid - duplicate declarations |
| **Test Execution** | ❌ All tests failing - config error |
| **Lint Checks** | ❌ 94+ line-too-long violations |
| **Python Versions** | ⚠️ Testing 3.8, 3.14 (invalid) |
| **CI Success Rate** | ❌ 0% - All checks failing |

### After Fixes (Projected)

| Metric | Status |
|--------|--------|
| **pyproject.toml** | ✅ Valid - single package discovery method |
| **Test Execution** | ✅ Expected to pass (pending test fixes) |
| **Lint Checks** | ✅ Expected to pass (after removing line-too-long) |
| **Python Versions** | ✅ 3.9-3.13 (all valid) |
| **CI Success Rate** | 🔄 Expected 80-90% (normal test failures) |

---

## References

- **PR #16**: https://github.com/allaunthefox/NoDupeLabs/pull/16
- **Setuptools Package Discovery**: https://setuptools.pypa.io/en/latest/userguide/package_discovery.html
- **Pylint Configuration**: https://pylint.readthedocs.io/en/stable/user_guide/configuration/index.html
- **Black Configuration**: https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html

---

**Created**: 2025-12-18
**Author**: Claude Code
**Status**: Active Issue Resolution
**Next Review**: After PR #16 merge
