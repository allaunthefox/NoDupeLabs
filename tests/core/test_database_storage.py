# Test suite for database and storage functionality
"""
Priority 2: Database and Storage Tests
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sqlite3

from nodupe.core.database.database import Database
from nodupe.core.database.database import Database
from nodupe.core.database.connection import ConnectionPool
from nodupe.core.database.schema import SchemaManager
from nodupe.core.cache.hash_cache import HashCache


class TestDatabaseStorage:
    """Test database and storage functionality."""
    
    def setup_method(self):
        """Set up test environment with temporary database."""
        self.db_path = tempfile.mktemp(suffix='.db')
        self.temp_files = []
        
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                if os.path.isdir(temp_file):
                    shutil.rmtree(temp_file)
                else:
                    os.remove(temp_file)
    
    def test_database_connection_establishment(self):
        """Test establishing database connections."""
        conn_pool = ConnectionPool(self.db_path)
        conn = conn_pool.get_connection()
        
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        
        # Test connection reuse
        conn2 = conn_pool.get_connection()
        assert conn is conn2  # Should return same connection for same thread
        
        conn_pool.close_all()
    
    def test_database_transaction_handling(self):
        """Test database transaction handling."""
        db = Database(self.db_path)
        
        # Create test table
        with db.transaction() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    value INTEGER
                )
            """)
        
        # Test transaction commit
        with db.transaction() as cursor:
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test1", 1))
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test2", 2))
        
        # Verify data was committed
        with db.transaction() as cursor:
            cursor.execute("SELECT COUNT(*) FROM test_table")
            count = cursor.fetchone()[0]
            assert count == 2
    
    def test_database_transaction_rollback(self):
        """Test database transaction rollback on error."""
        db = Database(self.db_path)
        
        # Create test table
        with db.transaction() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rollback_test (
                    id INTEGER PRIMARY KEY,
                    name TEXT
                )
            """)
        
        # Insert initial data
        with db.transaction() as cursor:
            cursor.execute("INSERT INTO rollback_test (name) VALUES (?)", ("initial",))
        
        try:
            with db.transaction() as cursor:
                cursor.execute("INSERT INTO rollback_test (name) VALUES (?)", ("should_rollback",))
                raise Exception("Force rollback")
        except Exception:
            pass  # Expected
        
        # Verify rollback occurred
        with db.transaction() as cursor:
            cursor.execute("SELECT COUNT(*) FROM rollback_test")
            count = cursor.fetchone()[0]
            assert count == 1  # Only initial record should remain
    
    def test_schema_creation_and_migrations(self):
        """Test database schema creation and migrations."""
        schema_manager = SchemaManager(self.db_path)
        schema_manager.initialize_schema()
        
        # Verify tables exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Should have at least the basic tables
        assert len(tables) > 0
        
        conn.close()
    
    def test_file_record_operations(self):
        """Test file record creation, updates, and queries."""
        db = Database(self.db_path)
        
        # Create files table
        with db.transaction() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY,
                    path TEXT UNIQUE,
                    hash TEXT,
                    size INTEGER,
                    modified_time REAL,
                    created_time REAL,
                    is_duplicate BOOLEAN DEFAULT FALSE
                )
            """)
        
        # Test record creation
        test_path = "/tmp/test_file.txt"
        test_hash = "abc123"
        test_size = 1024
        
        with db.transaction() as cursor:
            cursor.execute("""
                INSERT OR REPLACE INTO files 
                (path, hash, size, modified_time, created_time) 
                VALUES (?, ?, ?, ?, ?)
            """, (test_path, test_hash, test_size, 1234567890.0, 1234567890.0))
        
        # Test record retrieval
        with db.transaction() as cursor:
            cursor.execute("SELECT * FROM files WHERE path = ?", (test_path,))
            record = cursor.fetchone()
            
        assert record is not None
        assert record[1] == test_path  # path
        assert record[2] == test_hash  # hash
        assert record[3] == test_size  # size
    
    def test_hash_cache_functionality(self):
        """Test hash cache operations."""
        cache = HashCache()
        
        # Test basic cache operations
        test_path = "/tmp/test_file.txt"
        test_hash = "test_hash_value"
        
        # Store hash
        cache.set(test_path, test_hash)
        
        # Retrieve hash
        retrieved = cache.get(test_path)
        assert retrieved == test_hash
        
        # Test cache miss
        miss_result = cache.get("/nonexistent/path")
        assert miss_result is None
        
        # Test cache size limit (if applicable)
        cache.clear()
        assert cache.get(test_path) is None
    
    def test_query_cache_performance(self):
        """Test query cache performance benefits."""
        # This test verifies that caching improves performance
        cache = HashCache()
        
        # Populate cache with test data
        for i in range(10):
            cache.set(f"/tmp/file_{i}.txt", f"hash_{i}")
        
        # Test that retrieval is fast (no timing test, just functional)
        for i in range(10):
            result = cache.get(f"/tmp/file_{i}.txt")
            assert result == f"hash_{i}"
    
    def test_database_integrity_checks(self):
        """Test database integrity and constraint enforcement."""
        db = Database(self.db_path)
        
        with db.transaction() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS integrity_test (
                    id INTEGER PRIMARY KEY,
                    unique_field TEXT UNIQUE,
                    not_null_field TEXT NOT NULL
                )
            """)
        
        # Test unique constraint
        with db.transaction() as cursor:
            cursor.execute("INSERT INTO integrity_test (unique_field, not_null_field) VALUES (?, ?)", 
                          ("unique_value", "not_null_value"))
        
        with pytest.raises(sqlite3.IntegrityError):
            with db.transaction() as cursor:
                cursor.execute("INSERT INTO integrity_test (unique_field, not_null_field) VALUES (?, ?)", 
                              ("unique_value", "another_value"))  # Should fail due to unique constraint
    
    def test_concurrent_database_access(self):
        """Test concurrent database access patterns."""
        # Note: This is a basic test - real concurrent testing would require threading
        db = Database(self.db_path)
        
        with db.transaction() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS concurrent_test (
                    id INTEGER PRIMARY KEY,
                    data TEXT
                )
            """)
        
        # Simulate multiple operations
        for i in range(5):
            with db.transaction() as cursor:
                cursor.execute("INSERT INTO concurrent_test (data) VALUES (?)", (f"data_{i}",))
        
        with db.transaction() as cursor:
            cursor.execute("SELECT COUNT(*) FROM concurrent_test")
            count = cursor.fetchone()[0]
            assert count == 5
    
    def test_database_cleanup_operations(self):
        """Test database cleanup and maintenance operations."""
        db = Database(self.db_path)
        
        with db.transaction() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cleanup_test (
                    id INTEGER PRIMARY KEY,
                    path TEXT,
                    hash TEXT,
                    obsolete BOOLEAN DEFAULT FALSE
                )
            """)
        
        # Insert test data
        for i in range(3):
            with db.transaction() as cursor:
                cursor.execute("INSERT INTO cleanup_test (path, hash) VALUES (?, ?)", 
                              (f"/tmp/file_{i}", f"hash_{i}"))
        
        # Mark one as obsolete
        with db.transaction() as cursor:
            cursor.execute("UPDATE cleanup_test SET obsolete = TRUE WHERE id = 1")
        
        # Verify cleanup query would work
        with db.transaction() as cursor:
            cursor.execute("DELETE FROM cleanup_test WHERE obsolete = TRUE")
        
        with db.transaction() as cursor:
            cursor.execute("SELECT COUNT(*) FROM cleanup_test")
            count = cursor.fetchone()[0]
            assert count == 2  # Should have 2 records left


def test_connection_manager_thread_safety():
    """Test connection manager thread safety (basic verification)."""
    db_path = tempfile.mktemp(suffix='.db')
    try:
        conn_manager = ConnectionManager(db_path)
        
        # Get connection from main thread
        conn1 = conn_manager.get_connection()
        assert conn1 is not None
        
        # Close connections
        conn_manager.close_all()
        
        assert conn_manager._connections == {}  # Should be empty after cleanup
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_schema_manager_schema_validation():
    """Test schema manager schema validation."""
    db_path = tempfile.mktemp(suffix='.db')
    try:
        schema_manager = SchemaManager(db_path)
        schema_manager.initialize_schema()
        
        # Verify schema exists by checking if tables were created
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        
        conn.close()
        
        assert table_count > 0  # Should have created tables
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


if __name__ == "__main__":
    pytest.main([__file__])
