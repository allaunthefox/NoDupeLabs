# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Progress tracker for file processing operations.

This module provides progress tracking functionality for file processing operations,
including time estimation, rate calculation, and progress reporting.

Key Features:
    - Progress tracking with time estimation
    - Rate calculation (files/second, bytes/second)
    - Console and callback-based reporting
    - Error handling
    - Thread-safe operations

Dependencies:
    - time (standard library)
    - typing (standard library)
    - threading (standard library)
"""

import threading
import time
from typing import Any, Callable, Optional


class ProgressTracker:
    """Progress tracker for file processing operations.

    Responsibilities:
    - Track progress of file processing operations
    - Calculate time estimates and rates
    - Report progress via callbacks
    - Handle progress tracking errors
    - Support thread-safe operations
    """

    def __init__(self):
        """Initialize progress tracker."""
        self._lock = threading.Lock()
        self._start_time: float = 0.0
        self._last_update_time: float = 0.0
        self._total_items = 0
        self._completed_items = 0
        self._total_bytes = 0
        self._processed_bytes = 0
        self._status = "not_started"
        self._error_count = 0

    def start(self, total_items: int = 0, total_bytes: int = 0) -> None:
        """Start progress tracking.

        Args:
            total_items: Total number of items to process
            total_bytes: Total number of bytes to process
        """
        with self._lock:
            self._start_time = time.monotonic()
            self._last_update_time = self._start_time
            self._total_items = total_items
            self._completed_items = 0
            self._total_bytes = total_bytes
            self._processed_bytes = 0
            self._status = "in_progress"
            self._error_count = 0

    def update(self, items_completed: int = 1, bytes_processed: int = 0) -> None:
        """Update progress with completed items and processed bytes.

        Args:
            items_completed: Number of items completed since last update
            bytes_processed: Number of bytes processed since last update
        """
        with self._lock:
            self._completed_items += items_completed
            self._processed_bytes += bytes_processed
            self._last_update_time = time.monotonic()

    def complete(self) -> None:
        """Mark progress as complete."""
        with self._lock:
            self._status = "completed"
            self._last_update_time = time.monotonic()

    def error(self) -> None:
        """Record an error."""
        with self._lock:
            self._error_count += 1
            self._last_update_time = time.monotonic()

    def get_progress(self) -> dict[str, Any]:
        """Get current progress information.

        Returns:
            Dictionary containing progress information
        """
        with self._lock:
            elapsed = time.monotonic() - self._start_time if self._start_time > 0 else 0

            # Calculate rates
            items_per_second: float = self._completed_items / elapsed if elapsed > 0 else 0.0
            bytes_per_second: float = self._processed_bytes / elapsed if elapsed > 0 else 0.0

            # Calculate estimates
            remaining_items = max(0, self._total_items - self._completed_items)
            remaining_bytes = max(0, self._total_bytes - self._processed_bytes)

            time_remaining: float = 0.0
            if items_per_second > 0:
                time_remaining = remaining_items / items_per_second
            elif bytes_per_second > 0:
                time_remaining = remaining_bytes / bytes_per_second

            percent_complete: float = 0.0
            if self._total_items > 0:
                percent_complete = (self._completed_items / self._total_items) * 100
            elif self._total_bytes > 0:
                percent_complete = (self._processed_bytes / self._total_bytes) * 100

            return {
                'status': self._status,
                'start_time': self._start_time,
                'elapsed_time': elapsed,
                'total_items': self._total_items,
                'completed_items': self._completed_items,
                'remaining_items': remaining_items,
                'total_bytes': self._total_bytes,
                'processed_bytes': self._processed_bytes,
                'remaining_bytes': remaining_bytes,
                'percent_complete': percent_complete,
                'items_per_second': items_per_second,
                'bytes_per_second': bytes_per_second,
                'time_remaining': time_remaining,
                'error_count': self._error_count
            }

    def report_progress(self, on_progress: Optional[Callable[[dict[str, Any]], None]] = None) -> None:
        """Report progress via callback.

        Args:
            on_progress: Optional progress callback
        """
        if on_progress:
            progress = self.get_progress()
            on_progress(progress)

    def reset(self) -> None:
        """Reset progress tracker."""
        with self._lock:
            self._start_time = 0
            self._last_update_time = 0
            self._total_items = 0
            self._completed_items = 0
            self._total_bytes = 0
            self._processed_bytes = 0
            self._status = "not_started"
            self._error_count = 0

    def get_elapsed_time(self) -> float:
        """Get elapsed time since start.

        Returns:
            Elapsed time in seconds
        """
        with self._lock:
            return time.monotonic() - self._start_time if self._start_time > 0 else 0

    def get_status(self) -> str:
        """Get current status.

        Returns:
            Current status string
        """
        with self._lock:
            return self._status

    def is_complete(self) -> bool:
        """Check if progress is complete.

        Returns:
            True if complete, False otherwise
        """
        with self._lock:
            return self._status == "completed"

    def get_error_count(self) -> int:
        """Get error count.

        Returns:
            Number of errors encountered
        """
        with self._lock:
            return self._error_count

    def format_progress(self, progress: Optional[dict[str, Any]] = None) -> str:
        """Format progress information as string.

        Args:
            progress: Optional progress dictionary

        Returns:
            Formatted progress string
        """
        if progress is None:
            progress = self.get_progress()

        status = progress.get('status', 'unknown')
        percent = progress.get('percent_complete', 0)
        elapsed = progress.get('elapsed_time', 0)
        remaining = progress.get('time_remaining', 0)
        items = progress.get('completed_items', 0)
        total = progress.get('total_items', 0)
        errors = progress.get('error_count', 0)

        return (f"Status: {status} | "
                f"Progress: {percent:.1f}% | "
                f"Items: {items}/{total} | "
                f"Time: {elapsed:.1f}s (remaining: {remaining:.1f}s) | "
                f"Errors: {errors}")


def create_progress_tracker() -> ProgressTracker:
    """Create and return a ProgressTracker instance.

    Returns:
        ProgressTracker instance
    """
    return ProgressTracker()
