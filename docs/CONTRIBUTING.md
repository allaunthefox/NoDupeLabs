<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright (c) 2025 Allaun -->

# Contributing to NoDupeLabs

Thank you for your interest in contributing to NoDupeLabs! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation Standards](#documentation-standards)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Community Guidelines](#community-guidelines)

## Code of Conduct

This project adheres to a code of conduct that promotes a welcoming and inclusive environment. By participating, you agree to uphold this code.

## How to Contribute

### Ways to Contribute

1. **Code Contributions**: Implement new features, fix bugs, improve performance
1. **Documentation**: Improve existing documentation, write tutorials, update API docs
1. **Testing**: Write tests, improve test coverage, fix flaky tests
1. **Bug Reports**: Report issues, provide reproduction steps
1. **Feature Requests**: Suggest new features, provide use cases
1. **Code Reviews**: Review pull requests, provide constructive feedback

### Getting Started

1. Fork the repository
1. Clone your fork
1. Create a feature branch
1. Make your changes
1. Test thoroughly
1. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.9+
- Git
- pip
- Virtual environment (recommended)

### Setup Instructions

```bash
# Clone the repository
git clone https://github.com/allaunthefox/NoDupeLabs.git
cd NoDupeLabs

# Create and activate virtual environment (PEP 668 compliant)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Verify you're in the virtual environment
# (pip will now install to .venv, not system Python)
which pip  # Should show .venv/bin/pip

# Install package with dev dependencies (includes pytest, hypothesis, coverage)
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

**Note:** The `--break-system-packages` flag is NOT needed when using a virtual environment. 
The `venv` module creates an isolated environment that bypasses PEP 668 externally-managed restrictions.

### Running the Project

```bash
# Run the main application
python -m nodupe.core.main --help

# Run tests
pytest

# Run with coverage
pytest --cov=nodupe --cov-report=html
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use 4 spaces for indentation
- Maximum line length: 120 characters
- Use descriptive variable and function names
- Follow snake_case naming convention

### Type Annotations

- Use Python type hints for all functions and methods
- Use `typing` module for complex types
- Ensure all code passes `mypy` strict type checking

### Code Formatting

- Use `black` for code formatting
- Use `isort` for import sorting
- Configure your editor to run these tools automatically

### Documentation

- Use Google-style docstrings
- Document all public functions, classes, and methods
- Include examples where appropriate
- Keep documentation up-to-date with code changes

## Testing Requirements

### Test Coverage

- Minimum 80% line coverage for new code
- Minimum 70% branch coverage for new code
- All tests must pass before submitting a pull request
- Write unit tests, integration tests, and end-to-end tests as appropriate

### Test Structure

- Unit tests in `tests/core/` for core functionality
- Integration tests in `tests/integration/` for system-level testing
- Plugin tests in `tests/plugins/` for plugin-specific functionality
- Use `pytest` framework with appropriate markers

### Test Examples

```python
def test_example_function():
    """Test example function with various inputs."""
    # Test normal case
    result = example_function("input")
    assert result == "expected_output"

    # Test edge cases
    with pytest.raises(ValueError):
        example_function("invalid_input")
```

## Documentation Standards

### Documentation Structure

- Use Markdown format for all documentation
- Follow the existing documentation structure and style
- Use clear, concise language
- Include code examples where helpful
- Keep documentation up-to-date with implementation

### Documentation Types

1. **API Documentation**: Auto-generated from docstrings
1. **User Guides**: Step-by-step instructions for users
1. **Developer Guides**: Technical documentation for contributors
1. **Architecture Documentation**: System design and patterns
1. **Release Notes**: Changes and updates for each release

### Documentation Updates

- Update documentation when adding new features
- Update documentation when changing existing functionality
- Update documentation when fixing bugs that affect usage
- Keep documentation in sync with code changes

## Pull Request Process

### Before Submitting

1. Ensure all tests pass
1. Ensure code follows style guidelines
1. Ensure type checking passes
1. Update documentation as needed
1. Add tests for new functionality
1. Update changelog if significant changes

### Submitting a Pull Request

1. Push your changes to your fork
1. Open a pull request to the main repository
1. Provide a clear title and description
1. Reference any related issues
1. Include screenshots if UI changes
1. Request review from maintainers

### Pull Request Requirements

- All tests must pass
- Code must follow style guidelines
- Type checking must pass
- Documentation must be updated
- Tests must be added for new functionality
- Coverage must not decrease
- At least one approval from maintainers

## Issue Reporting

### Bug Reports

When reporting bugs, please include:

1. Clear description of the issue
1. Steps to reproduce
1. Expected behavior
1. Actual behavior
1. Environment information (OS, Python version, etc.)
1. Screenshots if applicable
1. Log files if applicable

### Feature Requests

When requesting features, please include:

1. Clear description of the feature
1. Use cases and benefits
1. Proposed implementation (if known)
1. Examples or mockups (if applicable)
1. Related issues or discussions

## Community Guidelines

### Communication

- Be respectful and professional
- Use inclusive language
- Provide constructive feedback
- Be open to different perspectives
- Follow the project's code of conduct

### Collaboration

- Work together on issues and features
- Help review pull requests
- Share knowledge and expertise
- Mentor new contributors
- Participate in discussions

### Recognition

- Contributions are valued and appreciated
- Significant contributors may be invited to join the core team
- Contributions are recognized in release notes
- Contributors are listed in project documentation

## Development Workflow

### Branching Strategy

- `main`: Stable production-ready code
- `develop`: Integration branch for features
- `feature/*`: Feature development branches
- `bugfix/*`: Bug fix branches
- `release/*`: Release preparation branches

### Commit Messages

- Use clear, descriptive commit messages
- Follow conventional commit format
- Reference issues when applicable
- Keep commits focused and atomic

### Code Reviews

- All changes require code review
- Reviews should be constructive and helpful
- Address review comments promptly
- Multiple iterations may be needed
- Final approval from maintainers required

## Getting Help

### Resources

- Project documentation
- Issue tracker
- Discussion forums
- Community chat
- Developer guides

### Support

- Check existing issues before reporting
- Provide detailed information when asking for help
- Be patient with responses
- Help others when you can

## License

By contributing to NoDupeLabs, you agree that your contributions will be licensed under the Apache 2.0 license.

---

**Thank you for contributing to NoDupeLabs!** Your contributions help make this project better for everyone.

For questions or additional guidance, please refer to the project documentation or contact the maintainers.
