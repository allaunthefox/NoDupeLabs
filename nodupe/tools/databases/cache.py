# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Database Cache Module.

This module provides caching functionality for database query results.

Classes:
    DatabaseCache: In-memory cache for database operations.

Example:
    >>> from nodupe.core.database import Database
    >>> db = Database("/path/to/db.db")
    >>> db.cache.set("key", "value")
    >>> db.cache.get("key")
"""

from __future__ import annotations

import time
from typing import Any, Optional


class DatabaseCache:
    """In-memory database cache.

    Provides caching for database query results to improve performance.

    Attributes:
        max_size: Maximum number of cached entries.
        ttl: Time-to-live for cached entries in seconds.

    Example:
        >>> cache = DatabaseCache(connection)
        >>> cache.set("query_1", [{"id": 1}])
        >>> cache.get("query_1")
    """

    def __init__(
        self, connection: Any, max_size: int = 1000, ttl: float = 300.0
    ) -> None:
        """Initialize database cache.

        Args:
            connection: Database connection instance.
            max_size: Maximum cache size.
            ttl: Time-to-live in seconds.
        """
        self.connection = connection
        self._cache: dict[str, tuple[Any, float]] = {}
        self.max_size = max_size
        self.ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        """Get cached value.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found or expired.

        Example:
            >>> cache.get("query_1")
            [{'id': 1}]
        """
        if key not in self._cache:
            return None

        value, timestamp = self._cache[key]

        # Check TTL
        if time.time() - timestamp > self.ttl:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any) -> None:
        """Set cached value.

        Args:
            key: Cache key.
            value: Value to cache.

        Example:
            >>> cache.set("query_1", [{"id": 1}])
        """
        # Evict oldest if at capacity
        if len(self._cache) >= self.max_size:
            oldest_key = min(
                self._cache.keys(), key=lambda k: self._cache[k][1]
            )
            del self._cache[oldest_key]

        self._cache[key] = (value, time.time())

    def clear(self) -> None:
        """Clear all cached values.

        Example:
            >>> cache.clear()
        """
        self._cache.clear()

    def delete(self, key: str) -> bool:
        """Delete a cached value.

        Args:
            key: Cache key.

        Returns:
            True if key was deleted, False if not found.

        Example:
            >>> cache.delete("query_1")
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def size(self) -> int:
        """Get current cache size.

        Returns:
            Number of cached entries.

        Example:
            >>> cache.size()
            10
        """
        return len(self._cache)
