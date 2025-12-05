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


class Metrics:
    """Container for application metrics and statistics.

    Attributes:
        path (Path): Path to the metrics JSON file
        data (dict): Dictionary containing metric values
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

    def save(self):
        """Write current metrics to the JSON file.

        Creates parent directories if they don't exist.
        """
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
