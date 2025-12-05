# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Database layer for NoDupeLabs.

This module exposes a simple DB facade which manages the SQLite connection
and delegates operations to specialized repositories.
"""
from pathlib import Path
from typing import Iterable, Tuple, List, Dict, Optional

from .connection import DatabaseConnection
from .files import FileRepository
from .embeddings import EmbeddingRepository


class DB:
    """Facade for database operations.

    Maintains backward compatibility with the original DB class
    while delegating to specialized components.
    """

    def __init__(self, path: Path):
        """Initialize database facade.

        Args:
            path: Path to SQLite database file
        """
        self.connection = DatabaseConnection(path)
        self.files = FileRepository(self.connection)
        self.embeddings = EmbeddingRepository(self.connection)

    def close(self):
        """Close the underlying SQLite connection."""
        self.connection.close()

    # File operations delegated to FileRepository
    def upsert_files(
        self, records: Iterable[Tuple[str, int, int, str, str, str, str, str]]
    ):
        """Bulk insert or update file metadata records."""
        """
        Example:
            >>> from pathlib import Path
            >>> db = DB(Path('/tmp/test-index.db'))
            >>> records = [
            ...     ('/a.jpg', 1024, 1600000000, 'h1', 'image/jpeg', 'unarchived', 'sha512', '0'),
            ... ]
            >>> db.upsert_files(records)
        """
        self.files.upsert_files(records)

    def get_duplicates(self) -> List[Tuple[str, str, str]]:
        """Return groups of duplicate files."""
        return self.files.get_duplicates()

    def get_all(self):
        """Return a list of all file records."""
        return self.files.get_all()

    def iter_files(self):
        """Yield file metadata rows."""
        return self.files.iter_files()

    def get_known_files(self):
        """Yield (path, size, mtime, file_hash) for incremental scans."""
        return self.files.get_known_files()

    # Embedding operations delegated to EmbeddingRepository
    def upsert_embedding(self, path: str, vector: list, dim: int, mtime: int):
        """Insert or update a single embedding."""
        self.embeddings.upsert_embedding(path, vector, dim, mtime)

    def upsert_embeddings(self, records: Iterable[Tuple[str, list, int, int]]):
        """Batch insert/update vector embeddings."""
        self.embeddings.upsert_embeddings(records)

    def get_embedding(self, path: str) -> Optional[Dict]:
        """Get a single embedding by path."""
        return self.embeddings.get_embedding(path)

    def get_all_embeddings(self):
        """Yield (path, dim, vector, mtime) tuples for all embeddings."""
        return self.embeddings.get_all_embeddings()
