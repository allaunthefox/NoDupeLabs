# Contributing to NoDupeLabs

Thank you for your interest in contributing to NoDupeLabs! This guide provides clear, reproducible instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Documentation Standards](#documentation-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Release Process](#release-process)

## Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/) code of conduct. Please be respectful and considerate in all interactions.

## Getting Started

### Prerequisites

- Python 3.9+
- Git
- pip
- Virtual environment tool (venv, virtualenv, etc.)

### Recommended Tools

- VS Code with Python extension
- MyPy for type checking
- Flake8 for linting
- Pytest for testing
- Interrogate for docstring coverage

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/allaunthefox/NoDupeLabs.git
cd NoDupeLabs
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows
```

### 3. Install Development Dependencies

```bash
pip install --upgrade pip
pip install -r dev-requirements.txt
```

### 4. Install NoDupeLabs in Editable Mode

```bash
pip install -e .
```

### 5. Verify Installation

```bash
nodupe --help
```

## Code Style Guidelines

### Python Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use 4 spaces for indentation
- Limit lines to 88 characters
- Use descriptive variable and function names
- Follow [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) for docstrings

### Type Annotations

- Use Python type hints for all functions and methods
- Import from `typing` module when needed
- Use `Any` sparingly - prefer specific types

### Import Organization

- Standard library imports first
- Third-party imports next
- Local application imports last
- Group imports with blank lines

## Documentation Standards

### Module Docstrings

Every module must have a comprehensive docstring following this format:

```python
"""Brief one-line summary.

Detailed description spanning multiple paragraphs if needed. Explain
the module's purpose, key concepts, and architecture.

Key Features:
    - Feature 1
    - Feature 2

Dependencies:
    - Required dependency
    - Optional dependency (optional, falls back to X)

Example:
    >>> from nodupe import module
    >>> result = module.function()
"""
```

### Function/Method Docstrings

Every public function and method must have complete docstrings:

```python
def function(param1: str, param2: int = 0) -> bool:
    """Brief one-line summary.

    Detailed explanation of what the function does, including any
    important behavior, side effects, or usage notes.

    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2 (default: 0)

    Returns:
        Description of return value

    Raises:
        ExceptionType: When and why this exception is raised

    Example:
        >>> result = function("test", 5)
        True
    """
```

### Class Docstrings

Every class must have comprehensive docstrings:

```python
class ClassName:
    """Brief one-line summary.

    Detailed description of the class purpose, usage patterns,
    and important attributes.

    Attributes:
        attr1: Description of attribute 1
        attr2: Description of attribute 2

    Example:
        >>> obj = ClassName()
        >>> obj.method()
    """
```

## Testing Requirements

### Test Coverage

- All new code must have unit tests
- Aim for 90%+ test coverage
- Include both happy path and edge cases
- Test error conditions and exceptions

### Test Structure

```python
def test_function_name():
    """Test description."""
    # Setup
    input_data = "test"

    # Exercise
    result = function_under_test(input_data)

    # Verify
    assert result == expected_value

    # Teardown (if needed)
```

### Test Markers

Use appropriate pytest markers:
- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Tests that take >1 second
- `@pytest.mark.requires_model` - Tests requiring ML models
- `@pytest.mark.requires_ffmpeg` - Tests requiring FFmpeg

## Pull Request Process

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Follow code style guidelines
- Add comprehensive documentation
- Write tests for new functionality
- Update existing tests if needed

### 3. Run Quality Checks

```bash
# Run linter
flake8 nodupe/

# Run type checker
mypy nodupe/

# Check docstring coverage
interrogate -vv nodupe/ --fail-under 100

# Run tests
pytest tests/ -v -m "not slow and not integration"
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

Use conventional commit messages:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Build process or auxiliary tool changes

### 5. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 6. Create Pull Request

1. Go to the NoDupeLabs GitHub repository
2. Click "New Pull Request"
3. Select your feature branch
4. Fill out the PR template completely
5. Request review from maintainers

## Issue Reporting

### Bug Reports

When reporting bugs, please include:
- Clear description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)
- Relevant log output or error messages

### Feature Requests

When requesting features, please include:
- Clear description of the proposed feature
- Use case and justification
- Potential implementation approach
- Examples of similar features in other tools

## Release Process

### Versioning

NoDupeLabs follows [Semantic Versioning](https://semver.org/):
- `MAJOR` - Breaking changes
- `MINOR` - New features (backward compatible)
- `PATCH` - Bug fixes (backward compatible)

### Release Checklist

1. Update `CHANGELOG.md` with all changes since last release
2. Update version in `pyproject.toml`
3. Create GitHub release with changelog
4. Tag the release with version number
5. Push tags to repository

### Creating a Release

```bash
# Update version
sed -i 's/version = ".*"/version = "0.2.0"/' pyproject.toml

# Commit version change
git add pyproject.toml
git commit -m "chore: bump version to 0.2.0"

# Tag release
git tag v0.2.0
git push origin v0.2.0
```

## Getting Help

If you need help with contributing:
- Check existing issues and pull requests
- Review the documentation
- Ask questions in GitHub discussions
- Contact maintainers for guidance

## Code Review Guidelines

### For Contributors

- Be open to feedback and suggestions
- Address all review comments
- Make requested changes promptly
- Keep pull requests focused and small

### For Reviewers

- Be constructive and respectful
- Provide clear, actionable feedback
- Focus on code quality and maintainability
- Approve when requirements are met

## Documentation Updates

When adding new features or making changes:
- Update relevant documentation
- Add examples and usage instructions
- Update API documentation if needed
- Ensure docstrings are complete and accurate

## Continuous Integration

All pull requests must pass CI checks:
- Flake8 linting
- MyPy type checking
- Interrogate docstring coverage
- Pytest test suite

## License

By contributing to NoDupeLabs, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).
