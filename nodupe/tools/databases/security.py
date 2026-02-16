# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Lightweight database security module for local file management.

This module provides essential security features for the local SQLite database:
- Input validation and sanitization
- SQL injection prevention
- Path validation for file operations
- Secure error handling
"""

import re
import os
from typing import Any, Optional

class SecurityError(Exception):
    """Base security exception"""
    pass

class InputValidationError(SecurityError):
    """Input validation failed"""
    pass

class DatabaseSecurity:
    """Lightweight database security for local file management."""

    def __init__(self, db):
        """TODO: Document __init__."""
        self.db = db

    def validate_input(self, data: Any, data_type: Optional[str] = None) -> bool:
        """Validate input data for database operations.

        Args:
            data: Input data to validate
            data_type: Expected data type (optional)

        Returns:
            bool: True if validation passes

        Raises:
            InputValidationError: If validation fails
        """
        if data is None:
            raise InputValidationError("Input data cannot be None")

        # Type checking if specified - use safe type lookup instead of eval
        if data_type:
            # Safe type mapping - only allow known types
            safe_types = {
                'str': str, 'int': int, 'float': float, 'bool': bool,
                'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
                'bytes': bytes, 'bytearray': bytearray
            }
            expected_type = safe_types.get(data_type)
            if expected_type is None:
                raise InputValidationError(f"Unknown type: {data_type}")
            if not isinstance(data, expected_type):
                raise InputValidationError(f"Expected {data_type}, got {type(data)}")

        # String validation
        if isinstance(data, str):
            if not self._is_safe_string(data):
                raise InputValidationError("String contains potentially dangerous content")

        return True

    def _is_safe_string(self, value: str) -> bool:
        """Check if a string is safe for database operations.

        Args:
            value: String to validate

        Returns:
            bool: True if string is safe
        """
        if not value:
            return True

        # Check for SQL injection patterns
        dangerous_patterns = [
            r'--', r';', r'/\*', r'\*/', r'xp_', r'exec\(', r'union\s+select',
            r'drop\s+table', r'insert\s+into', r'delete\s+from', r'update\s+.*set',
            r'select\s+.*from', r'or\s+1=1'
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return False

        return True

    def validate_path(self, path: str, base_dir: Optional[str] = None) -> bool:
        """Validate file path to prevent directory traversal attacks.

        Args:
            path: File path to validate
            base_dir: Base directory to restrict paths to

        Returns:
            bool: True if path is valid

        Raises:
            InputValidationError: If path is invalid
        """
        if not path:
            raise InputValidationError("Path cannot be empty")

        try:
            # Convert to absolute path
            abs_path = os.path.abspath(path)

            # Check for directory traversal attempts
            if '..' in path or path.startswith('/') and not path.startswith(base_dir or ''):
                raise InputValidationError("Path contains directory traversal")

            # If base_dir is specified, ensure path is within it
            if base_dir:
                base_abs = os.path.abspath(base_dir)
                if not abs_path.startswith(base_abs):
                    raise InputValidationError(f"Path must be within {base_dir}")

            return True
        except Exception as e:
            raise InputValidationError(f"Path validation failed: {e}")

    def sanitize_error_message(self, error: Exception) -> str:
        """Sanitize error messages to prevent information leakage.

        Args:
            error: Exception to sanitize

        Returns:
            str: Sanitized error message
        """
        # Get error message
        error_msg = str(error)

        # Remove sensitive information
        sensitive_patterns = [
            r'password', r'secret', r'key', r'token', r'api[_-]?key',
            r'connection[_-]?string', r'database[_-]?url', r'user[_-]?name'
        ]

        for pattern in sensitive_patterns:
            error_msg = re.sub(pattern, '[REDACTED]', error_msg, flags=re.IGNORECASE)

        # Remove stack traces and file paths
        error_msg = re.sub(r'File ".*?", line \d+', '[REDACTED]', error_msg)
        error_msg = re.sub(r'Traceback.*?\n', '', error_msg)

        return error_msg

    def validate_identifier(self, identifier: str) -> bool:
        """Validate SQL identifier (table/column name).

        Args:
            identifier: SQL identifier to validate

        Returns:
            bool: True if identifier is valid

        Raises:
            InputValidationError: If identifier is invalid
        """
        if not identifier or not isinstance(identifier, str):
            raise InputValidationError("Identifier cannot be empty")

        # Only allow alphanumeric and underscore, must start with letter
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
            raise InputValidationError(f"Invalid identifier: {identifier}")

        return True

    def validate_schema(self, schema: str) -> bool:
        """Validate schema definition.

        Args:
            schema: Schema definition to validate

        Returns:
            bool: True if schema is valid

        Raises:
            InputValidationError: If schema is invalid
        """
        if not schema or not isinstance(schema, str):
            raise InputValidationError("Schema cannot be empty")

        # Basic validation - should contain valid column definitions
        if not re.match(r'^[a-zA-Z0-9_,\s\(\)]+$', schema):
            raise InputValidationError(f"Invalid schema definition: {schema}")

        return True
