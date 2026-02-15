# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Rate Limiting Module.

Provides rate limiting functionality using sliding window algorithm.
"""

from __future__ import annotations

import functools
import time
from collections import deque
from typing import Any, Callable, Deque, Dict, Optional


class RateLimiter:
    """Sliding Window Rate Limiter.

    Implements rate limiting using a sliding window algorithm to track
    request timestamps and enforce rate limits.
    """

    def __init__(self, requests_per_minute: int = 60) -> None:
        """Initialize rate limiter."""
        self.requests_per_minute = requests_per_minute
        self.window_size: float = 60.0
        self._requests: Dict[str, Deque[float]] = {}

    def check_rate_limit(self, client_id: Optional[str] = None) -> bool:
        """Check if request is within rate limit."""
        key = client_id or "default"
        current_time = time.time()

        if key not in self._requests:
            self._requests[key] = deque()

        window_start = current_time - self.window_size
        while self._requests[key] and self._requests[key][0] < window_start:
            self._requests[key].popleft()

        if len(self._requests[key]) < self.requests_per_minute:
            self._requests[key].append(current_time)
            return True

        return False

    def throttle(self, client_id: Optional[str] = None) -> float:
        """Get wait time until next request is allowed."""
        key = client_id or "default"

        if key not in self._requests or not self._requests[key]:
            return 0.0

        oldest = self._requests[key][0]
        current_time = time.time()
        window_start = current_time - self.window_size

        if oldest < window_start:
            return 0.0

        return oldest + self.window_size - current_time + 0.1


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: float = 0.0) -> None:
        """Initialize rate limit exception."""
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


def rate_limited(requests_per_minute: int = 60) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to apply rate limiting to a function."""
    limiter = RateLimiter(requests_per_minute=requests_per_minute)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not limiter.check_rate_limit():
                wait_time = limiter.throttle()
                raise RateLimitExceeded(f"Rate limit exceeded. Try again in {wait_time:.1f} seconds.", retry_after=wait_time)
            return func(*args, **kwargs)
        return wrapper

    return decorator
