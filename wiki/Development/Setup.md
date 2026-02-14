# Development Setup

## Prerequisites

- Python 3.9+
- Git
- pip

## Local Development

### Setup

```bash
# Clone repository
git clone https://github.com/allaunthefox/NoDupeLabs.git
cd NoDupeLabs

# Create venv
python -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e .

# Install dev dependencies
pip install pytest pytest-cov
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=nodupe tests/

# Run specific test file
pytest tests/core/test_database.py -v
```

### Code Quality

```bash
# Lint with pylint
pylint nodupe/

# Type checking
mypy nodupe/
```

## Tooling

Development tools are in `tools/`:

```bash
# Fix docstrings
python tools/core/fix_docstrings.py nodupe/

# API check
python tools/core/api_check.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## Documentation

All functions have docstrings. Run the docstring fixer:

```bash
python tools/core/fix_docstrings.py --apply nodupe/
```

See [Testing Guide](../Testing/Guide.md) for more on running tests.
