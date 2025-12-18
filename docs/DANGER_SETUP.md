# Danger PR Validation System

## Overview

The Danger PR validation system provides automated quality checks for pull requests in the NoDupeLabs repository. It runs on every PR (opened, synchronized, or reopened) and provides immediate feedback to contributors about code quality, formatting standards, and potential issues.

## Components

### 1. Dangerfile
Location: `/Dangerfile`

The Dangerfile contains Python-based rules that validate:
- **PR Size**: Warns when PRs exceed 500 lines of code
- **Commit Format**: Ensures PR titles follow Conventional Commits
- **API Stability**: Flags modifications to core API files
- **TODO Tracking**: Warns about TODOs without issue references
- **Documentation**: Checks if documentation is updated when code changes
- **Dependencies**: Notifies when dependencies are modified

### 2. GitHub Actions Workflow
Location: `.github/workflows/pr-validation.yml`

The workflow:
- Triggers on PR events (opened, synchronized, reopened)
- Runs on Ubuntu latest
- Installs Python 3.10 and danger-python
- Executes Danger with GitHub token authentication

### 3. API Check Script
Location: `scripts/api_check.py`

A standalone tool that:
- Scans the codebase for API decorators (`@stable_api`, `@beta_api`, `@experimental_api`, `@deprecated`)
- Reports all decorated functions and classes
- Can be run manually to audit API stability

## Usage

### For Contributors
1. Create a pull request as usual
2. The Danger workflow will automatically run
3. Check the PR comments for any warnings or messages from Danger
4. Address any issues before requesting review

### For Maintainers
1. Review Danger warnings in PRs
2. Use the API check script to audit API changes:
   ```bash
   chmod +x scripts/api_check.py
   python3 scripts/api_check.py
   ```
3. Customize Danger rules by editing the Dangerfile

## Configuration

### GitHub Token
The workflow uses `secrets.GITHUB_TOKEN` which is automatically provided by GitHub Actions. No additional setup is required.

### Danger Rules Customization
Edit the `Dangerfile` to add or modify rules. Available functions:
- `warn(message)`: Creates a warning comment
- `fail(message)`: Creates a failing status (blocks merge)
- `message(message)`: Creates an informational message

### API Decorators
The system recognizes these decorators:
- `@stable_api`: Stable, backwards-compatible APIs
- `@beta_api`: Beta APIs that may change
- `@experimental_api`: Experimental APIs likely to change
- `@deprecated`: APIs scheduled for removal

## Testing Locally

### Install Danger
```bash
pip install danger-python
```

### Run Danger Locally
```bash
# Simulate CI environment
DANGER_GITHUB_API_TOKEN=your_token_here danger-python ci
```

### Test API Check Script
```bash
python3 scripts/api_check.py
```

## Troubleshooting

### Common Issues

1. **Danger not running on PR**
   - Ensure workflow file is in `.github/workflows/`
   - Check that PR events are configured correctly
   - Verify GitHub token permissions

2. **API check script not finding decorators**
   - Ensure decorators use correct naming
   - Check file extensions (.py files only)
   - Verify script has execute permissions

3. **False positives in TODO detection**
   - Update the regex pattern in Dangerfile
   - Add specific file exclusions if needed

## Extending the System

### Adding New Rules
1. Edit the `Dangerfile`
2. Add new validation logic using Danger's API
3. Test locally before committing

### Custom API Decorators
1. Add new decorator names to `scripts/api_check.py`
2. Update the AST parsing logic if needed
3. Document the new decorator in this file

### Integration with Other Tools
The system can be extended to:
- Run linters (flake8, black, mypy)
- Check test coverage
- Validate security policies
- Enforce coding standards

## Best Practices

1. **Keep PRs Small**: Aim for <500 lines to facilitate review
2. **Use Conventional Commits**: Follow the established format
3. **Document Changes**: Update docs when modifying code
4. **Reference Issues**: Link TODOs to specific issues
5. **Review API Changes**: Pay special attention to stable API modifications

## Future Enhancements

Potential improvements:
- Integration with code coverage tools
- Automated changelog generation
- Security vulnerability scanning
- Performance impact analysis
- Dependency vulnerability checks

## Support

For issues with the Danger setup:
1. Check the GitHub Actions logs
2. Review this documentation
3. Consult the Danger-Python documentation
4. Create an issue in the repository

## References

- [Danger-Python Documentation](https://danger-python.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [NoDupeLabs Contributing Guide](../CONTRIBUTING.md)
