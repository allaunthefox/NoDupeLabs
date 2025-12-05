# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Database connection management.

Handles SQLite connection lifecycle, schema setup, and migrations.
Provides low-level query execution.
"""
import sqlite3
import sys
import time
import textwrap
from pathlib import Path
from typing import List, Optional, Tuple

# Current Schema Version for NoDupeLabs
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


class DatabaseConnection:
    """SQLite connection manager."""

    def __init__(self, db_path: Path):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        # Lock to serialize access to the sqlite connection across threads
        # (we use check_same_thread=False below to allow access from worker
        # threads when needed; the lock prevents concurrent queries corrupting
        # the connection state).
        self._lock = threading.RLock()
        self.connect()

    def connect(self):
        """Open database connection and initialize schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # allow cross-thread usage but guard with a lock
        self.conn = sqlite3.connect(
            str(self.db_path), timeout=30, check_same_thread=False
        )
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self):
        """Close database connection."""
        with self._lock:
            if self.conn:
                self.conn.close()
                self.conn = None

    def execute(
        self,
        query: str,
        params: Tuple = ()
    ) -> sqlite3.Cursor:
        """Execute SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Cursor with results
        """
        with self._lock:
            if not self.conn:
                raise RuntimeError("Database not connected")
            return self.conn.execute(query, params)

    def executemany(
        self,
        query: str,
        params_list: List[Tuple]
    ):
        """Execute query with multiple parameter sets.

        Args:
            query: SQL query string
            params_list: List of parameter tuples
        """
        with self._lock:
            if not self.conn:
                raise RuntimeError("Database not connected")
            self.conn.executemany(query, params_list)
            self.conn.commit()

    def _init_schema(self):
        """Ensure the required tables and indexes exist."""
        try:
            # Schema initialization touches multiple statements; guard with
            # the connection lock to avoid races on first-time init or
            # migrations when multiple threads create the DB simultaneously.
            with self._lock:
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
