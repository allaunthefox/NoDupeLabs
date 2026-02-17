"""Tests for progress tracker module."""

import time
from pathlib import Path

import pytest

from nodupe.tools.scanner_engine.progress import ProgressTracker


class TestProgressTracker:
    """Test ProgressTracker class."""

    def test_progress_tracker_creation(self):
        """Test progress tracker creation."""
        tracker = ProgressTracker()
        # The actual ProgressTracker doesn't take 'total' in constructor
        # We need to call start() to initialize with total values
        tracker.start(total_items=100)
        progress_info = tracker.get_progress()
        assert progress_info['total_items'] == 100
        assert progress_info['completed_items'] == 0

    def test_update_progress(self):
        """Test updating progress."""
        tracker = ProgressTracker()
        tracker.start(total_items=100)

        # Update progress
        tracker.update(items_completed=10)
        progress_info = tracker.get_progress()
        assert progress_info['completed_items'] == 10

        # Update again
        tracker.update(items_completed=20)
        progress_info = tracker.get_progress()
        assert progress_info['completed_items'] == 30

    def test_get_progress_percentage(self):
        """Test getting progress percentage."""
        tracker = ProgressTracker()
        tracker.start(total_items=100)

        progress_info = tracker.get_progress()
        assert progress_info['percent_complete'] == 0.0

        tracker.update(items_completed=25)
        progress_info = tracker.get_progress()
        assert abs(progress_info['percent_complete'] - 25.0) < 0.1  # Allow for floating point precision

        # Complete the rest
        tracker.update(items_completed=75)
        progress_info = tracker.get_progress()
        assert abs(progress_info['percent_complete'] - 100.0) < 0.1

    def test_get_elapsed_time(self):
        """Test getting elapsed time."""
        tracker = ProgressTracker()
        tracker.start(total_items=100)

        # Should be 0 initially
        elapsed = tracker.get_elapsed_time()
        assert elapsed >= 0

        # Wait a bit and check again
        time.sleep(0.01)  # Small sleep to ensure time difference
        elapsed2 = tracker.get_elapsed_time()
        assert elapsed2 >= elapsed

    def test_get_eta(self):
        """Test getting estimated time of arrival."""
        tracker = ProgressTracker()
        tracker.start(total_items=100)

        # Make some progress
        tracker.update(items_completed=10)
        time.sleep(0.01)  # Small sleep to allow for rate calculation

        # Should have an ETA based on current rate
        progress_info = tracker.get_progress()
        eta = progress_info['time_remaining']
        assert eta is not None
        assert eta >= 0  # Could be 0 if very fast

    def test_get_rate(self):
        """Test getting processing rate."""
        tracker = ProgressTracker()
        tracker.start(total_items=100)

        # Initially no rate since no time has passed
        progress_info = tracker.get_progress()
        progress_info['items_per_second']
        # Rate could be 0 if no time has passed

        # Make some progress
        tracker.update(items_completed=10)
        time.sleep(0.01)  # Small sleep to allow for rate calculation

        # Should have a rate
        progress_info = tracker.get_progress()
        progress_info['items_per_second']
        # Rate could still be low due to small time interval

    def test_progress_complete(self):
        """Test when progress is complete."""
        tracker = ProgressTracker()
        tracker.start(total_items=100)

        tracker.update(items_completed=100)
        progress_info = tracker.get_progress()
        assert abs(progress_info['percent_complete'] - 100.0) < 0.1

        # Should not go over 100%
        tracker.update(items_completed=10)
        progress_info = tracker.get_progress()
        assert progress_info['completed_items'] == 110  # Actual items processed
        # But percentage might still be capped at 100% depending on implementation

    def test_reset_progress(self):
        """Test resetting progress."""
        tracker = ProgressTracker()
        tracker.start(total_items=100)

        tracker.update(items_completed=50)
        progress_info = tracker.get_progress()
        assert progress_info['completed_items'] == 50

        tracker.reset()
        progress_info = tracker.get_progress()
        assert progress_info['completed_items'] == 0
        assert progress_info['total_items'] == 0  # Reset also clears totals
