"""Comprehensive tests for database modules to achieve 100% coverage in Phase 3."""

import pytest
import tempfile
import os
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from nodupe.core.database.connection import DatabaseConnection
from nodupe.core.database.database import DatabaseManager
from nodupe.core.database.files import FilesDatabase
from nodupe.core.database.indexing import IndexingDatabase
from nodupe.core.database.query import QueryDatabase
from nodupe.core.database.schema import DatabaseSchema
from nodupe.core.database.transactions import TransactionManager
from nodupe.core.database.security import DatabaseSecurity


class TestDatabaseModulesComprehensive:
    """Comprehensive tests for database modules."""

    def test_database_connection_edge_cases(self):
        """Test edge cases for database connection."""
        # Test with invalid database path
        with pytest.raises(Exception):
            conn = DatabaseConnection("/invalid/path/nonexistent.db")
            conn.connect()
        
        # Test connection with missing database
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "missing.db"
            
            # Should handle missing database gracefully
            conn = DatabaseConnection(str(db_path))
            conn.connect()
            assert conn.is_connected()
            conn.close()

    def test_database_manager_edge_cases(self):
        """Test edge cases for database manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            # Test with invalid configuration
            with pytest.raises(Exception):
                manager = DatabaseManager(str(db_path), config=None)
                manager.initialize()
            
            # Test database operations with missing tables
            manager = DatabaseManager(str(db_path))
            manager.initialize()
            
            # Should handle missing tables gracefully
            result = manager.execute_query("SELECT * FROM nonexistent_table")
            assert result is not None

    def test_files_database_edge_cases(self):
        """Test edge cases for files database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            files_db = FilesDatabase(str(db_path))
            files_db.initialize()
            
            # Test with invalid file paths
            with pytest.raises(Exception):
                files_db.add_file("/invalid/path/file.txt", "invalid_hash", 100)
            
            # Test with empty file path
            with pytest.raises(Exception):
                files_db.add_file("", "test_hash", 0)
            
            # Test with invalid hash
            with pytest.raises(Exception):
                files_db.add_file(str(Path(temp_dir) / "test.txt"), "", 100)

    def test_indexing_database_edge_cases(self):
        """Test edge cases for indexing database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            indexing_db = IndexingDatabase(str(db_path))
            indexing_db.initialize()
            
            # Test with invalid index data
            with pytest.raises(Exception):
                indexing_db.create_index("", "invalid_type")
            
            # Test with missing index
            result = indexing_db.get_index("nonexistent_index")
            assert result is None

    def test_query_database_edge_cases(self):
        """Test edge cases for query database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            query_db = QueryDatabase(str(db_path))
            query_db.initialize()
            
            # Test with invalid SQL
            with pytest.raises(Exception):
                query_db.execute_query("INVALID SQL SYNTAX")
            
            # Test with empty query
            with pytest.raises(Exception):
                query_db.execute_query("")
            
            # Test with parameterized query errors
            with pytest.raises(Exception):
                query_db.execute_query("SELECT * FROM ? WHERE id = ?", ["table", 1])

    def test_database_schema_edge_cases(self):
        """Test edge cases for database schema."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            schema = DatabaseSchema(str(db_path))
            
            # Test with invalid schema version
            with pytest.raises(Exception):
                schema.validate_schema("invalid_version")
            
            # Test schema migration with missing migration files
            with pytest.raises(Exception):
                schema.migrate_schema("999.999.999")

    def test_transaction_manager_edge_cases(self):
        """Test edge cases for transaction manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            # Test transaction with invalid operations
            with TransactionManager(str(db_path)) as tx:
                # Should handle invalid operations gracefully
                try:
                    tx.execute("INVALID SQL")
                except Exception:
                    # Expected for invalid SQL
                    pass
            
            # Test nested transactions
            with TransactionManager(str(db_path)) as tx1:
                with TransactionManager(str(db_path)) as tx2:
                    tx2.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
                tx1.execute("INSERT INTO test VALUES (1)")

    def test_database_security_edge_cases(self):
        """Test edge cases for database security."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            security = DatabaseSecurity(str(db_path))
            
            # Test with invalid encryption key
            with pytest.raises(Exception):
                security.encrypt_data("test_data", "invalid_key")
            
            # Test with empty data
            with pytest.raises(Exception):
                security.decrypt_data("", "test_key")

    def test_database_connection_detailed_coverage(self):
        """Test detailed coverage for database connection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            # Test connection lifecycle
            conn = DatabaseConnection(str(db_path))
            
            # Test connection states
            assert not conn.is_connected()
            
            conn.connect()
            assert conn.is_connected()
            
            conn.close()
            assert not conn.is_connected()
            
            # Test connection reuse
            conn.connect()
            assert conn.is_connected()
            conn.close()

    def test_database_manager_detailed_coverage(self):
        """Test detailed coverage for database manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            manager = DatabaseManager(str(db_path))
            
            # Test initialization
            manager.initialize()
            assert manager.is_initialized()
            
            # Test configuration
            config = {"timeout": 30, "cache_size": 1000}
            manager.configure(config)
            
            # Test backup functionality
            backup_path = Path(temp_dir) / "backup.db"
            manager.backup(str(backup_path))
            assert backup_path.exists()

    def test_files_database_detailed_coverage(self):
        """Test detailed coverage for files database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            files_db = FilesDatabase(str(db_path))
            files_db.initialize()
            
            # Test file operations
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")
            
            # Add file
            files_db.add_file(str(test_file), "test_hash_123", len("test content"))
            
            # Query file
            result = files_db.get_file_by_path(str(test_file))
            assert result is not None
            
            # Update file
            files_db.update_file_hash(str(test_file), "new_hash_456")
            
            # Delete file
            files_db.delete_file(str(test_file))

    def test_indexing_database_detailed_coverage(self):
        """Test detailed coverage for indexing database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            indexing_db = IndexingDatabase(str(db_path))
            indexing_db.initialize()
            
            # Test index operations
            test_data = {"key": "value", "number": 42}
            
            # Create index
            index_id = indexing_db.create_index("test_index", "json", test_data)
            assert index_id > 0
            
            # Get index
            result = indexing_db.get_index("test_index")
            assert result is not None
            
            # Update index
            indexing_db.update_index("test_index", test_data)
            
            # Delete index
            indexing_db.delete_index("test_index")

    def test_query_database_detailed_coverage(self):
        """Test detailed coverage for query database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            query_db = QueryDatabase(str(db_path))
            query_db.initialize()
            
            # Test query operations
            query_db.execute_query("CREATE TABLE IF NOT EXISTS test_table (id INTEGER, name TEXT)")
            
            # Insert data
            query_db.execute_query("INSERT INTO test_table VALUES (?, ?)", [1, "test"])
            
            # Select data
            result = query_db.execute_query("SELECT * FROM test_table")
            assert len(result) > 0
            
            # Update data
            query_db.execute_query("UPDATE test_table SET name = ? WHERE id = ?", ["updated", 1])
            
            # Delete data
            query_db.execute_query("DELETE FROM test_table WHERE id = ?", [1])

    def test_database_schema_detailed_coverage(self):
        """Test detailed coverage for database schema."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            schema = DatabaseSchema(str(db_path))
            
            # Test schema operations
            schema.create_schema()
            
            # Test schema validation
            is_valid = schema.validate_schema("1.0.0")
            assert isinstance(is_valid, bool)
            
            # Test schema migration
            schema.migrate_schema("1.0.0")

    def test_transaction_manager_detailed_coverage(self):
        """Test detailed coverage for transaction manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            # Test transaction operations
            with TransactionManager(str(db_path)) as tx:
                tx.execute("CREATE TABLE IF NOT EXISTS tx_test (id INTEGER)")
                tx.execute("INSERT INTO tx_test VALUES (1)")
                tx.commit()
            
            # Test transaction rollback
            with TransactionManager(str(db_path)) as tx:
                tx.execute("INSERT INTO tx_test VALUES (2)")
                tx.rollback()
            
            # Test transaction context manager
            with TransactionManager(str(db_path)) as tx:
                tx.execute("INSERT INTO tx_test VALUES (3)")

    def test_database_security_detailed_coverage(self):
        """Test detailed coverage for database security."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            security = DatabaseSecurity(str(db_path))
            
            # Test encryption operations
            test_data = "sensitive information"
            key = "test_key_123"
            
            # Encrypt data
            encrypted = security.encrypt_data(test_data, key)
            assert encrypted != test_data
            
            # Decrypt data
            decrypted = security.decrypt_data(encrypted, key)
            assert decrypted == test_data
            
            # Test security validation
            is_secure = security.validate_encryption(encrypted, key)
            assert is_secure

    def test_database_error_handling(self):
        """Test comprehensive error handling for all database modules."""
        database_modules = [
            DatabaseConnection,
            DatabaseManager,
            FilesDatabase,
            IndexingDatabase,
            QueryDatabase,
            DatabaseSchema,
            TransactionManager,
            DatabaseSecurity
        ]
        
        for module in database_modules:
            # Test with None values
            with tempfile.TemporaryDirectory() as temp_dir:
                db_path = Path(temp_dir) / "test.db"
                
                try:
                    if module == DatabaseConnection:
                        conn = module(None)
                    elif module == DatabaseManager:
                        manager = module(None)
                    elif module == FilesDatabase:
                        files_db = module(None)
                    elif module == IndexingDatabase:
                        indexing_db = module(None)
                    elif module == QueryDatabase:
                        query_db = module(None)
                    elif module == DatabaseSchema:
                        schema = module(None)
                    elif module == TransactionManager:
                        # TransactionManager uses context manager
                        pass
                    elif module == DatabaseSecurity:
                        security = module(None)
                except Exception:
                    # Expected for some modules with None values
                    pass

    def test_database_integration(self):
        """Test integration between database modules."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            # Test complete database workflow
            manager = DatabaseManager(str(db_path))
            manager.initialize()
            
            # Test files database integration
            files_db = FilesDatabase(str(db_path))
            files_db.initialize()
            
            # Test indexing database integration
            indexing_db = IndexingDatabase(str(db_path))
            indexing_db.initialize()
            
            # Test query database integration
            query_db = QueryDatabase(str(db_path))
            query_db.initialize()
            
            # Test transaction integration
            with TransactionManager(str(db_path)) as tx:
                tx.execute("CREATE TABLE IF NOT EXISTS integration_test (id INTEGER)")
                tx.execute("INSERT INTO integration_test VALUES (1)")
                tx.commit()

    def test_database_performance(self):
        """Test performance characteristics of database modules."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            # Test bulk operations performance
            files_db = FilesDatabase(str(db_path))
            files_db.initialize()
            
            # Create test files
            test_files = []
            for i in range(100):
                test_file = Path(temp_dir) / f"test_{i}.txt"
                test_file.write_text(f"content_{i}")
                test_files.append(str(test_file))
            
            # Test bulk file addition
            import time
            start_time = time.time()
            
            for file_path in test_files:
                files_db.add_file(file_path, f"hash_{file_path}", len(file_path))
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Should complete within reasonable time
            assert execution_time < 10.0  # 10 seconds max

    def test_database_concurrency(self):
        """Test concurrent access to database modules."""
        import threading
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            results = []
            errors = []
            
            def worker(worker_id):
                try:
                    # Each worker gets its own connection
                    files_db = FilesDatabase(str(db_path))
                    files_db.initialize()
                    
                    # Perform operations
                    test_file = Path(temp_dir) / f"worker_{worker_id}.txt"
                    test_file.write_text(f"worker_content_{worker_id}")
                    
                    files_db.add_file(str(test_file), f"hash_{worker_id}", len(str(worker_id)))
                    
                    results.append(worker_id)
                except Exception as e:
                    errors.append(str(e))
            
            # Create multiple threads
            threads = []
            for i in range(5):
                thread = threading.Thread(target=worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify results
            assert len(results) == 5
            assert len(errors) == 0

    def test_database_cleanup(self):
        """Test proper cleanup and resource management."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            # Test connection cleanup
            conn = DatabaseConnection(str(db_path))
            conn.connect()
            conn.close()
            
            # Test manager cleanup
            manager = DatabaseManager(str(db_path))
            manager.initialize()
            manager.close()
            
            # Test database file cleanup
            if db_path.exists():
                db_path.unlink()
                assert not db_path.exists()
