"""Database Schema Module.

Database schema definitions and migrations using standard library only.

Key Features:
    - Complete SQLite schema management
    - Schema versioning and migrations
    - Forward and backward migrations
    - Schema validation
    - Safe schema updates
    - Standard library only (no external dependencies)

Dependencies:
    - sqlite3 (standard library)
    - typing (standard library)
"""

import sqlite3
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import time


class SchemaError(Exception):
    """Schema operation error"""


class DatabaseSchema:
    """Handle database schema management.

    Provides complete schema lifecycle management including creation,
    migration, and validation based on DATABASE_SCHEMA.md specification.
    """

    # Current schema version
    SCHEMA_VERSION = "1.0.0"

    # Schema definitions from DATABASE_SCHEMA.md
    TABLES = {
        'files': """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                size INTEGER NOT NULL,
                modified_time INTEGER NOT NULL,
                created_time INTEGER NOT NULL,
                accessed_time INTEGER,
                file_type TEXT,
                mime_type TEXT,
                hash TEXT,
                is_duplicate BOOLEAN DEFAULT FALSE,
                duplicate_of INTEGER,
                status TEXT DEFAULT 'active',
                scanned_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                FOREIGN KEY (duplicate_of) REFERENCES files(id) ON DELETE SET NULL
            )
        """,

        'embeddings': """
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                model_version TEXT NOT NULL,
                created_time INTEGER NOT NULL,
                dimensions INTEGER NOT NULL,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """,

        'file_relationships': """
            CREATE TABLE IF NOT EXISTS file_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file1_id INTEGER NOT NULL,
                file2_id INTEGER NOT NULL,
                relationship_type TEXT NOT NULL,
                similarity_score REAL,
                created_at INTEGER NOT NULL,
                UNIQUE(file1_id, file2_id, relationship_type),
                FOREIGN KEY (file1_id) REFERENCES files(id) ON DELETE CASCADE,
                FOREIGN KEY (file2_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """,

        'plugins': """
            CREATE TABLE IF NOT EXISTS plugins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                version TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                load_order INTEGER DEFAULT 0,
                enabled BOOLEAN DEFAULT TRUE,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
        """,

        'plugin_config': """
            CREATE TABLE IF NOT EXISTS plugin_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plugin_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                updated_at INTEGER NOT NULL,
                UNIQUE(plugin_id, key),
                FOREIGN KEY (plugin_id) REFERENCES plugins(id) ON DELETE CASCADE
            )
        """,

        'scans': """
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_path TEXT NOT NULL,
                start_time INTEGER NOT NULL,
                end_time INTEGER,
                files_scanned INTEGER DEFAULT 0,
                files_added INTEGER DEFAULT 0,
                files_updated INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                error_message TEXT
            )
        """,

        'schema_version': """
            CREATE TABLE IF NOT EXISTS schema_version (
                version TEXT PRIMARY KEY,
                applied_at INTEGER NOT NULL,
                description TEXT
            )
        """
    }

    # Index definitions from DATABASE_SCHEMA.md
    INDEXES = [
        # Files table indexes
        "CREATE INDEX IF NOT EXISTS idx_files_path ON files(path)",
        "CREATE INDEX IF NOT EXISTS idx_files_size ON files(size)",
        "CREATE INDEX IF NOT EXISTS idx_files_hash ON files(hash)",
        "CREATE INDEX IF NOT EXISTS idx_files_is_duplicate ON files(is_duplicate)",
        "CREATE INDEX IF NOT EXISTS idx_files_duplicate_of ON files(duplicate_of)",
        "CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)",

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
        "CREATE INDEX IF NOT EXISTS idx_plugins_name ON plugins(name)",
        "CREATE INDEX IF NOT EXISTS idx_plugins_type ON plugins(type)",
        "CREATE INDEX IF NOT EXISTS idx_plugins_status ON plugins(status)",
        "CREATE INDEX IF NOT EXISTS idx_plugins_enabled ON plugins(enabled)",

        # Plugin config indexes
        "CREATE INDEX IF NOT EXISTS idx_plugin_config_plugin_id ON plugin_config(plugin_id)",
        "CREATE INDEX IF NOT EXISTS idx_plugin_config_key ON plugin_config(key)",

        # Scans table indexes
        "CREATE INDEX IF NOT EXISTS idx_scans_scan_path ON scans(scan_path)",
        "CREATE INDEX IF NOT EXISTS idx_scans_start_time ON scans(start_time)",
        "CREATE INDEX IF NOT EXISTS idx_scans_status ON scans(status)",
    ]

    def __init__(self, connection: sqlite3.Connection):
        """Initialize schema manager.

        Args:
            connection: SQLite database connection
        """
        self.connection = connection
        self.schemas = self.TABLES.copy()

    def create_schema(self) -> None:
        """Create complete database schema.

        Creates all tables and indexes according to DATABASE_SCHEMA.md
        specification.

        Raises:
            SchemaError: If schema creation fails
        """
        try:
            cursor = self.connection.cursor()

            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")

            # Create all tables
            for table_name, table_sql in self.TABLES.items():
                cursor.execute(table_sql)

            # Create all indexes
            for index_sql in self.INDEXES:
                cursor.execute(index_sql)

            # Record schema version
            current_time = int(time.monotonic())
            cursor.execute(
                "INSERT OR REPLACE INTO schema_version (version, applied_at, description) "
                "VALUES (?, ?, ?)",
                (self.SCHEMA_VERSION, current_time, "Initial schema creation")
            )

            self.connection.commit()

        except sqlite3.Error as e:
            self.connection.rollback()
            raise SchemaError(f"Failed to create schema: {e}") from e

    def get_schema_version(self) -> Optional[str]:
        """Get current schema version.

        Returns:
            Schema version string or None if not set

        Raises:
            SchemaError: If version check fails
        """
        try:
            cursor = self.connection.cursor()

            # Check if schema_version table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            )
            if not cursor.fetchone():
                return None

            # Get latest version
            cursor.execute(
                "SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1"
            )
            result = cursor.fetchone()
            return result[0] if result else None

        except sqlite3.Error as e:
            raise SchemaError(f"Failed to get schema version: {e}") from e

    def migrate_schema(self, target_version: Optional[str] = None) -> None:
        """Migrate database schema to target version.

        Args:
            target_version: Version to migrate to (None = latest)

        Raises:
            SchemaError: If migration fails
        """
        try:
            if target_version is None:
                target_version = self.SCHEMA_VERSION

            current_version = self.get_schema_version()

            if current_version == target_version:
                # Already at target version
                return

            if current_version is None:
                # No schema exists, create fresh
                self.create_schema()
                return

            # Perform migration based on version
            self._migrate_from_version(current_version, target_version)

        except Exception as e:
            if isinstance(e, SchemaError):
                raise
            raise SchemaError(f"Schema migration failed: {e}") from e

    def _migrate_from_version(self, from_version: str, to_version: str) -> None:
        """Perform migration from one version to another.

        Args:
            from_version: Current version
            to_version: Target version

        Raises:
            SchemaError: If migration not supported
        """
        # For now, only support 1.0.0 as this is the initial version
        # Future versions would add migration logic here
        if from_version == to_version:
            return

        raise SchemaError(
            f"Migration from {from_version} to {to_version} not implemented"
        )

    def validate_schema(self) -> Tuple[bool, List[str]]:
        """Validate database schema against specification.

        Returns:
            Tuple of (is_valid, list_of_errors)

        Raises:
            SchemaError: If validation fails
        """
        try:
            cursor = self.connection.cursor()
            errors = []

            # Check all tables exist
            for table_name in self.TABLES.keys():
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,)
                )
                if not cursor.fetchone():
                    errors.append(f"Table '{table_name}' does not exist")

            # Check all indexes exist
            expected_indexes = set()
            for index_sql in self.INDEXES:
                # Extract index name from SQL
                parts = index_sql.split()
                if 'INDEX' in parts:
                    idx = parts.index('INDEX')
                    if idx + 2 < len(parts):
                        index_name = parts[idx + 2]
                        expected_indexes.add(index_name)

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            existing_indexes = set(row[0] for row in cursor.fetchall())

            missing_indexes = expected_indexes - existing_indexes
            for index_name in missing_indexes:
                errors.append(f"Index '{index_name}' does not exist")

            return (len(errors) == 0, errors)

        except sqlite3.Error as e:
            raise SchemaError(f"Schema validation failed: {e}") from e

    def drop_schema(self) -> None:
        """Drop all tables (DANGEROUS - for testing only).

        Raises:
            SchemaError: If drop fails
        """
        try:
            cursor = self.connection.cursor()

            # Get all tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]

            # Drop all tables
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")

            self.connection.commit()

        except sqlite3.Error as e:
            self.connection.rollback()
            raise SchemaError(f"Failed to drop schema: {e}") from e

    def get_table_info(self, table_name: str) -> List[Dict]:
        """Get table column information.

        Args:
            table_name: Name of table

        Returns:
            List of column information dictionaries

        Raises:
            SchemaError: If table info cannot be retrieved
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")

            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'cid': row[0],
                    'name': row[1],
                    'type': row[2],
                    'notnull': bool(row[3]),
                    'default': row[4],
                    'pk': bool(row[5])
                })

            return columns

        except sqlite3.Error as e:
            raise SchemaError(f"Failed to get table info for {table_name}: {e}") from e

    def get_indexes(self, table_name: str) -> List[str]:
        """Get indexes for a table.

        Args:
            table_name: Name of table

        Returns:
            List of index names

        Raises:
            SchemaError: If index info cannot be retrieved
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?",
                (table_name,)
            )

            return [row[0] for row in cursor.fetchall()]

        except sqlite3.Error as e:
            raise SchemaError(f"Failed to get indexes for {table_name}: {e}") from e

    def optimize_database(self) -> None:
        """Optimize database (VACUUM and ANALYZE).

        Raises:
            SchemaError: If optimization fails
        """
        try:
            # Run ANALYZE to update statistics
            self.connection.execute("ANALYZE")

            # Run VACUUM to reclaim space (cannot be in transaction)
            # Save connection state
            isolation_level = self.connection.isolation_level
            self.connection.isolation_level = None
            try:
                self.connection.execute("VACUUM")
            finally:
                self.connection.isolation_level = isolation_level

        except sqlite3.Error as e:
            raise SchemaError(f"Database optimization failed: {e}") from e


def create_database(db_path: Path) -> sqlite3.Connection:
    """Create and initialize a new database.

    Args:
        db_path: Path to database file

    Returns:
        Database connection with schema created

    Raises:
        SchemaError: If database creation fails
    """
    try:
        # Create parent directory if needed
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect to database
        connection = sqlite3.connect(str(db_path))

        # Create schema
        schema = DatabaseSchema(connection)
        schema.create_schema()

        return connection

    except Exception as e:
        raise SchemaError(f"Failed to create database: {e}") from e
