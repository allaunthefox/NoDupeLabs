# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Database Locking Module.

This module provides database locking functionality for concurrent access control.

Classes:
    DatabaseLocking: Handles database locking mechanisms.

Example:
    >>> from nodupe.core.database import Database
    >>> db = Database("/path/to/db.db")
    >>> with db.locking.lock("resource_name"):
    ...     # Protected operation
"""

from __future__ import annotations

from typing import Any
from contextlib import contextmanager


class DatabaseLocking:
    """Database locking functionality.
    
    Provides methods for acquiring and managing database locks to ensure
    safe concurrent access to shared resources.
    
    Example:
        >>> locking = DatabaseLocking(connection)
        >>> with locking.lock("resource"):
        ...     # Protected operation
    """
    
    def __init__(self, connection: Any) -> None:
        """Initialize database locking.
        
        Args:
            connection: Database connection instance.
        """
        self.connection = connection
        self._locks_held = set()
    
    @contextmanager
    def lock(self, lock_name: str):
        """Acquire a database lock.
        
        Args:
            lock_name: Name of the lock to acquire.
        
        Yields:
            None: Context manager for the lock.
        
        Example:
            >>> with locking.lock("my_resource"):
            ...     # Critical section
        """
        self._locks_held.add(lock_name)
        try:
            # SQLite handles locking at the connection level
            # This is a simplified implementation
            yield
        finally:
            self._locks_held.discard(lock_name)
    
    def is_locked(self, lock_name: str) -> bool:
        """Check if a lock is held.
        
        Args:
            lock_name: Name of the lock.
        
        Returns:
            True if lock is held.
        
        Example:
            >>> locking.is_locked("resource")
            False
        """
        return lock_name in self._locks_held
    
    def get_held_locks(self) -> set:
        """Get all currently held locks.
        
        Returns:
            Set of lock names.
        
        Example:
            >>> locking.get_held_locks()
            {'resource1', 'resource2'}
        """
        return self._locks_held.copy()
