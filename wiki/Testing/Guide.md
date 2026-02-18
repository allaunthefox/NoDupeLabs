# Testing Guide

## Running Tests

### Basic Usage

```bash
# Run all tests
pytest tests/ -v

# Run with verbose output
pytest tests/ -vv

# Stop on first failure
pytest -x
```

### Coverage

```bash
# Run with coverage
pytest --cov=nodupe tests/

# Generate HTML report
pytest --cov=nodupe --cov-report=html tests/

# View report
open htmlcov/index.html
```

### Test Organization

```
tests/
├── core/           # Core module tests
├── plugins/        # Plugin tests
├── integration/    # Integration tests
└── performance/   # Performance tests
```

### Running Specific Tests

```bash
# By file
pytest tests/core/test_database.py -v

# By keyword
pytest -k "database" -v

# By marker
pytest -m "slow" -v
```

## Test Coverage

| Area | Status |
|------|--------|
| Core | 9% (current; core-first tests added) |
| Target | 80% (CI gate) |

**Recent progress**
- Added focused unit tests for core API (decorators, ratelimit, validation, logging) and initial `ScanTool` / `ApplyTool` tests; smoke-imports expanded to exercise module-level code.

**Next priorities (short-term)**
1. Core `tool_system` tests — `loader`, `registry`, `lifecycle` (highest leverage)
2. Representative tool tests — `hashing`, `scanner_engine`, `commands`
3. Add more smoke-imports and small deterministic unit tests until coverage meets CI gate

## Writing Tests

Follow the existing patterns in `tests/`:

```python
def test_example():
    """Test description."""
    result = function_under_test()
    assert result == expected
```

## CI/CD

Tests run automatically on GitHub Actions for every push.
