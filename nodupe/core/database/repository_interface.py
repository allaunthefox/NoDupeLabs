"""Database Repository Interface.

Generic repository pattern for database operations.

Key Features:
    - Generic CRUD operations for any table
    - Type-safe parameter handling
    - Error handling and validation
    - Connection management
    - Standard library only (no external dependencies)

Dependencies:
    - sqlite3 (standard library)
    - typing (standard library)
"""

import sqlite3
from typing import Dict, Any, Optional, List


class RepositoryError(Exception):
    """Repository operation error"""


class DatabaseRepository:
    """Generic database repository pattern for CRUD operations.
    
    Provides a consistent interface for database operations across tables.
    """

    def __init__(self, connection: sqlite3.Connection):
        """Initialize repository with database connection.
        
        Args:
            connection: SQLite database connection
        """
        self.connection = connection

    def create(self, table: str, data: Dict[str, Any]) -> int:
        """Create a new record in the specified table."""
        raise NotImplementedError("create must be implemented by subclasses")

    def read(self, table: str, record_id: int) -> Optional[Dict[str, Any]]:
        """Read a record by ID from the specified table."""
        raise NotImplementedError("read must be implemented by subclasses")

    def read_all(self, table: str, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Read all records from the specified table.
        
        Args:
            table: Name of the table
            where: Optional dictionary of column names to values for filtering
            
        Returns:
            List of dictionaries of column names to values
            
        Raises:
            RepositoryError: If read operation fails
        """
        try:
            cursor = self.connection.cursor()
            
            if where:
                # Build WHERE clause
                where_clause = ' AND '.join([f"{k} = ?" for k in where.keys()])
                query = f"SELECT * FROM {table} WHERE {where_clause}"
                cursor.execute(query, list(where.values()))
            else:
                cursor.execute(f"SELECT * FROM {table}")
            
            rows = cursor.fetchall()
            if not rows:
                return []
                
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Build list of dictionaries
            return [dict(zip(columns, row)) for row in rows]
            
        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to read records from {table}: {e}") from e

    def update(self, table: str, record_id: int, data: Dict[str, Any]) -> bool:
        """Update a record in the specified table."""
        raise NotImplementedError("update must be implemented by subclasses")

    def delete(self, table: str, record_id: int) -> bool:
        """Delete a record from the specified table."""
        raise NotImplementedError("delete must be implemented by subclasses")

    def count(self, table: str, where: Optional[Dict[str, Any]] = None) -> int:
        """Count records in the specified table.
        
        Args:
            table: Name of the table
            where: Optional dictionary of column names to values for filtering
            
        Returns:
            Number of records
            
        Raises:
            RepositoryError: If count operation fails
        """
        try:
            cursor = self.connection.cursor()
            
            if where:
                # Build WHERE clause
                where_clause = ' AND '.join([f"{k} = ?" for k in where.keys()])
                query = f"SELECT COUNT(*) FROM {table} WHERE {where_clause}"
                cursor.execute(query, list(where.values()))
            else:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
            
            result = cursor.fetchone()
            return result[0] if result else 0
            
        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to count records in {table}: {e}") from e

    def exists(self, table: str, record_id: int) -> bool:
        """Check if a record exists in the specified table.
        
        Args:
            table: Name of the table
            record_id: ID of the record to check
            
        Returns:
            True if record exists, False otherwise
            
        Raises:
            RepositoryError: If check fails
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT 1 FROM {table} WHERE id = ? LIMIT 1", (record_id,))
            
            return cursor.fetchone() is not None
            
        except sqlite3.Error as e:
            raise RepositoryError(f"Failed to check existence in {table}: {e}") from e


def create_repository(connection: sqlite3.Connection) -> DatabaseRepository:
    """Create a database repository instance.
    
    Args:
        connection: SQLite database connection
        
    Returns:
        DatabaseRepository instance
    """
    return DatabaseRepository(connection)
