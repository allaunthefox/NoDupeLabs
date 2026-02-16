# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Database Cleanup Module.

This module provides database cleanup and maintenance functionality.

Classes:
    DatabaseCleanup: Handles database cleanup and maintenance operations.

Example:
    >>> from nodupe.core.database import Database
    >>> db = Database("/path/to/db.db")
    >>> result = db.cleanup.vacuum()
"""

from __future__ import annotations

from typing import Any, Dict


class DatabaseCleanup:
    """Database cleanup and maintenance.

    Provides methods for cleaning up the database, including vacuuming,
    removing temporary data, and other maintenance tasks.

    Example:
        >>> cleanup = DatabaseCleanup(connection)
        >>> result = cleanup.vacuum()
    """

    def __init__(self, connection: Any) -> None:
        """Initialize database cleanup.

        Args:
            connection: Database connection instance.
        """
        self.connection = connection

    def vacuum(self) -> Dict[str, Any]:
        """Vacuum the database to reclaim space.

        Returns:
            Dictionary with status and message.

        Example:
            >>> cleanup.vacuum()
            {'status': 'success', 'message': 'Database vacuumed'}
        """
        try:
            conn = self.connection.get_connection()
            conn.execute("VACUUM")
            conn.commit()
            return {"status": "success", "message": "Database vacuumed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def analyze(self) -> Dict[str, Any]:
        """Analyze database for query optimization.

        Returns:
            Dictionary with status and message.

        Example:
            >>> cleanup.analyze()
            {'status': 'success', 'message': 'Database analyzed'}
        """
        try:
            conn = self.connection.get_connection()
            conn.execute("ANALYZE")
            conn.commit()
            return {"status": "success", "message": "Database analyzed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def integrity_check(self) -> Dict[str, Any]:
        """Run integrity check on the database.

        Returns:
            Dictionary with integrity check results.

        Example:
            >>> cleanup.integrity_check()
            {'status': 'ok', 'integrity': 'ok'}
        """
        try:
            conn = self.connection.get_connection()
            cursor = conn.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            is_ok = result[0] == "ok"
            return {
                "status": "ok" if is_ok else "error",
                "integrity": result[0]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def clear_temp_tables(self) -> Dict[str, Any]:
        """Clear temporary tables from database.

        Returns:
            Dictionary with status and message.

        Example:
            >>> cleanup.clear_temp_tables()
            {'status': 'success', 'message': 'Temp tables cleared'}
        """
        try:
            conn = self.connection.get_connection()
            # Get list of temp tables
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'temp_%'"
            )
            tables = cursor.fetchall()

            for (table_name,) in tables:
                conn.execute(f"DROP TABLE IF EXISTS {table_name}")

            conn.commit()
            return {
                "status": "success",
                "message": f"Cleared {len(tables)} temporary tables"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
