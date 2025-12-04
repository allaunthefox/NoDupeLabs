# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Database layer for NoDupeLabs.

This module provides a thin wrapper around SQLite3 for storing file
metadata, deduplication information, and vector embeddings used by the
similarity backends. It exposes a simple DB class which manages a
single SQLite connection, initialization/migration of the schema, and
convenience methods for upserting and querying files and embeddings.

Design notes:
- Uses WAL journaling mode and tuned PRAGMAs for reasonable concurrent
    reads/writes.
- The database schema is intentionally compact: `files` holds the
    deduplication metadata and `embeddings` stores serialized vectors
    (JSON) for persistence.
- The DB class is not fully thread-safe; callers should serialize
    concurrent access (connections may be created per-thread in higher
    concurrency scenarios).
"""

import sqlite3
import json
import textwrap
import sys
import time
from pathlib import Path
from typing import Iterable, Tuple, List

# Current Schema Version for NoDupeLabs (Fresh Start)
SCHEMA_VERSION = 1

# Clean Base Schema
BASE_SCHEMA = textwrap.dedent(
    """
    PRAGMA journal_mode=WAL;
    PRAGMA synchronous=NORMAL;

    CREATE TABLE IF NOT EXISTS files(
            path TEXT PRIMARY KEY,
            size INTEGER NOT NULL,
            mtime INTEGER NOT NULL,
            file_hash TEXT NOT NULL,
            mime TEXT DEFAULT 'application/octet-stream',
            context_tag TEXT DEFAULT 'unarchived',
            hash_algo TEXT DEFAULT 'sha512',
            permissions TEXT DEFAULT '0'
    );

    CREATE INDEX IF NOT EXISTS idx_file_hash ON files(file_hash);
    CREATE INDEX IF NOT EXISTS idx_files_hash_ctx ON files(
        file_hash, context_tag
    );

    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY,
        applied_at INTEGER NOT NULL,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS embeddings(
            path TEXT PRIMARY KEY,
            dim INTEGER NOT NULL,
            vector TEXT NOT NULL,
            mtime INTEGER NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_embeddings_mtime ON embeddings(mtime);
    """
)


class DB:
    """Lightweight SQLite-backed persistence for file metadata.

    Usage example:

        >>> db = DB(Path('data/nodupe.db'))
        >>> db.upsert_files([(path, size, mtime, sha, mime, ctx, algo, perms)])
        >>> for row in db.iter_files():
        ...     print(row)

    Args:
        path: Path to the sqlite database file. The parent directory will
            be created if necessary.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path.as_posix(), timeout=30)
        self._init_schema()

    def _init_schema(self):
        """Ensure the required tables and indexes exist for the current schema.

        This method is idempotent and performs lightweight migrations for
        older schema versions (for example, adding a missing `permissions`
        column or creating the `embeddings` table). Any schema changes are
        committed immediately to keep the on-disk state consistent.
        """
        try:
            # Check if table exists
            cur = self.conn.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='files'"
            )
            if not cur.fetchone():
                self.conn.executescript(BASE_SCHEMA)
                self.conn.execute(
                    "INSERT INTO schema_version "
                    "(version, applied_at, description) VALUES (?, ?, ?)",
                    (
                        SCHEMA_VERSION, int(time.time()),
                        "Initial NoDupe Schema"
                    )
                )
                self.conn.commit()
            else:
                # Check for permissions column
                cur.execute("PRAGMA table_info(files)")
                columns = [row[1] for row in cur.fetchall()]
                if "permissions" not in columns:
                    print(
                        "[db] Migrating schema: Adding permissions column...",
                        file=sys.stderr
                    )
                    cur.execute(
                        "ALTER TABLE files "
                        "ADD COLUMN permissions TEXT DEFAULT '0'"
                    )
                    self.conn.commit()
                # Ensure embeddings table exists
                cur.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='embeddings'"
                )
                if not cur.fetchone():
                    print(
                        "[db] Migrating schema: Adding embeddings table...",
                        file=sys.stderr
                    )
                    cur.executescript(textwrap.dedent(
                        '''
                        CREATE TABLE IF NOT EXISTS embeddings(
                            path TEXT PRIMARY KEY,
                            dim INTEGER NOT NULL,
                            vector TEXT NOT NULL,
                            mtime INTEGER NOT NULL
                        );

                        CREATE INDEX IF NOT EXISTS idx_embeddings_mtime
                        ON embeddings(mtime);
                        '''
                    ))
                    self.conn.commit()
        except sqlite3.Error as e:
            print(
                f"[db][ERROR] Failed to initialize schema: {e}",
                file=sys.stderr
            )
            raise

    def close(self):
        """Close the underlying SQLite connection.

        Call this when the DB instance is no longer needed to release
        file handles and ensure all pending transactions are persisted.
        """
        self.conn.close()

    def upsert_files(
        self, records: Iterable[Tuple[str, int, int, str, str, str, str, str]]
    ):
        """Bulk insert or update file metadata records.

        This method is used by the scanner pipeline to persist discovered
        files into the `files` table. It performs an UPSERT (INSERT ON
        CONFLICT DO UPDATE) to make repeated runs idempotent and safe for
        incremental updates.

        Args:
            records: Iterable of tuples matching the table columns:
                (path, size, mtime, file_hash, mime, context_tag, hash_algo, permissions)

        Returns:
            None
        """
        cur = self.conn.cursor()
        cur.executemany(
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
            records,
        )
        self.conn.commit()

    def get_duplicates(self) -> List[Tuple[str, str, str]]:
        """Return groups of duplicate files.

        Returns a list of tuples:
            (file_hash, context_tag, concatenated_paths)

        Files are grouped by (file_hash, context_tag, hash_algo) and only
        groups with more than one member are returned.
        """
        query = """
            SELECT file_hash, context_tag, GROUP_CONCAT(path, '|')
            FROM files
            GROUP BY file_hash, context_tag, hash_algo
            HAVING COUNT(*) > 1
        """
        return list(self.conn.execute(query))

    def get_all(self):
        """Return a list of all file records (helper wrapper).

        This eagerly loads all rows into memory so callers should prefer
        `iter_files()` when iterating large databases.
        """
        return list(self.iter_files())

    def iter_files(self):
        """Yield file metadata rows as a DB cursor iterator.

        Yields rows in the same order as the SELECT statement. Each row
        contains (path, size, mtime, file_hash, mime, context_tag, hash_algo, permissions).
        """
        return self.conn.execute(
            "SELECT path, size, mtime, file_hash, mime, "
            "context_tag, hash_algo, permissions FROM files"
        )

    def get_known_files(self):
        """Yield (path, size, mtime, file_hash) tuples used by incremental scans.

        This generator is usually loaded into memory by the scanner to
        build a lightweight known-files mapping to avoid re-hashing
        unchanged files.
        """
        cur = self.conn.cursor()
        cur.execute("SELECT path, size, mtime, file_hash FROM files")
        for row in cur:
            yield row

    # Embedding helpers
    def upsert_embedding(self, path: str, vector: list, dim: int, mtime: int):
        self.upsert_embeddings([(path, vector, dim, mtime)])

    def upsert_embeddings(self, records: Iterable[Tuple[str, list, int, int]]):
        """Batch insert/update vector embeddings.

        Embeddings are serialized to JSON for storage. Each record must be
        a tuple: (path, vector, dim, mtime). The method uses an UPSERT so
        repeated writes for the same path overwrite the previous vector.
        """
        cur = self.conn.cursor()
        # Prepare data: serialize vector to JSON
        data = [
            (
                path, int(dim), json.dumps(vector, ensure_ascii=False),
                int(mtime)
            )
            for path, vector, dim, mtime in records
        ]
        cur.executemany(
            (
                "INSERT INTO embeddings(path, dim, vector, mtime) "
                "VALUES(?, ?, ?, ?) "
                "ON CONFLICT(path) DO UPDATE SET "
                "dim=excluded.dim, vector=excluded.vector, "
                "mtime=excluded.mtime"
            ),
            data,
        )
        self.conn.commit()

    def get_embedding(self, path: str):
        cur = self.conn.cursor()
        r = cur.execute(
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
        """Yield (path, dim, vector, mtime) tuples for all embeddings.

        The stored vector is deserialized from JSON; corrupt or malformed
        JSON will result in an empty vector for that row.
        """
        cur = self.conn.cursor()
        # Use the cursor as an iterator to avoid loading all rows into memory
        cur.execute("SELECT path, dim, vector, mtime FROM embeddings")
        for p, dim, vec_text, mtime in cur:
            try:
                vec = json.loads(vec_text)
            except (ValueError, TypeError):
                vec = []
            yield (p, int(dim), vec, int(mtime))
