# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Performance and statistics tracking.

This module handles the collection and persistence of runtime metrics
for the NoDupe application. It tracks scan statistics, durations,
and operation counts, saving them to a JSON file for reporting and
historical analysis.

Key Features:
    - Track files scanned, bytes processed, and durations
    - Record duplicate counts and planned operations
    - Persist metrics to a JSON file

Classes:
    - Metrics: Metrics container and persistence handler

Dependencies:
    - json: Serialization
    - pathlib: File handling
    - datetime: Timestamp generation

Example:
    >>> metrics = Metrics(Path("metrics.json"))
    >>> metrics.data["files_scanned"] = 100
    >>> metrics.save()
"""

import json
from pathlib import Path
import threading
from datetime import datetime, timezone
from typing import Any, Dict


class Metrics:
    """Container for application metrics and statistics.

    This class provides a structured container for collecting and persisting
    runtime metrics during NoDupe operations. It tracks various performance
    indicators and operation statistics, saving them to a JSON file for
    reporting, analysis, and historical tracking.

    Key Features:
        - Structured metrics collection with predefined categories
        - Thread-safe operations for concurrent access
        - Automatic directory creation and JSON serialization
        - Timestamp tracking for each run
        - Flexible data structure for custom metrics

    Attributes:
        path (Path): Path to the metrics JSON file
        data (dict): Dictionary containing metric values with keys:
            - last_run: ISO 8601 timestamp of last operation
            - files_scanned: Number of files processed
            - bytes_scanned: Total bytes processed
            - durations: Dictionary of operation durations
            - meta_exported: Number of metadata files exported
            - meta_errors: Number of metadata export errors
            - duplicates_found: Number of duplicate files detected
            - planned_ops: Number of planned operations
            - apply: Dictionary of apply operation statistics
        _lock (threading.RLock): Thread lock for safe concurrent access

    Dependencies:
        - json: Serialization to JSON format
        - pathlib: File and directory handling
        - datetime: Timestamp generation
        - threading: Thread-safe operations

    Example:
        >>> from pathlib import Path
        >>> from nodupe.metrics import Metrics
        >>> metrics = Metrics(Path("metrics.json"))
        >>> metrics.data["files_scanned"] = 1000
        >>> metrics.data["bytes_scanned"] = 500000000
        >>> metrics.data["durations"]["scan"] = 45.2
        >>> metrics.save()
        >>> print("Metrics saved successfully")
    """

    def __init__(self, path: Path):
        """Initialize metrics with default values.

        Args:
            path: Path where metrics will be saved
        """
        self.path = Path(path)
        self.data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "files_scanned": 0,
            "bytes_scanned": 0,
            "durations": {},
            "meta_exported": 0,
            "meta_errors": 0,
            "duplicates_found": 0,
            "planned_ops": 0,
            "apply": {}
        }
        # Protect concurrent saves/updates
        self._lock = threading.RLock()

    def save(self) -> None:
        """Write current metrics to the JSON file.

        This method persists the collected metrics to a JSON file at the specified
        path. It automatically creates any necessary parent directories and uses
        thread-safe operations to prevent data corruption in concurrent scenarios.

        The save process:
        1. Acquires thread lock for safe concurrent access
        2. Creates parent directories if they don't exist
        3. Serializes metrics data to JSON format with indentation
        4. Writes JSON data to the specified file
        5. Releases the thread lock

        Raises:
            OSError: If file cannot be written due to permissions or disk issues
            json.JSONEncodeError: If metrics data cannot be serialized
            Exception: For unexpected errors during file operations

        Example:
            >>> metrics = Metrics(Path("metrics.json"))
            >>> metrics.data["files_scanned"] = 1000
            >>> metrics.save()
            # Creates metrics.json with formatted JSON content
        """
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # Split arguments across lines to satisfy line-length checks
            payload = json.dumps(self.data, indent=2)
            self.path.write_text(payload, encoding="utf-8")
