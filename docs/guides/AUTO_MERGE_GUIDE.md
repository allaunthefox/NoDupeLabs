# 🚀 Safe Auto-Merge Configuration Guide

## Overview

This guide explains the safe auto-merge system configured for the NoDupeLabs repository. The system is designed to automatically merge pull requests when they meet specific safety criteria, while ensuring code quality and preventing conflicts.

## Configuration File

The auto-merge configuration is defined in `.github/auto-merge-config.json` with the following safety parameters:

## 🔒 Safety Requirements

### Basic Requirements (All PRs)

- **CI Success**: All required checks must pass (CI, Tests, Coverage, Linting)
- **No Conflicts**: PR must be up-to-date with main branch
- **Conversation Resolved**: All discussions must be resolved
- **Semantic Title**: PR title must follow conventional commits format
- **Code Owner Approval**: Required for files with CODEOWNERS

### Auto-Merge Strategies

| PR Type | Auto-Merge | Approvals Needed | Size Limit | Additional Requirements |
|---------|------------|------------------|------------|-------------------------|
| **Dependency Updates** | ✅ Yes | 0 | Small (<100 lines) | - |
| **Documentation** | ✅ Yes | 1 | Medium (<500 lines) | - |
| **Bug Fixes** | ✅ Yes | 1 | Medium (<500 lines) | Tests required |
| **Features** | ❌ No | 2 | Large (<1000 lines) | Tests + Documentation |
| **Breaking Changes** | ❌ No | 2 | Any | Extensive tests + Changelog |

## 🎯 Auto-Merge Categories

### 1. Dependency Updates (Auto-Merge Enabled)
- GitHub Dependabot PRs
- Security updates
- Minor version bumps
- No manual approval required
- Automatically merged when CI passes

### 2. Documentation (Auto-Merge Enabled)
- README updates
- Documentation improvements
- Typo fixes
- 1 approval required
- Automatically merged when approved and CI passes

### 3. Bug Fixes (Auto-Merge Enabled)
- Critical bug fixes
- Hotfixes
- 1 approval required
- Tests must be included
- Automatically merged when approved and CI passes

### 4. Features (Manual Merge Required)
- New functionality
- Major enhancements
- 2 approvals required
- Tests and documentation required
- Manual review and merge

### 5. Breaking Changes (Manual Merge Required)
- API changes
- Major version updates
- 2 approvals required
- Extensive testing required
- Changelog entry required
- Manual review and merge

## 🔧 How to Use Auto-Merge

### For Contributors

1. **Create PR with proper title** (follow conventional commits)
2. **Ensure CI passes** (all checks green)
3. **Resolve all conversations**
4. **Add appropriate labels** (bug, documentation, dependencies, etc.)
5. **Wait for auto-merge** (if eligible) or request reviews

### For Maintainers

1. **Review PR eligibility** based on type and size
2. **Add/remove labels** to control auto-merge behavior
3. **Monitor auto-merge queue**
4. **Override when necessary** for critical PRs

## 📋 Auto-Merge Labels

| Label | Effect |
|-------|--------|
| `automerge:ready` | Mark PR as ready for auto-merge |
| `automerge:block` | Prevent auto-merge |
| `size:small` | Small PR (<100 lines) |
| `size:medium` | Medium PR (<500 lines) |
| `size:large` | Large PR (<1000 lines) |
| `type:dependencies` | Dependency update |
| `type:documentation` | Documentation change |
| `type:bug` | Bug fix |
| `type:feature` | New feature |
| `type:breaking` | Breaking change |

## ⚠️ Safety Features

### Branch Protection
- Prevent force pushes to main
- Require status checks to pass
- Block branch deletions
- Enforce code owner approvals

### Conflict Prevention
- Linear history not enforced (allow merge commits)
- Require PRs to be up-to-date with main
- Automatic conflict detection

### Quality Gates
- All CI checks must pass
- Required approvals based on PR type
- Documentation requirements for features
- Test coverage requirements

## 📊 Monitoring and Notifications

- **Success**: Slack + Email notifications
- **Failure**: Slack + Email + GitHub notifications
- **Manual Review Required**: Slack + GitHub notifications

## 🔄 Manual Override

Maintainers can manually override auto-merge behavior:

```bash
# Enable auto-merge for a specific PR
gh pr merge <PR_NUMBER> --auto

# Disable auto-merge
gh pr edit <PR_NUMBER> --add-label "automerge:block"

# Force merge (emergency only)
gh pr merge <PR_NUMBER> --merge
```

## 🎓 Best Practices

1. **Keep PRs small** for better auto-merge eligibility
2. **Write good commit messages** following conventional commits
3. **Add tests** for all bug fixes and features
4. **Update documentation** for new features
5. **Monitor CI status** and fix failures promptly
6. **Use labels appropriately** to control merge behavior

## 📝 Examples

### Auto-Merge Eligible PR
```markdown
# Title: fix: resolve memory leak in file processor
# Labels: type:bug, size:small, automerge:ready
# Changes: <100 lines
# Tests: Included
# Approvals: 1 required
```

### Manual Merge Required PR
```markdown
# Title: feat: add new similarity detection algorithm
# Labels: type:feature, size:large, automerge:block
# Changes: >500 lines
# Tests: Required
# Documentation: Required
# Approvals: 2 required
```

## 🔧 Configuration Reference

```json
{
  "auto_merge_config": {
    "enabled": true,
    "requirements": {
      "min_approvals": 1,
      "ci_success": true,
      "required_checks": ["CI", "Tests", "Coverage", "Linting"],
      "no_conflicts": true,
      "conversation_resolved": true,
      "semantic_title": true
    }
  }
}
```

## 📚 Related Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md) - PR template
- [.github/auto-merge-config.json](.github/auto-merge-config.json) - Configuration file

---

**Safe auto-merge is now configured and ready to use!** 🎉
