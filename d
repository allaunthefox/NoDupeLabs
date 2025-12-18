# Danger PR Validation Setup

## Overview

This document describes the Danger integration for automated PR validation in NoDupeLabs. Danger helps enforce code quality standards, maintain documentation, and ensure proper PR formatting.

## Components

### 1. Dangerfile

The `Dangerfile` at the root of the repository contains the validation rules that run on every PR:

- **PR Size Check**: Warns when PRs exceed 500 lines
- **Conventional Commits**: Validates PR titles follow conventional commit format
- **API Stability**: Flags changes to `nodupe/core/api.py`
- **TODO Tracking**: Warns about new TODOs without issue references
- **Documentation**: Reminds to update docs when Python files change
- **Dependencies**: Flags dependency changes in `pyproject.toml`

### 2. GitHub Actions Workflow

`.github/workflows/pr-validation.yml` runs Danger on every PR:

```yaml
name: PR Validation
on:
  pull_request:
    types: [opened, synchronize, reopened]
```

### 3. API Stability Checker

`scripts/api_check.py` scans the codebase for API stability decorators:

```bash
python3 scripts/api_check.py
```

This tool identifies functions/classes marked with:
- `@stable_api` - Stable public API
- `@beta_api` - Beta features
- `@experimental_api` - Experimental features
- `@deprecated` - Deprecated features

## Usage

### For Contributors

When you open a PR, Danger will automatically:

1. Comment on the PR with warnings/suggestions
2. Check PR title format (e.g., `feat: add new feature`)
3. Remind you about documentation updates
4. Flag large PRs that should be split

### PR Title Format

Follow Conventional Commits:

```
type(scope): description

Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
```

Examples:
- `feat: add archive support`
- `fix(cli): resolve argument parsing bug`
- `docs: update API documentation`

### Running Locally

Install Danger:

```bash
pip install danger-python
```

Run checks:

```bash
danger-python local
```

## API Stability

The API module (`nodupe/core/api.py`) provides decorators for marking API stability:

```python
from nodupe.core.api import stable_api, beta_api, experimental_api

@stable_api
def important_function():
    """This function is part of the stable public API"""
    pass

@beta_api
def new_feature():
    """This feature is in beta"""
    pass
```

### Checking API Usage

Run the API checker to see all decorated APIs:

```bash
python3 scripts/api_check.py
```

## Configuration

### Danger Rules

Edit `Dangerfile` to modify validation rules. The file uses Python syntax:

```python
from danger_python import Danger, fail, warn, message

danger = Danger()

# Add your custom rules
if some_condition:
    warn("Your warning message")
```

### GitHub Actions

The PR validation workflow runs automatically. To modify:

1. Edit `.github/workflows/pr-validation.yml`
2. Adjust Python version, dependencies, or trigger conditions
3. Commit and push changes

## Dependencies

- **danger-python**: Core Danger framework for Python
- **Python 3.10+**: Required for the validation scripts

## Troubleshooting

### Danger Not Running

- Check that `GITHUB_TOKEN` is available in the workflow
- Verify the workflow file syntax is correct
- Ensure the PR is from a branch (not a fork without secrets access)

### API Checker Issues

- Verify Python files use decorators from `nodupe.core.api`
- Check that AST parsing doesn't fail on syntax errors
- Ensure script has execute permissions: `chmod +x scripts/api_check.py`

## Future Enhancements

Potential improvements to the Danger setup:

1. **API Breaking Change Detection**: Compare decorated APIs between branches
2. **Test Coverage Requirements**: Enforce minimum coverage for new code
3. **License Header Checks**: Verify all files have proper license headers
4. **Commit Message Validation**: Check individual commit messages
5. **Changelog Updates**: Ensure CHANGELOG.md is updated

## References

- [Danger Python Documentation](https://danger.systems/python/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
