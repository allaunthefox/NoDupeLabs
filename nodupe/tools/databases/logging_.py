# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Database Logging Module.

This module provides database logging functionality for tracking operations,

# pylint: disable=W0718  # broad-exception-caught - intentional for graceful degradation
queries, and events within the database layer.

Classes:
    DatabaseLogging: Handles logging of database operations.

Example:
    >>> from nodupe.core.database import Database
    >>> db = Database("/path/to/db.db")
    >>> db.logging.log("Operation completed", "INFO")
"""

from __future__ import annotations

from typing import Any


class DatabaseLogging:
    """Database logging functionality.

    Provides methods for logging database operations, queries, and events
    to both console and database storage.

    Attributes:
        enabled: Whether logging is enabled.
        log_to_db: Whether to store logs in the database.

    Example:
        >>> logger = DatabaseLogging(connection)
        >>> logger.log("Query executed", "INFO")
    """

    def __init__(self, connection: Any) -> None:
        """Initialize database logging.

        Args:
            connection: Database connection instance.
        """
        self.connection = connection
        self.enabled = True
        self.log_to_db = False

    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message.

        Args:
            message: The message to log.
            level: The log level (INFO, WARNING, ERROR, DEBUG).

        Example:
            >>> logger.log("Database operation", "INFO")
        """
        if not self.enabled:
            return

        # Simple console logging for now
        print(f"[{level}] {message}")

        if self.log_to_db:
            self._log_to_database(message, level)

    def _log_to_database(self, message: str, level: str) -> None:
        """Log to database table.

        Args:
            message: The message to log.
            level: The log level.
        """
        try:
            conn = self.connection.get_connection()
            conn.execute(
                "CREATE TABLE IF NOT EXISTS db_logs ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "timestamp DEFAULT CURRENT_TIMESTAMP, "
                "level TEXT, "
                "message TEXT"
                ")"
            )
            conn.execute(
                "INSERT INTO db_logs (level, message) VALUES (?, ?)",
                (level, message)
            )
            conn.commit()
        except Exception:
            pass  # Silently fail if logging table creation fails

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable logging.

        Args:
            enabled: Whether to enable logging.

        Example:
            >>> logger.set_enabled(False)
        """
        self.enabled = enabled

    def set_log_to_db(self, log_to_db: bool) -> None:
        """Enable or disable database logging.

        Args:
            log_to_db: Whether to log to database.

        Example:
            >>> logger.set_log_to_db(True)
        """
        self.log_to_db = log_to_db
