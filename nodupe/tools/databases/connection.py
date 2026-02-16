# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Database connection management with connection pooling.

This module provides SQLite database connection management with
basic connection pooling using only standard library.

Key Features:
    - SQLite connection management
    - Basic connection pooling
    - Thread-safe connection handling
    - Transaction management
    - Error handling with resilience

Dependencies:
    - sqlite3 (standard library only)
    - threading (standard library only)
"""

import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional, TypeVar, Union


T = TypeVar('T')


class DatabaseConnection:
    """SQLite database connection with basic pooling.

    Responsibilities:
    - Manage database connections
    - Provide thread-safe access
    - Handle transactions
    - Manage connection lifecycle
    """

    _instances: dict[str, 'DatabaseConnection'] = {}
    _lock = threading.Lock()

    def __init__(self, db_path: str = "output/index.db"):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        if db_path == ":memory:":
            self.db_path = ":memory:"
        else:
            self.db_path = str(Path(db_path).absolute())
        self._local = threading.local()

    @classmethod
    def get_instance(cls, db_path: str = "output/index.db") -> 'DatabaseConnection':
        """Get singleton instance of DatabaseConnection.

        Args:
            db_path: Path to SQLite database file

        Returns:
            DatabaseConnection instance
        """
        with cls._lock:
            if db_path not in cls._instances:
                cls._instances[db_path] = cls(db_path)
            return cls._instances[db_path]

    def get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection.

        Returns:
            sqlite3.Connection instance
        """
        if not hasattr(self._local, 'connection'):
            # Create database directory if it doesn't exist
            db_dir = Path(self.db_path).parent
            if db_dir and not db_dir.exists():
                db_dir.mkdir(parents=True, exist_ok=True)

            # Connect to database with timeout and isolation level
            connection = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                isolation_level='IMMEDIATE',
                check_same_thread=False
            )

            # Configure connection for better performance
            connection.execute('PRAGMA journal_mode=WAL')
            connection.execute('PRAGMA synchronous=NORMAL')
            connection.execute('PRAGMA temp_store=MEMORY')
            connection.execute('PRAGMA cache_size=-20000')  # 20MB cache

            # Enable foreign key constraints
            connection.execute('PRAGMA foreign_keys=ON')

            self._local.connection = connection

        return self._local.connection

    def execute(
        self,
        query: str,
        params: Optional[Union[tuple[Any, ...], dict[str, Any]]] = None
    ) -> sqlite3.Cursor:
        """Execute SQL query with parameters.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            sqlite3.Cursor with results
        """
        conn = self.get_connection()
        try:
            if params:
                return conn.execute(query, params)
            else:
                return conn.execute(query)
        except sqlite3.Error as e:
            print(f"[ERROR] Database query failed: {e}")
            raise

    def executemany(
        self,
        query: str,
        params_list: list[Union[tuple[Any, ...], dict[str, Any]]]
    ) -> sqlite3.Cursor:
        """Execute SQL query with multiple parameter sets.

        Args:
            query: SQL query to execute
            params_list: List of parameter tuples

        Returns:
            sqlite3.Cursor with results
        """
        conn = self.get_connection()
        try:
            return conn.executemany(query, params_list)
        except sqlite3.Error as e:
            print(f"[ERROR] Database batch query failed: {e}")
            raise

    def commit(self) -> None:
        """Commit current transaction."""
        try:
            self.get_connection().commit()
        except sqlite3.Error as e:
            print(f"[ERROR] Database commit failed: {e}")
            raise

    def rollback(self) -> None:
        """Roll back current transaction."""
        try:
            self.get_connection().rollback()
        except sqlite3.Error as e:
            print(f"[ERROR] Database rollback failed: {e}")
            raise

    def close(self) -> None:
        """Close database connection."""
        if hasattr(self._local, 'connection'):
            try:
                self._local.connection.close()
            except sqlite3.Error as e:
                print(f"[ERROR] Database connection close failed: {e}")
            finally:
                del self._local.connection

    def __del__(self) -> None:
        """Clean up database connection when object is destroyed."""
        self.close()

    def initialize_database(self) -> None:
        """Initialize database schema if it doesn't exist."""
        conn = self.get_connection()

        # Create files table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                size INTEGER NOT NULL,
                modified_time INTEGER NOT NULL,
                hash TEXT,
                is_duplicate BOOLEAN DEFAULT FALSE,
                duplicate_of INTEGER,
                FOREIGN KEY (duplicate_of) REFERENCES files(id)
            )
        ''')

        # Create file indexes for better performance
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_files_path ON files(path)')
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_files_hash ON files(hash)')
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_files_size ON files(size)')
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_files_duplicate ON files(is_duplicate)')

        # Create embeddings table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                model_version TEXT NOT NULL,
                created_time INTEGER NOT NULL,
                FOREIGN KEY (file_id) REFERENCES files(id),
                UNIQUE(file_id, model_version)
            )
        ''')

        # Create embedding indexes
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_embeddings_file ON embeddings(file_id)')
        conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model_version)')

        conn.commit()


def get_connection(db_path: str = "output/index.db") -> DatabaseConnection:
    """Get database connection instance.

    Args:
        db_path: Path to SQLite database file

    Returns:
        DatabaseConnection instance
    """
    return DatabaseConnection.get_instance(db_path)
