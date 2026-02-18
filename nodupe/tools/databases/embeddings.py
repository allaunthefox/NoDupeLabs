# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Embedding repository for database operations.

This module provides embedding repository functionality for the database layer,
handling file embedding storage and retrieval.

Key Features:
    - Embedding CRUD operations
    - Model version management
    - Batch operations
    - Error handling

Dependencies:
    - sqlite3 (standard library only)
    - typing (standard library only)
"""

import pickle
from typing import Any, Optional

from .connection import DatabaseConnection


class EmbeddingRepository:
    """Embedding repository for database operations.

    Responsibilities:
    - Manage file embeddings in database
    - Handle embedding CRUD operations
    - Manage model versions
    - Support batch operations
    """

    def __init__(self, db_connection: DatabaseConnection):
        """Initialize embedding repository.

        Args:
            db_connection: Database connection instance
        """
        self.db = db_connection

    def add_embedding(
        self,
        file_id: int,
        embedding: Any,
        model_version: str,
        created_time: int,
    ) -> Optional[int]:
        """Add embedding to database.

        Args:
            file_id: File ID
            embedding: Embedding data
            model_version: Model version
            created_time: Creation timestamp

        Returns:
            Embedding ID
        """
        try:
            # Serialize embedding to bytes
            embedding_bytes = pickle.dumps(embedding)

            cursor = self.db.execute(
                """
                INSERT INTO embeddings (file_id, embedding, model_version, created_time)
                VALUES (?, ?, ?, ?)
                """,
                (file_id, embedding_bytes, model_version, created_time),
            )
            return cursor.lastrowid
        except Exception as e:
            print(f"[ERROR] Failed to add embedding: {e}")
            raise

    def get_embedding(self, embedding_id: int) -> Optional[dict[str, Any]]:
        """Get embedding by ID.

        Args:
            embedding_id: Embedding ID

        Returns:
            Embedding data or None if not found
        """
        try:
            cursor = self.db.execute(
                "SELECT * FROM embeddings WHERE id = ?", (embedding_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "file_id": row[1],
                    "embedding": pickle.loads(row[2]),
                    "model_version": row[3],
                    "created_time": row[4],
                }
            return None
        except Exception as e:
            print(f"[ERROR] Failed to get embedding: {e}")
            raise

    def get_embedding_by_file(
        self, file_id: int, model_version: str
    ) -> Optional[dict[str, Any]]:
        """Get embedding by file ID and model version.

        Args:
            file_id: File ID
            model_version: Model version

        Returns:
            Embedding data or None if not found
        """
        try:
            cursor = self.db.execute(
                "SELECT * FROM embeddings WHERE file_id = ? AND model_version = ?",
                (file_id, model_version),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "file_id": row[1],
                    "embedding": pickle.loads(row[2]),
                    "model_version": row[3],
                    "created_time": row[4],
                }
            return None
        except Exception as e:
            print(f"[ERROR] Failed to get embedding by file: {e}")
            raise

    def get_embeddings_by_file(self, file_id: int) -> list[dict[str, Any]]:
        """Get all embeddings for a file.

        Args:
            file_id: File ID

        Returns:
            List of embeddings for the file
        """
        try:
            cursor = self.db.execute(
                "SELECT * FROM embeddings WHERE file_id = ? ORDER BY model_version",
                (file_id,),
            )
            return [
                {
                    "id": row[0],
                    "file_id": row[1],
                    "embedding": pickle.loads(row[2]),
                    "model_version": row[3],
                    "created_time": row[4],
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"[ERROR] Failed to get embeddings by file: {e}")
            raise

    def get_embeddings_by_model(
        self, model_version: str
    ) -> list[dict[str, Any]]:
        """Get all embeddings for a model version.

        Args:
            model_version: Model version

        Returns:
            List of embeddings for the model
        """
        try:
            cursor = self.db.execute(
                "SELECT * FROM embeddings WHERE model_version = ? ORDER BY file_id",
                (model_version,),
            )
            return [
                {
                    "id": row[0],
                    "file_id": row[1],
                    "embedding": pickle.loads(row[2]),
                    "model_version": row[3],
                    "created_time": row[4],
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"[ERROR] Failed to get embeddings by model: {e}")
            raise

    def update_embedding(self, embedding_id: int, embedding: Any) -> bool:
        """Update embedding data.

        Args:
            embedding_id: Embedding ID
            embedding: New embedding data

        Returns:
            True if updated, False if not found
        """
        try:
            # Serialize embedding to bytes
            embedding_bytes = pickle.dumps(embedding)

            cursor = self.db.execute(
                "UPDATE embeddings SET embedding = ? WHERE id = ?",
                (embedding_bytes, embedding_id),
            )
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ERROR] Failed to update embedding: {e}")
            raise

    def delete_embedding(self, embedding_id: int) -> bool:
        """Delete embedding from database.

        Args:
            embedding_id: Embedding ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            cursor = self.db.execute(
                "DELETE FROM embeddings WHERE id = ?", (embedding_id,)
            )
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ERROR] Failed to delete embedding: {e}")
            raise

    def delete_embeddings_by_file(self, file_id: int) -> int:
        """Delete all embeddings for a file.

        Args:
            file_id: File ID

        Returns:
            Number of embeddings deleted
        """
        try:
            cursor = self.db.execute(
                "DELETE FROM embeddings WHERE file_id = ?", (file_id,)
            )
            return cursor.rowcount
        except Exception as e:
            print(f"[ERROR] Failed to delete embeddings by file: {e}")
            raise

    def delete_embeddings_by_model(self, model_version: str) -> int:
        """Delete all embeddings for a model version.

        Args:
            model_version: Model version

        Returns:
            Number of embeddings deleted
        """
        try:
            cursor = self.db.execute(
                "DELETE FROM embeddings WHERE model_version = ?",
                (model_version,),
            )
            return cursor.rowcount
        except Exception as e:
            print(f"[ERROR] Failed to delete embeddings by model: {e}")
            raise

    def get_all_embeddings(self) -> list[dict[str, Any]]:
        """Get all embeddings from database.

        Returns:
            List of all embeddings
        """
        try:
            cursor = self.db.execute(
                "SELECT * FROM embeddings ORDER BY file_id, model_version"
            )
            return [
                {
                    "id": row[0],
                    "file_id": row[1],
                    "embedding": pickle.loads(row[2]),
                    "model_version": row[3],
                    "created_time": row[4],
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"[ERROR] Failed to get all embeddings: {e}")
            raise

    def count_embeddings(self) -> int:
        """Count total embeddings in database.

        Returns:
            Total embedding count
        """
        try:
            cursor = self.db.execute("SELECT COUNT(*) FROM embeddings")
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"[ERROR] Failed to count embeddings: {e}")
            raise

    def count_embeddings_by_model(self, model_version: str) -> int:
        """Count embeddings for a model version.

        Args:
            model_version: Model version

        Returns:
            Embedding count for the model
        """
        try:
            cursor = self.db.execute(
                "SELECT COUNT(*) FROM embeddings WHERE model_version = ?",
                (model_version,),
            )
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"[ERROR] Failed to count embeddings by model: {e}")
            raise

    def batch_add_embeddings(self, embeddings: list[dict[str, Any]]) -> int:
        """Add multiple embeddings in batch.

        Args:
            embeddings: List of embedding data dictionaries

        Returns:
            Number of embeddings added
        """
        if not embeddings:
            return 0

        try:
            data = [
                (
                    emb_data["file_id"],
                    pickle.dumps(emb_data["embedding"]),
                    emb_data["model_version"],
                    emb_data["created_time"],
                )
                for emb_data in embeddings
            ]

            self.db.executemany(
                """INSERT INTO embeddings
                (file_id, embedding, model_version, created_time)
                VALUES (?, ?, ?, ?)""",
                [tuple(item) for item in data],
            )
            return len(embeddings)
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[ERROR] Failed to batch add embeddings: {e}")
            raise

    def clear_all_embeddings(self) -> None:
        """Clear all embeddings from database."""
        try:
            self.db.execute("DELETE FROM embeddings")
            self.db.commit()
        except Exception as e:
            print(f"[ERROR] Failed to clear all embeddings: {e}")
            raise


def get_embedding_repository(
    db_path: str = "output/index.db",
) -> EmbeddingRepository:
    """Get embedding repository instance.

    Args:
        db_path: Path to SQLite database file

    Returns:
        EmbeddingRepository instance
    """
    db_connection = DatabaseConnection.get_instance(db_path)
    return EmbeddingRepository(db_connection)
