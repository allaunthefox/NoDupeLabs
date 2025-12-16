# NoDupeLabs Test Suite

This directory contains the test suite for NoDupeLabs, using pytest as the testing framework.

## Test Structure

```text
tests/
├──__init__.py          # Package initializer
├── conftest.py          # Test configuration and fixtures
├── test_basic.py        # Basic functionality tests
├── run_tests.py         # Test runner script
├── core/                # Core module tests
├── integration/         # Integration tests
└── plugins/             # Plugin tests
```

## Running Tests

### Using pytest directly

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_basic.py

# Run with verbose output
python -m pytest -v

# Run with coverage
python -m pytest --cov=nodupe
```

## Using the test runner

```bash
## Run all tests
python tests/run_tests.py

## Run specific test file
python tests/run_tests.py tests/test_basic.py

## Run with verbose output
python tests/run_tests.py -v

# Run specific test markers
python tests/run_tests.py --unit
python tests/run_tests.py --integration
python tests/run_tests.py --slow
```

## Test Markers

The following markers are available for test selection:

- `unit`: Unit tests
- `integration`: Integration tests
- `slow`: Slow-running tests
- `e2e`: End-to-end tests

## Fixtures

### Available Fixtures

- `temp_dir`: Creates a temporary directory for testing
- `sample_files`: Creates sample files for duplicate detection testing
- `mock_config`: Provides mock configuration data

### Using Fixtures

```python
def test_example(temp_dir):
    # temp_dir is a Path object pointing to a temporary directory
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")
    assert test_file.exists()
```

## Configuration

Test configuration is defined in `pyproject.toml` under `[tool.pytest.ini_options]`.

Key settings:

- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`
- Default options: Coverage reporting, verbose output, short traceback
