import time

import pytest

from nodupe.core.api.ratelimit import (
    RateLimiter,
    rate_limited,
    RateLimitExceeded,
)


def test_rate_limiter_allows_then_blocks():
    rl = RateLimiter(requests_per_minute=2)

    assert rl.check_rate_limit("c1") is True
    assert rl.check_rate_limit("c1") is True
    # third call should be blocked
    assert rl.check_rate_limit("c1") is False


def test_throttle_reports_positive_wait_after_limit():
    rl = RateLimiter(requests_per_minute=1)
    assert rl.check_rate_limit("u") is True
    # immediate throttle should be > 0
    t = rl.throttle("u")
    assert t >= 0.0

    # new client has no throttle
    assert rl.throttle("new_client") == 0.0


def test_rate_limited_decorator_raises_after_limit():
    @rate_limited(requests_per_minute=1)
    def f():
        return "ok"

    assert f() == "ok"
    with pytest.raises(RateLimitExceeded):
        f()
