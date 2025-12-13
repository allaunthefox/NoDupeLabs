# GitHub Actions CI/CD Workflows

This directory contains the GitHub Actions workflows for the NoDupeLabs project.

## Available Workflows

### 1. Python Testing (`python-testing.yml`)
- **Trigger**: Push and pull requests to `main` branch
- **Purpose**: Run comprehensive Python tests across multiple Python versions
- **Features**:
  - Tests on Python 3.8, 3.9, 3.10, 3.11
  - Code coverage with pytest-cov
  - Codecov integration for coverage reporting

### 2. Code Quality Checks (`code-quality.yml`)
- **Trigger**: Push and pull requests to `main` branch
- **Purpose**: Enforce code quality standards
- **Features**:
  - Pylint with custom configuration
  - Black code formatting checks
  - isort import sorting checks
  - mypy type checking
  - Markdown linting
  - **100% docstring coverage requirement** (strict enforcement)
  - Detailed docstring coverage reporting

### 3. Deployment (`deployment.yml`)
- **Trigger**: Tag pushes (v*.*.*) and manual workflow dispatch
- **Purpose**: Automated deployment to PyPI and GitHub Pages
- **Features**:
  - PyPI package deployment
  - Documentation deployment to GitHub Pages
  - Sequential deployment (docs after PyPI)

### 4. Comprehensive CI (`ci-comprehensive.yml`)
- **Trigger**: Push and pull requests to `main` branch
- **Purpose**: All-in-one CI pipeline
- **Features**:
  - Parallel execution of testing and quality checks
  - Security scanning with bandit and safety
  - Integration tests
  - End-to-end validation

## Secrets Required

For full functionality, the following GitHub secrets should be configured:

- `CODECOV_TOKEN`: Codecov upload token
- `PYPI_API_TOKEN`: PyPI API token for package deployment

## Workflow Triggers

- **Push to main**: Runs all CI checks
- **Pull Request to main**: Runs all CI checks
- **Tag push (v*.*.*)**: Triggers deployment workflow
- **Manual dispatch**: Can trigger deployment workflow

## Strict Requirements Enforcement

### 🔒 Pull Request Requirements (Before Merging to Main)

**All of the following must pass for PR approval:**

1. **Python Testing**: All tests must pass across Python 3.8-3.11
2. **Code Quality Checks**:
   - **Pylint**: Minimum score of 10/10, all checks enabled (except fixme/line-too-long)
   - **Black**: Code formatting must be perfect
   - **isort**: Import sorting must be perfect
   - **mypy**: Strict type checking with no untyped definitions
   - **Docstrings**: 100% coverage required for all public classes and functions
3. **Comprehensive CI**: All parallel checks must pass
4. **Branch Protection**: Requires admin approval and code owner reviews

### 📋 Code Quality Standards

- **Linting**: Zero tolerance for linting violations
- **Formatting**: Perfect black/isort compliance required
- **Type Checking**: Strict mypy enforcement with full type coverage
- **Documentation**: 100% docstring coverage mandatory
- **Testing**: All tests must pass with good coverage

## Best Practices

1. **Run Locally First**: `pylint nodupe/ --fail-under=10.0 --enable=all`
2. **Format Before Committing**: `black nodupe/ tests/ && isort nodupe/ tests/`
3. **Type Check**: `mypy nodupe/ --strict`
4. **Document Everything**: Ensure 100% docstring coverage
5. **Test Thoroughly**: Run `pytest tests/ --cov=nodupe`
6. **Branch Protection**: Configure `.github/settings.yml` for strict PR requirements
7. **Version Tags**: Use semantic versioning for releases (v1.0.0, v2.1.0, etc.)
