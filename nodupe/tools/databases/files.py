# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""File repository for database operations.

This module provides file repository functionality for the database layer,
handling file metadata storage and retrieval.

Key Features:
    - File metadata CRUD operations
    - Duplicate detection
    - File indexing
    - Batch operations
    - Error handling

Dependencies:
    - sqlite3 (standard library only)
    - typing (standard library only)
"""

from typing import Optional, List, Dict, Any
import time
from .connection import DatabaseConnection


class FileRepository:
    """File repository for database operations.

    Responsibilities:
    - Manage file metadata in database
    - Handle file CRUD operations
    - Detect and manage duplicates
    - Provide file indexing
    - Support batch operations
    """

    def __init__(self, db_connection: DatabaseConnection):
        """Initialize file repository.

        Args:
            db_connection: Database connection instance
        """
        self.db = db_connection

    def add_file(self, file_path: str, size: int, modified_time: int,
                 hash_value: Optional[str] = None) -> Optional[int]:
        """Add file to database.

        Args:
            file_path: Path to file
            size: File size in bytes
            modified_time: File modification time
            hash_value: Optional file hash

        Returns:
            File ID
        """
        try:
            current_time = int(time.monotonic())
            cursor = self.db.execute(
                '''
                INSERT INTO files (path, size, modified_time, hash, created_time, scanned_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (file_path, size, modified_time, hash_value, modified_time, current_time, current_time)
            )
            return cursor.lastrowid
        except Exception as e:
            print(f"[ERROR] Failed to add file: {e}")
            raise

    def get_file(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Get file by ID.

        Args:
            file_id: File ID

        Returns:
            File data or None if not found
        """
        try:
            cursor = self.db.execute(
                'SELECT * FROM files WHERE id = ?',
                (file_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'path': row[1],
                    'size': row[2],
                    'modified_time': row[3],
                    'hash': row[8],
                    'is_duplicate': bool(row[9]),
                    'duplicate_of': row[10]
                }
            return None
        except Exception as e:
            print(f"[ERROR] Failed to get file: {e}")
            raise

    def get_file_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file by path.

        Args:
            file_path: File path

        Returns:
            File data or None if not found
        """
        try:
            cursor = self.db.execute(
                'SELECT * FROM files WHERE path = ?',
                (file_path,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'path': row[1],
                    'size': row[2],
                    'modified_time': row[3],
                    'hash': row[8],
                    'is_duplicate': bool(row[9]),
                    'duplicate_of': row[10]
                }
            return None
        except Exception as e:
            print(f"[ERROR] Failed to get file by path: {e}")
            raise

    def update_file(self, file_id: int, **kwargs: Any) -> bool:
        """Update file data.

        Args:
            file_id: File ID
            **kwargs: File attributes to update

        Returns:
            True if updated, False if not found
        """
        if not kwargs:
            return False

        valid_fields = {'size', 'modified_time', 'hash', 'is_duplicate', 'duplicate_of'}
        update_fields = {k: v for k, v in kwargs.items() if k in valid_fields}

        if not update_fields:
            return False

        try:
            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            values = list(update_fields.values())
            values.append(file_id)

            query = f"UPDATE files SET {set_clause} WHERE id = ?"
            cursor = self.db.execute(query, tuple(values))

            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ERROR] Failed to update file: {e}")
            raise

    def mark_as_duplicate(self, file_id: int, duplicate_of: int) -> bool:
        """Mark file as duplicate.

        Args:
            file_id: File ID to mark as duplicate
            duplicate_of: ID of original file

        Returns:
            True if updated, False if not found
        """
        try:
            cursor = self.db.execute(
                'UPDATE files SET is_duplicate = TRUE, duplicate_of = ? WHERE id = ?',
                (duplicate_of, file_id)
            )
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ERROR] Failed to mark file as duplicate: {e}")
            raise

    def mark_as_original(self, file_id: int) -> bool:
        """Mark a file as an original (not a duplicate).

        Args:
            file_id: File ID to mark as original

        Returns:
            True if updated, False if not found
        """
        try:
            cursor = self.db.execute(
                'UPDATE files SET is_duplicate = FALSE, duplicate_of = NULL WHERE id = ?',
                (file_id,)
            )
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ERROR] Failed to mark file as original: {e}")
            raise

    def batch_mark_as_duplicate(self, duplicate_ids: List[int], keeper_id: int) -> int:
        """Mark multiple files as duplicates in a single DB statement.

        Args:
            duplicate_ids: List of file IDs to mark as duplicates
            keeper_id: File ID of the keeper/original

        Returns:
            Number of rows updated
        """
        if not duplicate_ids:
            return 0

        try:
            placeholders = ','.join('?' for _ in duplicate_ids)
            params = [keeper_id] + duplicate_ids
            cursor = self.db.execute(
                f'UPDATE files SET is_duplicate = TRUE, duplicate_of = ? WHERE id IN ({placeholders})',
                tuple(params)
            )
            return cursor.rowcount
        except Exception as e:
            print(f"[ERROR] Failed to batch mark files as duplicate: {e}")
            raise

    def get_duplicate_hashes(self) -> List[str]:
        """Return list of hash values that have more than one file entry.

        This allows callers to stream or iterate duplicate groups without
        loading the entire files table into memory.
        """
        try:
            cursor = self.db.execute(
                'SELECT hash FROM files WHERE hash IS NOT NULL GROUP BY hash HAVING COUNT(*) > 1'
            )
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"[ERROR] Failed to get duplicate hashes: {e}")
            raise

    def find_duplicates_by_hash(self, hash_value: str) -> List[Dict[str, Any]]:
        """Find files with same hash.

        Args:
            hash_value: Hash value to search for

        Returns:
            List of files with matching hash
        """
        try:
            cursor = self.db.execute(
                'SELECT * FROM files WHERE hash = ? ORDER BY path',
                (hash_value,)
            )
            return [
                {
                    'id': row[0],
                    'path': row[1],
                    'size': row[2],
                    'modified_time': row[3],
                    'hash': row[8],
                    'is_duplicate': bool(row[9]),
                    'duplicate_of': row[10]
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"[ERROR] Failed to find duplicates by hash: {e}")
            raise

    def find_duplicates_by_size(self, size: int) -> List[Dict[str, Any]]:
        """Find files with same size.

        Args:
            size: File size to search for

        Returns:
            List of files with matching size
        """
        try:
            cursor = self.db.execute(
                'SELECT * FROM files WHERE size = ? ORDER BY path',
                (size,)
            )
            return [
                {
                    'id': row[0],
                    'path': row[1],
                    'size': row[2],
                    'modified_time': row[3],
                    'hash': row[8],
                    'is_duplicate': bool(row[9]),
                    'duplicate_of': row[10]
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"[ERROR] Failed to find duplicates by size: {e}")
            raise

    def get_all_files(self) -> List[Dict[str, Any]]:
        """Get all files from database.

        Returns:
            List of all files
        """
        try:
            cursor = self.db.execute('SELECT * FROM files ORDER BY path')
            return [
                {
                    'id': row[0],
                    'path': row[1],
                    'size': row[2],
                    'modified_time': row[3],
                    'hash': row[8],
                    'is_duplicate': bool(row[9]),
                    'duplicate_of': row[10]
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"[ERROR] Failed to get all files: {e}")
            raise

    def delete_file(self, file_id: int) -> bool:
        """Delete file from database.

        Args:
            file_id: File ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            cursor = self.db.execute(
                'DELETE FROM files WHERE id = ?',
                (file_id,)
            )
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ERROR] Failed to delete file: {e}")
            raise

    def get_duplicate_files(self) -> List[Dict[str, Any]]:
        """Get all duplicate files.

        Returns:
            List of duplicate files
        """
        try:
            cursor = self.db.execute(
                'SELECT * FROM files WHERE is_duplicate = TRUE ORDER BY path'
            )
            return [
                {
                    'id': row[0],
                    'path': row[1],
                    'size': row[2],
                    'modified_time': row[3],
                    'hash': row[8],
                    'is_duplicate': bool(row[9]),
                    'duplicate_of': row[10]
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"[ERROR] Failed to get duplicate files: {e}")
            raise

    def get_original_files(self) -> List[Dict[str, Any]]:
        """Get all original files (not duplicates).

        Returns:
            List of original files
        """
        try:
            cursor = self.db.execute(
                'SELECT * FROM files WHERE is_duplicate = FALSE ORDER BY path'
            )
            return [
                {
                    'id': row[0],
                    'path': row[1],
                    'size': row[2],
                    'modified_time': row[3],
                    'hash': row[8],
                    'is_duplicate': bool(row[9]),
                    'duplicate_of': row[10]
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"[ERROR] Failed to get original files: {e}")
            raise

    def count_files(self) -> int:
        """Count total files in database.

        Returns:
            Total file count
        """
        try:
            cursor = self.db.execute('SELECT COUNT(*) FROM files')
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"[ERROR] Failed to count files: {e}")
            raise

    def count_duplicates(self) -> int:
        """Count duplicate files in database.

        Returns:
            Duplicate file count
        """
        try:
            cursor = self.db.execute('SELECT COUNT(*) FROM files WHERE is_duplicate = TRUE')
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"[ERROR] Failed to count duplicates: {e}")
            raise

    def batch_add_files(self, files: List[Dict[str, Any]]) -> int:
        """Add multiple files in batch.

        Args:
            files: List of file data dictionaries

        Returns:
            Number of files added
        """
        if not files:
            return 0

        try:
            current_time = int(time.monotonic())
            data = [
                (
                    file_data['path'],
                    file_data['size'],
                    file_data['modified_time'],
                    file_data.get('hash'),
                    file_data.get('created_time', file_data['modified_time']),
                    current_time,
                    current_time
                )
                for file_data in files
            ]

            self.db.executemany(
                '''INSERT INTO files
                (path, size, modified_time, hash, created_time, scanned_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                data
            )
            return len(files)
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[ERROR] Failed to batch add files: {e}")
            raise

    def clear_all_files(self) -> None:
        """Clear all files from database."""
        try:
            self.db.execute('DELETE FROM files')
            self.db.commit()
        except Exception as e:
            print(f"[ERROR] Failed to clear all files: {e}")
            raise


def get_file_repository(db_path: str = "output/index.db") -> FileRepository:
    """Get file repository instance.

    Args:
        db_path: Path to SQLite database file

    Returns:
        FileRepository instance
    """
    db_connection = DatabaseConnection.get_instance(db_path)
    return FileRepository(db_connection)
