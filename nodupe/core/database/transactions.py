"""Database Transactions Module.

Transaction management for database operations using standard library only.

Key Features:
    - ACID transaction support
    - Context manager for automatic rollback
    - Savepoint support
    - Transaction isolation levels
    - Nested transaction handling
    - Standard library only (no external dependencies)

Dependencies:
    - sqlite3 (standard library)
    - typing (standard library)
"""

import sqlite3
from typing import Any, Callable
from contextlib import contextmanager
from enum import Enum


class TransactionError(Exception):
    """Transaction operation error"""


class IsolationLevel(Enum):
    """SQL isolation levels"""
    DEFERRED = "DEFERRED"
    IMMEDIATE = "IMMEDIATE"
    EXCLUSIVE = "EXCLUSIVE"


class DatabaseTransaction:
    """Handle database transactions.

    Provides transaction management with support for commits, rollbacks,
    savepoints, and automatic cleanup using context managers.
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
        isolation_level: IsolationLevel = IsolationLevel.DEFERRED
    ):
        """Initialize transaction manager.

        Args:
            connection: SQLite database connection
            isolation_level: Transaction isolation level
        """
        self.connection = connection
        self.isolation_level = isolation_level
        self._in_transaction = False
        self._savepoints = []

    def begin_transaction(self) -> None:
        """Begin a transaction.

        Raises:
            TransactionError: If transaction is already active
        """
        try:
            if self._in_transaction:
                raise TransactionError("Transaction already active")

            # SQLite uses BEGIN to start transactions
            self.connection.execute(f"BEGIN {self.isolation_level.value}")
            self._in_transaction = True

        except sqlite3.Error as e:
            raise TransactionError(f"Failed to begin transaction: {e}") from e

    def commit_transaction(self) -> None:
        """Commit the current transaction.

        Raises:
            TransactionError: If no transaction is active
        """
        try:
            if not self._in_transaction:
                raise TransactionError("No active transaction to commit")

            self.connection.commit()
            self._in_transaction = False
            self._savepoints.clear()

        except sqlite3.Error as e:
            raise TransactionError(f"Failed to commit transaction: {e}") from e

    def rollback_transaction(self) -> None:
        """Rollback the current transaction.

        Raises:
            TransactionError: If no transaction is active
        """
        try:
            if not self._in_transaction:
                raise TransactionError("No active transaction to rollback")

            self.connection.rollback()
            self._in_transaction = False
            self._savepoints.clear()

        except sqlite3.Error as e:
            raise TransactionError(f"Failed to rollback transaction: {e}") from e

    def create_savepoint(self, name: str) -> None:
        """Create a savepoint within the current transaction.

        Args:
            name: Savepoint name

        Raises:
            TransactionError: If no transaction is active or savepoint creation fails
        """
        try:
            if not self._in_transaction:
                raise TransactionError("No active transaction for savepoint")

            # SQLite savepoint syntax
            self.connection.execute(f"SAVEPOINT {name}")
            self._savepoints.append(name)

        except sqlite3.Error as e:
            raise TransactionError(f"Failed to create savepoint '{name}': {e}") from e

    def release_savepoint(self, name: str) -> None:
        """Release a savepoint.

        Args:
            name: Savepoint name

        Raises:
            TransactionError: If savepoint doesn't exist
        """
        try:
            if name not in self._savepoints:
                raise TransactionError(f"Savepoint '{name}' does not exist")

            self.connection.execute(f"RELEASE SAVEPOINT {name}")
            self._savepoints.remove(name)

        except sqlite3.Error as e:
            raise TransactionError(f"Failed to release savepoint '{name}': {e}") from e

    def rollback_to_savepoint(self, name: str) -> None:
        """Rollback to a savepoint.

        Args:
            name: Savepoint name

        Raises:
            TransactionError: If savepoint doesn't exist
        """
        try:
            if name not in self._savepoints:
                raise TransactionError(f"Savepoint '{name}' does not exist")

            self.connection.execute(f"ROLLBACK TO SAVEPOINT {name}")

        except sqlite3.Error as e:
            raise TransactionError(f"Failed to rollback to savepoint '{name}': {e}") from e

    def execute_in_transaction(
        self,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute an operation within a transaction.

        Args:
            operation: Callable to execute
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation

        Returns:
            Result from operation

        Raises:
            TransactionError: If transaction fails
        """
        try:
            # Start transaction if not already active
            started_here = False
            if not self._in_transaction:
                self.begin_transaction()
                started_here = True

            try:
                # Execute operation
                result = operation(*args, **kwargs)

                # Commit if we started the transaction
                if started_here:
                    self.commit_transaction()

                return result

            except Exception:
                # Rollback if we started the transaction
                if started_here:
                    self.rollback_transaction()
                raise

        except Exception as e:
            if isinstance(e, TransactionError):
                raise
            raise TransactionError(f"Transaction execution failed: {e}") from e

    @contextmanager
    def transaction(self):
        """Context manager for automatic transaction handling.

        Yields:
            DatabaseTransaction instance

        Example:
            with db_transaction.transaction():
                # Do database operations
                db.execute("INSERT ...")
                # Automatically commits on success, rolls back on exception
        """
        self.begin_transaction()
        try:
            yield self
            self.commit_transaction()
        except Exception:
            self.rollback_transaction()
            raise

    @contextmanager
    def savepoint(self, name: str):
        """Context manager for savepoint handling.

        Args:
            name: Savepoint name

        Yields:
            Savepoint name

        Example:
            with db_transaction.savepoint('sp1'):
                # Do operations
                # Automatically releases on success, rolls back on exception
        """
        self.create_savepoint(name)
        try:
            yield name
            self.release_savepoint(name)
        except Exception:
            self.rollback_to_savepoint(name)
            raise

    @property
    def is_active(self) -> bool:
        """Check if transaction is active.

        Returns:
            True if transaction is active
        """
        return self._in_transaction

    def __enter__(self):
        """Context manager entry."""
        self.begin_transaction()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic rollback on exception."""
        if exc_type is not None:
            # Exception occurred, rollback
            self.rollback_transaction()
        else:
            # No exception, commit
            self.commit_transaction()
        return False  # Don't suppress exceptions


class DatabaseTransactions:
    """Factory class for creating transaction instances.

    Provides convenience methods for transaction management
    with backward compatibility for legacy code.
    """

    def __init__(self, connection: sqlite3.Connection):
        """Initialize transaction factory.

        Args:
            connection: SQLite database connection
        """
        self.connection = connection

    def begin_transaction(
        self,
        isolation_level: IsolationLevel = IsolationLevel.DEFERRED
    ) -> DatabaseTransaction:
        """Begin a new transaction.

        Args:
            isolation_level: Transaction isolation level

        Returns:
            DatabaseTransaction instance
        """
        transaction = DatabaseTransaction(self.connection, isolation_level)
        transaction.begin_transaction()
        return transaction

    def commit_transaction(self) -> None:
        """Commit the current transaction (legacy compatibility).

        Raises:
            TransactionError: If commit fails
        """
        try:
            self.connection.commit()
        except sqlite3.Error as e:
            raise TransactionError(f"Commit failed: {e}") from e

    def rollback_transaction(self) -> None:
        """Rollback the current transaction (legacy compatibility).

        Raises:
            TransactionError: If rollback fails
        """
        try:
            self.connection.rollback()
        except sqlite3.Error as e:
            raise TransactionError(f"Rollback failed: {e}") from e

    @contextmanager
    def transaction(
        self,
        isolation_level: IsolationLevel = IsolationLevel.DEFERRED
    ):
        """Context manager for transaction.

        Args:
            isolation_level: Transaction isolation level

        Yields:
            DatabaseTransaction instance

        Example:
            with db.transaction():
                # Database operations here
                cursor.execute("INSERT ...")
        """
        transaction = DatabaseTransaction(self.connection, isolation_level)
        with transaction:
            yield transaction

    @contextmanager
    def savepoint(self, name: str):
        """Context manager for savepoint.

        Args:
            name: Savepoint name

        Yields:
            Savepoint name

        Example:
            with db.savepoint('sp1'):
                # Operations that might fail
                cursor.execute("UPDATE ...")
        """
        try:
            self.connection.execute(f"SAVEPOINT {name}")
            yield name
            self.connection.execute(f"RELEASE SAVEPOINT {name}")
        except Exception:
            self.connection.execute(f"ROLLBACK TO SAVEPOINT {name}")
            raise

    def execute_in_transaction(
        self,
        operation: Callable,
        *args,
        isolation_level: IsolationLevel = IsolationLevel.DEFERRED,
        **kwargs
    ) -> Any:
        """Execute operation in a transaction.

        Args:
            operation: Callable to execute
            *args: Positional arguments
            isolation_level: Transaction isolation level
            **kwargs: Keyword arguments

        Returns:
            Result from operation
        """
        transaction = DatabaseTransaction(self.connection, isolation_level)
        return transaction.execute_in_transaction(operation, *args, **kwargs)


# Convenience function for creating transaction manager
def create_transaction_manager(
    connection: sqlite3.Connection
) -> DatabaseTransactions:
    """Create a transaction manager for a database connection.

    Args:
        connection: SQLite database connection

    Returns:
        DatabaseTransactions instance
    """
    return DatabaseTransactions(connection)
