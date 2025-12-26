"""
Progress tracking module for monitoring long-running operations.
"""

import time
from typing import Optional


class ProgressTracker:
    """
    Tracks progress of long-running operations and provides metrics
    like percentage complete, elapsed time, ETA, and processing rate.
    """
    
    def __init__(self, total: int):
        """
        Initialize progress tracker.
        
        Args:
            total: Total number of items to process
        """
        self.total = total
        self.current = 0
        self.start_time = time.time()
        self.last_update_time = self.start_time
    
    def update(self, increment: int = 1) -> None:
        """
        Update progress by increment amount.
        
        Args:
            increment: Number of items to increment by (default: 1)
        """
        self.current = min(self.current + increment, self.total)
        self.last_update_time = time.time()
    
    def get_progress(self) -> float:
        """
        Get current progress as percentage (0.0 to 100.0).
        
        Returns:
            Progress percentage
        """
        if self.total == 0:
            return 100.0
        return (self.current / self.total) * 100.0
    
    def get_elapsed_time(self) -> float:
        """
        Get elapsed time in seconds.
        
        Returns:
            Elapsed time in seconds
        """
        return time.time() - self.start_time
    
    def get_eta(self) -> Optional[float]:
        """
        Get estimated time of arrival in seconds.
        
        Returns:
            ETA in seconds, or None if no progress has been made
        """
        if self.current == 0:
            return None
        
        elapsed = self.get_elapsed_time()
        if self.current == 0:
            return None
        
        rate = self.current / elapsed if elapsed > 0 else 0
        remaining = self.total - self.current
        return remaining / rate if rate > 0 else 0
    
    def get_rate(self) -> float:
        """
        Get current processing rate (items per second).
        
        Returns:
            Processing rate in items per second
        """
        elapsed = self.get_elapsed_time()
        return self.current / elapsed if elapsed > 0 else 0.0
    
    def reset(self) -> None:
        """Reset progress to zero."""
        self.current = 0
        self.start_time = time.time()
        self.last_update_time = self.start_time
