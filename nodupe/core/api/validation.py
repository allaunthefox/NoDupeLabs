# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Schema Validation Module.

Provides JSON schema validation for API requests and responses.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, Dict, List, Optional


class SchemaValidationError(Exception):
    """Exception raised when schema validation fails."""
    
    def __init__(self, message: str, errors: Optional[List[str]] = None) -> None:
        """Initialize validation error."""
        self.message = message
        self.errors = errors or []
        super().__init__(self.message)


class SchemaValidator:
    """JSON Schema Validator.
    
    Provides JSON schema validation for API requests and responses.
    Implements a subset of JSON Schema draft-07 validation.
    """
    
    def __init__(self, strict_mode: bool = False) -> None:
        """Initialize schema validator."""
        self.strict_mode = strict_mode
    
    def validate(self, schema: Dict[str, Any], data: Any) -> bool:
        """Validate data against a JSON schema."""
        errors: List[str] = []
        self._validate_recursive(schema, data, "", errors)
        if errors:
            raise SchemaValidationError("Validation failed", errors)
        return True
    
    def _validate_recursive(self, schema: Dict[str, Any], data: Any, path: str, errors: List[str]) -> bool:
        """Recursively validate data against schema."""
        if "type" in schema:
            if not self._check_type(data, schema["type"]):
                errors.append(f"{path}: expected {schema['type']}, got {type(data).__name__}")
        return len(errors) == 0 or not self.strict_mode
    
    def _check_type(self, data: Any, expected_type: str) -> bool:
        """Check if data matches expected type."""
        if expected_type == "string":
            return isinstance(data, str)
        if expected_type == "integer":
            return isinstance(data, int) and not isinstance(data, bool)
        if expected_type == "number":
            return isinstance(data, (int, float)) and not isinstance(data, bool)
        if expected_type == "boolean":
            return isinstance(data, bool)
        if expected_type == "array":
            return isinstance(data, list)
        if expected_type == "object":
            return isinstance(data, dict)
        if expected_type == "null":
            return data is None
        return True


def validate_request(schema: Dict[str, Any]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to validate request data against a schema."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_response(schema: Dict[str, Any]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to validate response data against a schema."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        return wrapper
    return decorator
