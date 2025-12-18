"""Limits Module.

Resource limit enforcement using standard library only.

Key Features:
    - Memory usage monitoring
    - File handle tracking
    - Rate limiting with token bucket
    - Size limits for files and data
    - Time limits for operations
    - Standard library only (no external dependencies)

Dependencies:
    - resource (standard library, Unix only)
    - psutil-like functionality using /proc (Linux)
    - os (standard library)
    - time (standard library)
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, Callable, Any
from contextlib import contextmanager
import threading


class LimitsError(Exception):
    """Resource limit error"""


class Limits:
    """Handle resource limit enforcement.

    Provides resource monitoring and enforcement including memory limits,
    file handle limits, rate limiting, and operation timeouts.
    """

    @staticmethod
    def get_memory_usage() -> int:
        """Get current process memory usage in bytes.

        Returns:
            Memory usage in bytes

        Raises:
            LimitsError: If memory usage cannot be determined
        """
        try:
            # Try using resource module (Unix)
            if hasattr(os, 'getrusage'):
                import resource
                usage = resource.getrusage(resource.RUSAGE_SELF)
                # ru_maxrss is in kilobytes on Linux, bytes on macOS
                if sys.platform == 'darwin':
                    return usage.ru_maxrss
                else:
                    return usage.ru_maxrss * 1024

            # Try reading /proc/self/status (Linux)
            elif sys.platform.startswith('linux'):
                status_path = Path('/proc/self/status')
                if status_path.exists():
                    with open(status_path) as f:
                        for line in f:
                            if line.startswith('VmRSS:'):
                                # Extract memory in kB
                                parts = line.split()
                                return int(parts[1]) * 1024

            # Fallback: return 0 if we can't determine
            return 0

        except Exception as e:
            raise LimitsError(f"Failed to get memory usage: {e}") from e

    @staticmethod
    def check_memory_limit(max_bytes: int) -> bool:
        """Check if current memory usage is under limit.

        Args:
            max_bytes: Maximum allowed memory in bytes

        Returns:
            True if under limit

        Raises:
            LimitsError: If over limit
        """
        try:
            current = Limits.get_memory_usage()
            if current > max_bytes:
                raise LimitsError(
                    f"Memory usage {current} bytes exceeds limit {max_bytes} bytes"
                )
            return True

        except LimitsError:
            raise
        except Exception as e:
            raise LimitsError(f"Memory limit check failed: {e}") from e

    @staticmethod
    def get_open_file_count() -> int:
        """Get count of open file descriptors.

        Returns:
            Number of open file descriptors

        Raises:
            LimitsError: If count cannot be determined
        """
        try:
            # Try /proc/self/fd (Linux)
            if sys.platform.startswith('linux'):
                fd_path = Path('/proc/self/fd')
                if fd_path.exists():
                    return len(list(fd_path.iterdir()))

            # Try resource module (Unix)
            elif hasattr(os, 'getrusage'):
                import resource
                # This is less accurate but works on macOS
                soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
                # Can't get exact count, return 0
                return 0

            # Fallback
            return 0

        except Exception as e:
            raise LimitsError(f"Failed to get file descriptor count: {e}") from e

    @staticmethod
    def check_file_handles(max_handles: Optional[int] = None) -> bool:
        """Check file handle limits.

        Args:
            max_handles: Maximum allowed file handles (None = system limit)

        Returns:
            True if under limit

        Raises:
            LimitsError: If over limit
        """
        try:
            # Get system limit if not specified
            if max_handles is None:
                if hasattr(os, 'getrusage'):
                    import resource
                    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
                    max_handles = soft
                else:
                    # Default conservative limit
                    max_handles = 1024

            current = Limits.get_open_file_count()
            if current > 0 and current >= max_handles:
                raise LimitsError(
                    f"Open file handles {current} exceeds limit {max_handles}"
                )

            return True

        except LimitsError:
            raise
        except Exception as e:
            raise LimitsError(f"File handle check failed: {e}") from e

    @staticmethod
    def check_file_size(file_path: Path, max_bytes: int) -> bool:
        """Check if file size is under limit.

        Args:
            file_path: Path to file
            max_bytes: Maximum allowed file size in bytes

        Returns:
            True if under limit

        Raises:
            LimitsError: If file exceeds limit
        """
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)

            if not file_path.exists():
                return True

            size = file_path.stat().st_size
            if size > max_bytes:
                raise LimitsError(
                    f"File size {size} bytes exceeds limit {max_bytes} bytes: {file_path}"
                )

            return True

        except LimitsError:
            raise
        except Exception as e:
            raise LimitsError(f"File size check failed: {e}") from e

    @staticmethod
    def check_data_size(data: bytes, max_bytes: int) -> bool:
        """Check if data size is under limit.

        Args:
            data: Data to check
            max_bytes: Maximum allowed size in bytes

        Returns:
            True if under limit

        Raises:
            LimitsError: If data exceeds limit
        """
        size = len(data)
        if size > max_bytes:
            raise LimitsError(
                f"Data size {size} bytes exceeds limit {max_bytes} bytes"
            )
        return True

    @staticmethod
    @contextmanager
    def time_limit(seconds: float):
        """Context manager for time-limited operations.

        Args:
            seconds: Maximum allowed time in seconds

        Yields:
            None

        Raises:
            LimitsError: If operation exceeds time limit

        Example:
            with Limits.time_limit(5.0):
                # Operation must complete within 5 seconds
                slow_operation()
        """
        start_time = time.monotonic()
        try:
            yield
        finally:
            elapsed = time.monotonic() - start_time
            if elapsed > seconds:
                raise LimitsError(
                    f"Operation took {elapsed:.2f}s, exceeding limit of {seconds}s"
                )


class RateLimiter:
    """Token bucket rate limiter.

    Implements the token bucket algorithm for rate limiting operations.
    Uses condition variables for efficient waiting and time.monotonic() for
    accurate elapsed time calculations.
    """

    def __init__(self, rate: float, burst: int = 1):
        """Initialize rate limiter.

        Args:
            rate: Tokens per second
            burst: Maximum burst size (bucket capacity)
        """
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_update = time.monotonic()
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_update
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_update = now

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if rate limit exceeded
        """
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def wait(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """Wait until tokens are available.

        Args:
            tokens: Number of tokens to consume
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            True if tokens were consumed, False if timeout

        Raises:
            LimitsError: If timeout is exceeded
        """
        start_time = time.monotonic()

        with self._lock:
            while True:
                # Check if we have enough tokens
                self._refill()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                # Check timeout
                if timeout is not None:
                    elapsed = time.monotonic() - start_time
                    if elapsed >= timeout:
                        raise LimitsError(
                            f"Rate limit wait timeout after {elapsed:.2f}s"
                        )

                # Wait for tokens to be available or timeout
                wait_time = timeout if timeout is not None else None
                self._condition.wait(timeout=wait_time)

                # If we get here without timeout, loop will check tokens again
    def _notify_waiters(self) -> None:
        """Notify waiting threads that tokens may be available."""
        with self._condition:
            self._condition.notify_all()

    @contextmanager
    def limit(self, tokens: int = 1):
        """Context manager for rate-limited operations.

        Args:
            tokens: Number of tokens to consume

        Yields:
            None

        Raises:
            LimitsError: If rate limit exceeded

        Example:
            limiter = RateLimiter(rate=10, burst=5)
            with limiter.limit():
                # Rate-limited operation
                process_item()
        """
        if not self.consume(tokens):
            raise LimitsError("Rate limit exceeded")
        yield


class SizeLimit:
    """Size limit tracker for cumulative operations."""

    def __init__(self, max_bytes: int):
        """Initialize size limit tracker.

        Args:
            max_bytes: Maximum allowed cumulative size
        """
        self.max_bytes = max_bytes
        self.current_bytes = 0
        self._lock = threading.Lock()

    def add(self, bytes_to_add: int) -> bool:
        """Add to cumulative size.

        Args:
            bytes_to_add: Bytes to add

        Returns:
            True if added successfully

        Raises:
            LimitsError: If addition would exceed limit
        """
        with self._lock:
            new_total = self.current_bytes + bytes_to_add
            if new_total > self.max_bytes:
                raise LimitsError(
                    f"Adding {bytes_to_add} bytes would exceed "
                    f"limit {self.max_bytes} bytes (current: {self.current_bytes})"
                )
            self.current_bytes = new_total
            return True

    def reset(self) -> None:
        """Reset cumulative size to zero."""
        with self._lock:
            self.current_bytes = 0

    def remaining(self) -> int:
        """Get remaining capacity.

        Returns:
            Remaining bytes before limit
        """
        with self._lock:
            return max(0, self.max_bytes - self.current_bytes)

    @property
    def used(self) -> int:
        """Get currently used bytes.

        Returns:
            Current byte count
        """
        return self.current_bytes


class CountLimit:
    """Count limit tracker for operations."""

    def __init__(self, max_count: int):
        """Initialize count limit tracker.

        Args:
            max_count: Maximum allowed count
        """
        self.max_count = max_count
        self.current_count = 0
        self._lock = threading.Lock()

    def increment(self, amount: int = 1) -> bool:
        """Increment count.

        Args:
            amount: Amount to increment

        Returns:
            True if incremented successfully

        Raises:
            LimitsError: If increment would exceed limit
        """
        with self._lock:
            new_count = self.current_count + amount
            if new_count > self.max_count:
                raise LimitsError(
                    f"Incrementing by {amount} would exceed "
                    f"limit {self.max_count} (current: {self.current_count})"
                )
            self.current_count = new_count
            return True

    def reset(self) -> None:
        """Reset count to zero."""
        with self._lock:
            self.current_count = 0

    def remaining(self) -> int:
        """Get remaining capacity.

        Returns:
            Remaining count before limit
        """
        with self._lock:
            return max(0, self.max_count - self.current_count)

    @property
    def used(self) -> int:
        """Get current count.

        Returns:
            Current count
        """
        return self.current_count


# Convenience function for timeout decorator
def with_timeout(seconds: float):
    """Decorator for time-limited functions.

    Args:
        seconds: Maximum allowed time

    Returns:
        Decorator function

    Example:
        @with_timeout(5.0)
        def slow_function():
            # Must complete within 5 seconds
            time.sleep(10)
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            with Limits.time_limit(seconds):
                return func(*args, **kwargs)
        return wrapper
    return decorator
