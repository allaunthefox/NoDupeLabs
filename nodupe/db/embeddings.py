# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Embedding repository for vector storage.

Handles storage and retrieval of file embeddings for similarity search in
NoDupeLabs. This module provides efficient storage and retrieval of vector
embeddings used for content-based similarity analysis, enabling features
like finding visually similar images or semantically related content.

Key Features:
    - Efficient storage of high-dimensional vectors as JSON
    - Atomic upsert operations for embedding records
    - Batch operations for bulk embedding processing
    - Memory-friendly iteration over large embedding datasets
    - Automatic JSON serialization/deserialization of vector data

Dependencies:
    - json: Vector serialization/deserialization
    - typing: Type annotations for code safety
    - .connection: Database connection management

Example:
    >>> from pathlib import Path
    >>> from nodupe.db.connection import DatabaseConnection
    >>> from nodupe.db.embeddings import EmbeddingRepository
    >>>
    >>> # Initialize repository
    >>> conn = DatabaseConnection(Path('output/index.db'))
    >>> repo = EmbeddingRepository(conn)
    >>>
    >>> # Store embeddings
    >>> embeddings = [
    ...     ('/photo1.jpg', [0.1, 0.2, 0.3], 3, 1600000000),
    ...     ('/photo2.jpg', [0.4, 0.5, 0.6], 3, 1600000001)
    ... ]
    >>> repo.upsert_embeddings(embeddings)
    >>>
    >>> # Retrieve an embedding
    >>> embedding = repo.get_embedding('/photo1.jpg')
    >>> print(f"Retrieved {embedding['dim']}-dimensional embedding")
    >>>
    >>> # Iterate through all embeddings
    >>> for path, dim, vector, mtime in repo.get_all_embeddings():
    ...     print(f"Embedding for {path}: {dim} dimensions")
    >>>
    >>> # Clean up
    >>> conn.close()
"""
import json
from typing import Iterable, Optional, Tuple

from .connection import DatabaseConnection


class EmbeddingRepository:
    """Repository for embedding operations."""

    def __init__(self, connection: DatabaseConnection):
        """Initialize repository.

        Args:
            connection: Database connection
        """
        self.conn = connection

    def upsert_embedding(self, path: str, vector: list, dim: int, mtime: int):
        """Insert or update single embedding.

        Convenience method for storing a single file embedding. Automatically
        delegates to the batch upsert method for consistent handling.

        Args:
            path: File path associated with this embedding
            vector: Numeric vector as list of floats representing the embedding
            dim: Dimension of the embedding vector
            mtime: Modification time of the file

        Example:
            >>> # Store a single embedding
            >>> embedding_vector = [0.1, 0.2, 0.3, 0.4]
            >>> repo.upsert_embedding('/photo.jpg', embedding_vector, 4,
            ...                       1600000000)
        """
        self.upsert_embeddings([(path, vector, dim, mtime)])

    def upsert_embeddings(
        self,
        records: Iterable[Tuple[str, list, int, int]]
    ):
        """Insert or update multiple embeddings.

        Args:
            records: Iterable of (path, vector, dim, mtime) tuples
        """
        data = [
            (
                path, int(dim), json.dumps(vector, ensure_ascii=False),
                int(mtime)
            )
            for path, vector, dim, mtime in records
        ]

        self.conn.executemany(
            """
            INSERT INTO embeddings(path, dim, vector, mtime)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                dim=excluded.dim, vector=excluded.vector,
                mtime=excluded.mtime
            """,
            data
        )

    def get_embedding(self, path: str) -> Optional[dict]:
        """Get embedding for file.

        Args:
            path: File path

        Returns:
            Dict with dim, vector, mtime or None
        """
        r = self.conn.execute(
            "SELECT dim, vector, mtime FROM embeddings WHERE path = ?", (path,)
        ).fetchone()

        if not r:
            return None

        dim, vec_text, mtime = r
        try:
            vec = json.loads(vec_text)
        except (ValueError, TypeError):
            vec = []

        return {'dim': int(dim), 'vector': vec, 'mtime': int(mtime)}

    def get_all_embeddings(self):
        """Yield (path, dim, vector, mtime) tuples for all embeddings."""
        cursor = self.conn.execute(
            "SELECT path, dim, vector, mtime FROM embeddings")
        for p, dim, vec_text, mtime in cursor:
            try:
                vec = json.loads(vec_text)
            except (ValueError, TypeError):
                vec = []
            yield (p, int(dim), vec, int(mtime))
