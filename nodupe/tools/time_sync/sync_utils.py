# pylint: disable=logging-fstring-interpolation
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""
TimeSync Utilities - Core Performance Optimizations.

This module contains optimized utilities for the TimeSync plugin, including:
- Parallel NTP client for concurrent network queries
- Monotonic timing calculations for robust RTT measurements
- Precompiled struct formats for reduced CPU overhead
- DNS caching for faster address resolution
- Targeted file system scanning for efficient fallback

These utilities are designed to address critical performance bottlenecks in the
NoDupeLabs TimeSync plugin while maintaining full compatibility and correctness.

Classes:
    DNSCache: Thread-safe DNS resolution cache with TTL.
    MonotonicTimeCalculator: Robust timing calculator using monotonic time.
    TargetedFileScanner: Efficient file system scanner for time fallback.
    ParallelNTPClient: High-performance parallel NTP client.
    FastDate64Encoder: Optimized FastDate64 timestamp encoder/decoder.
    PerformanceMetrics: Performance metrics collector for TimeSync operations.

Functions:
    get_global_dns_cache: Get global DNS cache instance.
    get_global_metrics: Get global metrics instance.
    clear_global_caches: Clear all global caches.
    performance_timer: Context manager for timing operations.

Example:
    >>> from nodupe.tools.time_sync.sync_utils import ParallelNTPClient, DNSCache
    >>> dns_cache = DNSCache(ttl=60.0, max_size=200)
    >>> client = ParallelNTPClient(timeout=5.0, dns_cache=dns_cache)
    >>> result = client.query_hosts_parallel(["time.google.com"])
    >>> print(f"Success: {result.success}, Delay: {result.best_response.delay if result.best_response else 'N/A'}")
"""

from __future__ import annotations

import logging
import os
import socket
import struct
import threading
import time
import weakref
from collections import OrderedDict
from collections.abc import Iterable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Optional


logger = logging.getLogger(__name__)


# Constants
NTP_TO_UNIX = 2208988800  # seconds between 1900-01-01 and 1970-01-01
DEFAULT_TIMEOUT = 3.0
DEFAULT_ATTEMPTS = 2
DEFAULT_MAX_ACCEPTABLE_DELAY = 0.5
DEFAULT_SMOOTHING_ALPHA = 0.3

# Precompiled struct formats for performance
NTP_PACKET_STRUCT = struct.Struct("!12I")  # Precompiled "!12I" format
NTP_TIMESTAMP_STRUCT = struct.Struct("!II")  # Precompiled "!II" format for timestamps

# FastDate64 constants
FASTDATE_SECONDS_BITS = 34
FASTDATE_FRAC_BITS = 30
FASTDATE_FRAC_SCALE = 1 << FASTDATE_FRAC_BITS
FASTDATE_SECONDS_MAX = (1 << FASTDATE_SECONDS_BITS) - 1


# Type aliases
AddressTuple = tuple[int, int, int, int, tuple[str, int]]
NTPQueryResult = tuple[str, Exception]
MetricsDict = dict[str, Any]


@dataclass
class NTPResponse:
    """NTP response data structure.

    Attributes:
        server_time: Server timestamp in POSIX format.
        offset: NTP offset in seconds.
        delay: Round-trip delay in seconds.
        host: NTP server hostname.
        address: Socket address tuple.
        attempt: Attempt number.
        timestamp: Response timestamp.
    """
    server_time: float
    offset: float
    delay: float
    host: str
    address: tuple[str, int]
    attempt: int
    timestamp: float


@dataclass
class ParallelQueryResult:
    """Result of parallel NTP query.

    Attributes:
        success: Whether query was successful.
        best_response: Best NTP response found.
        all_responses: All responses received.
        errors: List of errors encountered.
    """
    success: bool
    best_response: Optional[NTPResponse]
    all_responses: list[NTPResponse]
    errors: list[NTPQueryResult]


class DNSCache:
    """Thread-safe DNS resolution cache with TTL.

    Caches getaddrinfo results to avoid repeated DNS lookups during
    multiple attempts and parallel queries.

    Attributes:
        ttl: Time-to-live for cached entries in seconds.
        max_size: Maximum number of cached entries.

    Example:
        >>> cache = DNSCache(ttl=30.0, max_size=100)
        >>> cache.set("time.google.com", 123, [(2, 2, 17, '', ('216.239.35.0', 123))])
        >>> result = cache.get("time.google.com", 123)
        >>> print(f"Cached: {result is not None}")
    """

    def __init__(self, ttl: float = 30.0, max_size: int = 100) -> None:
        """Initialize DNS cache.

        Args:
            ttl: Time-to-live for cached entries in seconds.
            max_size: Maximum number of cached entries.
        """
        self._ttl = ttl
        self._max_size = max_size
        self._cache: OrderedDict[str, tuple[list[AddressTuple], float]] = OrderedDict()
        self._lock = threading.RLock()

    def get(self, host: str, port: int = 123) -> Optional[list[AddressTuple]]:
        """Get cached DNS resolution.

        Args:
            host: Hostname to resolve.
            port: Port number.

        Returns:
            Cached address list or None if not cached or expired.
        """
        key = f"{host}:{port}"

        with self._lock:
            if key not in self._cache:
                return None

            addresses, timestamp = self._cache[key]

            # Check TTL
            if time.time() - timestamp > self._ttl:
                del self._cache[key]
                return None

            # Move to end (LRU)
            self._cache.move_to_end(key)
            return addresses.copy()

    def set(self, host: str, port: int, addresses: list[AddressTuple]) -> None:
        """Cache DNS resolution.

        Args:
            host: Hostname that was resolved.
            port: Port number.
            addresses: List of resolved addresses.
        """
        key = f"{host}:{port}"

        with self._lock:
            # Remove old entry if exists
            if key in self._cache:
                del self._cache[key]

            # Evict oldest entries if at capacity
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)

            self._cache[key] = (addresses.copy(), time.time())

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()

    def invalidate(self, host: str, port: int = 123) -> None:
        """Invalidate cache entry for specific host.

        Args:
            host: Hostname to invalidate.
            port: Port number.
        """
        key = f"{host}:{port}"
        with self._lock:
            self._cache.pop(key, None)


class MonotonicTimeCalculator:
    """Robust timing calculator using monotonic time for elapsed measurements.

    This class addresses the fragility of wall-clock time by using time.monotonic()
    for elapsed time calculations while still providing wall-clock timestamps
    for NTP packet generation.

    Example:
        >>> timer = MonotonicTimeCalculator()
        >>> wall, mono = timer.start_timing()
        >>> elapsed = timer.elapsed_monotonic()
        >>> print(f"Elapsed: {elapsed:.3f}s")
    """

    def __init__(self) -> None:
        """Initialize the timing calculator."""
        self._wall_start: Optional[float] = None
        self._mono_start: Optional[float] = None

    def start_timing(self) -> tuple[float, float]:
        """Start timing and return both wall and monotonic timestamps.

        Returns:
            Tuple of (wall_time, monotonic_time).
        """
        self._wall_start = time.time()
        self._mono_start = time.monotonic()
        assert self._wall_start is not None
        assert self._mono_start is not None
        return self._wall_start, self._mono_start

    def elapsed_monotonic(self) -> float:
        """Get elapsed time using monotonic clock.

        Returns:
            Elapsed time in seconds.

        Raises:
            ValueError: If timing not started.
        """
        if self._mono_start is None:
            raise ValueError("Timing not started")
        return time.monotonic() - self._mono_start

    def wall_time_from_monotonic(self, mono_elapsed: float) -> float:
        """Convert monotonic elapsed time to wall time.

        Args:
            mono_elapsed: Elapsed time from monotonic clock.

        Returns:
            Corresponding wall time timestamp.

        Raises:
            ValueError: If timing not started.
        """
        if self._wall_start is None:
            raise ValueError("Timing not started")
        return self._wall_start + mono_elapsed

    @staticmethod
    def calculate_ntp_rtt(t1_wall: float, t2_wall: float,
                         t3_wall: float, t4_mono: float,
                         mono_start: float) -> tuple[float, float]:
        """Calculate NTP round-trip delay and offset using monotonic timing.

        Args:
            t1_wall: Client send time (wall clock).
            t2_wall: Server receive time (from NTP response).
            t3_wall: Server send time (from NTP response).
            t4_mono: Client receive time (monotonic).
            mono_start: Monotonic start time.

        Returns:
            Tuple of (delay, offset) in seconds.
        """
        # Convert t4_mono to wall time estimate
        t4_wall = t1_wall + (t4_mono - mono_start)

        # Calculate delay and offset
        delay = (t4_wall - t1_wall) - (t3_wall - t2_wall)
        offset = ((t2_wall - t1_wall) + (t3_wall - t4_wall)) / 2.0

        return delay, offset


class TargetedFileScanner:
    """Efficient file system scanner for time fallback.

    Replaces slow recursive glob with targeted scanning of trusted locations
    and limited-depth directory traversal.

    Attributes:
        max_files: Maximum number of files to scan.
        max_depth: Maximum directory depth to traverse.

    Example:
        >>> scanner = TargetedFileScanner(max_files=100, max_depth=2)
        >>> ts = scanner.get_recent_file_time()
        >>> print(f"Recent: {ts}")
    """

    def __init__(self, max_files: int = 100, max_depth: int = 2) -> None:
        """Initialize file scanner.

        Args:
            max_files: Maximum number of files to scan.
            max_depth: Maximum directory depth to traverse.
        """
        self._max_files = max_files
        self._max_depth = max_depth
        self._trusted_paths = [
            "/etc/adjtime",
            "/etc/localtime",
            "/var/log",
            "/tmp",
        ]

    def get_recent_file_time(self, additional_paths: Optional[list[str]] = None) -> Optional[float]:
        """Get timestamp from most recently modified file.

        Args:
            additional_paths: Additional paths to search.

        Returns:
            Most recent file modification time or None if no files found.
        """
        search_paths = self._trusted_paths.copy()
        if additional_paths:
            search_paths.extend(additional_paths)

        latest_time: float = 0.0
        file_count = 0

        for path in search_paths:
            if file_count >= self._max_files:
                break

            try:
                path_time = self._scan_path(path, file_count)
                latest_time = max(latest_time, path_time)
                file_count = min(file_count + 100, self._max_files)  # Estimate files per path
            except OSError:
                continue

        return latest_time if latest_time > 0 else None

    def _scan_path(self, path: str, file_count: int) -> float:
        """Scan a single path for recent files.

        Args:
            path: Path to scan.
            file_count: Current file count estimate.

        Returns:
            Most recent file modification time.
        """
        if not os.path.exists(path):
            return 0.0

        latest_time: float = 0.0

        if os.path.isfile(path):
            try:
                mtime = os.path.getmtime(path)
                if mtime > latest_time and mtime > 1000000000:  # After year 2002
                    latest_time = mtime
            except OSError:
                pass
            return latest_time

        # Directory scanning with limited depth
        for root, dirs, files in os.walk(path):
            # Limit depth
            if root != path:
                depth = root[len(path):].count(os.sep)
                if depth >= self._max_depth:
                    dirs[:] = []  # Don't recurse deeper
                    continue

            # Limit file count
            for file in files:
                if file_count >= self._max_files:
                    break

                try:
                    file_path = os.path.join(root, file)
                    mtime = os.path.getmtime(file_path)
                    if mtime > latest_time and mtime > 1000000000:  # After year 2002
                        latest_time = mtime
                    file_count += 1
                except OSError:
                    continue

        return latest_time


class ParallelNTPClient:
    """High-performance parallel NTP client.

    Performs concurrent queries across multiple hosts and addresses to minimize
    wall-clock time while maintaining accuracy and reliability.

    Attributes:
        timeout: Socket timeout for individual queries.
        max_workers: Maximum concurrent workers.
        dns_cache: DNS cache for address resolution.

    Example:
        >>> client = ParallelNTPClient(timeout=5.0, max_workers=8)
        >>> result = client.query_hosts_parallel(["time.google.com", "pool.ntp.org"])
        >>> print(f"Success: {result.success}")
    """

    def __init__(self,
                 timeout: float = DEFAULT_TIMEOUT,
                 max_workers: Optional[int] = None,
                 dns_cache: Optional[DNSCache] = None) -> None:
        """Initialize parallel NTP client.

        Args:
            timeout: Socket timeout for individual queries.
            max_workers: Maximum concurrent workers (defaults to CPU count).
            dns_cache: Optional DNS cache for address resolution.
        """
        self._timeout = timeout
        self._max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self._dns_cache = dns_cache or DNSCache()
        self._executor: Optional[ThreadPoolExecutor] = None
        self._executor_ref: Optional[weakref.ref] = None

    @property
    def executor(self) -> ThreadPoolExecutor:
        """Get or create thread pool executor."""
        if self._executor is None or self._executor._broken:
            self._executor = ThreadPoolExecutor(
                max_workers=self._max_workers,
                thread_name_prefix="NTPWorker"
            )
            # Keep weak reference to detect external shutdown
            self._executor_ref = weakref.ref(self._executor)
        assert self._executor is not None
        return self._executor

    def query_hosts_parallel(self,
                           hosts: Iterable[str],
                           attempts_per_host: int = DEFAULT_ATTEMPTS,
                           max_acceptable_delay: float = DEFAULT_MAX_ACCEPTABLE_DELAY,
                           stop_on_good_result: bool = True,
                           good_delay_threshold: float = 0.1) -> ParallelQueryResult:
        """Query multiple NTP hosts in parallel.

        Args:
            hosts: List of NTP server hostnames.
            attempts_per_host: Number of attempts per host.
            max_acceptable_delay: Maximum acceptable network delay.
            stop_on_good_result: Stop early if a result with low delay is found.
            good_delay_threshold: Delay threshold for "good" result.

        Returns:
            ParallelQueryResult with best response and statistics.
        """
        # Resolve all addresses first
        host_addresses: dict[str, list[AddressTuple]] = {}
        for host in hosts:
            addresses = self._resolve_host_addresses(host)
            if addresses:
                host_addresses[host] = addresses

        if not host_addresses:
            return ParallelQueryResult(False, None, [], [("No hosts resolved", Exception("DNS resolution failed"))])

        # Submit all queries
        futures_to_query: dict[Future, tuple[str, AddressTuple, int]] = {}
        query_id = 0

        for host, addresses in host_addresses.items():
            for attempt in range(attempts_per_host):
                for addr_info in addresses:
                    future = self.executor.submit(
                        self._query_single_address,
                        query_id,
                        host,
                        addr_info,
                        attempt
                    )
                    futures_to_query[future] = (host, addr_info, attempt)
                    query_id += 1

        # Collect results
        responses: list[NTPResponse] = []
        errors: list[NTPQueryResult] = []
        best_response: Optional[NTPResponse] = None
        good_result_found = False

        for future in as_completed(futures_to_query, timeout=self._timeout * 2):
            host, addr_info, attempt = futures_to_query[future]

            try:
                response = future.result()
                responses.append(response)

                # Update best response
                if (best_response is None or
                    response.delay < best_response.delay):
                    best_response = response

                # Check for early termination
                if (stop_on_good_result and
                    response.delay <= good_delay_threshold and
                    abs(response.offset) < 1.0):
                    good_result_found = True
                    break

            except Exception as e:
                errors.append((f"{host}:{addr_info[4][0]}", e))

        # Cancel remaining futures if we found a good result
        if good_result_found:
            for future in futures_to_query:
                if not future.done():
                    future.cancel()

        # Validate best response
        success = (best_response is not None and
                  best_response.delay <= max_acceptable_delay)

        return ParallelQueryResult(success, best_response, responses, errors)

    def _resolve_host_addresses(self, host: str) -> list[AddressTuple]:
        """Resolve host to address list using cache.

        Args:
            host: Hostname to resolve.

        Returns:
            List of address tuples.
        """
        # Check cache first
        cached = self._dns_cache.get(host)
        if cached:
            return cached

        # Resolve and cache
        try:
            addresses = socket.getaddrinfo(host, 123, 0, socket.SOCK_DGRAM)
            self._dns_cache.set(host, 123, addresses)  # type: ignore[arg-type]
            return addresses  # type: ignore[return-value]
        except socket.gaierror:
            self._dns_cache.set(host, 123, [])  # Cache failure
            return []

    def _query_single_address(self,
                            query_id: int,
                            host: str,
                            addr_info: AddressTuple,
                            attempt: int) -> NTPResponse:
        """Query a single address and return response.

        Args:
            query_id: Unique query identifier.
            host: Hostname being queried.
            addr_info: Address info tuple from getaddrinfo.
            attempt: Attempt number.

        Returns:
            NTPResponse with timing data.
        """
        family, socktype, proto, _, sockaddr = addr_info

        # Prepare NTP packet
        packet = bytearray(48)
        packet[0] = 0x23  # LI=0, VN=4, Mode=3

        # Capture timing
        timer = MonotonicTimeCalculator()
        t1_wall, t1_mono = timer.start_timing()

        # Pack transmit timestamp
        sec, frac = self._to_ntp(t1_wall)
        NTP_TIMESTAMP_STRUCT.pack_into(packet, 40, sec, frac)

        # Send and receive
        with socket.socket(family, socktype, proto) as sock:
            sock.settimeout(self._timeout)
            sock.sendto(packet, sockaddr)

            data, _ = sock.recvfrom(512)
            t4_mono = time.monotonic()

        # Validate response
        if len(data) < 48:
            raise ValueError("Short NTP response")

        # Unpack response using precompiled struct
        unpacked = NTP_PACKET_STRUCT.unpack(data[0:48])
        t2 = self._from_ntp(unpacked[8], unpacked[9])
        t3 = self._from_ntp(unpacked[10], unpacked[11])

        # Calculate delay and offset using monotonic timing
        delay, offset = timer.calculate_ntp_rtt(t1_wall, t2, t3, t4_mono, t1_mono)

        return NTPResponse(
            server_time=t3,
            offset=offset,
            delay=delay,
            host=host,
            address=sockaddr,
            attempt=attempt,
            timestamp=time.time()
        )

    def _to_ntp(self, ts: float) -> tuple[int, int]:
        """Convert POSIX timestamp to NTP format.

        Args:
            ts: POSIX timestamp.

        Returns:
            Tuple of (seconds, fraction).
        """
        ntp = ts + NTP_TO_UNIX
        sec = int(ntp)
        frac = int((ntp - sec) * (1 << 32))
        return sec, frac

    def _from_ntp(self, sec: int, frac: int) -> float:
        """Convert NTP timestamp to POSIX format.

        Args:
            sec: NTP seconds.
            frac: NTP fraction.

        Returns:
            POSIX timestamp.
        """
        return (sec + float(frac) / (1 << 32)) - NTP_TO_UNIX

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the thread pool executor.

        Args:
            wait: Whether to wait for pending tasks.
        """
        if self._executor:
            self._executor.shutdown(wait=wait)
            self._executor = None
            self._executor_ref = None


class FastDate64Encoder:
    """Optimized FastDate64 timestamp encoder/decoder.

    Provides high-performance 64-bit timestamp encoding with minimal CPU overhead.

    Example:
        >>> encoded = FastDate64Encoder.encode(1700000000.0)
        >>> decoded = FastDate64Encoder.decode(encoded)
        >>> print(f"Decoded: {decoded}")
    """

    @staticmethod
    def encode(ts: float) -> int:
        """Encode POSIX timestamp to 64-bit unsigned integer.

        Args:
            ts: POSIX timestamp in seconds (float).

        Returns:
            64-bit unsigned integer encoding of the timestamp.

        Raises:
            ValueError: If timestamp is negative.
            OverflowError: If timestamp is too large for encoding.
        """
        if ts < 0:
            raise ValueError("Negative timestamps not supported")

        sec = int(ts)
        frac = int((ts - sec) * FASTDATE_FRAC_SCALE)

        if sec > FASTDATE_SECONDS_MAX:
            raise OverflowError(f"Timestamp seconds {sec} too large for {FASTDATE_SECONDS_BITS}-bit field")

        return (sec << FASTDATE_FRAC_BITS) | (frac & (FASTDATE_FRAC_SCALE - 1))

    @staticmethod
    def decode(value: int) -> float:
        """Decode 64-bit unsigned integer to POSIX timestamp.

        Args:
            value: 64-bit unsigned integer encoding of timestamp.

        Returns:
            POSIX timestamp in seconds (float).
        """
        frac_mask = FASTDATE_FRAC_SCALE - 1
        sec = value >> FASTDATE_FRAC_BITS
        frac = value & frac_mask
        return float(sec) + (float(frac) / FASTDATE_FRAC_SCALE)

    @staticmethod
    def encode_safe(ts: float) -> int:
        """Safely encode timestamp with bounds checking.

        Args:
            ts: POSIX timestamp in seconds.

        Returns:
            Encoded timestamp or 0 if invalid.
        """
        try:
            return FastDate64Encoder.encode(ts)
        except (ValueError, OverflowError):
            return 0

    @staticmethod
    def decode_safe(value: int) -> float:
        """Safely decode timestamp with error handling.

        Args:
            value: 64-bit unsigned integer encoding.

        Returns:
            Decoded timestamp or 0.0 if invalid.
        """
        try:
            return FastDate64Encoder.decode(value)
        except (ValueError, OverflowError):
            return 0.0


class PerformanceMetrics:
    """Performance metrics collector for TimeSync operations.

    Tracks timing, success rates, and other performance indicators.

    Attributes:
        metrics: Internal metrics storage.

    Example:
        >>> metrics = PerformanceMetrics()
        >>> metrics.record_ntp_query("time.google.com", 0.05, True, 0.5)
        >>> summary = metrics.get_summary()
        >>> print(f"Success rate: {summary['success_rate']}")
    """

    def __init__(self) -> None:
        """Initialize performance metrics collector."""
        self._metrics: dict[str, Any] = {
            'ntp_queries': [],
            'dns_cache_hits': 0,
            'dns_cache_misses': 0,
            'parallel_queries': [],
            'fallback_usage': [],
            'errors': []
        }
        self._lock = threading.Lock()

    def record_ntp_query(self, host: str, delay: float, success: bool, duration: float) -> None:
        """Record NTP query metrics.

        Args:
            host: NTP server hostname.
            delay: Round-trip delay in seconds.
            success: Whether query was successful.
            duration: Query duration in seconds.
        """
        with self._lock:
            self._metrics['ntp_queries'].append({
                'host': host,
                'delay': delay,
                'success': success,
                'duration': duration,
                'timestamp': time.time()
            })

    def record_dns_cache_hit(self) -> None:
        """Record DNS cache hit."""
        with self._lock:
            self._metrics['dns_cache_hits'] += 1

    def record_dns_cache_miss(self) -> None:
        """Record DNS cache miss."""
        with self._lock:
            self._metrics['dns_cache_misses'] += 1

    def record_parallel_query(self, num_hosts: int, num_addresses: int,
                            success: bool, duration: float, best_delay: float) -> None:
        """Record parallel query metrics.

        Args:
            num_hosts: Number of hosts queried.
            num_addresses: Total number of addresses.
            success: Whether query was successful.
            duration: Total duration in seconds.
            best_delay: Best delay achieved.
        """
        with self._lock:
            self._metrics['parallel_queries'].append({
                'hosts': num_hosts,
                'addresses': num_addresses,
                'success': success,
                'duration': duration,
                'best_delay': best_delay,
                'timestamp': time.time()
            })

    def record_fallback_usage(self, method: str, duration: float) -> None:
        """Record fallback method usage.

        Args:
            method: Fallback method name.
            duration: Duration in seconds.
        """
        with self._lock:
            self._metrics['fallback_usage'].append({
                'method': method,
                'duration': duration,
                'timestamp': time.time()
            })

    def record_error(self, error_type: str, message: str) -> None:
        """Record error occurrence.

        Args:
            error_type: Type of error.
            message: Error message.
        """
        with self._lock:
            self._metrics['errors'].append({
                'type': error_type,
                'message': message,
                'timestamp': time.time()
            })

    def get_summary(self) -> dict[str, Any]:
        """Get performance metrics summary.

        Returns:
            Dictionary containing summary statistics.
        """
        with self._lock:
            metrics = self._metrics.copy()

        # Calculate summary statistics
        summary: dict[str, Any] = {
            'total_queries': len(metrics['ntp_queries']),
            'success_rate': 0.0,
            'avg_delay': 0.0,
            'avg_duration': 0.0,
            'dns_cache_hit_rate': 0.0,
            'total_parallel_queries': len(metrics['parallel_queries']),
            'fallback_count': len(metrics['fallback_usage']),
            'error_count': len(metrics['errors'])
        }

        if metrics['ntp_queries']:
            successful = [q for q in metrics['ntp_queries'] if q['success']]
            summary['success_rate'] = len(successful) / len(metrics['ntp_queries'])
            summary['avg_delay'] = sum(q['delay'] for q in successful) / len(successful) if successful else 0.0
            summary['avg_duration'] = sum(q['duration'] for q in metrics['ntp_queries']) / len(metrics['ntp_queries'])

        total_dns = metrics['dns_cache_hits'] + metrics['dns_cache_misses']
        if total_dns > 0:
            summary['dns_cache_hit_rate'] = metrics['dns_cache_hits'] / total_dns

        return summary


# Global instances for shared use
_global_dns_cache: DNSCache = DNSCache()
_global_metrics: PerformanceMetrics = PerformanceMetrics()


def get_global_dns_cache() -> DNSCache:
    """Get global DNS cache instance.

    Returns:
        Global DNSCache instance.
    """
    return _global_dns_cache


def get_global_metrics() -> PerformanceMetrics:
    """Get global metrics instance.

    Returns:
        Global PerformanceMetrics instance.
    """
    return _global_metrics


def clear_global_caches() -> None:
    """Clear all global caches."""
    _global_dns_cache.clear()


@contextmanager
def performance_timer(operation_name: str):
    """Context manager for timing operations and recording metrics.

    Args:
        operation_name: Name of the operation being timed.

    Yields:
        Timer context for manual control.

    Example:
        >>> with performance_timer("scan_files"):
        ...     pass
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start_time
        logger.debug(f"{operation_name} completed in {duration:.3f}s")
        get_global_metrics().record_error("performance", f"{operation_name}: {duration:.3f}s")
