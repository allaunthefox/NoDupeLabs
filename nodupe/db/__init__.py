# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Database layer for NoDupeLabs.

Provides a unified database interface for storing and retrieving file metadata,
duplicate information, and similarity embeddings. This module serves as the
primary data persistence layer for NoDupeLabs, handling all database operations
through a facade pattern that delegates to specialized repositories.

Key Features:
    - SQLite-based storage with WAL mode for concurrent access
    - Schema versioning and automatic migrations
    - Background writer support for improved performance
    - File metadata storage with comprehensive indexing
    - Embedding storage for similarity search functionality
    - Thread-safe operations with connection pooling

Dependencies:
    - sqlite3: Standard library SQLite database
    - pathlib: Filesystem path handling
    - typing: Type annotations for code safety

Example:
    >>> from pathlib import Path
    >>> from nodupe.db import DB
    >>>
    >>> # Initialize database
    >>> db = DB(Path('output/index.db'))
    >>>
    >>> # Store file metadata
    >>> records = [('/photo.jpg', 1024, 1600000000, 'hash123',
                   'image/jpeg', 'unarchived', 'sha512', '0')]
    >>> db.upsert_files(records)
    >>>
    >>> # Find duplicates
    >>> duplicates = db.get_duplicates()
    >>> print(f"Found {len(duplicates)} duplicate groups")
    >>>
    >>> # Close database
    >>> db.close()
"""
from pathlib import Path
from typing import Any, Iterable, Tuple, List, Dict, Optional

from .connection import DatabaseConnection
from .files import FileRepository
from .embeddings import EmbeddingRepository


class DB:
    """Database facade for NoDupeLabs.

    Maintains backward compatibility with the original DB class while
    delegating to specialized repositories for file metadata and embedding
    operations. This class serves as the primary interface for all database
    operations in NoDupeLabs, providing a unified API for data persistence.

    Attributes:
        connection: DatabaseConnection instance managing SQLite operations
        files: FileRepository instance for file metadata operations
        embeddings: EmbeddingRepository instance for embedding storage

    Example:
        >>> from pathlib import Path
        >>> from nodupe.db import DB
        >>>
        >>> # Initialize with background writer for better performance
        >>> db = DB(Path('output/index.db'), writer_mode='auto')
        >>>
        >>> # Use the database
        >>> files = db.get_all()
        >>> duplicates = db.get_duplicates()
        >>>
        >>> # Clean up
        >>> db.close()
    """

    def __init__(
        self, path: Path, *,
        writer_mode: Optional[str] = None,
        writer_batch_size: Optional[int] = None
    ):
        """Initialize database facade.

        Args:
            path: Path to SQLite database file
            writer_mode: Optional background writer mode ('auto', 'thread',
                'process')
            writer_batch_size: Optional batch size for background writer
                operations

        Raises:
            RuntimeError: If database connection cannot be established
            ValueError: If writer_mode is invalid

        Example:
            >>> # Basic initialization
            >>> db = DB(Path('output/index.db'))
            >>>
            >>> # With background writer for performance
            >>> db = DB(Path('output/index.db'), writer_mode='auto',
            ...         writer_batch_size=200)
            >>>
            >>> # Using environment variables
            >>> import os
            >>> os.environ['NODUPE_DB_WRITER_MODE'] = 'thread'
            >>> db = DB(Path('output/index.db'))  # Uses thread writer
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

    def get_all(self) -> List[Dict[str, Any]]:
        """Return a list of all file metadata records stored in the DB.

        Returns:
            List[Dict[str, any]]: List of file record mappings containing
            file metadata such as path, size, hash, mime type, etc.

        Example:
            >>> files = db.get_all()
            >>> for file in files:
            ...     print(f"File: {file['path']}, Size: {file['size']}")
        """
        return self.files.get_all()

    def iter_files(self) -> Iterable[Dict[str, Any]]:
        """Return an iterator of all file metadata rows.

        Yields:
            Dict[str, any]: File record mapping for each file in the DB.
            This is a memory-friendly iterator suitable for bulk processing.

        Returns:
            Iterable[Dict[str, any]]: An iterator that yields file record
            mappings.

        Example:
            >>> for file_record in db.iter_files():
            ...     print(f"Processing: {file_record['path']}")
        """
        return self.files.iter_files()

    def get_known_files(self) -> Iterable[Tuple[str, int, int, str]]:
        """Return a mapping of known files keyed by file path or hash.

        The precise mapping shape is implementation-defined but is typically
        used by scanners to quickly check which files are already known.

        Returns:
            Iterable[Tuple[str, int, int, str]]: An iterator that yields
            tuples of (path, size, mtime, file_hash) for known files.

        Example:
            >>> known_files = db.get_known_files()
            >>> for path, size, mtime, file_hash in known_files:
            ...     print(f"Known file: {path}")
        """
        return self.files.get_known_files()

    # Embedding operations delegated to EmbeddingRepository
    def upsert_embedding(
        self, path: str, vector: List[float], dim: int, mtime: int
    ):
        """Insert or update a single vector embedding.

        Args:
            path: File path associated with this embedding.
            vector: Numeric vector (list of floats) representing the embedding.
            dim: Dimension of the embedding vector.
            mtime: Modification time of the file associated with the embedding.

        Example:
            >>> # Store an embedding for a file
            >>> embedding = [0.1, 0.2, 0.3, 0.4]  # 4-dimensional vector
            >>> db.upsert_embedding('/photo.jpg', embedding, 4, 1600000000)
        """
        self.embeddings.upsert_embedding(path, vector, dim, mtime)

    def upsert_embeddings(
        self, records: Iterable[Tuple[str, List[float], int, int]]
    ):
        """Batch insert or update multiple embeddings.

        Args:
            records: Iterable of tuples (path, vector, dim, mtime) to upsert.

        Example:
            >>> # Batch insert multiple embeddings
            >>> embeddings = [
            ...     ('/photo1.jpg', [0.1, 0.2], 2, 1600000000),
            ...     ('/photo2.jpg', [0.3, 0.4], 2, 1600000001)
            ... ]
            >>> db.upsert_embeddings(embeddings)
        """
        self.embeddings.upsert_embeddings(records)

    def get_embedding(self, path: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single embedding record for the given path.

        Args:
            path: File path associated with the embedding.

        Returns:
            Optional[Dict[str, any]]: Embedding metadata and vector payload if
            present, otherwise None.

        Example:
            >>> # Retrieve an embedding
            >>> embedding = db.get_embedding('/photo.jpg')
            >>> if embedding:
            ...     print(f"Found embedding with {embedding['dim']} "
            ...            f"dimensions")
        """
        return self.embeddings.get_embedding(path)

    def iter_embeddings(self) -> Iterable[Tuple[str, int, List[float], int]]:
        """Return an iterator over embedding records.

        Yields:
            Tuple[str, int, List[float], int]: Path, dimension, vector,
            and modification time.

        Returns:
            Iterable[Tuple[str, int, List[float], int]]: An iterator that
            yields embedding records.

        Example:
            >>> # Iterate through all embeddings
            >>> for path, dim, vector, mtime in db.iter_embeddings():
            ...     print(f"Embedding for {path}: {dim} dimensions")
        """
        return self.embeddings.get_all_embeddings()

    def get_all_embeddings(
        self
    ) -> Iterable[Tuple[str, int, List[float], int]]:
        """Compatibility alias for :py:meth:`iter_embeddings`.

        Returns:
            Iterable[Tuple[str, int, List[float], int]]: Iterator over
            embedding tuples for backward compatibility.

        Example:
            >>> # Get all embeddings (same as iter_embeddings)
            >>> embeddings = list(db.get_all_embeddings())
            >>> print(f"Total embeddings: {len(embeddings)}")
        """
        return self.iter_embeddings()
