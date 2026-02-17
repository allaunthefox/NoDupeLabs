"""Database Indexing Module.

Index creation and optimization using standard library only.

Key Features:
    - Index creation and management
    - Index optimization and analysis
    - Query performance monitoring
    - Index usage statistics
    - Covering indexes
    - Standard library only (no external dependencies)

Dependencies:
    - sqlite3 (standard library)
    - typing (standard library)
"""

import sqlite3
from typing import Any, Optional


class IndexingError(Exception):
    """Indexing operation error"""


class DatabaseIndexing:
    """Handle database indexing operations.

    Provides comprehensive index management including creation,
    optimization, and performance monitoring.
    """

    def __init__(self, connection: sqlite3.Connection):
        """Initialize indexing manager.

        Args:
            connection: SQLite database connection
        """
        self.connection = connection

    def create_indexes(self) -> None:
        """Create all recommended indexes.

        Raises:
            IndexingError: If index creation fails
        """
        try:
            cursor = self.connection.cursor()

            # Files table indexes (from schema)
            indexes: list[str] = [
                "CREATE INDEX IF NOT EXISTS idx_files_path ON files(path)",
                "CREATE INDEX IF NOT EXISTS idx_files_size ON files(size)",
                "CREATE INDEX IF NOT EXISTS idx_files_hash ON files(hash)",
                "CREATE INDEX IF NOT EXISTS idx_files_is_duplicate ON files(is_duplicate)",
                "CREATE INDEX IF NOT EXISTS idx_files_duplicate_of ON files(duplicate_of)",
                "CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)",
                "CREATE INDEX IF NOT EXISTS idx_files_modified_time ON files(modified_time)",

                # Embeddings table indexes
                "CREATE INDEX IF NOT EXISTS idx_embeddings_file_id ON embeddings(file_id)",
                "CREATE INDEX IF NOT EXISTS idx_embeddings_model_version ON embeddings(model_version)",
                "CREATE INDEX IF NOT EXISTS idx_embeddings_created_time ON embeddings(created_time)",

                # File relationships indexes
                "CREATE INDEX IF NOT EXISTS idx_file_relationships_file1_id ON file_relationships(file1_id)",
                "CREATE INDEX IF NOT EXISTS idx_file_relationships_file2_id ON file_relationships(file2_id)",
                "CREATE INDEX IF NOT EXISTS idx_file_relationships_type ON file_relationships(relationship_type)",
                "CREATE INDEX IF NOT EXISTS idx_file_relationships_similarity ON file_relationships(similarity_score)",

                # Plugins table indexes
                "CREATE INDEX IF NOT EXISTS idx_tools_name ON tools(name)",
                "CREATE INDEX IF NOT EXISTS idx_tools_type ON tools(type)",
                "CREATE INDEX IF NOT EXISTS idx_tools_status ON tools(status)",
                "CREATE INDEX IF NOT EXISTS idx_tools_enabled ON tools(enabled)",

                # Composite indexes for common queries
                (
                    "CREATE INDEX IF NOT EXISTS idx_files_status_duplicate "
                    "ON files(status, is_duplicate)"
                ),
                (
                    "CREATE INDEX IF NOT EXISTS idx_file_relationships_similarity_type "
                    "ON file_relationships(similarity_score, relationship_type)"
                ),
            ]

            for index_sql in indexes:
                cursor.execute(index_sql)

            self.connection.commit()

        except sqlite3.Error as e:
            self.connection.rollback()
            raise IndexingError(f"Failed to create indexes: {e}") from e

    def optimize_indexes(self) -> None:
        """Optimize database indexes using ANALYZE.

        Updates SQLite query planner statistics for better query performance.

        Raises:
            IndexingError: If optimization fails
        """
        try:
            # Run ANALYZE to update index statistics
            self.connection.execute("ANALYZE")
            self.connection.commit()

        except sqlite3.Error as e:
            raise IndexingError(f"Index optimization failed: {e}") from e

    def create_index(
        self,
        index_name: str,
        table_name: str,
        columns: list[str],
        unique: bool = False,
        if_not_exists: bool = True
    ) -> None:
        """Create a custom index.

        Args:
            index_name: Name of the index
            table_name: Name of the table
            columns: List of column names
            unique: Create unique index
            if_not_exists: Use IF NOT EXISTS clause

        Raises:
            IndexingError: If index creation fails
        """
        try:
            cursor = self.connection.cursor()

            # Build index SQL
            unique_clause = "UNIQUE " if unique else ""
            exists_clause = "IF NOT EXISTS " if if_not_exists else ""
            columns_str = ", ".join(columns)

            index_sql = (
                f"CREATE {unique_clause}INDEX {exists_clause}{index_name} "
                f"ON {table_name}({columns_str})"
            )

            cursor.execute(index_sql)
            self.connection.commit()

        except sqlite3.Error as e:
            self.connection.rollback()
            raise IndexingError(f"Failed to create index {index_name}: {e}") from e

    def drop_index(self, index_name: str, if_exists: bool = True) -> None:
        """Drop an index.

        Args:
            index_name: Name of the index to drop
            if_exists: Use IF EXISTS clause

        Raises:
            IndexingError: If index drop fails
        """
        try:
            cursor = self.connection.cursor()

            exists_clause = "IF EXISTS " if if_exists else ""
            drop_sql = f"DROP INDEX {exists_clause}{index_name}"

            cursor.execute(drop_sql)
            self.connection.commit()

        except sqlite3.Error as e:
            self.connection.rollback()
            raise IndexingError(f"Failed to drop index {index_name}: {e}") from e

    def get_indexes(self, table_name: Optional[str] = None) -> list[dict[str, Any]]:
        """Get list of indexes.

        Args:
            table_name: Filter by table name (None = all indexes)

        Returns:
            List of index information dictionaries

        Raises:
            IndexingError: If getting indexes fails
        """
        try:
            cursor = self.connection.cursor()

            if table_name:
                cursor.execute(
                    "SELECT name, tbl_name, sql FROM sqlite_master "
                    "WHERE type='index' AND tbl_name=? AND name NOT LIKE 'sqlite_%'",
                    (table_name,)
                )
            else:
                cursor.execute(
                    "SELECT name, tbl_name, sql FROM sqlite_master "
                    "WHERE type='index' AND name NOT LIKE 'sqlite_%'"
                )

            indexes: list[dict[str, Any]] = []
            for row in cursor.fetchall():
                indexes.append({
                    'name': row[0],
                    'table': row[1],
                    'sql': row[2]
                })

            return indexes

        except sqlite3.Error as e:
            raise IndexingError(f"Failed to get indexes: {e}") from e

    def get_index_info(self, index_name: str) -> list[dict[str, Any]]:
        """Get detailed information about an index.

        Args:
            index_name: Name of the index

        Returns:
            List of column information for the index

        Raises:
            IndexingError: If getting index info fails
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA index_info({index_name})")

            columns: list[dict[str, Any]] = []
            for row in cursor.fetchall():
                columns.append({
                    'seqno': row[0],
                    'cid': row[1],
                    'name': row[2]
                })

            return columns

        except sqlite3.Error as e:
            raise IndexingError(f"Failed to get index info for {index_name}: {e}") from e

    def analyze_query(self, query: str) -> list[dict[str, Any]]:
        """Analyze query execution plan.

        Args:
            query: SQL query to analyze

        Returns:
            List of execution plan steps

        Raises:
            IndexingError: If query analysis fails
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")

            plan: list[dict[str, Any]] = []
            rows = cursor.fetchall()
            for row in rows:
                plan_item: dict[str, Any] = {
                    'id': row[0],
                    'parent': row[1],
                    'detail': row[3] if len(row) > 3 else row[2]
                }
                plan.append(plan_item)

            return plan

        except sqlite3.Error as e:
            raise IndexingError(f"Query analysis failed: {e}") from e

    def is_index_used(self, query: str, index_name: str) -> bool:
        """Check if a query uses a specific index.

        Args:
            query: SQL query
            index_name: Name of the index

        Returns:
            True if index is used in query plan

        Raises:
            IndexingError: If check fails
        """
        try:
            plan = self.analyze_query(query)

            for step in plan:
                detail = step.get('detail', '').lower()
                if index_name.lower() in detail:
                    return True

            return False

        except Exception as e:
            if isinstance(e, IndexingError):
                raise
            raise IndexingError(f"Index usage check failed: {e}") from e

    def get_table_stats(self, table_name: str) -> dict[str, Any]:
        """Get table statistics.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with table statistics

        Raises:
            IndexingError: If getting stats fails
        """
        try:
            cursor = self.connection.cursor()

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]

            # Get table size (approximate)
            cursor.execute(
                "SELECT SUM(pgsize) FROM dbstat WHERE name=?",
                (table_name,)
            )
            result = cursor.fetchone()
            table_size = result[0] if result[0] else 0

            # Get indexes
            cursor.execute(
                "SELECT COUNT(*) FROM sqlite_master "
                "WHERE type='index' AND tbl_name=?",
                (table_name,)
            )
            index_count = cursor.fetchone()[0]

            return {
                'table_name': table_name,
                'row_count': row_count,
                'table_size_bytes': table_size,
                'index_count': index_count
            }

        except sqlite3.Error as e:
            raise IndexingError(f"Failed to get table stats for {table_name}: {e}") from e

    def reindex(self, index_name: Optional[str] = None) -> None:
        """Rebuild indexes.

        Args:
            index_name: Specific index to rebuild (None = all)

        Raises:
            IndexingError: If reindex fails
        """
        try:
            if index_name:
                self.connection.execute(f"REINDEX {index_name}")
            else:
                self.connection.execute("REINDEX")

            self.connection.commit()

        except sqlite3.Error as e:
            self.connection.rollback()
            raise IndexingError(f"Reindex failed: {e}") from e

    def find_missing_indexes(self) -> list[dict[str, Any]]:
        """Find tables without indexes (except primary key).

        Returns:
            List of tables that might benefit from indexes

        Raises:
            IndexingError: If analysis fails
        """
        try:
            cursor = self.connection.cursor()

            # Get all tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [row[0] for row in cursor.fetchall()]

            suggestions: list[dict[str, Any]] = []

            for table in tables:
                # Get table info
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]

                # Get existing indexes
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?",
                    (table,)
                )
                indexes = [row[0] for row in cursor.fetchall()]

                # Check if table has non-pk indexes
                if not indexes:
                    # Suggest indexes on common column types
                    for col in columns:
                        if col.lower() in ['id', 'created_at', 'updated_at', 'status', 'type']:
                            suggestions.append({
                                'table': table,
                                'column': col,
                                'reason': f'Common query column: {col}'
                            })

            return suggestions

        except sqlite3.Error as e:
            raise IndexingError(f"Missing index analysis failed: {e}") from e

    def get_index_stats(self) -> dict[str, Any]:
        """Get overall index statistics.

        Returns:
            Dictionary with index statistics

        Raises:
            IndexingError: If getting stats fails
        """
        try:
            cursor = self.connection.cursor()

            # Total indexes
            cursor.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
            )
            total_indexes = cursor.fetchone()[0]

            # Indexes by table
            cursor.execute(
                "SELECT tbl_name, COUNT(*) FROM sqlite_master "
                "WHERE type='index' AND name NOT LIKE 'sqlite_%' GROUP BY tbl_name"
            )
            by_table = {row[0]: row[1] for row in cursor.fetchall()}

            # Total tables
            cursor.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            total_tables = cursor.fetchone()[0]

            return {
                'total_indexes': total_indexes,
                'total_tables': total_tables,
                'indexes_by_table': by_table,
                'avg_indexes_per_table': total_indexes / total_tables if total_tables > 0 else 0
            }

        except sqlite3.Error as e:
            raise IndexingError(f"Failed to get index stats: {e}") from e


# Convenience function for creating covering indexes
def create_covering_index(
    connection: sqlite3.Connection,
    index_name: str,
    table_name: str,
    where_columns: list[str],
    select_columns: list[str]
) -> None:
    """Create a covering index for a specific query pattern.

    Args:
        connection: Database connection
        index_name: Name for the index
        table_name: Table name
        where_columns: Columns used in WHERE clause
        select_columns: Columns used in SELECT clause

    Raises:
        IndexingError: If index creation fails
    """
    try:
        # Combine columns (WHERE columns first, then SELECT columns)
        all_columns = where_columns + [c for c in select_columns if c not in where_columns]
        columns_str = ", ".join(all_columns)

        index_sql = (
            f"CREATE INDEX IF NOT EXISTS {index_name} "
            f"ON {table_name}({columns_str})"
        )

        connection.execute(index_sql)
        connection.commit()

    except sqlite3.Error as e:
        connection.rollback()
        raise IndexingError(f"Failed to create covering index: {e}") from e
