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
from pathlib import Path
from datetime import datetime, timezone
import threading


class JsonlLogger:
    """Structured logger writing to JSONL files with rotation.

    Attributes:
        log_dir (Path): Directory where logs are stored
        rotate_mb (int): Max size in MB before rotation
        keep (int): Number of rotated logs to keep
        current_log (Path): Path to the active log file
    """

    def __init__(self, log_dir: Path, rotate_mb: int = 10, keep: int = 7):
        """Initialize the logger.

        Args:
            log_dir: Directory to store log files
            rotate_mb: Maximum size of a log file in MB before rotation
            keep: Number of rotated log files to keep
        """
        self.log_dir = Path(log_dir)
        self.rotate_mb = rotate_mb
        self.keep = keep
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_log = self.log_dir / "nodupe.log.jsonl"
        # Protect rotation and writes from concurrent threads
        self._lock = threading.RLock()
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
            self.current_log.rename(self.log_dir / f"nodupe.log.{ts}.jsonl")
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

    def log(self, level: str, event: str, **kwargs):
        """Write a log entry.

        Args:
            level: Log level (e.g., "INFO", "ERROR")
            event: Event name (e.g., "scan_start")
            **kwargs: Additional structured data to include in the log entry
        """
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "event": event,
            "data": kwargs
        }
        # Use a lock to avoid races with rotation / cleanup
        with self._lock:
            with self.current_log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
