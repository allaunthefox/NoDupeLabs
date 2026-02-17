"""Tests for limits module."""

import time
from pathlib import Path
from unittest.mock import patch

import pytest

from nodupe.core.limits import (
    CountLimit,
    Limits,
    LimitsError,
    RateLimiter,
    SizeLimit,
)


class TestLimits:
    """Test Limits class."""

    def test_get_memory_usage(self):
        """Test getting memory usage."""
        usage = Limits.get_memory_usage()
        assert isinstance(usage, int)
        assert usage >= 0

    def test_check_file_size(self, tmp_path):
        """Test file size checking."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"X" * 1000)

        # Should pass
        assert Limits.check_file_size(test_file, max_bytes=2000)

        # Should fail
        with pytest.raises(LimitsError):
            Limits.check_file_size(test_file, max_bytes=500)

    def test_check_data_size(self):
        """Test data size checking."""
        data = b"X" * 1000

        # Should pass
        assert Limits.check_data_size(data, max_bytes=2000)

        # Should fail
        with pytest.raises(LimitsError):
            Limits.check_data_size(data, max_bytes=500)

    def test_time_limit(self):
        """Test time limit context manager."""
        # Should pass
        with patch('time.monotonic', side_effect=[0, 0.5]), Limits.time_limit(1.0):
            pass

        # Should fail
        with patch('time.monotonic', side_effect=[0, 0.5]), pytest.raises(LimitsError):
            with Limits.time_limit(0.1):
                pass


class TestRateLimiter:
    """Test RateLimiter class."""

    def test_rate_limiter_creation(self):
        """Test rate limiter creation."""
        limiter = RateLimiter(rate=10, burst=5)
        assert limiter.rate == 10
        assert limiter.burst == 5

    def test_consume_TOKEN_REMOVEDs(self):
        """Test consuming TOKEN_REMOVEDs."""
        limiter = RateLimiter(rate=10, burst=5)

        # Should succeed
        assert limiter.consume(1)
        assert limiter.consume(1)

    def test_consume_too_many_TOKEN_REMOVEDs(self):
        """Test consuming more TOKEN_REMOVEDs than available."""
        limiter = RateLimiter(rate=1, burst=2)

        # Consume all TOKEN_REMOVEDs
        assert limiter.consume(2)

        # Should fail immediately (no TOKEN_REMOVEDs left)
        assert not limiter.consume(1)

    def test_rate_limiter_refill(self):
        """Test that TOKEN_REMOVEDs refill over time."""
        with patch('time.monotonic', side_effect=[0, 0, 0.3]):
            limiter = RateLimiter(rate=10, burst=2)

            # Consume all TOKEN_REMOVEDs
            assert limiter.consume(2)

            # Should have TOKEN_REMOVEDs again after simulated time
            assert limiter.consume(1)

    def test_rate_limiter_context(self):
        """Test rate limiter context manager."""
        limiter = RateLimiter(rate=10, burst=5)

        # Should succeed
        with limiter.limit(1):
            pass

    def test_rate_limiter_context_exceeds(self):
        """Test rate limiter context when limit exceeded."""
        limiter = RateLimiter(rate=1, burst=1)

        # Consume all TOKEN_REMOVEDs
        limiter.consume(1)

        # Should fail
        with pytest.raises(LimitsError), limiter.limit(1):
            pass


class TestSizeLimit:
    """Test SizeLimit class."""

    def test_size_limit_creation(self):
        """Test size limit creation."""
        limit = SizeLimit(max_bytes=1000)
        assert limit.max_bytes == 1000
        assert limit.current_bytes == 0

    def test_add_bytes(self):
        """Test adding bytes."""
        limit = SizeLimit(max_bytes=1000)

        # Should succeed
        assert limit.add(500)
        assert limit.current_bytes == 500

        # Add more
        assert limit.add(300)
        assert limit.current_bytes == 800

    def test_add_bytes_exceeds_limit(self):
        """Test adding bytes that exceed limit."""
        limit = SizeLimit(max_bytes=1000)

        limit.add(900)

        # Should fail
        with pytest.raises(LimitsError):
            limit.add(200)

    def test_reset_size_limit(self):
        """Test resetting size limit."""
        limit = SizeLimit(max_bytes=1000)

        limit.add(500)
        assert limit.current_bytes == 500

        limit.reset()
        assert limit.current_bytes == 0

    def test_remaining_capacity(self):
        """Test getting remaining capacity."""
        limit = SizeLimit(max_bytes=1000)

        assert limit.remaining() == 1000

        limit.add(300)
        assert limit.remaining() == 700

    def test_used_property(self):
        """Test used property."""
        limit = SizeLimit(max_bytes=1000)

        assert limit.used == 0

        limit.add(500)
        assert limit.used == 500


class TestCountLimit:
    """Test CountLimit class."""

    def test_count_limit_creation(self):
        """Test count limit creation."""
        limit = CountLimit(max_count=10)
        assert limit.max_count == 10
        assert limit.current_count == 0

    def test_increment_count(self):
        """Test incrementing count."""
        limit = CountLimit(max_count=10)

        # Should succeed
        assert limit.increment(1)
        assert limit.current_count == 1

        # Increment more
        assert limit.increment(5)
        assert limit.current_count == 6

    def test_increment_exceeds_limit(self):
        """Test incrementing beyond limit."""
        limit = CountLimit(max_count=10)

        limit.increment(9)

        # Should fail
        with pytest.raises(LimitsError):
            limit.increment(2)

    def test_reset_count_limit(self):
        """Test resetting count limit."""
        limit = CountLimit(max_count=10)

        limit.increment(5)
        assert limit.current_count == 5

        limit.reset()
        assert limit.current_count == 0

    def test_remaining_count(self):
        """Test getting remaining count."""
        limit = CountLimit(max_count=10)

        assert limit.remaining() == 10

        limit.increment(3)
        assert limit.remaining() == 7

    def test_used_count_property(self):
        """Test used property."""
        limit = CountLimit(max_count=10)

        assert limit.used == 0

        limit.increment(5)
        assert limit.used == 5
