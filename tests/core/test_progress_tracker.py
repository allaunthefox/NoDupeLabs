"""Tests for ProgressTracker module."""

import pytest
import time
from nodupe.core.scan.progress import ProgressTracker, create_progress_tracker

class TestProgressTracker:
    """Test ProgressTracker class."""

    def test_progress_tracker_initialization(self):
        """Test ProgressTracker initialization."""
        tracker = ProgressTracker()
        assert isinstance(tracker, ProgressTracker)

    def test_create_progress_tracker(self):
        """Test create_progress_tracker factory function."""
        tracker = create_progress_tracker()
        assert isinstance(tracker, ProgressTracker)

    def test_start_progress(self):
        """Test starting progress tracking."""
        tracker = ProgressTracker()
        tracker.start(total_items=10, total_bytes=1024)

        progress = tracker.get_progress()

        assert progress['total_items'] == 10
        assert progress['total_bytes'] == 1024
        assert progress['completed_items'] == 0
        assert progress['processed_bytes'] == 0
        assert progress['status'] == "in_progress"
        assert progress['error_count'] == 0

    def test_start_progress_default_values(self):
        """Test starting progress with default values."""
        tracker = ProgressTracker()
        tracker.start()

        progress = tracker.get_progress()

        assert progress['total_items'] == 0
        assert progress['total_bytes'] == 0
        assert progress['completed_items'] == 0
        assert progress['processed_bytes'] == 0
        assert progress['status'] == "in_progress"

    def test_update_progress(self):
        """Test updating progress."""
        tracker = ProgressTracker()
        tracker.start(total_items=10, total_bytes=1000)

        # Update progress
        tracker.update(items_completed=3, bytes_processed=300)

        progress = tracker.get_progress()

        assert progress['completed_items'] == 3
        assert progress['processed_bytes'] == 300
        assert progress['status'] == "in_progress"

    def test_multiple_updates(self):
        """Test multiple progress updates."""
        tracker = ProgressTracker()
        tracker.start(total_items=10, total_bytes=1000)

        # Multiple updates
        tracker.update(items_completed=2, bytes_processed=200)
        tracker.update(items_completed=3, bytes_processed=300)
        tracker.update(items_completed=1, bytes_processed=100)

        progress = tracker.get_progress()

        assert progress['completed_items'] == 6  # 2+3+1
        assert progress['processed_bytes'] == 600  # 200+300+100
        assert progress['status'] == "in_progress"

    def test_complete_progress(self):
        """Test completing progress."""
        tracker = ProgressTracker()
        tracker.start(total_items=10, total_bytes=1000)

        tracker.update(items_completed=10, bytes_processed=1000)
        tracker.complete()

        progress = tracker.get_progress()

        assert progress['status'] == "completed"
        assert progress['error_count'] == 0

    def test_error_progress(self):
        """Test error progress."""
        tracker = ProgressTracker()
        tracker.start(total_items=10, total_bytes=1000)

        tracker.update(items_completed=5, bytes_processed=500)
        tracker.error()

        progress = tracker.get_progress()

        assert progress['status'] == "in_progress"
        assert progress['error_count'] == 1

    def test_reset_progress(self):
        """Test resetting progress."""
        tracker = ProgressTracker()
        tracker.start(total_items=10, total_bytes=1000)
        tracker.update(items_completed=5, bytes_processed=500)

        # Reset
        tracker.reset()

        progress = tracker.get_progress()

        assert progress['total_items'] == 0
        assert progress['total_bytes'] == 0
        assert progress['completed_items'] == 0
        assert progress['processed_bytes'] == 0
        assert progress['status'] == "not_started"
        assert progress['error_count'] == 0

    def test_get_status(self):
        """Test getting progress status."""
        tracker = ProgressTracker()
        tracker.start(total_items=10, total_bytes=1000)

        # Should be in_progress after start
        assert tracker.get_status() == "in_progress"

        tracker.update(items_completed=5, bytes_processed=500)
        status = tracker.get_status()
        assert status == "in_progress"

        tracker.complete()
        assert tracker.get_status() == "completed"

        tracker.reset()
        assert tracker.get_status() == "not_started"

        tracker.start(total_items=10, total_bytes=1000)
        tracker.update(items_completed=3, bytes_processed=300)
        tracker.error()
        assert tracker.get_status() == "in_progress"  # Status remains in_progress, error is counted separately

    def test_is_complete(self):
        """Test is_complete method."""
        tracker = ProgressTracker()
        tracker.start(total_items=10, total_bytes=1000)

        assert tracker.is_complete() is False

        tracker.complete()
        assert tracker.is_complete() is True

    def test_get_error_count(self):
        """Test error counting."""
        tracker = ProgressTracker()
        tracker.start(total_items=10, total_bytes=1000)

        assert tracker.get_error_count() == 0

        tracker.error()
        assert tracker.get_error_count() == 1

        tracker.error()
        assert tracker.get_error_count() == 2

    def test_format_progress(self):
        """Test progress formatting."""
        tracker = ProgressTracker()
        tracker.start(total_items=10, total_bytes=1000)
        tracker.update(items_completed=3, bytes_processed=300)

        formatted = tracker.format_progress()

        # The actual format is different
        assert "Status: in_progress" in formatted
        assert "Progress: 30.0%" in formatted
        assert "Items: 3/10" in formatted
        assert "Time:" in formatted
        assert "Errors: 0" in formatted

    def test_format_progress_custom(self):
        """Test custom progress formatting."""
        tracker = ProgressTracker()
        tracker.start(total_items=5, total_bytes=500)
        tracker.update(items_completed=2, bytes_processed=200)

        progress_data = {
            'status': 'in_progress',
            'total_items': 5,
            'completed_items': 2,
            'total_bytes': 500,
            'processed_bytes': 200,
            'percent_complete': 40.0,
            'error_count': 0
        }

        formatted = tracker.format_progress(progress_data)

        assert "Status: in_progress" in formatted
        assert "Progress: 40.0%" in formatted
        assert "Items: 2/5" in formatted
        assert "Errors: 0" in formatted

    def test_format_progress_no_totals(self):
        """Test progress formatting with no totals."""
        tracker = ProgressTracker()
        tracker.start()  # No totals specified
        tracker.update(items_completed=3, bytes_processed=300)

        formatted = tracker.format_progress()

        assert "Status: in_progress" in formatted
        assert "Items: 3/0" in formatted
        assert "Errors: 0" in formatted

    def test_elapsed_time(self):
        """Test elapsed time tracking."""
        tracker = ProgressTracker()
        tracker.start(total_items=10, total_bytes=1000)

        # Small delay to ensure elapsed time is measured
        time.sleep(0.01)

        elapsed = tracker.get_elapsed_time()
        assert elapsed >= 0.01

    def test_report_progress_callback(self):
        """Test progress reporting with callback."""
        tracker = ProgressTracker()
        tracker.start(total_items=5, total_bytes=500)

        callback_data = []

        def progress_callback(progress):
            callback_data.append(progress)

        tracker.report_progress(on_progress=progress_callback)

        assert len(callback_data) == 1
        assert 'total_items' in callback_data[0]
        assert 'completed_items' in callback_data[0]
        assert 'status' in callback_data[0]
        assert 'error_count' in callback_data[0]

    def test_progress_with_zero_totals(self):
        """Test progress with zero totals."""
        tracker = ProgressTracker()
        tracker.start(total_items=0, total_bytes=0)

        tracker.update(items_completed=0, bytes_processed=0)

        progress = tracker.get_progress()
        assert progress['total_items'] == 0
        assert progress['total_bytes'] == 0
        assert progress['completed_items'] == 0
        assert progress['processed_bytes'] == 0

        # Should handle division by zero gracefully
        status = tracker.get_status()
        assert status == "in_progress"  # Should not be an error state

    def test_progress_percentage_calculation(self):
        """Test progress percentage calculations."""
        tracker = ProgressTracker()
        tracker.start(total_items=100, total_bytes=1000)

        # Test various percentages
        test_cases = [
            (0, 0, "0.0%"),
            (25, 250, "25.0%"),
            (50, 500, "50.0%"),
            (75, 750, "75.0%"),
            (100, 1000, "100.0%")
        ]

        for items, bytes_val, expected_pct in test_cases:
            tracker.reset()
            tracker.start(total_items=100, total_bytes=1000)
            tracker.update(items_completed=items, bytes_processed=bytes_val)

            progress = tracker.get_progress()
            assert f"Progress: {expected_pct}" in tracker.format_progress(progress)

    def test_progress_with_large_numbers(self):
        """Test progress with large numbers."""
        tracker = ProgressTracker()
        tracker.start(total_items=1000000, total_bytes=1000000000)  # 1GB

        tracker.update(items_completed=500000, bytes_processed=500000000)  # 500MB

        progress = tracker.get_progress()
        assert progress['completed_items'] == 500000
        assert progress['processed_bytes'] == 500000000

        formatted = tracker.format_progress()
        assert "Progress: 50.0%" in formatted

    def test_progress_state_transitions(self):
        """Test progress state transitions."""
        tracker = ProgressTracker()

        # Initial state
        assert tracker.is_complete() is False
        assert tracker.get_error_count() == 0
        assert tracker.get_status() == "not_started"

        # Start
        tracker.start(total_items=10, total_bytes=1000)
        assert tracker.is_complete() is False
        assert tracker.get_status() == "in_progress"

        # Update
        tracker.update(items_completed=5, bytes_processed=500)
        assert tracker.is_complete() is False
        assert tracker.get_status() == "in_progress"

        # Complete
        tracker.complete()
        assert tracker.is_complete() is True
        assert tracker.get_status() == "completed"

        # Reset
        tracker.reset()
        assert tracker.is_complete() is False
        assert tracker.get_error_count() == 0
        assert tracker.get_status() == "not_started"

        # Error
        tracker.start(total_items=10, total_bytes=1000)
        tracker.error()
        assert tracker.is_complete() is False
        assert tracker.get_error_count() == 1
        assert tracker.get_status() == "in_progress"  # Status remains in_progress
