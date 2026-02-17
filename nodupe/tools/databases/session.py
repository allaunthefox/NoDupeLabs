# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Database Session Module.

This module provides database session management for tracking and managing

# pylint: disable=W0718  # broad-exception-caught - intentional for graceful degradation
database connection sessions.

Classes:
    DatabaseSession: Handles database session lifecycle.

Example:
    >>> from nodupe.core.database import Database
    >>> db = Database("/path/to/db.db")
    >>> with db.session.begin() as conn:
    ...     conn.execute("SELECT 1")
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any


class DatabaseSession:
    """Database session management.

    Provides context managers for managing database sessions with automatic
    commit/rollback handling.

    Example:
        >>> session = DatabaseSession(connection)
        >>> with session.begin() as conn:
        ...     conn.execute("INSERT ...")
    """

    def __init__(self, connection: Any) -> None:
        """Initialize database session.

        Args:
            connection: Database connection instance.
        """
        self.connection = connection
        self._active = False

    @contextmanager
    def begin(self):
        """Begin a database session.

        Yields:
            Database connection for the session.

        Raises:
            Exception: Re-raises any exception after rollback.

        Example:
            >>> with session.begin() as conn:
            ...     conn.execute("INSERT ...")
        """
        conn = self.connection.get_connection()
        self._active = True
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._active = False

    @property
    def is_active(self) -> bool:
        """Check if session is active.

        Returns:
            True if session is active.

        Example:
            >>> session.is_active
            False
        """
        return self._active
