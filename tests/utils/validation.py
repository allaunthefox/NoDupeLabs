# Validation Test Utilities
# Helper functions for data validation and testing

import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from unittest.mock import MagicMock


def validate_test_data_structure(data: Any, schema: dict[str, Any]) -> bool:
    """
    Validate test data structure against a schema.

    Args:
        data: Data to validate
        schema: Schema definition

    Returns:
        True if data matches schema, False otherwise
    """

    def _validate(item, schema_part):
        if "type" in schema_part:
            expected_type = schema_part["type"]
            if (
                (expected_type == "dict" and not isinstance(item, dict))
                or (expected_type == "list" and not isinstance(item, list))
                or (expected_type == "str" and not isinstance(item, str))
                or (expected_type == "int" and not isinstance(item, int))
                or (expected_type == "float" and not isinstance(item, float))
                or (expected_type == "bool" and not isinstance(item, bool))
            ):
                return False

        if "required" in schema_part and not all(
            key in item for key in schema_part["required"]
        ):
            return False

        if "properties" in schema_part:
            for key, prop_schema in schema_part["properties"].items():
                if key in item and not _validate(item[key], prop_schema):
                    return False

        if "items" in schema_part and isinstance(item, list):
            for list_item in item:
                if not _validate(list_item, schema_part["items"]):
                    return False

        if "pattern" in schema_part and isinstance(item, str):
            if not re.match(schema_part["pattern"], item):
                return False

        if "min" in schema_part and isinstance(item, (int, float)):
            if item < schema_part["min"]:
                return False

        if "max" in schema_part and isinstance(item, (int, float)):
            if item > schema_part["max"]:
                return False

        return True

    return _validate(data, schema)


def create_data_validation_test_cases() -> list[dict[str, Any]]:
    """
    Create data validation test cases.

    Returns:
        List of data validation test cases
    """
    return [
        {
            "name": "valid_config_data",
            "data": {
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "username": "admin",
                    "PASSWORD_REMOVED": "SECRET_REMOVED",
                },
                "logging": {"level": "INFO", "file": "/var/log/app.log"},
            },
            "schema": {
                "type": "dict",
                "properties": {
                    "database": {
                        "type": "dict",
                        "required": [
                            "host",
                            "port",
                            "username",
                            "PASSWORD_REMOVED",
                        ],
                        "properties": {
                            "host": {"type": "str"},
                            "port": {"type": "int", "min": 1, "max": 65535},
                            "username": {"type": "str"},
                            "PASSWORD_REMOVED": {"type": "str"},
                        },
                    },
                    "logging": {
                        "type": "dict",
                        "required": ["level", "file"],
                        "properties": {
                            "level": {
                                "type": "str",
                                "pattern": "^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
                            },
                            "file": {"type": "str"},
                        },
                    },
                },
            },
            "expected_result": True,
        },
        {
            "name": "invalid_config_data",
            "data": {
                "database": {
                    "host": "localhost",
                    "port": 70000,  # Invalid port
                    "username": "admin",
                    # Missing PASSWORD_REMOVED
                }
            },
            "schema": {
                "type": "dict",
                "properties": {
                    "database": {
                        "type": "dict",
                        "required": [
                            "host",
                            "port",
                            "username",
                            "PASSWORD_REMOVED",
                        ],
                        "properties": {
                            "host": {"type": "str"},
                            "port": {"type": "int", "min": 1, "max": 65535},
                            "username": {"type": "str"},
                            "PASSWORD_REMOVED": {"type": "str"},
                        },
                    }
                },
            },
            "expected_result": False,
        },
    ]


def validate_file_integrity(
    file_path: Path, expected_hash: str, algorithm: str = "sha256"
) -> bool:
    """
    Validate file integrity using hash comparison.

    Args:
        file_path: Path to file
        expected_hash: Expected hash value
        algorithm: Hash algorithm to use

    Returns:
        True if file integrity is valid, False otherwise
    """
    hash_func = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)

    actual_hash = hash_func.hexdigest()
    return actual_hash == expected_hash


def create_file_validation_test_scenarios() -> list[dict[str, Any]]:
    """
    Create file validation test scenarios.

    Returns:
        List of file validation test scenarios
    """
    return [
        {
            "name": "valid_file_integrity",
            "file_content": "test content for integrity check",
            "expected_hash": "a1b2c3d4e5f6",  # Placeholder - would be actual hash in real test
            "expected_result": True,
        },
        {
            "name": "corrupted_file",
            "file_content": "corrupted content",
            "expected_hash": "a1b2c3d4e5f6",  # Different from actual hash
            "expected_result": False,
        },
        {
            "name": "missing_file",
            "file_content": None,
            "expected_hash": "a1b2c3d4e5f6",
            "expected_result": False,
        },
    ]


def validate_json_schema(
    json_data: Union[str, dict], schema: dict[str, Any]
) -> bool:
    """
    Validate JSON data against a schema.

    Args:
        json_data: JSON data to validate
        schema: JSON schema definition

    Returns:
        True if JSON is valid, False otherwise
    """
    if isinstance(json_data, str):
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return False
    else:
        data = json_data

    return validate_test_data_structure(data, schema)


def create_json_validation_test_cases() -> list[dict[str, Any]]:
    """
    Create JSON validation test cases.

    Returns:
        List of JSON validation test cases
    """
    return [
        {
            "name": "valid_json_api_response",
            "json_data": """
            {
                "status": "success",
                "data": {
                    "users": [
                        {"id": 1, "name": "Alice"},
                        {"id": 2, "name": "Bob"}
                    ]
                },
                "timestamp": "2023-01-01T00:00:00Z"
            }
            """,
            "schema": {
                "type": "dict",
                "required": ["status", "data", "timestamp"],
                "properties": {
                    "status": {
                        "type": "str",
                        "pattern": "^(success|error|warning)$",
                    },
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
                                        "name": {"type": "str"},
                                    },
                                },
                            }
                        },
                    },
                    "timestamp": {
                        "type": "str",
                        "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$",
                    },
                },
            },
            "expected_result": True,
        },
        {
            "name": "invalid_json_api_response",
            "json_data": """
            {
                "status": "invalid_status",
                "data": {
                    "users": [
                        {"id": "not_an_int", "name": "Alice"}
                    ]
                }
            }
            """,
            "schema": {
                "type": "dict",
                "required": ["status", "data", "timestamp"],
                "properties": {
                    "status": {
                        "type": "str",
                        "pattern": "^(success|error|warning)$",
                    },
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
                                        "name": {"type": "str"},
                                    },
                                },
                            }
                        },
                    },
                    "timestamp": {
                        "type": "str",
                        "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$",
                    },
                },
            },
            "expected_result": False,
        },
    ]


def validate_database_schema(
    database_schema: dict[str, Any], expected_schema: dict[str, Any]
) -> bool:
    """
    Validate database schema structure.

    Args:
        database_schema: Actual database schema
        expected_schema: Expected database schema

    Returns:
        True if schemas match, False otherwise
    """
    # Compare tables
    if set(database_schema.keys()) != set(expected_schema.keys()):
        return False

    # Compare table structures
    for table_name, table_def in expected_schema.items():
        if table_name not in database_schema:
            return False

        actual_table = database_schema[table_name]

        # Compare columns
        if set(table_def["columns"].keys()) != set(
            actual_table["columns"].keys()
        ):
            return False

        # Compare column definitions
        for col_name, col_def in table_def["columns"].items():
            if col_name not in actual_table["columns"]:
                return False

            actual_col = actual_table["columns"][col_name]

            if col_def["type"] != actual_col["type"]:
                return False

            if "constraints" in col_def and col_def[
                "constraints"
            ] != actual_col.get("constraints", []):
                return False

    return True


def create_database_validation_test_scenarios() -> list[dict[str, Any]]:
    """
    Create database validation test scenarios.

    Returns:
        List of database validation test scenarios
    """
    return [
        {
            "name": "valid_database_schema",
            "database_schema": {
                "users": {
                    "columns": {
                        "id": {
                            "type": "INTEGER",
                            "constraints": ["PRIMARY KEY"],
                        },
                        "name": {"type": "TEXT", "constraints": ["NOT NULL"]},
                        "email": {"type": "TEXT", "constraints": ["UNIQUE"]},
                    }
                },
                "posts": {
                    "columns": {
                        "id": {
                            "type": "INTEGER",
                            "constraints": ["PRIMARY KEY"],
                        },
                        "user_id": {
                            "type": "INTEGER",
                            "constraints": ["FOREIGN KEY"],
                        },
                        "title": {"type": "TEXT"},
                        "content": {"type": "TEXT"},
                    }
                },
            },
            "expected_schema": {
                "users": {
                    "columns": {
                        "id": {
                            "type": "INTEGER",
                            "constraints": ["PRIMARY KEY"],
                        },
                        "name": {"type": "TEXT", "constraints": ["NOT NULL"]},
                        "email": {"type": "TEXT", "constraints": ["UNIQUE"]},
                    }
                },
                "posts": {
                    "columns": {
                        "id": {
                            "type": "INTEGER",
                            "constraints": ["PRIMARY KEY"],
                        },
                        "user_id": {
                            "type": "INTEGER",
                            "constraints": ["FOREIGN KEY"],
                        },
                        "title": {"type": "TEXT"},
                        "content": {"type": "TEXT"},
                    }
                },
            },
            "expected_result": True,
        },
        {
            "name": "invalid_database_schema",
            "database_schema": {
                "users": {
                    "columns": {
                        "id": {
                            "type": "INTEGER",
                            "constraints": ["PRIMARY KEY"],
                        },
                        "name": {"type": "TEXT"},
                        # Missing email column
                    }
                }
            },
            "expected_schema": {
                "users": {
                    "columns": {
                        "id": {
                            "type": "INTEGER",
                            "constraints": ["PRIMARY KEY"],
                        },
                        "name": {"type": "TEXT", "constraints": ["NOT NULL"]},
                        "email": {"type": "TEXT", "constraints": ["UNIQUE"]},
                    }
                }
            },
            "expected_result": False,
        },
    ]


def validate_tool_structure(
    tool_definition: dict[str, Any], expected_structure: dict[str, Any]
) -> bool:
    """
    Validate tool structure and metadata.

    Args:
        tool_definition: Tool definition to validate
        expected_structure: Expected tool structure

    Returns:
        True if tool structure is valid, False otherwise
    """
    # Check required fields
    required_fields = expected_structure.get("required_fields", [])
    if not all(field in tool_definition for field in required_fields):
        return False

    # Check metadata structure
    if "metadata" in expected_structure:
        metadata_schema = expected_structure["metadata"]
        if not validate_test_data_structure(
            tool_definition.get("metadata", {}), metadata_schema
        ):
            return False

    # Check function signatures
    if "functions" in expected_structure:
        for func_name, func_schema in expected_structure["functions"].items():
            if func_name not in tool_definition.get("functions", {}):
                return False

            # Check function parameters
            actual_func = tool_definition["functions"][func_name]
            expected_params = func_schema.get("parameters", [])

            # Simple parameter count check
            if "parameters" in func_schema:
                try:
                    import inspect

                    sig = inspect.signature(actual_func)
                    if len(sig.parameters) != len(expected_params):
                        return False
                except:
                    pass

    return True


def create_tool_validation_test_cases() -> list[dict[str, Any]]:
    """
    Create tool validation test cases.

    Returns:
        List of tool validation test cases
    """
    return [
        {
            "name": "valid_tool_structure",
            "tool_definition": {
                "name": "test_tool",
                "version": "1.0.0",
                "author": "Test Author",
                "description": "Test tool",
                "metadata": {
                    "category": "utility",
                    "compatibility": ["1.0", "2.0"],
                },
                "functions": {
                    "initialize": lambda: True,
                    "execute": lambda x: x * 2,
                    "cleanup": lambda: None,
                },
            },
            "expected_structure": {
                "required_fields": ["name", "version", "author", "description"],
                "metadata": {
                    "type": "dict",
                    "required": ["category", "compatibility"],
                    "properties": {
                        "category": {"type": "str"},
                        "compatibility": {
                            "type": "list",
                            "items": {"type": "str"},
                        },
                    },
                },
                "functions": {
                    "initialize": {"parameters": []},
                    "execute": {"parameters": ["x"]},
                    "cleanup": {"parameters": []},
                },
            },
            "expected_result": True,
        },
        {
            "name": "invalid_tool_structure",
            "tool_definition": {
                "name": "test_tool",
                # Missing required fields
                "functions": {
                    "initialize": lambda: True
                    # Missing required functions
                },
            },
            "expected_structure": {
                "required_fields": ["name", "version", "author", "description"],
                "functions": {
                    "initialize": {"parameters": []},
                    "execute": {"parameters": ["x"]},
                    "cleanup": {"parameters": []},
                },
            },
            "expected_result": False,
        },
    ]


def validate_api_response(
    response: dict[str, Any], expected_schema: dict[str, Any]
) -> bool:
    """
    Validate API response structure.

    Args:
        response: API response to validate
        expected_schema: Expected response schema

    Returns:
        True if response is valid, False otherwise
    """
    return validate_test_data_structure(response, expected_schema)


def create_api_validation_test_scenarios() -> list[dict[str, Any]]:
    """
    Create API validation test scenarios.

    Returns:
        List of API validation test scenarios
    """
    return [
        {
            "name": "valid_api_response",
            "response": {
                "status": "success",
                "code": 200,
                "data": {
                    "items": [
                        {"id": 1, "name": "Item 1"},
                        {"id": 2, "name": "Item 2"},
                    ],
                    "pagination": {"page": 1, "page_size": 10, "total": 2},
                },
                "timestamp": "2023-01-01T00:00:00Z",
            },
            "expected_schema": {
                "type": "dict",
                "required": ["status", "code", "data", "timestamp"],
                "properties": {
                    "status": {
                        "type": "str",
                        "pattern": "^(success|error|warning)$",
                    },
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
                                        "name": {"type": "str"},
                                    },
                                },
                            },
                            "pagination": {
                                "type": "dict",
                                "required": ["page", "page_size", "total"],
                                "properties": {
                                    "page": {"type": "int", "min": 1},
                                    "page_size": {
                                        "type": "int",
                                        "min": 1,
                                        "max": 100,
                                    },
                                    "total": {"type": "int", "min": 0},
                                },
                            },
                        },
                    },
                    "timestamp": {
                        "type": "str",
                        "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$",
                    },
                },
            },
            "expected_result": True,
        },
        {
            "name": "invalid_api_response",
            "response": {
                "status": "invalid_status",
                "code": 999,  # Invalid code
                "data": {
                    "items": [
                        {
                            "id": "not_an_int",
                            "name": "Item 1",
                        }  # Invalid ID type
                    ]
                },
            },
            "expected_schema": {
                "type": "dict",
                "required": ["status", "code", "data", "timestamp"],
                "properties": {
                    "status": {
                        "type": "str",
                        "pattern": "^(success|error|warning)$",
                    },
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
                                        "name": {"type": "str"},
                                    },
                                },
                            }
                        },
                    },
                },
            },
            "expected_result": False,
        },
    ]


def validate_configuration_files(
    config_files: list[Path], expected_structure: dict[str, Any]
) -> dict[str, bool]:
    """
    Validate multiple configuration files.

    Args:
        config_files: List of configuration file paths
        expected_structure: Expected configuration structure

    Returns:
        Dictionary mapping file paths to validation results
    """
    results = {}

    for config_file in config_files:
        try:
            with open(config_file) as f:
                config_data = json.load(f)

            results[str(config_file)] = validate_test_data_structure(
                config_data, expected_structure
            )
        except (OSError, json.JSONDecodeError):
            results[str(config_file)] = False

    return results


def create_configuration_validation_test_cases() -> list[dict[str, Any]]:
    """
    Create configuration validation test cases.

    Returns:
        List of configuration validation test cases
    """
    return [
        {
            "name": "valid_configuration_files",
            "config_files": [
                {
                    "content": """
                    {
                        "database": {
                            "host": "localhost",
                            "port": 5432,
                            "username": "admin",
                            "PASSWORD_REMOVED": "SECRET_REMOVED"
                        },
                        "logging": {
                            "level": "INFO",
                            "file": "/var/log/app.log"
                        }
                    }
                    """,
                    "expected_result": True,
                },
                {
                    "content": """
                    {
                        "database": {
                            "host": "localhost",
                            "port": 5432,
                            "username": "admin",
                            "PASSWORD_REMOVED": "SECRET_REMOVED"
                        }
                    }
                    """,
                    "expected_result": True,
                },
            ],
            "expected_structure": {
                "type": "dict",
                "properties": {
                    "database": {
                        "type": "dict",
                        "required": [
                            "host",
                            "port",
                            "username",
                            "PASSWORD_REMOVED",
                        ],
                        "properties": {
                            "host": {"type": "str"},
                            "port": {"type": "int", "min": 1, "max": 65535},
                            "username": {"type": "str"},
                            "PASSWORD_REMOVED": {"type": "str"},
                        },
                    },
                    "logging": {
                        "type": "dict",
                        "properties": {
                            "level": {
                                "type": "str",
                                "pattern": "^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
                            },
                            "file": {"type": "str"},
                        },
                    },
                },
            },
        },
        {
            "name": "invalid_configuration_files",
            "config_files": [
                {
                    "content": """
                    {
                        "database": {
                            "host": "localhost",
                            "port": 70000,
                            "username": "admin"
                        }
                    }
                    """,
                    "expected_result": False,
                },
                {"content": "invalid json content", "expected_result": False},
            ],
            "expected_structure": {
                "type": "dict",
                "properties": {
                    "database": {
                        "type": "dict",
                        "required": [
                            "host",
                            "port",
                            "username",
                            "PASSWORD_REMOVED",
                        ],
                        "properties": {
                            "host": {"type": "str"},
                            "port": {"type": "int", "min": 1, "max": 65535},
                            "username": {"type": "str"},
                            "PASSWORD_REMOVED": {"type": "str"},
                        },
                    }
                },
            },
        },
    ]


def validate_data_consistency(
    data_source: Any, validation_rules: list[dict[str, Any]]
) -> bool:
    """
    Validate data consistency against validation rules.

    Args:
        data_source: Data to validate
        validation_rules: List of validation rules

    Returns:
        True if data is consistent, False otherwise
    """

    def get_nested_value(data, field_path):
        """Get value from nested data structure using dot notation or direct field name"""
        if not isinstance(data, dict):
            return None

        # Try direct field access first
        if field_path in data:
            return data[field_path]

        # Try nested access using dot notation
        if "." in field_path:
            parts = field_path.split(".")
            current = data
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
            return current

        return None

    for rule in validation_rules:
        field = rule["field"]
        validation_type = rule["type"]

        # Get field value using nested access
        value = get_nested_value(data_source, field)

        if value is None and rule.get("required", False):
            return False

        # Apply validation
        if validation_type == "range":
            min_val = rule.get("min")
            max_val = rule.get("max")
            if not (min_val <= value <= max_val):
                return False

        elif validation_type == "pattern":
            pattern = rule["pattern"]
            if not re.match(pattern, str(value)):
                return False

        elif validation_type == "enum":
            allowed_values = rule["values"]
            if value not in allowed_values:
                return False

        elif validation_type == "custom":
            validator = rule["validator"]
            if not validator(value):
                return False

    return True


def create_data_consistency_test_scenarios() -> list[dict[str, Any]]:
    """
    Create data consistency test scenarios.

    Returns:
        List of data consistency test scenarios
    """
    return [
        {
            "name": "valid_data_consistency",
            "data": {
                "user": {
                    "id": 123,
                    "username": "test_user",
                    "email": "test@example.com",
                    "status": "active",
                    "age": 25,
                }
            },
            "validation_rules": [
                {
                    "field": "id",
                    "type": "range",
                    "min": 1,
                    "max": 1000,
                    "required": True,
                },
                {
                    "field": "username",
                    "type": "pattern",
                    "pattern": "^[a-z_]+$",
                    "required": True,
                },
                {
                    "field": "email",
                    "type": "pattern",
                    "pattern": "^[^@]+@[^@]+\\.[^@]+$",
                    "required": True,
                },
                {
                    "field": "status",
                    "type": "enum",
                    "values": ["active", "inactive", "suspended"],
                    "required": True,
                },
                {"field": "age", "type": "range", "min": 18, "max": 120},
            ],
            "expected_result": True,
        },
        {
            "name": "invalid_data_consistency",
            "data": {
                "user": {
                    "id": 0,  # Invalid ID
                    "username": "Invalid User",  # Invalid username
                    "email": "not-an-email",  # Invalid email
                    "status": "unknown",  # Invalid status
                    "age": 15,  # Invalid age
                }
            },
            "validation_rules": [
                {
                    "field": "id",
                    "type": "range",
                    "min": 1,
                    "max": 1000,
                    "required": True,
                },
                {
                    "field": "username",
                    "type": "pattern",
                    "pattern": "^[a-z_]+$",
                    "required": True,
                },
                {
                    "field": "email",
                    "type": "pattern",
                    "pattern": "^[^@]+@[^@]+\\.[^@]+$",
                    "required": True,
                },
                {
                    "field": "status",
                    "type": "enum",
                    "values": ["active", "inactive", "suspended"],
                    "required": True,
                },
                {"field": "age", "type": "range", "min": 18, "max": 120},
            ],
            "expected_result": False,
        },
    ]
