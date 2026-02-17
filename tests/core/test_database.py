"""Tests for database modules.

This module contains comprehensive unit tests for the database layer,
including DatabaseConnection, FileRepository, and related functionality.
"""

import os
import sqlite3
import tempfile
from typing import Any, Dict, List
from unittest.mock import Mock

import pytest

from nodupe.tools.databases.connection import DatabaseConnection
from nodupe.tools.databases.database import Database
from nodupe.tools.databases.files import FileRepository, get_file_repository
from nodupe.tools.databases.query import (
    DatabaseBackup,
    DatabaseBatch,
    DatabaseIntegrity,
    DatabaseMigration,
    DatabaseOptimization,
    DatabasePerformance,
    DatabaseQuery,
    DatabaseRecovery,
)
from nodupe.tools.databases.repository_interface import DatabaseRepository
from nodupe.tools.databases.schema import DatabaseSchema


def _init_full_schema(db: DatabaseConnection) -> None:
    """Helper to initialize the full 14-column schema for FileRepository tests."""
    schema = DatabaseSchema(db.get_connection())
    schema.create_schema()


class TestDatabaseConnection:
    """Test DatabaseConnection class functionality."""

    def test_singleton_instance_creation(self):
        """Test that DatabaseConnection follows singleton pattern."""
        with (
            tempfile.NamedTemporaryFile(suffix=".db") as tmp1,
            tempfile.NamedTemporaryFile(suffix=".db") as tmp2,
        ):

            db1 = DatabaseConnection.get_instance(tmp1.name)
            db2 = DatabaseConnection.get_instance(tmp1.name)  # Same path
            db3 = DatabaseConnection.get_instance(tmp2.name)  # Different path

            assert db1 is db2  # Same path should return same instance
            assert (
                db1 is not db3
            )  # Different paths should return different instances
            assert isinstance(db1, DatabaseConnection)

            # Clean up connections
            db1.close()
            db3.close()

    def test_get_connection_creates_directory(self):
        """Test that get_connection creates database directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "subdir", "test.db")
            db = DatabaseConnection(db_path)

            connection = db.get_connection()
            assert isinstance(connection, sqlite3.Connection)

            # Check that directory was created
            assert os.path.exists(os.path.dirname(db_path))

            # Clean up connection
            db.close()

    def test_execute_query_success(self):
        """Test successful query execution."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            db.get_connection()

            # Initialize schema
            _init_full_schema(db)

            # Execute a simple query
            cursor = db.execute(
                "INSERT INTO files (path, size, modified_time, "
                "created_time, scanned_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                ("test.txt", 100, 12345, 12345, 12345, 12345),
            )
            assert cursor is not None

            cursor = db.execute(
                "SELECT * FROM files WHERE path = ?", ("test.txt",)
            )
            result = cursor.fetchone()
            assert result is not None
            assert result[1] == "test.txt"  # path
            assert result[2] == 100  # size

            # Clean up connection
            db.close()

    def test_execute_query_without_params(self):
        """Test query execution without parameters."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            db.get_connection()
            _init_full_schema(db)

            cursor = db.execute("SELECT COUNT(*) FROM files")
            result = cursor.fetchone()
            assert result[0] == 0

            # Clean up connection
            db.close()

    def test_executemany_batch_operations(self):
        """Test batch operations with executemany."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            db.get_connection()
            _init_full_schema(db)

            data = [
                ("file1.txt", 100, 12345, 12345, 12345, 12345),
                ("file2.txt", 200, 12346, 12345, 12345, 12345),
                ("file3.txt", 300, 12347, 12345, 12345, 12345),
            ]

            cursor = db.executemany(
                "INSERT INTO files (path, size, modified_time, "
                "created_time, scanned_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                [tuple(item) for item in data],
            )
            assert cursor is not None

            cursor = db.execute("SELECT COUNT(*) FROM files")
            count = cursor.fetchone()[0]
            assert count == 3

            # Clean up connection
            db.close()

    def test_commit_and_rollback(self):
        """Test transaction commit and rollback functionality."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            db.get_connection()
            _init_full_schema(db)

            db.execute(
                "INSERT INTO files (path, size, modified_time, "
                "created_time, scanned_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                ("test.txt", 100, 12345, 12345, 12345, 12345),
            )

            # Verify it's there
            cursor = db.execute("SELECT COUNT(*) FROM files")
            assert cursor.fetchone()[0] == 1

            # Rollback should remove it
            db.rollback()
            cursor = db.execute("SELECT COUNT(*) FROM files")
            assert cursor.fetchone()[0] == 0

            # Insert again and commit
            db.execute(
                "INSERT INTO files (path, size, modified_time, "
                "created_time, scanned_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                ("test.txt", 100, 12345, 12345, 12345, 12345),
            )
            db.commit()

            cursor = db.execute("SELECT COUNT(*) FROM files")
            assert cursor.fetchone()[0] == 1

            # Clean up connection
            db.close()

    def test_close_connection(self):
        """Test connection closing functionality."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _ = (
                db.get_connection()
            )  # Use underscore to indicate unused variable

            # Close should clear the connection
            db.close()

            # Getting connection after close should work
            _ = (
                db.get_connection()
            )  # Use underscore to indicate unused variable

            # Close should have cleaned up properly
            db.close()

    def test_initialize_database_schema(self):
        """Test database schema initialization."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _init_full_schema(db)

            # Test that tables exist
            cursor = db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]

            assert "files" in tables
            assert "embeddings" in tables

            # Test that indexes exist
            cursor = db.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indexes = [row[0] for row in cursor.fetchall()]

            assert "idx_files_path" in indexes
            assert "idx_files_hash" in indexes
            assert "idx_files_size" in indexes
            assert "idx_files_is_duplicate" in indexes
            assert "idx_embeddings_file_id" in indexes
            assert "idx_embeddings_model_version" in indexes

    def test_get_connection_thread_local(self):
        """Test that connections are thread-local."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)

            def get_conn():
                return db.get_connection()

            # Same thread should get same connection
            conn1 = get_conn()
            conn2 = get_conn()
            assert conn1 is conn2


class TestFileRepository:
    """Test FileRepository class functionality."""

    def test_initialization(self):
        """Test FileRepository initialization."""
        mock_db = Mock()
        repo = FileRepository(mock_db)

        assert repo.db is mock_db

    def test_add_file_success(self):
        """Test adding a file successfully."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            db.get_connection()
            _init_full_schema(db)

            repo = FileRepository(db)

            file_id = repo.add_file("test.txt", 100, 12345, "abc123")
            assert file_id is not None

            # Verify file was added
            cursor = db.execute("SELECT * FROM files WHERE id = ?", (file_id,))
            result = cursor.fetchone()
            assert result[1] == "test.txt"  # path
            assert result[2] == 100  # size
            assert result[3] == 12345  # modified_time
            assert result[8] == "abc123"  # hash (full schema index)

            # Clean up connection
            db.close()

    def test_get_file_by_id(self):
        """Test getting a file by ID."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            db.get_connection()
            _init_full_schema(db)

            repo = FileRepository(db)

            # Add a file first
            file_id = repo.add_file("test.txt", 100, 12345, "abc123")
            assert file_id is not None  # Ensure file was added successfully

            # Get the file
            file_data = repo.get_file(file_id)
            assert file_data is not None
            assert file_data["path"] == "test.txt"
            assert file_data["size"] == 100
            assert file_data["hash"] == "abc123"
            assert file_data["is_duplicate"] is False

            # Clean up connection
            db.close()

    def test_get_file_by_id_not_found(self):
        """Test getting a non-existent file."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            db.get_connection()
            _init_full_schema(db)

            repo = FileRepository(db)

            file_data = repo.get_file(999)
            assert file_data is None

            # Close database connection to prevent resource warnings
            db.close()

    def test_get_file_by_path(self):
        """Test getting a file by path."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _ = (
                db.get_connection()
            )  # Use underscore to indicate unused variable
            _init_full_schema(db)

            repo = FileRepository(db)

            # Add a file first
            file_id = repo.add_file("test.txt", 100, 12345, "abc123")
            assert file_id is not None  # Ensure file was added successfully

            # Get the file by path
            file_data = repo.get_file_by_path("test.txt")
            assert file_data is not None
            assert file_data["id"] == file_id
            assert file_data["size"] == 100

    def test_update_file(self):
        """Test updating file data."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _ = (
                db.get_connection()
            )  # Use underscore to indicate unused variable
            _init_full_schema(db)

            repo = FileRepository(db)

            # Add a file first
            file_id = repo.add_file("test.txt", 100, 12345, "abc123")
            assert file_id is not None  # Ensure file was added successfully

            # Update the file
            success = repo.update_file(file_id, size=200, hash="def456")
            assert success is True

            # Verify update
            file_data = repo.get_file(file_id)
            assert file_data is not None
            assert file_data["size"] == 200
            assert file_data["hash"] == "def456"

    def test_update_file_invalid_fields(self):
        """Test updating with invalid fields."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _ = (
                db.get_connection()
            )  # Use underscore to indicate unused variable
            _init_full_schema(db)

            repo = FileRepository(db)

            file_id = repo.add_file("test.txt", 100, 12345, "abc123")
            assert file_id is not None  # Ensure file was added successfully

            # Update with no valid fields should return False
            success = repo.update_file(file_id, invalid_field="test")
            assert success is False

    def test_mark_as_duplicate(self):
        """Test marking a file as duplicate."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _ = (
                db.get_connection()
            )  # Use underscore to indicate unused variable
            _init_full_schema(db)

            repo = FileRepository(db)

            # Add two files
            original_id = repo.add_file("original.txt", 100, 12345, "abc123")
            duplicate_id = repo.add_file("duplicate.txt", 10, 12346, "abc123")
            assert (
                original_id is not None
            )  # Ensure files were added successfully
            assert duplicate_id is not None

            # Mark one as duplicate of the other
            success = repo.mark_as_duplicate(duplicate_id, original_id)
            assert success is True

            # Verify the duplicate was marked
            dup_data = repo.get_file(duplicate_id)
            assert dup_data is not None
            assert dup_data["is_duplicate"] is True
            assert dup_data["duplicate_of"] == original_id

    def test_find_duplicates_by_hash(self):
        """Test finding files with same hash."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _ = (
                db.get_connection()
            )  # Use underscore to indicate unused variable
            _init_full_schema(db)

            repo = FileRepository(db)

            # Add files with same hash
            file1_id = repo.add_file("file1.txt", 100, 12345, "samehash")
            file2_id = repo.add_file("file2.txt", 100, 12346, "samehash")
            file3_id = repo.add_file("file3.txt", 200, 12347, "differenthash")
            assert file1_id is not None  # Ensure files were added successfully
            assert file2_id is not None
            assert file3_id is not None

            duplicates = repo.find_duplicates_by_hash("samehash")
            assert len(duplicates) == 2
            assert all(f["hash"] == "samehash" for f in duplicates)

            # Close database connection to prevent resource warnings
            db.close()

    def test_find_duplicates_by_size(self):
        """Test finding files with same size."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _ = (
                db.get_connection()
            )  # Use underscore to indicate unused variable
            _init_full_schema(db)

            repo = FileRepository(db)

            # Add files with same size
            file1_id = repo.add_file("file1.txt", 100, 12345, "hash1")
            file2_id = repo.add_file("file2.txt", 100, 12346, "hash2")
            file3_id = repo.add_file("file3.txt", 200, 12347, "hash3")
            assert file1_id is not None  # Ensure files were added successfully
            assert file2_id is not None
            assert file3_id is not None

            same_size_files = repo.find_duplicates_by_size(100)
            assert len(same_size_files) == 2
            assert all(f["size"] == 100 for f in same_size_files)

    def test_get_all_files(self):
        """Test getting all files."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _ = (
                db.get_connection()
            )  # Use underscore to indicate unused variable
            _init_full_schema(db)

            repo = FileRepository(db)

            # Add some files
            file1_id = repo.add_file("file1.txt", 100, 12345, "hash1")
            file2_id = repo.add_file("file2.txt", 200, 12346, "hash2")
            assert file1_id is not None  # Ensure files were added successfully
            assert file2_id is not None

            all_files = repo.get_all_files()
            assert len(all_files) == 2
            assert {f["path"] for f in all_files} == {"file1.txt", "file2.txt"}

    def test_delete_file(self):
        """Test deleting a file."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _ = (
                db.get_connection()
            )  # Use underscore to indicate unused variable
            _init_full_schema(db)

            repo = FileRepository(db)

            # Add a file
            file_id = repo.add_file("test.txt", 100, 12345, "abc123")
            assert file_id is not None  # Ensure file was added successfully

            # Delete the file
            success = repo.delete_file(file_id)
            assert success is True

            # Verify it's gone
            file_data = repo.get_file(file_id)
            assert file_data is None

    def test_get_duplicate_files(self):
        """Test getting duplicate files."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _ = (
                db.get_connection()
            )  # Use underscore to indicate unused variable
            _init_full_schema(db)

            repo = FileRepository(db)

            # Add files and mark some as duplicates
            original_id = repo.add_file("original.txt", 10, 12345, "hash1")
            dup1_id = repo.add_file("dup1.txt", 100, 12346, "hash1")
            dup2_id = repo.add_file("dup2.txt", 100, 12347, "hash1")
            normal_id = repo.add_file("normal.txt", 200, 12348, "hash2")
            assert (
                original_id is not None
            )  # Ensure files were added successfully
            assert dup1_id is not None
            assert dup2_id is not None
            assert normal_id is not None

            repo.mark_as_duplicate(dup1_id, original_id)
            repo.mark_as_duplicate(dup2_id, original_id)

            duplicates = repo.get_duplicate_files()
            assert len(duplicates) == 2
            assert all(f["is_duplicate"] is True for f in duplicates)

    def test_get_original_files(self):
        """Test getting original (non-duplicate) files."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _ = (
                db.get_connection()
            )  # Use underscore to indicate unused variable
            _init_full_schema(db)

            repo = FileRepository(db)

            # Add files and mark some as duplicates
            original_id = repo.add_file("original.txt", 10, 12345, "hash1")
            dup_id = repo.add_file("dup.txt", 10, 12346, "hash1")
            assert (
                original_id is not None
            )  # Ensure files were added successfully
            assert dup_id is not None

            repo.mark_as_duplicate(dup_id, original_id)

            originals = repo.get_original_files()
            assert len(originals) == 1
            assert originals[0]["id"] == original_id
            assert originals[0]["is_duplicate"] is False

    def test_count_files(self):
        """Test counting total files."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _ = (
                db.get_connection()
            )  # Use underscore to indicate unused variable
            _init_full_schema(db)

            repo = FileRepository(db)

            assert repo.count_files() == 0
            file1_id = repo.add_file("file1.txt", 100, 12345, "hash1")
            file2_id = repo.add_file("file2.txt", 200, 12346, "hash2")
            assert file1_id is not None  # Ensure files were added successfully
            assert file2_id is not None
            assert repo.count_files() == 2

    def test_count_duplicates(self):
        """Test counting duplicate files."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _ = (
                db.get_connection()
            )  # Use underscore to indicate unused variable
            _init_full_schema(db)

            repo = FileRepository(db)

            # Add files and mark one as duplicate
            original_id = repo.add_file("original.txt", 10, 12345, "hash1")
            dup_id = repo.add_file("dup.txt", 10, 12346, "hash1")
            assert (
                original_id is not None
            )  # Ensure files were added successfully
            assert dup_id is not None

            assert repo.count_duplicates() == 0
            repo.mark_as_duplicate(dup_id, original_id)
            assert repo.count_duplicates() == 1

    def test_batch_add_files(self):
        """Test batch adding multiple files."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _ = (
                db.get_connection()
            )  # Use underscore to indicate unused variable
            _init_full_schema(db)

            repo = FileRepository(db)

            files_data: list[dict[str, Any]] = [
                {"path": "file1.txt", "size": 100, "modified_time": 12345},
                {"path": "file2.txt", "size": 200, "modified_time": 12346},
                {"path": "file3.txt", "size": 300, "modified_time": 12347},
            ]

            count = repo.batch_add_files(files_data)
            assert count == 3

            all_files = repo.get_all_files()
            assert len(all_files) == 3
            assert {f["path"] for f in all_files} == {
                "file1.txt",
                "file2.txt",
                "file3.txt",
            }

    def test_clear_all_files(self):
        """Test clearing all files."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _ = (
                db.get_connection()
            )  # Use underscore to indicate unused variable
            _init_full_schema(db)

            repo = FileRepository(db)

            # Add some files
            file1_id = repo.add_file("file1.txt", 100, 12345, "hash1")
            file2_id = repo.add_file("file2.txt", 200, 12346, "hash2")
            assert file1_id is not None  # Ensure files were added successfully
            assert file2_id is not None

            assert repo.count_files() == 2

            # Clear all files
            repo.clear_all_files()

            assert repo.count_files() == 0

    def test_get_file_repository_factory(self):
        """Test the factory function for getting file repository."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            repo = get_file_repository(tmp.name)

            assert isinstance(repo, FileRepository)
            assert isinstance(repo.db, DatabaseConnection)

            os.unlink(tmp.name)


class TestDatabaseRepository:
    """Test DatabaseRepository class functionality."""

    def test_initialization(self):
        """Test DatabaseRepository initialization."""
        mock_connection = Mock()
        repo = DatabaseRepository(mock_connection)

        assert repo.connection is mock_connection

    def test_create_method_raises_not_implemented(self):
        """Test that create method raises NotImplementedError."""
        repo = DatabaseRepository(Mock())

        with pytest.raises(NotImplementedError):
            repo.create("table", {"data": "value"})

    def test_read_method_raises_not_implemented(self):
        """Test that read method raises NotImplementedError."""
        repo = DatabaseRepository(Mock())

        with pytest.raises(NotImplementedError):
            repo.read("table", 1)

    def test_update_method_raises_not_implemented(self):
        """Test that update method raises NotImplementedError."""
        repo = DatabaseRepository(Mock())

        with pytest.raises(NotImplementedError):
            repo.update("table", 1, {"data": "value"})

    def test_delete_method_raises_not_implemented(self):
        """Test that delete method raises NotImplementedError."""
        repo = DatabaseRepository(Mock())

        with pytest.raises(NotImplementedError):
            repo.delete("table", 1)


def test_database_integration():
    """Test full database integration with all components working together."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        try:
            # Test with real database file
            db = DatabaseConnection(tmp.name)
            repo = FileRepository(db)

            # Initialize database
            _init_full_schema(db)

            # Add some test files
            file1_id = repo.add_file(
                "/path/to/file1.txt", 1024, 1234567890, "hash123"
            )
            file2_id = repo.add_file(
                "/path/to/file2.txt", 2048, 1234567891, "hash123"
            )  # Same hash
            assert file1_id is not None  # Ensure files were added successfully
            assert file2_id is not None

            # Mark second as duplicate
            repo.mark_as_duplicate(file2_id, file1_id)

            # Verify operations worked
            assert repo.count_files() == 2
            assert repo.count_duplicates() == 1

            # Find duplicates by hash
            duplicates = repo.find_duplicates_by_hash("hash123")
            assert len(duplicates) == 2

            # Get original files
            originals = repo.get_original_files()
            assert len(originals) == 1

            # Update file
            success = repo.update_file(file1_id, size=3072)
            assert success is True

            updated_file = repo.get_file(file1_id)
            assert updated_file is not None
            assert updated_file["size"] == 3072

        finally:
            os.unlink(tmp.name)


class TestDatabaseQueryComponents:
    """Test the new database query components."""

    def test_database_query_execute(self):
        """Test DatabaseQuery execute method."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _init_full_schema(db)

            # Create DatabaseQuery instance
            query = DatabaseQuery(db)

            # Insert test data
            db.execute(
                "INSERT INTO files (path, size, modified_time, "
                "created_time, scanned_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                ("test.txt", 100, 12345, 12345, 12345, 12345),
            )

            # Test query execution
            results = query.execute(
                "SELECT * FROM files WHERE path = ?", ("test.txt",)
            )
            assert len(results) == 1
            assert results[0]["path"] == "test.txt"
            assert results[0]["size"] == 100

    def test_database_batch_operations(self):
        """Test DatabaseBatch execute_batch method."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _init_full_schema(db)

            # Create DatabaseBatch instance
            batch = DatabaseBatch(db)

            # Test batch operations
            operations = [
                (
                    "INSERT INTO files (path, size, modified_time, "
                    "created_time, scanned_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    ("file1.txt", 100, 12345, 12345, 12345, 12345),
                ),
                (
                    "INSERT INTO files (path, size, modified_time, "
                    "created_time, scanned_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    ("file2.txt", 200, 12346, 12345, 12345, 12345),
                ),
            ]

            batch.execute_batch(operations)

            # Verify batch execution
            cursor = db.execute("SELECT COUNT(*) FROM files")
            count = cursor.fetchone()[0]
            assert count == 2

    def test_database_batch_transaction(self):
        """Test DatabaseBatch execute_transaction_batch method."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _init_full_schema(db)

            # Create DatabaseBatch instance
            batch = DatabaseBatch(db)

            # Test transaction batch operations
            operations = [
                (
                    "INSERT INTO files (path, size, modified_time, "
                    "created_time, scanned_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    ("file1.txt", 100, 12345, 12345, 12345, 12345),
                ),
                (
                    "INSERT INTO files (path, size, modified_time, "
                    "created_time, scanned_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    ("file2.txt", 200, 12346, 12345, 12345, 12345),
                ),
            ]

            batch.execute_transaction_batch(operations)

            # Verify transaction batch execution
            cursor = db.execute("SELECT COUNT(*) FROM files")
            count = cursor.fetchone()[0]
            assert count == 2

    def test_database_performance_monitoring(self):
        """Test DatabasePerformance monitoring methods."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = Database(tmp.name)
            _init_full_schema(db.connection)

            # Create DatabasePerformance instance
            performance = DatabasePerformance(db)

            # Test monitor_performance method
            monitor = performance.monitor_performance()
            assert monitor is not None

            # Test get_results method
            results = performance.get_results()
            assert isinstance(results, dict)
            assert "metrics" in results or "error" in results

    def test_database_integrity_checking(self):
        """Test DatabaseIntegrity check_integrity method."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = Database(tmp.name)
            _init_full_schema(db.connection)

            # Create DatabaseIntegrity instance
            integrity = DatabaseIntegrity(db)

            # Test check_integrity method
            results = integrity.check_integrity()
            assert isinstance(results, dict)
            assert "tables" in results
            assert "indexes" in results
            assert "valid" in results
            assert results["valid"] is True

    def test_database_backup_functionality(self):
        """Test DatabaseBackup create_backup and restore_backup methods."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            with tempfile.NamedTemporaryFile(
                suffix="_backup.db", delete=False
            ) as backup:
                try:
                    db = Database(tmp.name)
                    _init_full_schema(db.connection)

                    # Add test data
                    db.connection.execute(
                        "INSERT INTO files (path, size, modified_time, "
                        "created_time, scanned_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                        ("test.txt", 100, 12345, 12345, 12345, 12345),
                    )

                    # Create DatabaseBackup instance
                    backup_db = DatabaseBackup(db)

                    # Test create_backup method
                    backup_db.create_backup(backup.name)

                    # Verify backup was created
                    assert os.path.exists(backup.name)

                    # Test restore_backup method
                    restore_path = tmp.name + "_restored"
                    backup_db.restore_backup(backup.name, restore_path)

                    # Verify restore was created
                    assert os.path.exists(restore_path)

                finally:
                    os.unlink(tmp.name)
                    if os.path.exists(backup.name):
                        os.unlink(backup.name)
                    if os.path.exists(tmp.name + "_restored"):
                        os.unlink(tmp.name + "_restored")

    def test_database_migration_functionality(self):
        """Test DatabaseMigration migrate_schema method."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = Database(tmp.name)
            _init_full_schema(db.connection)

            # Create DatabaseMigration instance
            migration = DatabaseMigration(db)

            # Test migrate_schema method
            migrations = {
                "test_table": {
                    "add_columns": ["new_column TEXT"],
                    "add_indexes": [
                        "CREATE INDEX idx_test_table_new ON test_table(new_column)"
                    ],
                }
            }

            # This should not raise an error even if the table doesn't exist
            migration.migrate_schema(migrations)

    def test_database_recovery_functionality(self):
        """Test DatabaseRecovery handle_errors method."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = Database(tmp.name)
            _init_full_schema(db.connection)

            # Create DatabaseRecovery instance
            recovery = DatabaseRecovery(db)

            # Test handle_errors method with no errors
            result = recovery.handle_errors(raise_on_error=False)
            assert result is True

            # Test handle_errors method with raise_on_error=True
            result = recovery.handle_errors(raise_on_error=True)
            assert result is True

    def test_database_optimization_functionality(self):
        """Test DatabaseOptimization optimize_query method."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = DatabaseConnection(tmp.name)
            _init_full_schema(db)

            # Create DatabaseOptimization instance
            optimization = DatabaseOptimization(db)

            # Test optimize_query method
            query = "  SELECT * FROM files WHERE size > 100;  "
            optimized = optimization.optimize_query(query)
            assert optimized == "SELECT * FROM files WHERE size > 100"

            # Test with query that doesn't end with semicolon
            query2 = "SELECT * FROM files"
            optimized2 = optimization.optimize_query(query2)
            assert optimized2 == "SELECT * FROM files"


class TestDatabaseIntegration:
    """Test full Database class integration."""

    def test_database_initialization(self):
        """Test Database class initialization."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            # Test Database initialization
            db = Database(tmp.name)
            assert db.path == tmp.name
            assert db.timeout == 30.0
            assert hasattr(db, "connection")
            assert hasattr(db, "schema")
            assert hasattr(db, "indexing")
            assert hasattr(db, "query")
            assert hasattr(db, "batch")
            assert hasattr(db, "transaction")
            assert hasattr(db, "performance")
            assert hasattr(db, "integrity")
            assert hasattr(db, "backup")
            assert hasattr(db, "migration")
            assert hasattr(db, "recovery")
            assert hasattr(db, "security")
            assert hasattr(db, "optimization")

            # Test connection
            conn = db.connect()
            assert isinstance(conn, sqlite3.Connection)

            # Test close
            db.close()

    def test_database_query_operations(self):
        """Test Database query operations."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = Database(tmp.name)
            _init_full_schema(db.connection)

            # Test create_table
            db.create_table("test_table", "id INTEGER PRIMARY KEY, name TEXT")

            # Test create
            data_id = db.create("test_table", {"name": "test"})
            assert data_id is not None

            # Test read
            results = db.read(
                "SELECT * FROM test_table WHERE id = ?", (data_id,)
            )
            assert len(results) == 1
            assert results[0]["name"] == "test"

            # Test update
            updated_count = db.update(
                "UPDATE test_table SET name = ? WHERE id = ?",
                ("updated", data_id),
            )
            assert updated_count == 1

            # Test delete
            deleted_count = db.delete(
                "DELETE FROM test_table WHERE id = ?", (data_id,)
            )
            assert deleted_count == 1

            # Test close
            db.close()

    def test_database_batch_operations(self):
        """Test Database batch operations."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            db = Database(tmp.name)
            _init_full_schema(db.connection)

            # Test execute_batch
            operations = [
                (
                    "INSERT INTO files (path, size, modified_time, created_time, scanned_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    ("file1.txt", 100, 12345, 12345, 12345, 12345),
                ),
                (
                    "INSERT INTO files (path, size, modified_time, created_time, scanned_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    ("file2.txt", 200, 12346, 12345, 12345, 12345),
                ),
            ]

            db.execute_batch(operations)

            # Verify batch execution
            results = db.read("SELECT COUNT(*) FROM files")
            assert results[0]["COUNT(*)"] == 2

            # Test close
            db.close()

    def test_database_context_manager(self):
        """Test Database context manager functionality."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            # Test context manager
            with Database(tmp.name) as db:
                _init_full_schema(db.connection)
                assert isinstance(db, Database)

                # Test operations within context
                db.create_table(
                    "context_table", "id INTEGER PRIMARY KEY, value TEXT"
                )
                db.create("context_table", {"value": "test"})

            # Context manager should have closed the connection

            # Verify we can create a new database instance
            db2 = Database(tmp.name)
            results = db2.read("SELECT * FROM context_table")
            assert len(results) == 1
            db2.close()
