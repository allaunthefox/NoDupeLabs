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
  - Docstring coverage validation

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

## Best Practices

1. **Commit Messages**: Use conventional commits for better CI integration
2. **Branch Protection**: Enable branch protection on `main` to require CI passes
3. **Code Reviews**: All pull requests should pass CI before merging
4. **Version Tags**: Use semantic versioning for releases (v1.0.0, v2.1.0, etc.)
