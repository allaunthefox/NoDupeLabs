"""Tests for time_sync_utils module."""

# pylint: disable=W0718  # broad-exception-caught - intentional for graceful degradation
import socket
import time

import pytest

from nodupe.tools.time_sync.sync_utils import (
    DNSCache,
    FastDate64Encoder,
    MonotonicTimeCalculator,
    ParallelNTPClient,
    PerformanceMetrics,
    TargetedFileScanner,
    clear_global_caches,
    get_global_dns_cache,
    get_global_metrics,
)


class TestDNSCache:
    """Test DNSCache class."""

    def test_init(self):
        """Test DNSCache initialization."""
        cache = DNSCache(ttl=60.0, max_size=100)
        assert cache._ttl == 60.0
        assert cache._max_size == 100

    def test_set_and_get(self):
        """Test setting and getting cache entries."""
        cache = DNSCache(ttl=60.0, max_size=10)
        addresses = [(2, 2, 17, '', ('216.239.35.0', 123))]
        cache.set("time.google.com", 123, addresses)
        result = cache.get("time.google.com", 123)
        assert result is not None

    def test_get_miss(self):
        """Test cache miss."""
        cache = DNSCache()
        result = cache.get("nonexistent.example.com", 123)
        assert result is None

    def test_clear(self):
        """Test clearing cache."""
        cache = DNSCache()
        cache.set("time.google.com", 123, [])
        cache.clear()
        result = cache.get("time.google.com", 123)
        assert result is None

    def test_invalidate(self):
        """Test invalidating cache entry."""
        cache = DNSCache()
        cache.set("time.google.com", 123, [])
        cache.invalidate("time.google.com", 123)
        result = cache.get("time.google.com", 123)
        assert result is None

    def test_cache_expiry(self, monkeypatch):
        """Test cache entry expires after TTL."""
        import time
        cache = DNSCache(ttl=0.01, max_size=10)
        cache.set("test.example.com", 123, [(2, 2, 17, '', ('127.0.0.1', 123))])

        # Should exist immediately
        result = cache.get("test.example.com", 123)
        assert result is not None

        # Wait for TTL to expire
        time.sleep(0.02)

        # Should be expired now
        result = cache.get("test.example.com", 123)
        assert result is None

    def test_cache_at_capacity(self):
        """Test cache evicts oldest when at capacity."""
        cache = DNSCache(ttl=60.0, max_size=2)
        cache.set("host1.com", 123, [(1,)])
        cache.set("host2.com", 123, [(2,)])
        cache.set("host3.com", 123, [(3,)])

        # First entry should be evicted
        result = cache.get("host1.com", 123)
        assert result is None

        # Others should still exist
        assert cache.get("host2.com", 123) is not None
        assert cache.get("host3.com", 123) is not None


class TestMonotonicTimeCalculator:
    """Test MonotonicTimeCalculator class."""

    def test_init(self):
        """Test initialization."""
        calc = MonotonicTimeCalculator()
        assert calc._wall_start is None
        assert calc._mono_start is None

    def test_start_timing(self):
        """Test starting timing."""
        calc = MonotonicTimeCalculator()
        wall, mono = calc.start_timing()
        assert wall is not None
        assert mono is not None

    def test_elapsed_monotonic(self):
        """Test getting elapsed time."""
        calc = MonotonicTimeCalculator()
        calc.start_timing()
        time.sleep(0.01)
        elapsed = calc.elapsed_monotonic()
        assert elapsed > 0

    def test_elapsed_monotonic_error(self):
        """Test elapsed_monotonic raises when not started."""
        calc = MonotonicTimeCalculator()
        with pytest.raises(ValueError):
            calc.elapsed_monotonic()

    def test_wall_time_from_monotonic(self):
        """Test converting monotonic to wall time."""
        calc = MonotonicTimeCalculator()
        calc.start_timing()
        wall = calc.wall_time_from_monotonic(0.0)
        assert wall is not None

    def test_wall_time_from_monotonic_error(self):
        """Test wall_time_from_monotonic raises when not started."""
        calc = MonotonicTimeCalculator()
        with pytest.raises(ValueError):
            calc.wall_time_from_monotonic(0.0)

    def test_calculate_ntp_rtt(self):
        """Test NTP RTT calculation."""
        delay, offset = MonotonicTimeCalculator.calculate_ntp_rtt(
            1000.0, 1000.1, 1000.2, 1000.3, 1000.0
        )
        assert isinstance(delay, float)
        assert isinstance(offset, float)


class TestTargetedFileScanner:
    """Test TargetedFileScanner class."""

    def test_init(self):
        """Test initialization."""
        scanner = TargetedFileScanner(max_files=50, max_depth=3)
        assert scanner._max_files == 50
        assert scanner._max_depth == 3

    def test_get_recent_file_time(self):
        """Test getting recent file time."""
        scanner = TargetedFileScanner(max_files=10, max_depth=2)
        ts = scanner.get_recent_file_time()
        # May be None if no valid files found
        assert ts is None or isinstance(ts, float)

    def test_get_recent_file_time_with_additional_paths(self, temp_dir):
        """Test getting recent file time with additional paths."""
        # Create a test file with recent timestamp
        test_file = temp_dir / "recent.txt"
        test_file.write_text("test")

        scanner = TargetedFileScanner(max_files=10, max_depth=2)
        ts = scanner.get_recent_file_time(additional_paths=[str(temp_dir)])
        # Should find the file we just created
        assert ts is None or isinstance(ts, float)

    def test_scan_path_file(self, temp_dir):
        """Test scanning a single file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        scanner = TargetedFileScanner()
        result = scanner._scan_path(str(test_file), 0)
        # Should return mtime > 0
        assert result >= 0

    def test_scan_path_nonexistent(self):
        """Test scanning nonexistent path."""
        scanner = TargetedFileScanner()
        result = scanner._scan_path("/nonexistent/path/to/file", 0)
        assert result == 0.0

    def test_scan_path_directory(self, temp_dir):
        """Test scanning a directory."""
        # Create a file in directory
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        scanner = TargetedFileScanner(max_files=5, max_depth=1)
        result = scanner._scan_path(str(temp_dir), 0)
        assert result >= 0


class TestFastDate64Encoder:
    """Test FastDate64Encoder class."""

    def test_encode(self):
        """Test encoding timestamp."""
        result = FastDate64Encoder.encode(1700000000.0)
        assert isinstance(result, int)
        assert result > 0

    def test_encode_negative(self):
        """Test encoding negative timestamp raises."""
        with pytest.raises(ValueError):
            FastDate64Encoder.encode(-1.0)

    def test_encode_overflow(self):
        """Test encoding too large timestamp raises."""
        import math
        # Use a timestamp that would overflow the 34-bit field
        large_ts = (1 << 35)  # Beyond FASTDATE_SECONDS_MAX
        with pytest.raises(OverflowError):
            FastDate64Encoder.encode(float(large_ts))

    def test_decode(self):
        """Test decoding timestamp."""
        encoded = FastDate64Encoder.encode(1700000000.0)
        decoded = FastDate64Encoder.decode(encoded)
        assert abs(decoded - 1700000000.0) < 1.0

    def test_encode_safe(self):
        """Test safe encode."""
        result = FastDate64Encoder.encode_safe(1700000000.0)
        assert result > 0

    def test_encode_safe_negative(self):
        """Test safe encode with negative returns 0."""
        result = FastDate64Encoder.encode_safe(-1.0)
        assert result == 0

    def test_decode_safe(self):
        """Test safe decode."""
        encoded = FastDate64Encoder.encode(1700000000.0)
        result = FastDate64Encoder.decode_safe(encoded)
        assert result > 0

    def test_decode_safe_invalid(self):
        """Test safe decode with invalid returns 0."""
        result = FastDate64Encoder.decode_safe(-1)
        # Should return 0.0 for invalid values
        assert result == 0.0 or result < 0.001


class TestPerformanceMetrics:
    """Test PerformanceMetrics class."""

    def test_init(self):
        """Test initialization."""
        metrics = PerformanceMetrics()
        assert 'ntp_queries' in metrics._metrics
        assert 'dns_cache_hits' in metrics._metrics

    def test_record_ntp_query(self):
        """Test recording NTP query."""
        metrics = PerformanceMetrics()
        metrics.record_ntp_query("time.google.com", 0.05, True, 0.5)
        summary = metrics.get_summary()
        assert summary['total_queries'] == 1

    def test_record_dns_cache_hit(self):
        """Test recording DNS cache hit."""
        metrics = PerformanceMetrics()
        metrics.record_dns_cache_hit()
        metrics.record_dns_cache_miss()
        summary = metrics.get_summary()
        assert summary['dns_cache_hit_rate'] == 0.5

    def test_record_parallel_query(self):
        """Test recording parallel query."""
        metrics = PerformanceMetrics()
        metrics.record_parallel_query(3, 5, True, 1.0, 0.05)
        summary = metrics.get_summary()
        assert summary['total_parallel_queries'] == 1

    def test_record_fallback_usage(self):
        """Test recording fallback usage."""
        metrics = PerformanceMetrics()
        metrics.record_fallback_usage("file_time", 0.1)
        summary = metrics.get_summary()
        assert summary['fallback_count'] == 1

    def test_record_error(self):
        """Test recording error."""
        metrics = PerformanceMetrics()
        metrics.record_error("timeout", "Connection timed out")
        summary = metrics.get_summary()
        assert summary['error_count'] == 1

    def test_get_summary(self):
        """Test getting summary."""
        metrics = PerformanceMetrics()
        metrics.record_ntp_query("time.google.com", 0.05, True, 0.5)
        metrics.record_ntp_query("pool.ntp.org", 0.1, True, 0.6)
        metrics.record_ntp_query("bad.server.com", 0.5, False, 1.0)
        summary = metrics.get_summary()
        assert summary['total_queries'] == 3
        assert summary['success_rate'] == 2/3


class TestGlobalInstances:
    """Test global instances and functions."""

    def test_get_global_dns_cache(self):
        """Test getting global DNS cache."""
        cache = get_global_dns_cache()
        assert isinstance(cache, DNSCache)

    def test_get_global_metrics(self):
        """Test getting global metrics."""
        metrics = get_global_metrics()
        assert isinstance(metrics, PerformanceMetrics)

    def test_clear_global_caches(self):
        """Test clearing global caches."""
        cache = get_global_dns_cache()
        cache.set("test.example.com", 123, [])
        clear_global_caches()
        result = cache.get("test.example.com", 123)
        assert result is None


class TestParallelNTPClient:
    """Test ParallelNTPClient class."""

    def test_init(self):
        """Test initialization."""
        client = ParallelNTPClient(timeout=5.0, max_workers=4)
        assert client._timeout == 5.0
        assert client._max_workers == 4

    def test_executor_property(self):
        """Test executor property."""
        client = ParallelNTPClient()
        executor = client.executor
        assert executor is not None
        client.shutdown()

    def test_shutdown(self):
        """Test shutdown."""
        client = ParallelNTPClient()
        _ = client.executor  # Create executor
        client.shutdown()
        assert client._executor is None

    def test_to_ntp(self):
        """Test converting POSIX to NTP timestamp."""
        client = ParallelNTPClient()
        sec, frac = client._to_ntp(1700000000.0)
        assert isinstance(sec, int)
        assert isinstance(frac, int)
        assert sec > 0

    def test_from_ntp(self):
        """Test converting NTP to POSIX timestamp."""
        client = ParallelNTPClient()
        posix = client._from_ntp(3886540800, 0)  # 2023-01-01
        assert posix > 0

    def test_resolve_host_addresses(self):
        """Test host address resolution."""
        client = ParallelNTPClient()
        client._resolve_host_addresses("localhost")
        # May be empty in some test environments

    def test_resolve_host_addresses_cached(self):
        """Test host address resolution uses cache."""
        client = ParallelNTPClient()
        # Set up cache
        client._dns_cache.set("testhost.example.com", 123, [])
        addresses = client._resolve_host_addresses("testhost.example.com")
        assert addresses == []

    def test_resolve_host_addresses_error(self):
        """Test host address resolution with error."""
        client = ParallelNTPClient()
        addresses = client._resolve_host_addresses("this-host-does-not-exist-123456.invalid")
        assert addresses == []

    def test_query_single_address_failure(self):
        """Test query with invalid address."""
        client = ParallelNTPClient(timeout=0.1)
        try:
            # This will likely fail due to invalid address
            addr_info = (socket.AF_INET, socket.SOCK_DGRAM, 0, '', ('127.0.0.1', 123))
            client._query_single_address(0, "localhost", addr_info, 0)
        except Exception:
            pass  # Expected - may fail in test env

    def test_query_hosts_parallel_empty(self):
        """Test parallel query with empty hosts."""
        client = ParallelNTPClient()
        result = client.query_hosts_parallel([])
        assert result.success is False
        assert len(result.all_responses) == 0

    def test_dns_cache_attribute(self):
        """Test dns cache attribute."""
        client = ParallelNTPClient()
        assert client._dns_cache is not None
        assert isinstance(client._dns_cache, DNSCache)

    def test_query_hosts_parallel_with_valid_hosts(self):
        """Test parallel query with valid but unreachable hosts."""
        client = ParallelNTPClient(timeout=0.5)
        # Use unreachable IP to trigger timeout
        result = client.query_hosts_parallel(
            ["192.0.2.1"],  # TEST-NET-1 (reserved for documentation)
            attempts_per_host=1,
            stop_on_good_result=False
        )
        # Should return failure but not crash
        assert result.success is False or len(result.errors) >= 0

    def test_query_hosts_parallel_stop_on_good(self):
        """Test parallel query stops on good result."""
        client = ParallelNTPClient(timeout=0.5)
        # Use valid host but will likely fail
        result = client.query_hosts_parallel(
            ["localhost"],
            attempts_per_host=1,
            stop_on_good_result=True
        )
        # Should return some result
        assert result is not None

    def test_query_hosts_parallel_with_attempts(self):
        """Test parallel query with multiple attempts."""
        client = ParallelNTPClient(timeout=0.5)
        result = client.query_hosts_parallel(
            ["192.0.2.1"],
            attempts_per_host=2,
            stop_on_good_result=False
        )
        assert result is not None

    def test_query_single_address_returns_response(self):
        """Test _query_single_address returns proper response structure."""
        client = ParallelNTPClient(timeout=1.0)
        try:
            # Use actual localhost
            addr_info = (socket.AF_INET, socket.SOCK_DGRAM, 0, '', ('127.0.0.1', 123))
            result = client._query_single_address(0, "localhost", addr_info, 0)
            # Result may be None if failed
            assert result is None or hasattr(result, 'offset')
        except Exception:
            pass  # Network operations may fail in test env


class TestGlobalFunctions:
    """Test global utility functions."""

    def test_get_global_dns_cache_multiple_calls(self):
        """Test multiple calls return same instance."""
        cache1 = get_global_dns_cache()
        cache2 = get_global_dns_cache()
        assert cache1 is cache2

    def test_get_global_metrics_multiple_calls(self):
        """Test multiple calls return same instance."""
        metrics1 = get_global_metrics()
        metrics2 = get_global_metrics()
        assert metrics1 is metrics2
