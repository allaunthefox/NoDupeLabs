# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Database connection management.

Handles SQLite connection lifecycle, schema setup, and migrations for NoDupeLabs.
This module provides the core database infrastructure, managing connection pooling,
transaction handling, and background writer processes for optimal performance.

Key Features:
    - SQLite connection management with WAL mode for concurrent access
    - Automatic schema initialization and versioning
    - Background writer support for non-blocking bulk operations
    - Thread-safe operations with connection locking
    - Schema migration capabilities for database evolution
    - Comprehensive error handling and recovery

Dependencies:
    - sqlite3: Standard library SQLite database
    - threading: Thread-safe connection management
    - time: Timestamp and timeout handling
    - textwrap: SQL query formatting
    - typing: Type annotations for code safety

Example:
    >>> from pathlib import Path
    >>> from nodupe.db.connection import DatabaseConnection
    >>>
    >>> # Initialize database connection
    >>> conn = DatabaseConnection(Path('output/index.db'))
    >>>
    >>> # Execute a query
    >>> cursor = conn.execute("SELECT COUNT(*) FROM files")
    >>> count = cursor.fetchone()[0]
    >>> print(f"Database contains {count} files")
    >>>
    >>> # Use background writer for bulk operations
    >>> conn.start_writer(mode='auto', batch_size=200)
    >>>
    >>> # Perform bulk insert
    >>> records = [('/file1.txt', 1024, 1600000000, 'hash1',
    ...            'text/plain', 'unarchived', 'sha512', '0')]
    >>> conn.executemany(
    ...     "INSERT INTO files VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
    ...     records
    ... )
    >>>
    >>> # Clean up
    >>> conn.stop_writer(flush=True)
    >>> conn.close()
"""
import sqlite3
import threading
import sys
import time
import textwrap
from pathlib import Path
from typing import Any, List, Optional, Tuple


def _db_process_writer_main(
    db_path_str: str,
    queue: Any,
    batch_size: int,
    stop_sentinel: str
) -> None:
    """Entry point for a separate process writer.

    This function runs in a separate process and performs batch commits
    against its own SQLite connection. It's a module-level function so it
    can be used safely as a multiprocessing target without pickling the
    DatabaseConnection instance.
    """
    import sqlite3 as _sqlite3

    conn = _sqlite3.connect(db_path_str, timeout=30)
    try:
        buffer: List[Tuple[str, List[Tuple[Any, ...]]]] = []
        while True:
            try:
                msg = queue.get(timeout=0.5)
            except Exception:
                msg = None

            if msg is None:
                continue

            if msg == stop_sentinel:
                # flush remaining
                for q, params in buffer:
                    try:
                        conn.executemany(q, params)
                    except Exception:
                        pass
                conn.commit()
                break

            buffer.append(msg)
            if len(buffer) >= batch_size:
                for q, params in buffer:
                    try:
                        conn.executemany(q, params)
                    except Exception:
                        pass
                conn.commit()
                buffer = []
    finally:
        try:
            conn.close()
        except Exception:
            pass


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
        # Optional background writer queue. Disabled by default —
        # callers may enable via `start_writer` to offload bulk writes.
        self._writer_enabled: bool = False
        self._writer_mode: Optional[str] = None
        self._writer_queue: Any = None
        self._writer_worker: Any = None
        self._writer_batch_size: int = 100
        self._writer_stop_event: Any = None
        self._writer_stop_sentinel: str = ""

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
        # Stop any background writer if active
        try:
            self.stop_writer(flush=True)
        except Exception:
            pass

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
        # If a background writer is enabled, enqueue the work so callers
        # don't block on database IO. Otherwise perform the operation
        # synchronously as before.
        writer_enabled = getattr(self, "_writer_enabled", False)
        if writer_enabled and self._writer_queue is not None:
            # Enqueue a unit-of-work for the background writer
            try:
                self._writer_queue.put((query, list(params_list)))
                return
            except Exception:
                # Fallback to synchronous execution if enqueue fails
                pass

        with self._lock:
            if not self.conn:
                raise RuntimeError("Database not connected")
            self.conn.executemany(query, params_list)
            self.conn.commit()

    # Writer queue management
    def _thread_writer_loop(
        self, queue: Any, stop_event: Any, batch_size: int
    ) -> None:
        """Background writer loop that runs in a dedicated thread."""
        buffer: List[Tuple[str, List[Tuple[Any, ...]]]] = []
        while True:
            try:
                item = queue.get(timeout=0.5)
            except Exception:
                item = None

            if item is None:
                # check stop_event and flush periodically
                if stop_event.is_set():
                    # drain
                    while True:
                        try:
                            it = queue.get_nowait()
                        except Exception:
                            break
                        buffer.append(it)
                    if buffer:
                        self._apply_batch(buffer)
                    break
                # otherwise loop again
                continue

            buffer.append(item)
            # flush when buffer reaches batch_size
            if len(buffer) >= batch_size:
                self._apply_batch(buffer)
                buffer = []

        # ensure connection available
        return

    def _apply_batch(self, batch):
        """Apply a batch of (query, params_list) to the DB in a single
        transactional context.
        """
        if not batch:
            return
        with self._lock:
            if not self.conn:
                # Try to reconnect if needed
                self.connect()
            try:
                for q, params in batch:
                    self.conn.executemany(q, params)
                self.conn.commit()
            except Exception as e:
                # Best-effort: print the error and continue
                print(f"[db][WARN] Writer batch failed: {e}", file=sys.stderr)
    # _process_writer_main removed (now a module-level function), see
    # _db_process_writer_main above

    def start_writer(self, mode: str = "auto", batch_size: int = 100):
        """Start a background writer which offloads executemany calls.

        Args:
            mode: 'auto' | 'thread' | 'process' - how the writer should run
            batch_size: number of enqueued items to group into a single
                transaction commit.
        """
        if mode not in ("auto", "thread", "process"):
            raise ValueError(
                "mode must be one of: 'auto', 'thread', 'process'")

        # Choose mode heuristically. Process writers can be more resilient
        # on pre-3.13 CPython because they avoid GIL contention, while
        # thread writers are appropriate when running a GIL-free runtime
        # or in constrained environments.
        chosen = mode
        if mode == "auto":
            # Use proper runtime detection for GIL-free Python
            from nodupe.runtime import is_gil_disabled
            if is_gil_disabled():
                chosen = "thread"
            else:
                chosen = "process"

        # ensure any previous writer stopped
        self.stop_writer(flush=True)

        self._writer_enabled = True
        self._writer_mode = chosen
        self._writer_batch_size = max(1, int(batch_size))

        if chosen == "thread":
            import queue as _queue
            self._writer_queue = _queue.Queue()
            self._writer_stop_event = threading.Event()
            self._writer_worker = threading.Thread(
                target=self._thread_writer_loop,
                args=(self._writer_queue, self._writer_stop_event,
                      self._writer_batch_size),
                daemon=True,
            )
            self._writer_worker.start()
        else:
            # process mode
            try:
                import multiprocessing as _mp
                self._writer_queue = _mp.Queue()
                self._writer_stop_event = None
                # sentinel must be picklable and comparable across process
                stop_sentinel = f"__DB_WRITER_STOP__::{str(self.db_path)}"
                self._writer_worker = _mp.Process(
                    target=_db_process_writer_main,
                    args=(str(self.db_path), self._writer_queue,
                          self._writer_batch_size, stop_sentinel),
                    daemon=True,
                )
                # store sentinel so stop_writer can signal the child
                self._writer_stop_sentinel = stop_sentinel
                self._writer_worker.start()
            except Exception:
                # fallback to thread if process creation fails
                import queue as _queue
                self._writer_queue = _queue.Queue()
                self._writer_stop_event = threading.Event()
                self._writer_worker = threading.Thread(
                    target=self._thread_writer_loop,
                    args=(self._writer_queue, self._writer_stop_event,
                          self._writer_batch_size),
                    daemon=True,
                )
                self._writer_worker.start()

    def stop_writer(self, flush: bool = True, timeout: float = 5.0):
        """Stop the background writer and optionally wait for it to finish.

        Args:
            flush: If True, block until queue drained and committed.
            timeout: time to wait for worker shutdown.
        """
        if not getattr(self, "_writer_enabled", False):
            return

        if self._writer_mode == "thread":
            # signal thread to stop
            if self._writer_stop_event:
                self._writer_stop_event.set()
            if flush and self._writer_worker:
                self._writer_worker.join(timeout=timeout)
        else:
            # process mode: send sentinel and join
            try:
                # send sentinel (picklable string)
                self._writer_queue.put(self._writer_stop_sentinel)
            except Exception:
                pass
            if flush and self._writer_worker:
                self._writer_worker.join(timeout=timeout)

        # cleanup
        self._writer_enabled = False
        self._writer_mode = None
        self._writer_queue = None
        self._writer_worker = None
        self._writer_stop_event = None

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
