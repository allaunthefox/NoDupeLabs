"""Tests for the RateLimiter and rate_limited decorator."""

import time
import pytest

from nodupe.core.api.ratelimit import (
    RateLimiter,
    rate_limited,
    RateLimitExceeded,
)


def test_check_rate_limit_allows_until_limit():
    limiter = RateLimiter(requests_per_minute=3)

    assert limiter.check_rate_limit("client") is True
    assert limiter.check_rate_limit("client") is True
    assert limiter.check_rate_limit("client") is True

    # Fourth request within the window should be denied
    assert limiter.check_rate_limit("client") is False


def test_throttle_returns_positive_after_limit():
    limiter = RateLimiter(requests_per_minute=1)

    assert limiter.check_rate_limit("c") is True
    assert limiter.check_rate_limit("c") is False

    wait = limiter.throttle("c")
    assert wait > 0.0


def test_throttle_zero_when_no_requests():
    limiter = RateLimiter(requests_per_minute=10)
    assert limiter.throttle("no-requests") == 0.0


def test_rate_limited_decorator_raises_and_has_retry_after():
    @rate_limited(requests_per_minute=1)
    def hello():
        return "ok"

    assert hello() == "ok"

    with pytest.raises(RateLimitExceeded) as exc_info:
        hello()

    exc = exc_info.value
    assert exc.retry_after >= 0.0
    assert "Rate limit exceeded" in str(exc)
