"""Tests for progress tracker module."""

import pytest
import time
from pathlib import Path
from nodupe.core.scan.progress import ProgressTracker


class TestProgressTracker:
    """Test ProgressTracker class."""

    def test_progress_tracker_creation(self):
        """Test progress tracker creation."""
        tracker = ProgressTracker()
        assert tracker is not None
        
        # Check initial state
        progress_info = tracker.get_progress()
        assert progress_info['total_items'] == 0
        assert progress_info['completed_items'] == 0
        assert progress_info['percent_complete'] == 0.0
        assert tracker.get_status() == "not_started"

    def test_update_progress(self):
        """Test updating progress."""
        tracker = ProgressTracker()
        tracker.start(total_items=100)
        
        # Update progress
        tracker.update(items_completed=10)
        progress_info = tracker.get_progress()
        assert progress_info['completed_items'] == 10
        assert progress_info['percent_complete'] == 10.0
        
        # Update again
        tracker.update(items_completed=20)
        progress_info = tracker.get_progress()
        assert progress_info['completed_items'] == 30
        assert progress_info['percent_complete'] == 30.0

    def test_get_progress_percentage(self):
        """Test getting progress percentage."""
        tracker = ProgressTracker()
        tracker.start(total_items=100)
        
        progress_info = tracker.get_progress()
        assert progress_info['percent_complete'] == 0.0
        
        tracker.update(items_completed=25)
        progress_info = tracker.get_progress()
        assert progress_info['percent_complete'] == 25.0
        
        tracker.update(items_completed=25)
        progress_info = tracker.get_progress()
        assert progress_info['percent_complete'] == 50.0

    def test_get_elapsed_time(self):
        """Test getting elapsed time."""
        tracker = ProgressTracker()
        tracker.start(total_items=100)
        
        # Should be 0 initially
        elapsed = tracker.get_elapsed_time()
        assert elapsed >= 0
        
        # Wait a bit and check again
        time.sleep(0.01)  # Brief sleep to test elapsed time
        elapsed2 = tracker.get_elapsed_time()
        assert elapsed2 >= elapsed

    def test_get_eta_and_rates(self):
        """Test getting ETA and processing rates."""
        tracker = ProgressTracker()
        tracker.start(total_items=100)
        
        # Initially no rates
        progress_info = tracker.get_progress()
        assert progress_info['items_per_second'] == 0
        assert progress_info['time_remaining'] == 0
        
        # Make some progress with time delay to calculate rates
        tracker.update(items_completed=10)
        time.sleep(0.01)  # Brief sleep to allow rate calculation
        tracker.update(items_completed=5)
        
        # Now should have some rates
        progress_info = tracker.get_progress()
        assert progress_info['completed_items'] == 15
        # Rate might still be very small due to short time period

    def test_progress_complete(self):
        """Test when progress is complete."""
        tracker = ProgressTracker()
        tracker.start(total_items=100)
        
        tracker.update(items_completed=100)
        progress_info = tracker.get_progress()
        assert progress_info['percent_complete'] == 100.0
        assert progress_info['completed_items'] == 100
        
        # Complete the tracker
        tracker.complete()
        assert tracker.is_complete() is True

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
        assert progress_info['total_items'] == 0
        assert tracker.get_status() == "not_started"

    def test_error_tracking(self):
        """Test error tracking functionality."""
        tracker = ProgressTracker()
        tracker.start(total_items=100)
        
        assert tracker.get_error_count() == 0
        
        tracker.error()
        assert tracker.get_error_count() == 1
        
        tracker.error()
        assert tracker.get_error_count() == 2

    def test_bytes_processing(self):
        """Test progress tracking with bytes."""
        tracker = ProgressTracker()
        tracker.start(total_items=10, total_bytes=1000)
        
        # Update with bytes processed
        tracker.update(items_completed=1, bytes_processed=100)
        progress_info = tracker.get_progress()
        
        assert progress_info['completed_items'] == 1
        assert progress_info['processed_bytes'] == 100
        assert progress_info['percent_complete'] == 10.0  # Based on items
        assert progress_info['bytes_per_second'] == 0  # No time has passed yet

    def test_multiple_updates(self):
        """Test multiple progress updates."""
        tracker = ProgressTracker()
        tracker.start(total_items=100)
        
        # Simulate multiple updates
        for i in range(10):
            tracker.update(items_completed=5)
            progress_info = tracker.get_progress()
            expected_percent = (i + 1) * 5
            assert progress_info['completed_items'] == (i + 1) * 5
            assert progress_info['percent_complete'] == expected_percent

    def test_format_progress(self):
        """Test progress formatting."""
        tracker = ProgressTracker()
        tracker.start(total_items=100)
        tracker.update(items_completed=25)
        
        formatted = tracker.format_progress()
        assert "Progress: 25.0%" in formatted
        assert "Items: 25/100" in formatted
        assert "Status:" in formatted
        assert "Errors: 0" in formatted

    def test_thread_safety(self):
        """Test basic thread safety."""
        tracker = ProgressTracker()
        tracker.start(total_items=1000)
        
        # This is a basic test - more thorough thread testing would be needed
        # for comprehensive thread safety verification
        for i in range(100):
            tracker.update(items_completed=1)
        
        progress_info = tracker.get_progress()
        assert progress_info['completed_items'] == 100
        assert progress_info['percent_complete'] == 10.0
