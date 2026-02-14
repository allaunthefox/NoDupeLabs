# NoDupeLabs Test Utilities

This directory contains comprehensive test utility functions for the NoDupeLabs project. These utilities are designed to support Task 1.3 of the test coverage implementation plan.

## Overview

The test utilities provide helper functions for common testing patterns and scenarios, including:

- **File System Operations** - Temporary file/directory creation and management
- **Database Operations** - Database state verification and mocking
- **Plugin System** - Plugin loading, validation, and testing
- **Performance Benchmarking** - Performance measurement and analysis
- **Error Condition Simulation** - Error scenario creation and testing
- **Data Validation** - Schema validation and consistency checking

## Modules

### 1. `filesystem.py` - File System Test Utilities

**Purpose**: Helper functions for file system operations testing

**Key Functions**:
- `create_test_file_structure()` - Create complex file structures for testing
- `create_duplicate_files()` - Create multiple duplicate files
- `create_files_with_varying_sizes()` - Create files with specific sizes
- `create_symlinks_and_hardlinks()` - Create symbolic and hard links
- `calculate_file_hash()` - Calculate file hashes for integrity checking
- `compare_files()` - Compare file contents
- `create_nested_directory_structure()` - Create nested directory structures
- `create_files_with_timestamps()` - Create files with specific timestamps
- `verify_file_structure()` - Verify file structure matches expectations
- `mock_file_operations()` - Create mock file system operations
- `create_large_file()` - Create large files for performance testing

### 2. `database.py` - Database Test Utilities

**Purpose**: Helper functions for database operations testing

**Key Functions**:
- `create_test_database()` - Create test databases with optional schema and data
- `setup_test_database_schema()` - Set up database schema for testing
- `insert_test_data()` - Insert test data into database tables
- `verify_database_state()` - Verify database state matches expected state
- `create_database_mock()` - Create mock database connections
- `create_database_fixture()` - Create pytest fixtures for database testing
- `simulate_database_errors()` - Simulate various database error conditions
- `benchmark_database_operations()` - Benchmark database operation performance
- `create_transaction_test_scenarios()` - Create transaction testing scenarios
- `verify_database_performance()` - Verify database query performance
- `create_database_snapshot()` - Create database state snapshots
- `restore_database_snapshot()` - Restore database to previous state

### 3. `plugins.py` - Plugin Test Utilities

**Purpose**: Helper functions for plugin system testing

**Key Functions**:
- `create_mock_plugin()` - Create mock plugins for testing
- `create_plugin_directory_structure()` - Create plugin directory structures
- `mock_plugin_loader()` - Create mock plugin loaders
- `create_plugin_test_scenarios()` - Create plugin testing scenarios
- `simulate_plugin_errors()` - Simulate plugin error conditions
- `verify_plugin_functionality()` - Verify plugin functionality
- `create_plugin_dependency_graph()` - Create plugin dependency graphs
- `test_plugin_dependency_resolution()` - Test plugin dependency resolution
- `create_plugin_sandbox_environment()` - Create sandbox environments for plugins
- `mock_plugin_registry()` - Create mock plugin registries
- `create_plugin_lifecycle_test_scenarios()` - Create plugin lifecycle scenarios
- `benchmark_plugin_performance()` - Benchmark plugin performance
- `create_plugin_security_test_scenarios()` - Create plugin security scenarios

### 4. `performance.py` - Performance Test Utilities

**Purpose**: Helper functions for performance benchmarking and testing

**Key Functions**:
- `benchmark_function_performance()` - Benchmark function performance
- `measure_memory_usage()` - Measure memory usage of functions
- `create_performance_test_scenarios()` - Create performance test scenarios
- `simulate_resource_constraints()` - Simulate resource constraints
- `create_load_test_scenarios()` - Create load test scenarios
- `benchmark_file_operations()` - Benchmark file operations
- `create_performance_monitor()` - Create performance monitoring contexts
- `simulate_slow_operations()` - Simulate slow operations
- `create_stress_test_scenarios()` - Create stress test scenarios
- `benchmark_database_operations()` - Benchmark database operations
- `create_network_performance_test_scenarios()` - Create network performance scenarios
- `measure_concurrency_performance()` - Measure concurrency performance
- `create_performance_regression_test_scenarios()` - Create regression test scenarios
- `simulate_performance_degradation()` - Simulate performance degradation
- `create_resource_monitoring_scenarios()` - Create resource monitoring scenarios

### 5. `errors.py` - Error Test Utilities

**Purpose**: Helper functions for error condition simulation and testing

**Key Functions**:
- `simulate_file_system_errors()` - Simulate file system errors
- `create_error_test_scenarios()` - Create error test scenarios
- `simulate_network_errors()` - Simulate network errors
- `create_exception_test_cases()` - Create exception test cases
- `simulate_memory_errors()` - Simulate memory errors
- `create_error_recovery_test_scenarios()` - Create error recovery scenarios
- `simulate_database_errors()` - Simulate database errors
- `create_error_injection_test_scenarios()` - Create error injection scenarios
- `simulate_plugin_errors()` - Simulate plugin errors
- `create_error_handling_test_scenarios()` - Create error handling scenarios
- `simulate_concurrency_errors()` - Simulate concurrency errors
- `create_error_validation_test_scenarios()` - Create error validation scenarios
- `simulate_resource_exhaustion_errors()` - Simulate resource exhaustion
- `create_error_monitoring_test_scenarios()` - Create error monitoring scenarios
- `simulate_timeout_errors()` - Simulate timeout errors
- `create_error_recovery_validation_scenarios()` - Create error recovery validation scenarios

### 6. `validation.py` - Validation Test Utilities

**Purpose**: Helper functions for data validation and testing

**Key Functions**:
- `validate_test_data_structure()` - Validate data structure against schema
- `create_data_validation_test_cases()` - Create data validation test cases
- `validate_file_integrity()` - Validate file integrity using hashes
- `create_file_validation_test_scenarios()` - Create file validation scenarios
- `validate_json_schema()` - Validate JSON data against schema
- `create_json_validation_test_cases()` - Create JSON validation test cases
- `validate_database_schema()` - Validate database schema structure
- `create_database_validation_test_scenarios()` - Create database validation scenarios
- `validate_plugin_structure()` - Validate plugin structure and metadata
- `create_plugin_validation_test_cases()` - Create plugin validation test cases
- `validate_api_response()` - Validate API response structure
- `create_api_validation_test_scenarios()` - Create API validation scenarios
- `validate_configuration_files()` - Validate configuration files
- `create_configuration_validation_test_cases()` - Create configuration validation scenarios
- `validate_data_consistency()` - Validate data consistency
- `create_data_consistency_test_scenarios()` - Create data consistency scenarios

## Usage

### Importing Utilities

```python
# Import specific modules
from tests.utils import filesystem, database, plugins, performance, errors, validation

# Or import all utilities
from tests.utils import *
```

### Example Usage

```python
# Create a test file structure
structure = {
    "config": {
        "settings.json": '{"debug": true}',
        "cache": {}
    },
    "data.txt": "Test data"
}

created_files = filesystem.create_test_file_structure(Path("/tmp/test"), structure)

# Create a test database
conn = database.create_test_database(use_memory=True)
schema = "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);"
database.setup_test_database_schema(conn, schema)

# Create mock plugins
mock_plugin = plugins.create_mock_plugin("test_plugin")
result = mock_plugin.execute("test_input")

# Benchmark performance
def process_data(data):
    return [x * 2 for x in data]

results = performance.benchmark_function_performance(
    process_data,
    iterations=100,
    args=([1, 2, 3, 4, 5],)
)

# Validate data structure
data = {"user": {"id": 123, "name": "test"}}
schema = {
    "type": "dict",
    "properties": {
        "user": {
            "type": "dict",
            "required": ["id", "name"],
            "properties": {
                "id": {"type": "int"},
                "name": {"type": "str"}
            }
        }
    }
}

is_valid = validation.validate_test_data_structure(data, schema)
```

## Testing

The utilities include comprehensive test coverage in `tests/test_utils.py`. Run the tests with:

```bash
# Run utility tests
python tests/test_utils.py

# Or with pytest
python -m pytest tests/test_utils.py -v
```

## Integration with Test Coverage Plan

These utilities directly support **Task 1.3: Test Utility Functions** from the test coverage implementation plan:

- ✅ **Temporary file/directory creation** - `filesystem.py`
- ✅ **Database state verification** - `database.py`
- ✅ **Plugin loading and validation** - `plugins.py`
- ✅ **Performance benchmarking** - `performance.py`
- ✅ **Error condition simulation** - `errors.py`
- ✅ **Data validation** - `validation.py`

## Best Practices

1. **Isolation**: Each utility function is designed to be independent and reusable
2. **Comprehensive Documentation**: All functions include detailed docstrings
3. **Error Handling**: Utilities include proper error handling and validation
4. **Performance**: Performance-critical functions are optimized
5. **Maintainability**: Code follows consistent style and patterns

## Future Enhancements

- Add more specific validation patterns for NoDupeLabs data structures
- Enhance performance benchmarking with more detailed metrics
- Add support for additional database types beyond SQLite
- Expand error simulation capabilities for more edge cases
- Add utilities for testing parallel and distributed operations

## Contributing

Contributions to the test utilities are welcome. Please follow the existing patterns and ensure all new functions include:

1. Comprehensive docstrings
2. Type hints
3. Unit tests in `test_utils.py`
4. Integration with the existing module structure
