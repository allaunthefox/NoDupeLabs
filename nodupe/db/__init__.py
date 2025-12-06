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

    def __init__(
        self, path: Path, *,
        writer_mode: Optional[str] = None,
        writer_batch_size: Optional[int] = None
    ):
        """Initialize database facade.

        Args:
            path: Path to SQLite database file
        """
        self.connection = DatabaseConnection(path)
        # Optionally start the background DB writer based on constructor
        # args or environment variable NODUPE_DB_WRITER_MODE.
        import os as _os
        if writer_mode is None:
            writer_mode = _os.environ.get("NODUPE_DB_WRITER_MODE")

        if writer_mode:
            batch = (
                writer_batch_size if writer_batch_size is not None else int(
                    _os.environ.get("NODUPE_DB_WRITER_BATCH", "100")
                )
            )
            # start writer in chosen mode (thread/process/auto)
            self.connection.start_writer(mode=writer_mode, batch_size=batch)
        self.files = FileRepository(self.connection)
        self.embeddings = EmbeddingRepository(self.connection)

    def close(self):
        """Close the underlying SQLite connection and stop background writers.

        This method ensures the database connection and any background writer
        threads/processes are cleanly shut down.
        """
        self.connection.close()

    # File operations delegated to FileRepository
    def upsert_files(
        self, records: Iterable[Tuple[str, int, int, str, str, str, str, str]]
    ):
        """Bulk insert or update file metadata records.

        Args:
            records: Iterable of tuples representing file metadata in the
                form (path, size, mtime, file_hash, mime, category, hash_algo,
                topic). The repository will insert or update records atomically
                where possible.
        """
        """
        Example:
            >>> from pathlib import Path
            >>> db = DB(Path('/tmp/test-index.db'))
            >>> records = [
            ...     ('/a.jpg', 1024, 1600000000, 'h1',
                     'image/jpeg', 'unarchived', 'sha512', '0'),
            ... ]
            >>> db.upsert_files(records)
        """
        self.files.upsert_files(records)

    def get_duplicates(self) -> List[Tuple[str, str, str]]:
        """Return a list of duplicate file groups.

        Returns:
            List[Tuple[str, str, str]]: A list of tuples representing duplicate
            groups. Each tuple typically contains identifying information for
            the group (e.g., (file_hash, representative_path, count)).
        """
        return self.files.get_duplicates()

    def get_all(self):
        """Return a list of all file metadata records stored in the DB.

        Returns:
            List[Dict]: List of file record mappings.
        """
        return self.files.get_all()

    def iter_files(self):
        """Return an iterator of all file metadata rows.

        Yields:
            Dict: File record mapping for each file in the DB. This is a
            memory-friendly iterator suitable for bulk processing.

        Returns:
            An iterator that yields file record mappings.
        """
        return self.files.iter_files()

    def get_known_files(self):
        """Return a mapping of known files keyed by file path or hash.

        The precise mapping shape is implementation-defined but is typically
        used by scanners to quickly check which files are already known.

        Returns:
            A mapping (usually dict) with keys representing file path or
            hash and values containing metadata used to identify known
            files.
        """
        return self.files.get_known_files()

    # Embedding operations delegated to EmbeddingRepository
    def upsert_embedding(self, path: str, vector: list, dim: int, mtime: int):
        """Insert or update a single vector embedding.

        Args:
            path: File path associated with this embedding.
            vector: Numeric vector (list/bytes) representing the embedding.
            dim: Dimension of the embedding vector.
            mtime: Modification time of the file associated with the embedding.
        """
        self.embeddings.upsert_embedding(path, vector, dim, mtime)

    def upsert_embeddings(self, records: Iterable[Tuple[str, list, int, int]]):
        """Batch insert or update multiple embeddings.

        Args:
            records: Iterable of tuples (path, vector, dim, mtime) to upsert.
        """
        self.embeddings.upsert_embeddings(records)

    def get_embedding(self, path: str) -> Optional[Dict]:
        """Retrieve a single embedding record for the given path.

        Args:
            path: File path associated with the embedding.

        Returns:
            Optional[Dict]: Embedding metadata and binary/vector payload if
            present, otherwise None.
        """
        return self.embeddings.get_embedding(path)

    def iter_embeddings(self) -> Iterable[Tuple[str, int, bytes, float]]:
        """Return an iterator over embedding records.

        Yields:
            Tuple[str,int,bytes,float]: Path, dimension, serialized vector
            payload, and modification time.

        Returns:
            An iterator that yields (path, dim, vector, mtime) tuples.
        """
        return self.embeddings.get_all_embeddings()

    def get_all_embeddings(self):
        """Compatibility alias for :py:meth:`iter_embeddings`.

        Returns:
            Iterator over embedding tuples for backward compatibility.
        """
        return self.iter_embeddings()
