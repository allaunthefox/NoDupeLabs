# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

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
    CREATE INDEX IF NOT EXISTS idx_files_hash_ctx ON files(file_hash, context_tag);

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
            else:
                # Check for permissions column
                cur.execute("PRAGMA table_info(files)")
                columns = [row[1] for row in cur.fetchall()]
                if "permissions" not in columns:
                    print("[db] Migrating schema: Adding permissions column...", file=sys.stderr)
                    cur.execute("ALTER TABLE files ADD COLUMN permissions TEXT DEFAULT '0'")
                    self.conn.commit()
                # Ensure embeddings table exists
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='embeddings'")
                if not cur.fetchone():
                    print("[db] Migrating schema: Adding embeddings table...", file=sys.stderr)
                    cur.executescript(textwrap.dedent(
                        '''
                        CREATE TABLE IF NOT EXISTS embeddings(
                            path TEXT PRIMARY KEY,
                            dim INTEGER NOT NULL,
                            vector TEXT NOT NULL,
                            mtime INTEGER NOT NULL
                        );

                        CREATE INDEX IF NOT EXISTS idx_embeddings_mtime ON embeddings(mtime);
                        '''
                    ))
                    self.conn.commit()
        except sqlite3.Error as e:
            print(f"[db][ERROR] Failed to initialize schema: {e}", file=sys.stderr)
            raise

    def close(self):
        self.conn.close()

    def upsert_files(self, records: Iterable[Tuple[str, int, int, str, str, str, str, str]]):
        """
        Insert or update file records.
        Args:
            records: (path, size, mtime, file_hash, mime, context_tag, hash_algo, permissions)
        """
        cur = self.conn.cursor()
        cur.executemany(
            textwrap.dedent(
                """
                INSERT INTO files(path, size, mtime, file_hash, mime, context_tag, hash_algo, permissions)
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
                "SELECT path, size, mtime, file_hash, mime, context_tag, hash_algo, permissions FROM files"
            )
        )

    # Embedding helpers
    def upsert_embedding(self, path: str, vector: list, dim: int, mtime: int):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO embeddings(path, dim, vector, mtime) VALUES(?, ?, ?, ?)"
            " ON CONFLICT(path) DO UPDATE SET dim=excluded.dim, vector=excluded.vector, mtime=excluded.mtime",
            (path, int(dim), json.dumps(vector, ensure_ascii=False), int(mtime)),
        )
        self.conn.commit()

    def get_embedding(self, path: str):
        cur = self.conn.cursor()
        r = cur.execute("SELECT dim, vector, mtime FROM embeddings WHERE path = ?", (path,)).fetchone()
        if not r:
            return None
        dim, vec_text, mtime = r
        try:
            vec = json.loads(vec_text)
        except Exception:
            vec = []
        return {'dim': int(dim), 'vector': vec, 'mtime': int(mtime)}

    def get_all_embeddings(self):
        cur = self.conn.cursor()
        rows = cur.execute("SELECT path, dim, vector, mtime FROM embeddings").fetchall()
        out = []
        for p, dim, vec_text, mtime in rows:
            try:
                vec = json.loads(vec_text)
            except Exception:
                vec = []
            out.append((p, int(dim), vec, int(mtime)))
        return out
