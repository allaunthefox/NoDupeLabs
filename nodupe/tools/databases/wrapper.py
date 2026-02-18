# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Database Wrapper Module.

This module provides the main Database wrapper class for comprehensive database
operations in NoDupeLabs. It serves as the primary interface for all database
interactions, including connection management, query execution, transactions,
and component orchestration.

This is a clean refactored version that fixes architectural issues from the
original implementation, including:
- Fixed dual-purpose attribute conflict (transaction object vs context manager)
- Added missing component attributes (logging, cache, locking, session, etc.)
- Fixed component dependencies (pass Connection, not Database)

Classes:
    Database: High-level database wrapper for SQLite operations.
    DatabaseError: Exception raised for database operation errors.

Example:
    >>> from nodupe.core.database import Database
    >>> db = Database("/path/to/database.db")
    >>> db.connect()
    >>> results = db.read("SELECT * FROM files WHERE id = ?", (1,))
    >>> db.close()
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any, Optional

from .cache import DatabaseCache
from .cleanup import DatabaseCleanup
from .compression import DatabaseCompression
from .connection import DatabaseConnection
from .indexing import DatabaseIndexing
from .locking import DatabaseLocking
from .logging_ import DatabaseLogging
from .query import (
    DatabaseBackup,
    DatabaseBatch,
    DatabaseIntegrity,
    DatabaseMigration,
    DatabasePerformance,
    DatabaseQuery,
    DatabaseRecovery,
)
from .schema import DatabaseSchema
from .security import DatabaseSecurity
from .serialization import DatabaseSerialization
from .session import DatabaseSession
from .transactions import DatabaseTransaction


class DatabaseError(Exception):
    """Exception raised for database operation errors.

    This exception is raised when any database operation fails, including
    connection errors, query execution errors, or transaction errors.

    Attributes:
        message: The error message describing the failure.

    Example:
        >>> try:
        ...     db.create_table("invalid name", "col TEXT")
        ... except DatabaseError as e:
        ...     print(f"Database error: {e}")
        >>> # doctest: +SKIP
    """

    def __init__(self, message: str) -> None:
        """Initialize DatabaseError with message.

        Args:
            message: The error message describing the failure.
        """
        self.message = message
        super().__init__(self.message)


class Database:
    """High-level database wrapper class for comprehensive database operations.

    This class provides a unified interface for all database operations in
    NoDupeLabs. It manages connections, executes queries, handles transactions,
    and provides access to various database components.

    Attributes:
        path: Path to the SQLite database file.
        timeout: Database connection timeout in seconds.
        connection: DatabaseConnection instance for low-level operations.
        schema: DatabaseSchema instance for schema management.
        indexing: DatabaseIndexing instance for index management.
        query: DatabaseQuery instance for query execution.
        batch: DatabaseBatch instance for batch operations.
        transaction_manager: DatabaseTransaction instance for transaction handling.
        performance: DatabasePerformance instance for performance monitoring.
        integrity: DatabaseIntegrity instance for integrity checks.
        backup: DatabaseBackup instance for backup operations.
        migration: DatabaseMigration instance for schema migrations.
        recovery: DatabaseRecovery instance for error recovery.
        security: DatabaseSecurity instance for security validation.
        logging: DatabaseLogging instance for logging operations.
        cache: DatabaseCache instance for caching.
        locking: DatabaseLocking instance for locking mechanisms.
        session: DatabaseSession instance for session management.
        compression: DatabaseCompression instance for data compression.
        serialization: DatabaseSerialization instance for serialization.
        cleanup: DatabaseCleanup instance for cleanup operations.

    Example:
        >>> db = Database("/path/to/database.db", timeout=30.0)
        >>> with db.transaction():
        ...     db.create("files", {"path": "/test.txt", "size": 100})
        >>> db.close()
    """

    def __init__(self, db_path: str, timeout: float = 30.0) -> None:
        """Initialize the Database wrapper.

        Args:
            db_path: Path to SQLite database file.
            timeout: Database connection timeout in seconds (default: 30.0).

        Raises:
            DatabaseError: If database initialization fails.

        Example:
            >>> db = Database("/path/to/database.db")
            >>> db = Database("/path/to/database.db", timeout=60.0)
        """
        self.path: str = db_path
        self.timeout: float = timeout
        self._connection: Optional[sqlite3.Connection] = None

        # Initialize connection first (components depend on it)
        # Note: DatabaseConnection only takes db_path (timeout is handled internally)
        self.connection: DatabaseConnection = DatabaseConnection(db_path)

        # Initialize components with connection (not Database instance)
        self.schema: DatabaseSchema = DatabaseSchema(self.connection)
        self.indexing: DatabaseIndexing = DatabaseIndexing(self.connection)
        self.query: DatabaseQuery = DatabaseQuery(self.connection)
        self.batch: DatabaseBatch = DatabaseBatch(self.connection)

        # FIXED: Renamed from 'transaction' to 'transaction_manager'
        # to avoid conflict with the context manager method below
        self.transaction_manager: DatabaseTransaction = DatabaseTransaction(
            self.connection
        )

        self.performance: DatabasePerformance = DatabasePerformance(
            self.connection
        )
        self.integrity: DatabaseIntegrity = DatabaseIntegrity(self.connection)
        self.backup: DatabaseBackup = DatabaseBackup(self.connection)
        self.migration: DatabaseMigration = DatabaseMigration(self.connection)
        self.recovery: DatabaseRecovery = DatabaseRecovery(self.connection)
        self.security: DatabaseSecurity = DatabaseSecurity(self.connection)

        # ADDED: Missing components that were referenced but didn't exist
        self.logging: DatabaseLogging = DatabaseLogging(self.connection)
        self.cache: DatabaseCache = DatabaseCache(self.connection)
        self.locking: DatabaseLocking = DatabaseLocking(self.connection)
        self.session: DatabaseSession = DatabaseSession(self.connection)
        self.compression: DatabaseCompression = DatabaseCompression(
            self.connection
        )
        self.serialization: DatabaseSerialization = DatabaseSerialization(
            self.connection
        )
        self.cleanup: DatabaseCleanup = DatabaseCleanup(self.connection)

        # BACKWARD COMPATIBILITY ALIASES - Map old attribute names to new
        # These aliases ensure compatibility with existing code/tests
        self.monitoring = self.performance  # Alias for performance monitoring
        self.validation = self.integrity  # Alias for integrity checking
        self.schema_migration = self.migration  # Alias for migration
        self.optimization = self.performance  # Alias for optimization

    def connect(self) -> sqlite3.Connection:
        """Get a database connection.

        Returns the SQLite connection object for direct database operations.

        Returns:
            sqlite3.Connection: The active database connection.

        Raises:
            DatabaseError: If connection fails.

        Example:
            >>> conn = db.connect()
            >>> cursor = conn.execute("SELECT * FROM files")
        """
        return self.connection.get_connection()

    def close(self) -> None:
        """Close the database connection.

        Closes the underlying database connection and releases all resources.
        After calling this method, the database should not be used until
        a new connection is established.

        Example:
            >>> db.close()
        """
        self.connection.close()

    def create_table(self, table_name: str, schema: str) -> None:
        """Create a table with the given schema.

        Validates the table name and schema using the security module,
        then creates the table in the database.

        Args:
            table_name: Name of the table to create.
            schema: SQL schema definition for the table.

        Raises:
            DatabaseError: If table creation fails.
            ValueError: If table name or schema fails validation.

        Example:
            >>> db.create_table("files", "id INTEGER PRIMARY KEY, path TEXT")
        """
        # Validate table name and schema using security module
        self.security.validate_identifier(table_name)
        self.security.validate_schema(schema)

        conn = self.connect()
        try:
            # Use parameterized query for table creation
            conn.execute(f"CREATE TABLE {table_name} ({schema})")
        except sqlite3.Error as e:
            raise DatabaseError(
                f"Failed to create table {table_name}: {self.security.sanitize_error_message(str(e))}"
            )

    def create(self, table_name: str, data: dict[str, Any]) -> Optional[int]:
        """Create a record and return the inserted ID.

        Inserts a new record into the specified table with the given data.

        Args:
            table_name: Name of the table to insert into.
            data: Dictionary of column names to values.

        Returns:
            Optional[int]: The ID of the inserted row, or None if no ID was generated.

        Raises:
            DatabaseError: If insert operation fails.

        Example:
            >>> db.create("files", {"path": "/test.txt", "size": 100})
            1
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, tuple(data.values()))
        conn.commit()
        return cursor.lastrowid

    def read(
        self, query: str, params: Optional[tuple] = None
    ) -> list[dict[str, Any]]:
        """Read records from the database.

        Executes a SELECT query and returns the results as a list of dictionaries.

        Args:
            query: SQL SELECT query to execute.
            params: Optional tuple of parameters for the query.

        Returns:
            List[Dict[str, Any]]: List of row dictionaries.

        Raises:
            DatabaseError: If query execution fails.

        Example:
            >>> results = db.read("SELECT * FROM files WHERE size > ?", (100,))
            [{'id': 1, 'path': '/test.txt', 'size': 200}, ...]
        """
        return self.query.execute(query, params or ())

    def update(self, query: str, params: Optional[tuple] = None) -> int:
        """Update records in the database.

        Executes an UPDATE query and returns the number of affected rows.

        Args:
            query: SQL UPDATE query to execute.
            params: Optional tuple of parameters for the query.

        Returns:
            int: Number of rows affected.

        Raises:
            DatabaseError: If update operation fails.

        Example:
            >>> count = db.update("UPDATE files SET size = ? WHERE id = ?", (200, 1))
            1
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.rowcount

    def delete(self, query: str, params: Optional[tuple] = None) -> int:
        """Delete records from the database.

        Executes a DELETE query and returns the number of affected rows.

        Args:
            query: SQL DELETE query to execute.
            params: Optional tuple of parameters for the query.

        Returns:
            int: Number of rows deleted.

        Raises:
            DatabaseError: If delete operation fails.

        Example:
            >>> count = db.delete("DELETE FROM files WHERE id = ?", (1,))
            1
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.rowcount

    def execute_batch(self, operations: list[tuple[str, tuple]]) -> None:
        """Execute multiple operations as a batch.

        Executes multiple SQL operations in sequence without transaction wrapping.

        Args:
            operations: List of (query, params) tuples.

        Raises:
            DatabaseError: If any operation fails.

        Example:
            >>> ops = [
            ...     ("INSERT INTO files (path, size) VALUES (?, ?)", ("/a.txt", 100)),
            ...     ("INSERT INTO files (path, size) VALUES (?, ?)", ("/b.txt", 200))
            ... ]
            >>> db.execute_batch(ops)
        """
        self.batch.execute_batch(operations)

    def execute_transaction_batch(
        self, operations: list[tuple[str, tuple]]
    ) -> None:
        """Execute multiple operations within a transaction.

        Executes multiple SQL operations atomically within a single transaction.
        If any operation fails, all changes are rolled back.

        Args:
            operations: List of (query, params) tuples.

        Raises:
            DatabaseError: If any operation fails.

        Example:
            >>> ops = [
            ...     ("INSERT INTO files (path, size) VALUES (?, ?)", ("/a.txt", 100)),
            ...     ("UPDATE files SET size = ? WHERE path = ?", (200, "/a.txt"))
            ... ]
            >>> db.execute_transaction_batch(ops)
        """
        self.batch.execute_transaction_batch(operations)

    @contextmanager
    def transaction(self):
        """Context manager for database transactions.

        Provides transactional semantics for database operations. All operations
        within the context are executed atomically - if any operation fails,
        all changes are rolled back.

        Yields:
            None: No value is yielded, the context manages the transaction.

        Raises:
            DatabaseError: If transaction fails.

        Example:
            >>> with db.transaction():
            ...     db.create("files", {"path": "/test.txt"})
            ...     db.update("UPDATE files SET size = 100 WHERE path = ?", ("/test.txt",))
        """
        # FIXED: Now references transaction_manager (not transaction itself)
        # to avoid the dual-purpose attribute conflict
        # Using the transaction context manager from DatabaseTransaction
        with self.transaction_manager.transaction():
            yield

    def __enter__(self) -> Database:
        """Enter the context manager protocol.

        Returns:
            Database: Self reference for context management.

        Example:
            >>> with Database("/path/to/db.db") as db:
            ...     db.read("SELECT * FROM files")
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context manager protocol.

        Closes the database connection when exiting the context.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.

        Example:
            >>> with Database("/path/to/db.db") as db:
            ...     pass
            >>> # db is now closed
        """
        self.close()
