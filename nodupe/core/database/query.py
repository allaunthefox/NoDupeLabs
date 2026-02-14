# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Database query functionality."""

from typing import Any, Dict, List, Tuple
import sqlite3

class DatabaseQuery:
    """Database query functionality."""

    def __init__(self, db):
        """TODO: Document __init__."""
        self.db = db

    def execute(self, query: str, params: Tuple = None) -> List[Dict[str, Any]]:
        """Execute query and return results."""
        if hasattr(self.db, 'get_connection'):
            conn = self.db.get_connection()
        else:
            conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        results = []

        for row in cursor.fetchall():
            results.append(dict(zip([d[0] for d in cursor.description], row)))

        return results

class DatabaseBatch:
    """Database batch operations."""

    def __init__(self, db):
        """TODO: Document __init__."""
        self.db = db

    def execute_batch(self, operations: List[Tuple[str, Tuple]]) -> None:
        """Execute batch operations."""
        if hasattr(self.db, 'get_connection'):
            conn = self.db.get_connection()
        else:
            conn = self.db.connect()
        cursor = conn.cursor()

        for query, params in operations:
            cursor.execute(query, params)

        conn.commit()

    def execute_transaction_batch(self, operations: List[Tuple[str, Tuple]]) -> None:
        """Execute batch operations within a transaction."""
        if hasattr(self.db, 'get_connection'):
            conn = self.db.get_connection()
        else:
            conn = self.db.connect()
        cursor = conn.cursor()

        try:
            for query, params in operations:
                cursor.execute(query, params)

            conn.commit()
        except Exception:
            conn.rollback()
            raise

class DatabasePerformance:
    """Database performance monitoring."""

    def __init__(self, db):
        """TODO: Document __init__."""
        self.db = db

    def monitor_performance(self):
        """Context manager for performance monitoring."""
        return self.db.monitoring

    def get_results(self):
        """Get performance results."""
        return self.db.monitoring.get_metrics()

class DatabaseIntegrity:
    """Database integrity checking."""

    def __init__(self, db):
        """TODO: Document __init__."""
        self.db = db

    def check_integrity(self) -> Dict[str, Any]:
        """Check database integrity."""
        return self.db.validation.validate()

class DatabaseBackup:
    """Database backup functionality."""

    def __init__(self, db):
        """TODO: Document __init__."""
        self.db = db

    def create_backup(self, backup_path: str) -> None:
        """Create database backup."""
        import shutil
        shutil.copy2(self.db.path, backup_path)

    def restore_backup(self, backup_path: str, restore_path: str) -> None:
        """Restore database from backup."""
        import shutil
        shutil.copy2(backup_path, restore_path)

class DatabaseMigration:
    """Database migration functionality."""

    def __init__(self, db):
        """TODO: Document __init__."""
        self.db = db

    def migrate_schema(self, migrations: Dict[str, Dict[str, List[str]]]) -> None:
        """Migrate database schema."""
        self.db.schema_migration.migrate_schema(migrations)

    def migrate_data(self, table_name: str, transformations: Dict[str, str], new_columns: List[str] = None) -> None:
        """Migrate data in the specified table."""
        self.db.data_migration.migrate_data(table_name, transformations, new_columns)

class DatabaseRecovery:
    """Database recovery functionality."""

    def __init__(self, db):
        """TODO: Document __init__."""
        self.db = db

    def handle_errors(self, raise_on_error: bool = False):
        """Handle database errors."""
        try:
            # Check database integrity
            integrity = self.db.integrity.check_integrity()
            if not integrity.get('valid', True):
                if raise_on_error:
                    raise Exception("Database integrity check failed")
                return False
            return True
        except Exception as e:
            if raise_on_error:
                raise
            return False

class DatabaseOptimization:
    """Database optimization functionality."""

    def __init__(self, db):
        """TODO: Document __init__."""
        self.db = db

    def optimize_query(self, query: str) -> str:
        """Optimize database query."""
        # Basic query optimization
        optimized = query.strip()
        if optimized.endswith(';'):
            optimized = optimized[:-1]
        return optimized
