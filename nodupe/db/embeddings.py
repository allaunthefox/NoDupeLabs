# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Embedding repository for vector storage.

Handles storage and retrieval of file embeddings for similarity search.
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
        """Insert or update single embedding."""
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
