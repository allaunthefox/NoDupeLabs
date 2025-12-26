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
- `database_connection`: Provides in-memory SQLite database connection
- `mock_plugin`: Creates mock plugin for plugin system testing

### Using Fixtures

```python
def test_example(temp_dir):
    """Test example using temp_dir fixture."""
    # temp_dir is a Path object pointing to a temporary directory
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")
    assert test_file.exists()
    assert test_file.read_text() == "test content"

def test_database_operations(database_connection):
    """Test database operations using database_connection fixture."""
    cursor = database_connection.cursor()
    cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
    cursor.execute("INSERT INTO test (name) VALUES (?)", ("test",))
    cursor.execute("SELECT * FROM test")
    result = cursor.fetchone()
    assert result[1] == "test"
```

## Test Best Practices

### Robust Test Structure

```python
import pytest
from pathlib import Path
from nodupe.core.filesystem import safe_write, atomic_write

class TestFilesystemOperations:
    """Test suite for filesystem operations."""

    def test_safe_write_success(self, temp_dir):
        """Test successful safe file write operation."""
        test_file = temp_dir / "test.txt"
        content = "Hello, World!"

        # Execute
        safe_write(test_file, content)

        # Verify
        assert test_file.exists()
        assert test_file.read_text() == content
        assert test_file.stat().st_size == len(content)

    def test_safe_write_permission_error(self, temp_dir, mocker):
        """Test safe write handles permission errors gracefully."""
        test_file = temp_dir / "restricted.txt"
        content = "Should fail"

        # Mock permission error
        mocker.patch('builtins.open', side_effect=PermissionError("No permission"))

        # Execute and verify exception
        with pytest.raises(PermissionError):
            safe_write(test_file, content)

    def test_atomic_write_rollback(self, temp_dir, mocker):
        """Test atomic write rolls back on failure."""
        test_file = temp_dir / "atomic.txt"
        temp_file = temp_dir / f".{test_file.name}.tmp"

        # Mock failure during write
        def mock_write_side_effect(*args, **kwargs):
            if "atomic.txt.tmp" in str(args[0]):
                raise IOError("Simulated failure")
            return original_open(*args, **kwargs)

        original_open = builtins.open
        mocker.patch('builtins.open', side_effect=mock_write_side_effect)

        # Execute
        with pytest.raises(IOError):
            atomic_write(test_file, "content")

        # Verify no files created
        assert not test_file.exists()
        assert not temp_file.exists()
```

### Test Coverage Patterns

```python
def test_happy_path():
    """Test normal successful execution path."""
    result = function_under_test("valid_input")
    assert result == expected_output

def test_edge_cases():
    """Test boundary conditions and edge cases."""
    # Empty input
    result = function_under_test("")
    assert result == default_value

    # Maximum allowed input
    max_input = "x" * MAX_LENGTH
    result = function_under_test(max_input)
    assert len(result) == MAX_LENGTH

def test_error_conditions():
    """Test error handling and exception cases."""
    # Invalid input type
    with pytest.raises(TypeError):
        function_under_test(123)

    # None input
    with pytest.raises(ValueError):
        function_under_test(None)

def test_performance_constraints():
    """Test performance characteristics."""
    import time

    # Test execution time
    start_time = time.time()
    result = function_under_test(large_input)
    duration = time.time() - start_time

    assert duration < MAX_ALLOWED_TIME
    assert result == expected_output
```

## Test Organization

### Recommended Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Global fixtures and configuration
├── test_basic.py        # Basic functionality tests
├── run_tests.py         # Test runner script
├── core/
│   ├── __init__.py
│   ├── conftest.py      # Core-specific fixtures
│   ├── test_database.py # Database tests
│   ├── test_filesystem.py # Filesystem tests
│   ├── test_config.py   # Configuration tests
│   └── test_plugins.py  # Plugin system tests
├── integration/
│   ├── __init__.py
│   ├── conftest.py      # Integration test fixtures
│   ├── test_workflows.py # End-to-end workflows
│   └── test_cli.py      # CLI integration tests
└── plugins/
    ├── __init__.py
    ├── conftest.py      # Plugin test fixtures
    ├── test_commands.py # Command plugin tests
    └── test_similarity.py # Similarity plugin tests
```

## Configuration

Test configuration is defined in `pyproject.toml` under `[tool.pytest.ini_options]`.

### Key Settings:

- **Test files**: `test_*.py` - All test files follow this pattern
- **Test functions**: `test_*` - All test functions start with `test_`
- **Test classes**: `Test*` - All test classes start with `Test`
- **Coverage threshold**: 80% minimum line coverage
- **Branch coverage**: Enabled for comprehensive testing
- **Parallel execution**: Automatic based on CPU cores
- **Markers**: Support for unit, integration, performance, and stress tests

### Advanced Configuration:

```toml
[tool.pytest.ini_options]
addopts = """
    --cov=nodupe
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-fail-under=100
    --cov-branch
    -n auto
    -v
    --tb=short
    --durations=20
    --color=yes
    --junitxml=test_results.xml
"""
```

## Test Quality Metrics

### Coverage Requirements

- **Minimum line coverage**: 80% for all new code
- **Minimum branch coverage**: 70% for all new code
- **Core modules**: 90%+ coverage target
- **Critical paths**: 100% coverage required
- **Final Goal**: 100% unit test coverage for all code paths

### Ultimate Coverage Targets

| Coverage Type | Current | Phase 1 | Phase 2 | Phase 3 | Final |
|---------------|---------|---------|---------|---------|-------|
| **Line Coverage** | ~31% | >60% | >80% | >90% | **100%** |
| **Branch Coverage** | ~31% | >50% | >70% | >85% | **100%** |
| **Unit Tests** | ~31% | >60% | >80% | >95% | **100%** |
| **Integration Tests** | ~10% | >30% | >50% | >70% | >80% |
| **E2E Tests** | ~5% | >15% | >30% | >50% | >60% |

### Test Types and Distribution

| Test Type | Coverage Target | Purpose |
|-----------|----------------|---------|
| Unit Tests | 80-90% | Test individual functions and classes |
| Integration Tests | 70-80% | Test module interactions |
| End-to-End Tests | 60-70% | Test complete workflows |
| Performance Tests | N/A | Test execution speed and resource usage |
| Stress Tests | N/A | Test system under heavy load |

## Continuous Integration

### CI/CD Pipeline Configuration

The project uses GitHub Actions for automated testing with the following workflow:

```yaml
name: CI/CD Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11', '3.12', '3.13']
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests with coverage
        run: |
          pytest --cov=nodupe --cov-report=xml --cov-fail-under=80
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Quality Gates

All pull requests must pass the following quality gates:

1. **All tests pass**: No test failures allowed
2. **Coverage maintained**: Coverage must not decrease
3. **Minimum coverage**: 80% line coverage required
4. **Type checking**: MyPy must pass with no errors
5. **Code style**: Pylint score must be 10.0/10.0
6. **Documentation**: All new features must be documented

## Test Development Workflow

### Writing New Tests

1. **Identify test cases**: Determine what needs to be tested
2. **Write test first**: Follow TDD approach when possible
3. **Implement functionality**: Write code to make tests pass
4. **Add edge cases**: Test boundary conditions and error cases
5. **Verify coverage**: Ensure adequate test coverage
6. **Update documentation**: Document new test cases

### Test Review Checklist

- [ ] Tests follow naming conventions (`test_*` functions)
- [ ] Tests are properly categorized (unit/integration/e2e)
- [ ] Tests cover happy path, edge cases, and error conditions
- [ ] Tests use appropriate fixtures and mocks
- [ ] Tests are independent and isolated
- [ ] Tests have clear, descriptive docstrings
- [ ] Tests maintain or improve coverage
- [ ] Tests run efficiently (< 1s for unit tests)
- [ ] Tests follow project coding standards

## Performance Testing

### Benchmark Tests

```python
import pytest
import time
from nodupe.core.scan import FileWalker

def test_file_walker_performance(benchmark, temp_dir):
    """Benchmark file walker performance."""
    # Create test directory structure
    create_large_directory_structure(temp_dir, 1000, 3)

    # Benchmark the walker
    walker = FileWalker(str(temp_dir))
    result = benchmark(walker.walk)

    # Verify results
    assert len(result) == 1000
    assert benchmark.extra_info['min_rounds'] >= 5

def test_hashing_throughput(benchmark, temp_dir):
    """Benchmark hashing throughput."""
    # Create test files
    test_files = create_test_files(temp_dir, 100, 1024)

    # Benchmark hashing
    def hash_all_files():
        from nodupe.core.scan import FileHasher
        hasher = FileHasher()
        for file in test_files:
            hasher.hash_file(file)

    result = benchmark(hash_all_files)

    # Verify throughput (files/second)
    files_per_second = 100 / result
    assert files_per_second > 50  # Minimum 50 files/second
```

### Stress Testing

```python
def test_memory_usage_under_load():
    """Test memory usage with large datasets."""
    import tracemalloc

    tracemalloc.start()

    # Process large dataset
    process_large_dataset(10000)

    # Check memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert peak < MAX_MEMORY_USAGE
    assert current < MAX_MEMORY_USAGE / 2

def test_concurrent_operations():
    """Test thread safety and concurrency."""
    from concurrent.futures import ThreadPoolExecutor
    import threading

    # Test with multiple threads
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(process_file, f) for f in test_files]
        results = [f.result() for f in futures]

    # Verify all operations completed successfully
    assert all(r.success for r in results)
    assert len(results) == len(test_files)
```

## Test Maintenance

### Updating Existing Tests

1. **Review test coverage**: Identify gaps in existing tests
2. **Add missing test cases**: Cover new functionality and edge cases
3. **Refactor tests**: Improve test structure and readability
4. **Update fixtures**: Enhance test fixtures as needed
5. **Verify coverage**: Ensure coverage meets requirements
6. **Document changes**: Update test documentation

### Test Refactoring Patterns

```python
# Before: Duplicated test setup
def test_function_a():
    setup = create_complex_setup()
    result = function_a(setup)
    assert result == expected_a

def test_function_b():
    setup = create_complex_setup()  # Duplicated
    result = function_b(setup)
    assert result == expected_b

# After: Using fixtures
@pytest.fixture
def complex_setup():
    return create_complex_setup()

def test_function_a(complex_setup):
    result = function_a(complex_setup)
    assert result == expected_a

def test_function_b(complex_setup):
    result = function_b(complex_setup)
    assert result == expected_b
```

## Resources

### Test Utilities

- **pytest**: Primary testing framework
- **pytest-cov**: Coverage reporting
- **pytest-benchmark**: Performance benchmarking
- **pytest-mock**: Mocking support
- **pytest-xdist**: Parallel test execution
- **hypothesis**: Property-based testing

### Learning Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Python Testing with pytest](https://pragprog.com/titles/bopytest/)
- [Test-Driven Development with Python](https://www.obeythetestinggoat.com/)
- [Python Mocking and Patching](https://docs.python.org/3/library/unittest.mock.html)

### Best Practices

- Follow the **Arrange-Act-Assert** pattern
- Keep tests **fast, isolated, repeatable, self-validating, and timely**
- Test **behavior, not implementation**
- Use **descriptive test names** that explain what's being tested
- Keep tests **small and focused** on single responsibilities
- Avoid **test interdependencies**
- Use **fixtures** for complex setup and teardown
- **Mock external dependencies** to ensure test isolation
- **Test edge cases and error conditions**
- **Document test assumptions and requirements**
