"""Tests for progress tracker module."""

import pytest
import time
from pathlib import Path
from nodupe.core.progress_tracker import ProgressTracker


class TestProgressTracker:
    """Test ProgressTracker class."""

    def test_progress_tracker_creation(self):
        """Test progress tracker creation."""
        tracker = ProgressTracker(total=100)
        assert tracker.total == 100
        assert tracker.current == 0
        assert tracker.start_time is not None

    def test_update_progress(self):
        """Test updating progress."""
        tracker = ProgressTracker(total=100)
        
        # Update progress
        tracker.update(10)
        assert tracker.current == 10
        
        # Update again
        tracker.update(20)
        assert tracker.current == 30

    def test_get_progress_percentage(self):
        """Test getting progress percentage."""
        tracker = ProgressTracker(total=100)
        
        assert tracker.get_progress() == 0.0
        
        tracker.update(25)
        assert tracker.get_progress() == 25.0
        
        tracker.update(75)
        assert tracker.get_progress() == 100.0

    def test_get_elapsed_time(self):
        """Test getting elapsed time."""
        tracker = ProgressTracker(total=100)
        
        # Should be very small initially
        elapsed = tracker.get_elapsed_time()
        assert elapsed >= 0
        
        # Wait a bit and check again
        # time.sleep(0.01)  # Removed for performance - use mock time in tests
        elapsed2 = tracker.get_elapsed_time()
        assert elapsed2 >= elapsed

    def test_get_eta(self):
        """Test getting estimated time of arrival."""
        tracker = ProgressTracker(total=100)
        
        # No progress yet, should return None
        assert tracker.get_eta() is None
        
        # Make some progress
        tracker.update(10)
        # time.sleep(0.01)  # Removed for performance - use mock time in tests
        
        # Should have an ETA
        eta = tracker.get_eta()
        assert eta is not None
        assert eta > 0

    def test_get_rate(self):
        """Test getting processing rate."""
        tracker = ProgressTracker(total=100)
        
        # No progress yet, rate should be 0
        assert tracker.get_rate() == 0
        
        # Make some progress
        tracker.update(10)
        # time.sleep(0.01)  # Removed for performance - use mock time in tests
        
        # Should have a rate
        rate = tracker.get_rate()
        assert rate > 0

    def test_progress_complete(self):
        """Test when progress is complete."""
        tracker = ProgressTracker(total=100)
        
        tracker.update(100)
        assert tracker.get_progress() == 100.0
        
        # Should not go over 100%
        tracker.update(10)
        assert tracker.current == 100
        assert tracker.get_progress() == 100.0

    def test_reset_progress(self):
        """Test resetting progress."""
        tracker = ProgressTracker(total=100)
        
        tracker.update(50)
        assert tracker.current == 50
        
        tracker.reset()
        assert tracker.current == 0
        assert tracker.start_time is not None
