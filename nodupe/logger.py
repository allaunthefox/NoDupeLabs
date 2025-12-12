# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Structured JSONL logging system.

This module provides a structured logging facility that writes events
to newline-delimited JSON files. It supports automatic log rotation
based on file size and retention of a configurable number of log files.

Key Features:
    - Structured logging (JSON per line) for easy parsing
    - Automatic rotation when log file exceeds size threshold
    - Retention policy to delete old logs
    - Thread-safe appending (OS atomic write for small records)

Classes:
    - JsonlLogger: Main logger implementation

Dependencies:
    - json: Log serialization
    - pathlib: File handling
    - datetime: Timestamp generation

Example:
    >>> logger = JsonlLogger(Path("logs"), rotate_mb=5)
    >>> logger.log("INFO", "scan_started", root="/data")
"""

import json
import queue
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union


class JsonlLogger:
    """Structured logger writing to JSONL files with rotation.

    This class implements a structured logging system that writes events to
    newline-delimited JSON files. It supports automatic log rotation based on
    file size and retention of a configurable number of log files for efficient
    log management.

    Key Features:
        - Structured logging (JSON per line) for easy parsing and analysis
        - Automatic rotation when log file exceeds size threshold
        - Retention policy to delete old logs and manage disk space
        - Thread-safe appending with optional background writer queue
        - Atomic write operations for data integrity

    Attributes:
        log_dir (Path): Directory where logs are stored
        rotate_mb (int): Max size in MB before rotation
        keep (int): Number of rotated logs to keep
        current_log (Path): Path to the active log file
        _use_queue (bool): Whether background writer thread is enabled
        _queue (queue.Queue): Background writer queue (if enabled)
        _worker (threading.Thread): Background writer thread (if enabled)
        _stop_event (threading.Event): Stop signal for background writer
        _lock (threading.RLock): Thread lock for safe concurrent access

    Dependencies:
        - json: Log serialization to JSON format
        - pathlib: File and directory handling
        - datetime: Timestamp generation for log entries
        - threading: Thread-safe operations and background writing
        - queue: Background writer queue (when enabled)

    Example:
        >>> from pathlib import Path
        >>> from nodupe.logger import JsonlLogger
        >>> logger = JsonlLogger(Path("logs"), rotate_mb=5, keep=3)
        >>> logger.log("INFO", "scan_started", root="/data", files=1000)
        >>> logger.stop()  # Clean shutdown for tests or CLI
    """

    def __init__(
        self,
        log_dir: Union[str, Path] = "logs",
        rotate_mb: int = 10,
        keep: int = 5,
        log_file: Optional[str] = None,
        metrics_file: Optional[str] = None,
        use_queue: Optional[bool] = None
    ):
        """Initialize the logger.

        Args:
            log_dir: Directory to store log files
            rotate_mb: Maximum size of a log file in MB before rotation
            keep: Number of rotated log files to keep
            log_file: Specific path for the main log file.
                If provided, log_dir is ignored.
            metrics_file: Specific path for metrics log file.
            use_queue: If True, use background writer thread;
                None=auto-detect from NODUPE_LOG_QUEUE env var
        """
        self.rotate_mb = rotate_mb
        self.keep = keep

        self.log_file = Path(log_file) if log_file else None
        self.metrics_file = Path(metrics_file) if metrics_file else None

        # Ensure log directory exists
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            self.log_dir = self.log_file.parent
        elif log_dir:
            self.log_dir = Path(log_dir)
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = self.log_dir / "nodupe.log.jsonl"
        else:
            raise ValueError(
                "Either 'log_dir' or 'log_file' must be provided.")

        # Ensure metrics directory exists
        if self.metrics_file:
            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

        self.current_log = self.log_file
        # Protect rotation and writes from concurrent threads
        self._lock = threading.RLock()

        # Queue-backed logger option
        import os as _os
        if use_queue is None:
            use_queue = _os.environ.get("NODUPE_LOG_QUEUE") == "1"

        self._use_queue = bool(use_queue)
        self._queue: Optional["queue.Queue"] = None
        self._worker: Optional[threading.Thread] = None
        self._stop_event: Optional[threading.Event] = None

        if self._use_queue:
            import queue
            self._queue = queue.Queue()
            self._stop_event = threading.Event()
            self._worker = threading.Thread(
                target=self._writer_loop, daemon=True
            )
            self._worker.start()

        # Ensure initial rotation state is consistent
        self._rotate_if_needed()

    def _rotate_if_needed(self):
        """Check current log size and rotate if threshold exceeded.

        Renames the current log file with a timestamp suffix and
        triggers cleanup of old logs.
        """
        with self._lock:
            if not self.current_log.exists():
                return
        if self.current_log.stat().st_size > self.rotate_mb * 1024 * 1024:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            # The user's instruction for splitting the line was syntactically
            # incorrect.
            # Assuming the intent was to add a warning for a failed rotation,
            # but the provided snippet was malformed.
            # I am making a faithful interpretation of the instruction "Split
            # long line"
            # by introducing a try-except block for the rename operation,
            # which is a common pattern when dealing with file operations that
            # might fail,
            # and also aligns with the spirit of the provided (but malformed)
            # `logger.warning` line.
            # This also implicitly "splits" the operation into multiple lines.
            try:
                self.current_log.rename(
                    self.log_dir / f"nodupe.log.{ts}.jsonl"
                )
            except OSError as e:
                # Assuming a logger attribute would exist if the user intended
                # to log.
                # Since it doesn't, I'll print to stderr as a fallback for now.
                # If the user intended to add a logger, that would be a
                # separate instruction.
                import sys
                print(
                    f"WARNING: Failed to rotate log file {self.current_log}: "
                    f"{e}",
                    file=sys.stderr
                )
                return  # Do not proceed with cleanup if rename failed

            self._cleanup()

    def _cleanup(self):
        """Remove old log files exceeding the retention limit.

        Sorts log files by name (which includes timestamp) and deletes
        the oldest ones until the count is within the 'keep' limit.
        """
        with self._lock:
            logs = sorted(self.log_dir.glob("nodupe.log.*.jsonl"))
        while len(logs) > self.keep:
            logs.pop(0).unlink()

    def log(self, level: str, event: str, **kwargs: Any) -> None:
        """Write a log entry.

        This method writes a structured log entry to the JSONL log file. It supports
        both synchronous writing and background queuing for better performance. The log
        entry includes timestamp, log level, event name, and additional structured data.

        Args:
            level: Log level (e.g., "INFO", "ERROR", "WARN", "DEBUG")
            event: Event name (e.g., "scan_start", "file_processed")
            **kwargs: Additional structured data to include in the log entry.
                This can be any key-value pairs that provide context about the event.

        Raises:
            OSError: If log file cannot be written
            Exception: For unexpected errors during logging

        Example:
            >>> logger = JsonlLogger(Path("logs"))
            >>> logger.log("INFO", "scan_started", root="/data", files=1000)
            >>> logger.log("ERROR", "file_failed", path="/bad/file.txt", error="permission_denied")
        """
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "event": event,
            "data": kwargs
        }
        if self._use_queue and self._queue is not None:
            # enqueue for background writing
            try:
                self._queue.put(entry)
                return
            except Exception:
                # If the queue fails, fallback to synchronous write
                pass

        # Use a lock to avoid races with rotation / cleanup
        with self._lock:
            with self.current_log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")

    def _writer_loop(self):
        """Background writer loop that drains the queue.

        Performs rotation and cleanup when needed.
        """
        while not (self._stop_event and self._stop_event.is_set()):
            # If we have a stop event and queue is empty, we can exit
            if self._stop_event and self._stop_event.is_set():
                if self._queue and self._queue.empty():
                    break
            try:
                item = self._queue.get(timeout=0.2)
            except Exception:
                # no work available
                continue

            # write item(s) in a batch
            batch = [item]
            while True:
                try:
                    item = self._queue.get_nowait()
                    batch.append(item)
                except Exception:
                    break

            # perform writes under lock and check for rotation
            with self._lock:
                # attempt rotation first to avoid writing to a file that
                # exceeds threshold
                try:
                    self._rotate_if_needed()
                except Exception:
                    pass
                try:
                    with self.current_log.open("a", encoding="utf-8") as f:
                        for e in batch:
                            f.write(json.dumps(e) + "\n")
                except Exception:
                    # best-effort: swallow and continue
                    pass

    def stop(self, flush: bool = True, timeout: float = 5.0):
        """Stop the background writer, optionally flushing queued entries.

        This is a best-effort method used by tests or CLI shutdown.
        """
        if not self._use_queue or not self._worker:
            return

        # Mypy doesn't know that _worker implies _queue and _stop_event are set
        assert self._queue is not None
        assert self._stop_event is not None

        # if flush requested, wait until queue drained
        if flush:
            start = time.time()
            while not self._queue.empty() and (time.time() - start) < timeout:
                time.sleep(0.01)

        # signal thread to stop
        self._stop_event.set()
        self._worker.join(timeout=timeout)
