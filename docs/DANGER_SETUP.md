# Danger PR Validation System

## Overview

The Danger PR validation system provides automated quality checks for pull requests in the NoDupeLabs repository.

## Components

### 1. Dangerfile
Location: `/Dangerfile`

The Dangerfile contains Python-based rules that validate:
- **PR Size**: Warns when PRs exceed 500 lines of code
- **Commit Format**: Ensures PR titles follow Conventional Commits
- **API Stability**: Flags modifications to core API files
- **TODO Tracking**: Warns about TODOs without issue references
- **Documentation**: Checks if documentation is updated when code changes

### 2. GitHub Actions Workflow
Location: `.github/workflows/pr-validation.yml`

The workflow:
- Triggers on PR events (opened, synchronized, reopened)
- Runs on Ubuntu latest
- Installs Python 3.10 and danger-python

### 3. API Check Script
Location: `tools/core/api_check.py`

A standalone tool that scans the codebase for API decorators.

## Usage

### For Contributors
1. Create a pull request as usual
2. The Danger workflow will automatically run
3. Check the PR comments for any warnings

### For Maintainers
1. Review Danger warnings in PRs
2. Use the API check script:
   ```bash
   python3 tools/core/api_check.py
   ```

## API Decorators

The system recognizes:
- `@stable_api`: Stable, backwards-compatible APIs
- `@beta_api`: Beta APIs that may change
- `@experimental_api`: Experimental APIs
- `@deprecated`: APIs scheduled for removal

## Testing

### Run Danger Locally
```bash
DANGER_GITHUB_API_TOKEN=your_token danger-python ci
```

### Test API Check Script
```bash
python3 tools/core/api_check.py
```

## Troubleshooting

1. **Danger not running**: Check workflow file location and GitHub token permissions
2. **Script not finding decorators**: Verify decorator naming and file extensions

## References

- [Danger-Python Documentation](https://danger-python.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
