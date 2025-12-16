# Test Utility Functions
# Comprehensive tests for all utility functions

import pytest
import tempfile
from pathlib import Path
import sqlite3
import json
from unittest.mock import MagicMock

# Import all utility modules
from tests.utils import (
    filesystem, database, plugins, performance, errors, validation
)

def test_filesystem_utilities():
    """Test filesystem utility functions"""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)

        # Test create_test_file_structure
        structure = {
            "dir1": {
                "file1.txt": "Content 1",
                "file2.txt": "Content 2"
            },
            "file3.txt": "Content 3"
        }

        created_files = filesystem.create_test_file_structure(base_path, structure)
        assert len(created_files) == 3
        assert (base_path / "dir1" / "file1.txt").exists()
        assert (base_path / "file3.txt").exists()

        # Test create_duplicate_files
        duplicates = filesystem.create_duplicate_files(base_path / "duplicates", "Test content", 2)
        assert len(duplicates) == 3  # 1 original + 2 duplicates

        # Test create_files_with_varying_sizes
        sizes = [100, 1000, 10000]
        sized_files = filesystem.create_files_with_varying_sizes(base_path / "sized", sizes)
        assert len(sized_files) == 3

        # Test verify_file_structure
        expected_structure = {
            "dir1": {
                "file1.txt": "Content 1",
                "file2.txt": "Content 2"
            },
            "file3.txt": "Content 3"
        }

        assert filesystem.verify_file_structure(base_path, expected_structure)

def test_database_utilities():
    """Test database utility functions"""
    # Test create_test_database
    conn = database.create_test_database(use_memory=True)
    assert isinstance(conn, sqlite3.Connection)

    # Test setup_test_database_schema
    schema = """
    CREATE TABLE test (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        value REAL
    );
    """

    database.setup_test_database_schema(conn, schema)

    # Test insert_test_data
    test_data = [
        {"id": 1, "name": "Test 1", "value": 1.1},
        {"id": 2, "name": "Test 2", "value": 2.2}
    ]

    database.insert_test_data(conn, "test", test_data)

    # Test verify_database_state
    expected_state = {
        "test": test_data
    }

    assert database.verify_database_state(conn, expected_state)

    # Test create_database_mock
    mock_db = database.create_database_mock()
    assert isinstance(mock_db, MagicMock)

    # Test create_database_snapshot and restore
    snapshot = database.create_database_snapshot(conn)
    assert "test" in snapshot

    # Clear the table
    conn.execute("DELETE FROM test")
    conn.commit()

    # Restore from snapshot
    database.restore_database_snapshot(conn, snapshot)

    # Verify restoration
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM test")
    count = cursor.fetchone()[0]
    assert count == 2

    conn.close()

def test_plugin_utilities():
    """Test plugin utility functions"""
    # Test create_mock_plugin
    mock_plugin = plugins.create_mock_plugin("test_plugin")
    assert mock_plugin.name == "test_plugin"
    assert mock_plugin.metadata["version"] == "1.0.0"

    # Test create_plugin_directory_structure
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)

        plugin_defs = [
            {"name": "plugin1", "version": "1.0.0"},
            {"name": "plugin2", "version": "2.0.0"}
        ]

        plugin_paths = plugins.create_plugin_directory_structure(base_path, plugin_defs)
        assert len(plugin_paths) == 2
        assert (base_path / "plugin1" / "plugin1.py").exists()
        assert (base_path / "plugin2" / "plugin2.py").exists()

    # Test mock_plugin_loader
    mock_loader = plugins.mock_plugin_loader()
    assert isinstance(mock_loader, MagicMock)

    # Test create_plugin_test_scenarios
    scenarios = plugins.create_plugin_test_scenarios()
    assert len(scenarios) == 3

    # Test create_plugin_dependency_graph
    plugin_defs_with_deps = [
        {"name": "plugin_a", "dependencies": ["plugin_b"]},
        {"name": "plugin_b", "dependencies": []},
        {"name": "plugin_c", "dependencies": ["plugin_a", "plugin_b"]}
    ]

    graph = plugins.create_plugin_dependency_graph(plugin_defs_with_deps)
    assert graph["plugin_a"] == ["plugin_b"]
    assert graph["plugin_c"] == ["plugin_a", "plugin_b"]

    # Test test_plugin_dependency_resolution
    resolution_order = ["plugin_b", "plugin_a", "plugin_c"]
    assert plugins.test_plugin_dependency_resolution(graph, resolution_order)

def test_performance_utilities():
    """Test performance utility functions"""
    # Test benchmark_function_performance
    def test_function(x):
        return x * 2

    results = performance.benchmark_function_performance(test_function, iterations=10, warmup_iterations=5, args=(5,))
    assert "total_time" in results
    assert "average_time" in results
    assert "operations_per_second" in results

    # Test measure_memory_usage
    mem_results = performance.measure_memory_usage(test_function, 5, 10)
    assert "initial_memory" in mem_results
    assert "final_memory" in mem_results

    # Test create_performance_test_scenarios
    scenarios = performance.create_performance_test_scenarios()
    assert len(scenarios) == 3

    # Test create_load_test_scenarios
    load_scenarios = performance.create_load_test_scenarios()
    assert len(load_scenarios) == 3

    # Test create_stress_test_scenarios
    stress_scenarios = performance.create_stress_test_scenarios()
    assert len(stress_scenarios) == 3

def test_error_utilities():
    """Test error utility functions"""
    # Test create_error_test_scenarios
    scenarios = errors.create_error_test_scenarios()
    assert len(scenarios) == 5

    # Test create_exception_test_cases
    test_cases = errors.create_exception_test_cases()
    assert len(test_cases) == 5

    # Test create_error_recovery_test_scenarios
    recovery_scenarios = errors.create_error_recovery_test_scenarios()
    assert len(recovery_scenarios) == 4

    # Test create_error_handling_test_scenarios
    handling_scenarios = errors.create_error_handling_test_scenarios()
    assert len(handling_scenarios) == 4

    # Test create_error_monitoring_test_scenarios
    monitoring_scenarios = errors.create_error_monitoring_test_scenarios()
    assert len(monitoring_scenarios) == 4

def test_validation_utilities():
    """Test validation utility functions"""
    # Test validate_test_data_structure
    test_data = {
        "database": {
            "host": "localhost",
            "port": 5432
        }
    }

    schema = {
        "type": "dict",
        "properties": {
            "database": {
                "type": "dict",
                "required": ["host", "port"],
                "properties": {
                    "host": {"type": "str"},
                    "port": {"type": "int", "min": 1, "max": 65535}
                }
            }
        }
    }

    assert validation.validate_test_data_structure(test_data, schema)

    # Test create_data_validation_test_cases
    test_cases = validation.create_data_validation_test_cases()
    assert len(test_cases) == 2

    # Test validate_json_schema
    json_data = '''{
        "status": "success",
        "data": {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ]
        },
        "timestamp": "2023-01-01T00:00:00Z"
    }'''

    json_schema = {
        "type": "dict",
        "required": ["status", "data", "timestamp"],
        "properties": {
            "status": {"type": "str", "pattern": "^(success|error|warning)$"},
            "data": {
                "type": "dict",
                "required": ["users"],
                "properties": {
                    "users": {
                        "type": "list",
                        "items": {
                            "type": "dict",
                            "required": ["id", "name"],
                            "properties": {
                                "id": {"type": "int", "min": 1},
                                "name": {"type": "str"}
                            }
                        }
                    }
                }
            },
            "timestamp": {"type": "str", "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$"}
        }
    }

    assert validation.validate_json_schema(json_data, json_schema)

    # Test create_json_validation_test_cases
    json_test_cases = validation.create_json_validation_test_cases()
    assert len(json_test_cases) == 2

    # Test validate_database_schema
    db_schema = {
        "users": {
            "columns": {
                "id": {"type": "INTEGER", "constraints": ["PRIMARY KEY"]},
                "name": {"type": "TEXT", "constraints": ["NOT NULL"]},
                "email": {"type": "TEXT", "constraints": ["UNIQUE"]}
            }
        }
    }

    expected_db_schema = {
        "users": {
            "columns": {
                "id": {"type": "INTEGER", "constraints": ["PRIMARY KEY"]},
                "name": {"type": "TEXT", "constraints": ["NOT NULL"]},
                "email": {"type": "TEXT", "constraints": ["UNIQUE"]}
            }
        }
    }

    assert validation.validate_database_schema(db_schema, expected_db_schema)

    # Test create_database_validation_test_scenarios
    db_test_scenarios = validation.create_database_validation_test_scenarios()
    assert len(db_test_scenarios) == 2

    # Test validate_plugin_structure
    plugin_def = {
        "name": "test_plugin",
        "version": "1.0.0",
        "author": "Test Author",
        "description": "Test plugin",
        "metadata": {
            "category": "utility",
            "compatibility": ["1.0", "2.0"]
        },
        "functions": {
            "initialize": lambda: True,
            "execute": lambda x: x * 2,
            "cleanup": lambda: None
        }
    }

    expected_structure = {
        "required_fields": ["name", "version", "author", "description"],
        "metadata": {
            "type": "dict",
            "required": ["category", "compatibility"],
            "properties": {
                "category": {"type": "str"},
                "compatibility": {"type": "list", "items": {"type": "str"}}
            }
        },
        "functions": {
            "initialize": {"parameters": []},
            "execute": {"parameters": ["x"]},
            "cleanup": {"parameters": []}
        }
    }

    assert validation.validate_plugin_structure(plugin_def, expected_structure)

    # Test create_plugin_validation_test_cases
    plugin_test_cases = validation.create_plugin_validation_test_cases()
    assert len(plugin_test_cases) == 2

    # Test validate_api_response
    api_response = {
        "status": "success",
        "code": 200,
        "data": {
            "items": [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"}
            ],
            "pagination": {
                "page": 1,
                "page_size": 10,
                "total": 2
            }
        },
        "timestamp": "2023-01-01T00:00:00Z"
    }

    api_schema = {
        "type": "dict",
        "required": ["status", "code", "data", "timestamp"],
        "properties": {
            "status": {"type": "str", "pattern": "^(success|error|warning)$"},
            "code": {"type": "int", "min": 200, "max": 599},
            "data": {
                "type": "dict",
                "required": ["items", "pagination"],
                "properties": {
                    "items": {
                        "type": "list",
                        "items": {
                            "type": "dict",
                            "required": ["id", "name"],
                            "properties": {
                                "id": {"type": "int", "min": 1},
                                "name": {"type": "str"}
                            }
                        }
                    },
                    "pagination": {
                        "type": "dict",
                        "required": ["page", "page_size", "total"],
                        "properties": {
                            "page": {"type": "int", "min": 1},
                            "page_size": {"type": "int", "min": 1, "max": 100},
                            "total": {"type": "int", "min": 0}
                        }
                    }
                }
            },
            "timestamp": {"type": "str", "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$"}
        }
    }

    assert validation.validate_api_response(api_response, api_schema)

    # Test create_api_validation_test_scenarios
    api_test_scenarios = validation.create_api_validation_test_scenarios()
    assert len(api_test_scenarios) == 2

    # Test validate_data_consistency
    data = {
        "user": {
            "id": 123,
            "username": "test_user",
            "email": "test@example.com",
            "status": "active",
            "age": 25
        }
    }

    validation_rules = [
        {"field": "user.id", "type": "range", "min": 1, "max": 1000, "required": True},
        {"field": "user.username", "type": "pattern", "pattern": "^[a-z_]+$", "required": True},
        {"field": "user.email", "type": "pattern", "pattern": "^[^@]+@[^@]+\\.[^@]+$", "required": True},
        {"field": "user.status", "type": "enum", "values": ["active", "inactive", "suspended"], "required": True},
        {"field": "user.age", "type": "range", "min": 18, "max": 120}
    ]

    assert validation.validate_data_consistency(data, validation_rules)

    # Test create_data_consistency_test_scenarios
    consistency_scenarios = validation.create_data_consistency_test_scenarios()
    assert len(consistency_scenarios) == 2

if __name__ == "__main__":
    # Run all tests
    test_filesystem_utilities()
    test_database_utilities()
    test_plugin_utilities()
    test_performance_utilities()
    test_error_utilities()
    test_validation_utilities()
    print("All utility function tests passed!")
