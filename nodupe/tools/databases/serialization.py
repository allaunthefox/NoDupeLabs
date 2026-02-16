# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Database Serialization Module.

This module provides data serialization functionality for JSON encoding/decoding.

Classes:
    DatabaseSerialization: Handles data serialization for database storage.

Example:
    >>> from nodupe.core.database import Database
    >>> db = Database("/path/to/db.db")
    >>> json_str = db.serialization.serialize({"key": "value"})
"""

from __future__ import annotations

from typing import Any
import json


class DatabaseSerialization:
    """Database data serialization.

    Provides methods for serializing and deserializing data to/from JSON format
    for storage in the database.

    Example:
        >>> serialization = DatabaseSerialization(connection)
        >>> json_str = serialization.serialize({"key": "value"})
        >>> data = serialization.deserialize(json_str)
    """

    def __init__(self, connection: Any) -> None:
        """Initialize database serialization.

        Args:
            connection: Database connection instance.
        """
        self.connection = connection

    def serialize(self, data: Any) -> str:
        """Serialize data to JSON string.

        Args:
            data: Data to serialize (must be JSON-serializable).

        Returns:
            JSON string representation.

        Raises:
            ValueError: If data cannot be serialized.

        Example:
            >>> serialization.serialize({"key": "value"})
            '{"key": "value"}'
        """
        try:
            return json.dumps(data)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Serialization failed: {e}")

    def deserialize(self, serialized_data: str) -> Any:
        """Deserialize JSON string to data.

        Args:
            serialized_data: JSON string to deserialize.

        Returns:
            Deserialized Python object.

        Raises:
            ValueError: If data cannot be deserialized.

        Example:
            >>> serialization.deserialize('{"key": "value"}')
            {'key': 'value'}
        """
        try:
            return json.loads(serialized_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Deserialization failed: {e}")

    def serialize_safe(self, data: Any) -> str:
        """Safely serialize data, returning empty string on failure.

        Args:
            data: Data to serialize.

        Returns:
            JSON string or empty string on failure.

        Example:
            >>> serialization.serialize_safe({"key": "value"})
            '{"key": "value"}'
        """
        try:
            return self.serialize(data)
        except ValueError:
            return '{}'

    def deserialize_safe(self, serialized_data: str) -> Any:
        """Safely deserialize data, returning original on failure.

        Args:
            serialized_data: JSON string to deserialize.

        Returns:
            Deserialized data or original string on failure.

        Example:
            >>> serialization.deserialize_safe('{"key": "value"}')
            {'key': 'value'}
        """
        try:
            return self.deserialize(serialized_data)
        except ValueError:
            return serialized_data
