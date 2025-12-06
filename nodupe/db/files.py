# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""File repository for database operations.

Handles all file-related queries and persistence operations.
Abstracts SQL details from business logic.
"""
import textwrap
from typing import Dict, Iterable, List, Tuple

from .connection import DatabaseConnection


# Type alias for file records
FileRecord = Tuple[str, int, int, str, str, str, str, str]


class FileRepository:
    """Repository for file operations."""

    def __init__(self, connection: DatabaseConnection):
        """Initialize repository.

        Args:
            connection: Database connection
        """
        self.conn = connection

    def upsert_files(self, records: Iterable[FileRecord]):
        """Insert or update file records.

        Args:
            records: Iterable of tuples with the following shape:
                (path, size, mtime, hash, mime, context, algo,
                perms)

        Example:
            >>> repo = FileRepository(
            ...     DatabaseConnection(Path('/tmp/index.db'))
            ... )
            >>> rows = [(
            ...     '/a.jpg', 1024, 1600000000, 'h1',
            ...     'image/jpeg', 'unarchived', 'sha512', '0'
            ... )]
            >>> repo.upsert_files(rows)
        """
        self.conn.executemany(
            textwrap.dedent(
                """
                INSERT INTO files(
                    path, size, mtime, file_hash, mime,
                    context_tag, hash_algo, permissions
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    size=excluded.size,
                    mtime=excluded.mtime,
                    file_hash=excluded.file_hash,
                    mime=excluded.mime,
                    context_tag=excluded.context_tag,
                    hash_algo=excluded.hash_algo,
                    permissions=excluded.permissions
                """
            ),
            list(records)
        )

    def get_duplicates(self) -> List[Tuple[str, str, str]]:
        """Find duplicate files by hash.

        Returns:
            List of (hash, context, concatenated_paths) tuples
        """
        query = """
            SELECT file_hash, context_tag, GROUP_CONCAT(path, '|')
            FROM files
            GROUP BY file_hash, context_tag, hash_algo
            HAVING COUNT(*) > 1
        """
        return list(self.conn.execute(query))

    def get_all(self) -> List[Dict]:
        """Get all file records.

        Returns:
            List of file record dicts
        """
        return list(self.iter_files())

    def get_known_files(self):
        """Yield (path, size, mtime, file_hash) for incremental scans."""
        cursor = self.conn.execute(
            "SELECT path, size, mtime, file_hash FROM files")
        for row in cursor:
            yield row

    def iter_files(self):
        """Iterate over all file records.

        Yields:
            File record rows
        """
        return self.conn.execute(
            "SELECT path, size, mtime, file_hash, mime, "
            "context_tag, hash_algo, permissions FROM files"
        )
