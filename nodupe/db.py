# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import sqlite3
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
            hash_algo TEXT DEFAULT 'sha512'
    );

    CREATE INDEX IF NOT EXISTS idx_file_hash ON files(file_hash);
    CREATE INDEX IF NOT EXISTS idx_files_hash_ctx ON files(file_hash, context_tag);

    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY,
        applied_at INTEGER NOT NULL,
        description TEXT
    );
    """
)

class DB:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path.as_posix(), timeout=30)
        self._init_schema()

    def _init_schema(self):
        """Initialize the database schema."""
        try:
            # Check if table exists
            cur = self.conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
            if not cur.fetchone():
                self.conn.executescript(BASE_SCHEMA)
                self.conn.execute(
                    "INSERT INTO schema_version (version, applied_at, description) VALUES (?, ?, ?)",
                    (SCHEMA_VERSION, int(time.time()), "Initial NoDupe Schema")
                )
                self.conn.commit()
        except sqlite3.Error as e:
            print(f"[db][ERROR] Failed to initialize schema: {e}", file=sys.stderr)
            raise

    def close(self):
        self.conn.close()

    def upsert_files(self, records: Iterable[Tuple[str, int, int, str, str, str, str]]):
        """
        Insert or update file records.
        Args:
            records: (path, size, mtime, file_hash, mime, context_tag, hash_algo)
        """
        cur = self.conn.cursor()
        cur.executemany(
            textwrap.dedent(
                """
                INSERT INTO files(path, size, mtime, file_hash, mime, context_tag, hash_algo)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    size=excluded.size,
                    mtime=excluded.mtime,
                    file_hash=excluded.file_hash,
                    mime=excluded.mime,
                    context_tag=excluded.context_tag,
                    hash_algo=excluded.hash_algo
                """
            ),
            records,
        )
        self.conn.commit()

    def get_duplicates(self) -> List[Tuple[str, str, str]]:
        """
        Get duplicate file groups.
        Returns: (file_hash, context_tag, pipe-separated paths)
        """
        query = """
            SELECT file_hash, context_tag, GROUP_CONCAT(path, '|')
            FROM files
            GROUP BY file_hash, context_tag, hash_algo
            HAVING COUNT(*) > 1
        """
        return list(self.conn.execute(query))

    def get_all(self):
        return list(
            self.conn.execute(
                "SELECT path, size, mtime, file_hash, mime, context_tag, hash_algo FROM files"
            )
        )
