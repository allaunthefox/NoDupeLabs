"""Progress tracking utilities for long-running operations."""

import time
from typing import Optional


class ProgressTracker:
    """Track progress of long-running operations."""
    
    def __init__(self, total: int, description: str = "Progress"):
        """Initialize progress tracker.
        
        Args:
            total: Total number of items to process
            description: Description of the operation
        """
        self.total = total
        self.description = description
        self.current = 0
        self.start_time = time.time()
    
    def update(self, increment: int = 1) -> None:
        """Update progress by increment."""
        self.current += increment
        # Clamp to total
        if self.current > self.total:
            self.current = self.total
    
    def get_progress(self) -> float:
        """Get current progress as percentage."""
        if self.total == 0:
            return 100.0
        return (self.current / self.total) * 100.0
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time
    
    def get_eta(self) -> Optional[float]:
        """Get estimated time of arrival in seconds."""
        if self.current == 0:
            return None
        elapsed = self.get_elapsed_time()
        rate = self.current / elapsed
        remaining = self.total - self.current
        return remaining / rate if rate > 0 else None
    
    def get_rate(self) -> float:
        """Get processing rate (items per second)."""
        elapsed = self.get_elapsed_time()
        return self.current / elapsed if elapsed > 0 else 0.0
    
    def reset(self) -> None:
        """Reset progress tracker."""
        self.current = 0
        self.start_time = time.time()
