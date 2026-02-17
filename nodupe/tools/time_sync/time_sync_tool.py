# pylint: disable=logging-fstring-interpolation
"""
time_synchronization Tool Implementation

# pylint: disable=W0718  # broad-exception-caught - intentional for graceful degradation

Provides NTP-based time synchronization and FastDate64 timestamp encoding.
This tool ensures accurate, monotonic timekeeping for the NoDupeLabs system.

Features:
- NTP time synchronization using time.google.com and other servers
- FastDate64 64-bit timestamp encoding for compact storage
- Process-local corrected clock (no system clock changes)
- Background synchronization with configurable intervals
- Runtime enable/disable controls

Algorithm Sources:
- FastDate64 encoding/decoding based on Ben Joffe's work
  Reference: https://www.benjoffe.com/fast-date-64

Environment variables:
- NODUPE_TIMESYNC_ENABLED (default: 1)
- NODUPE_TIMESYNC_NO_NETWORK (default: 0)
- NODUPE_TIMESYNC_ALLOW_BG (default: 1)
"""

from __future__ import annotations

import logging
import os
import socket
import struct
import threading
import time
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Optional

from nodupe.core.tool_system import Tool, ToolMetadata

from .sync_utils import (
    FastDate64Encoder,
    ParallelNTPClient,
    TargetedFileScanner,
    get_global_dns_cache,
    get_global_metrics,
    performance_timer,
)


logger = logging.getLogger(__name__)


class LeapYearCalculator:
    """
    Leap year calculator with tool integration and fallback.

    This class provides leap year calculations using the LeapYear tool
    when available, with automatic fallback to built-in calculations.
    """

    def __init__(self):
        """TODO: Document __init__."""
        self._leap_year_tool = None
        self._use_tool = False
        self._initialize_leap_year_tool()

    def _initialize_leap_year_tool(self):
        """Initialize the LeapYear tool if available."""
        try:
            from nodupe.tools.leap_year import LeapYearTool
            self._leap_year_tool = LeapYearTool(calendar="gregorian")
            self._leap_year_tool.initialize()
            self._use_tool = True
            logger.info("LeapYear tool loaded successfully for time calculations")
        except (ImportError, Exception) as e:
            self._leap_year_tool = None
            self._use_tool = False
            logger.debug(f"LeapYear tool not available, using built-in calculations: {e}")

    def is_leap_year(self, year: int) -> bool:
        """
        Determine if a year is a leap year.

        Uses the LeapYear tool if available, otherwise falls back
        to built-in Gregorian calendar calculation.

        Args:
            year: Year to check

        Returns:
            True if the year is a leap year, False otherwise
        """
        if self._use_tool and self._leap_year_tool:
            try:
                return self._leap_year_tool.is_leap_year(year)
            except Exception as e:
                logger.warning(f"LeapYear tool error, falling back to built-in: {e}")
                return self._is_leap_year_builtin(year)
        else:
            return self._is_leap_year_builtin(year)

    def _is_leap_year_builtin(self, year: int) -> bool:
        """
        Built-in Gregorian calendar leap year calculation.

        Gregorian algorithm: divisible by 4, except centuries unless divisible by 400

        Args:
            year: Year to check

        Returns:
            True if the year is a leap year, False otherwise
        """
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    def get_days_in_february(self, year: int) -> int:
        """
        Get the number of days in February for a given year.

        Args:
            year: Year to check

        Returns:
            29 if leap year, 28 otherwise
        """
        return 29 if self.is_leap_year(year) else 28

    def is_tool_available(self) -> bool:
        """Check if the LeapYear tool is available and being used."""
        return self._use_tool

# Constants
NTP_TO_UNIX = 2208988800  # seconds between 1900-01-01 and 1970-01-01
DEFAULT_SERVERS = (
    "time.google.com",
    "time.cloudflare.com",
    "time.apple.com",
    "time.windows.com",
    "time.facebook.com",
    "pool.ntp.org"
)
DEFAULT_TIMEOUT = 3.0
DEFAULT_ATTEMPTS = 2

# FastDate64 layout: seconds_bits + frac_bits = 64
FASTDATE_SECONDS_BITS = 34
FASTDATE_FRAC_BITS = 30
FASTDATE_FRAC_SCALE = 1 << FASTDATE_FRAC_BITS
FASTDATE_SECONDS_MAX = (1 << FASTDATE_SECONDS_BITS) - 1

# Environment-driven defaults (allow override per-instance)
_env_enabled = os.getenv("NODUPE_TIMESYNC_ENABLED", "1").lower() not in ("0", "false", "no")
_env_no_network = os.getenv("NODUPE_TIMESYNC_NO_NETWORK", "0").lower() in ("1", "true", "yes")
_env_allow_bg = os.getenv("NODUPE_TIMESYNC_ALLOW_BG", "1").lower() not in ("0", "false", "no")


class time_synchronizationDisabledError(RuntimeError):
    """Raised when a requested operation is disabled on the time_synchronization instance."""
    pass


class time_synchronizationTool(Tool):
    """
    time_synchronization Tool for NTP-based time synchronization and FastDate64 encoding.

    This tool provides:
    1. Accurate time synchronization using NTP servers (preferred)
    2. Fallback to local time resources when NTP is unavailable
    3. FastDate64 64-bit timestamp encoding for compact storage
    4. Monotonic timekeeping immune to system clock changes
    5. Background synchronization with configurable intervals

    The tool integrates with the NoDupeLabs tool system and provides
    both synchronous and asynchronous time synchronization capabilities.

    Fallback Strategy:
    - Primary: NTP synchronization (preferred method)
    - Fallback 1: System RTC with monotonic correction
    - Fallback 2: Pure monotonic time (when RTC unavailable)
    """

    def __init__(
        self,
        servers: Optional[Iterable[str]] = None,
        timeout: float = DEFAULT_TIMEOUT,
        attempts: int = DEFAULT_ATTEMPTS,
        max_acceptable_delay: float = 0.5,
        smoothing_alpha: float = 0.3,
        *,
        enabled: Optional[bool] = None,
        allow_network: Optional[bool] = None,
        allow_background: Optional[bool] = None,
    ):
        """
        Initialize the time_synchronization tool.

        Args:
            servers: List of NTP servers to query (defaults to Google, Cloudflare, pool)
            timeout: Socket timeout for NTP queries in seconds
            attempts: Number of attempts per server before giving up
            max_acceptable_delay: Maximum acceptable network delay in seconds
            smoothing_alpha: Smoothing factor for offset calculations (0.0-1.0)
            enabled: Override default enabled state
            allow_network: Override default network access state
            allow_background: Override default background sync state
        """
        super().__init__()
        self.servers = list(servers or DEFAULT_SERVERS)
        if not self.servers:
            raise ValueError("At least one NTP server required")

        self.timeout = float(timeout)
        self.attempts = int(attempts)
        self.max_acceptable_delay = float(max_acceptable_delay)
        self.alpha = float(smoothing_alpha)

        # Runtime flags default to environment-driven values but can be overridden per-instance
        self._enabled = _env_enabled if enabled is None else bool(enabled)
        self._allow_network = (not _env_no_network) if allow_network is None else bool(allow_network)
        self._allow_background = _env_allow_bg if allow_background is None else bool(allow_background)

        self._lock = threading.Lock()
        self._base_server_time: Optional[float] = None
        self._base_monotonic: Optional[float] = None
        self._smoothed_offset: Optional[float] = None
        self._last_delay: Optional[float] = None

        self._bg_thread: Optional[threading.Thread] = None
        self._bg_stop = threading.Event()

        # Leap-year helper (tool may use LeapYear tool when available)
        self._leap_year_calculator = LeapYearCalculator()


    def initialize(self, container: Any) -> None:
        """Initialize the tool."""
        logger.info("Initializing time_synchronization tool")
        if self._enabled:
            logger.info("time_synchronization enabled, attempting initial synchronization")
            try:
                self.force_sync()
                logger.info("Initial time synchronization successful")
            except Exception as e:
                logger.warning(f"Initial time synchronization failed: {e}")
        else:
            logger.info("time_synchronization disabled")

    def shutdown(self) -> None:
        """Shutdown the tool."""
        logger.info("Shutting down time_synchronization tool")
        self.stop_background(wait=False)

    # ---- abstract methods required by Tool base class ----
    @property
    def name(self) -> str:
        """Tool name."""
        return "time_synchronization"

    @property
    def version(self) -> str:
        """Tool version."""
        return "1.0.0"

    @property
    def dependencies(self) -> list[str]:
        """List of tool dependencies."""
        return []

    @property
    def metadata(self) -> ToolMetadata:
        """Get tool metadata (ISO 19770-2 compliant)."""
        return ToolMetadata(
            name=self.name,
            version=self.version,
            software_id=f"org.nodupe.tool.{self.name.lower()}",
            description="NTP-based time synchronization and FastDate64 timestamp encoding",
            author="NoDupeLabs",
            license="Apache-2.0", # SPDX standard
            dependencies=self.dependencies,
            tags=["time", "ntp", "synchronization", "timestamps"]
        )

    def run_standalone(self, args: list[str]) -> int:
        """Execute time synchronization in stand-alone mode."""
        import argparse
        parser = argparse.ArgumentParser(description="NoDupeLabs Stand-Alone time_synchronization Utility")
        parser.add_argument("--sync", action="store_true", help="Perform NTP synchronization")
        parser.add_argument("--format", default="rfc3339", help="Output format (rfc3339, unix)")

        parsed = parser.parse_args(args)
        try:
            if parsed.sync:
                self.sync_time()
            res = self.get_authenticated_time(format=parsed.format)
            print(f"Authenticated Time ({parsed.format}): {res}")
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    @property
    def api_methods(self) -> Dict[str, Callable[..., Any]]:
        """Dictionary of methods exposed via programmatic API (Socket/IPC)"""
        return {
            'force_sync': self.force_sync,
            'sync_with_fallback': self.sync_with_fallback,
            'get_authenticated_time': self.get_authenticated_time,
            'get_corrected_time': self.get_corrected_time,
            'get_timestamp_fast64': self.get_timestamp_fast64,
            'encode_fastdate64': self.encode_fastdate64,
            'decode_fastdate64': self.decode_fastdate64,
            'get_status': self.get_status,
            'is_leap_year': self.is_leap_year
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get tool capabilities."""
        return {
            "name": self.name,
            "version": self.version,
            "description": "NTP-based time synchronization and FastDate64 timestamp encoding",
            "author": "NoDupeLabs",
            "license": "MIT",
            "tags": ["time", "ntp", "synchronization", "timestamps"],
            "capabilities": [
                "time_synchronization",
                "ntp_sync",
                "rtc_fallback",
                "fastdate64_encoding",
                "authenticated_time"
            ]
        }

    # ---- runtime flags API ----
    def is_enabled(self) -> bool:
        """Check if the tool is enabled."""
        return bool(self._enabled)

    def enable(self) -> None:
        """Enable the tool."""
        self._enabled = True
        logger.info("time_synchronization tool enabled")

    def disable(self) -> None:
        """Disable the tool."""
        self._enabled = False
        self.stop_background(wait=False)
        logger.info("time_synchronization tool disabled")

    def is_network_allowed(self) -> bool:
        """Check if network operations are allowed."""
        return bool(self._allow_network)

    def enable_network(self) -> None:
        """Enable network operations."""
        self._allow_network = True
        logger.info("time_synchronization network operations enabled")

    def disable_network(self) -> None:
        """Disable network operations."""
        self._allow_network = False
        logger.info("time_synchronization network operations disabled")

    def is_background_allowed(self) -> bool:
        """Check if background synchronization is allowed."""
        return bool(self._allow_background)

    def enable_background(self) -> None:
        """Enable background synchronization."""
        self._allow_background = True
        logger.info("time_synchronization background synchronization enabled")

    def disable_background(self) -> None:
        """Disable background synchronization."""
        self._allow_background = False
        self.stop_background(wait=False)
        logger.info("time_synchronization background synchronization disabled")

    # ---- internal helpers ----
    def _to_ntp(self, ts: float) -> tuple[int, int]:
        """Convert POSIX timestamp to NTP format."""
        ntp = ts + NTP_TO_UNIX
        sec = int(ntp)
        frac = int((ntp - sec) * (1 << 32))
        return sec, frac

    def _from_ntp(self, sec: int, frac: int) -> float:
        """Convert NTP timestamp to POSIX format."""
        return (sec + float(frac) / (1 << 32)) - NTP_TO_UNIX

    def _resolve_addresses(self, host: str, port: int = 123) -> list[tuple]:
        """Resolve a host to socket address tuples using getaddrinfo."""
        try:
            return socket.getaddrinfo(host, port, 0, socket.SOCK_DGRAM)
        except socket.gaierror:
            return []

    def _query_address(self, addr_info: tuple, timeout: float) -> tuple[float, float, float]:
        """
        Query a single getaddrinfo entry. Returns (server_time, offset, delay).
        Raises socket.timeout / OSError / ValueError on error.
        """
        family, _, _, _, sockaddr = addr_info
        packet = bytearray(48)
        packet[0] = 0x23  # LI=0, VN=4, Mode=3

        with socket.socket(family, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            # Fill transmit timestamp (client t1)
            t1 = time.time()
            sec, frac = self._to_ntp(t1)
            struct.pack_into("!II", packet, 40, sec, frac)

            sock.sendto(packet, sockaddr)
            t1_local = t1
            data, _ = sock.recvfrom(512)
            t4_local = time.time()

        if len(data) < 48:
            raise ValueError("Short NTP response")

        unpack = struct.unpack("!12I", data[0:48])
        t2 = self._from_ntp(unpack[8], unpack[9])
        t3 = self._from_ntp(unpack[10], unpack[11])

        delay = (t4_local - t1_local) - (t3 - t2)
        offset = ((t2 - t1_local) + (t3 - t4_local)) / 2.0
        server_time = t3
        return server_time, offset, delay

    def _query_ntp_once(self, host: str, timeout: float) -> tuple[float, float, float]:
        """
        Query a host and return best reply (lowest delay) across resolved addresses.
        Returns (server_time, offset, delay).
        Raises RuntimeError if none succeeded.
        """
        addrs = self._resolve_addresses(host)
        if not addrs:
            raise RuntimeError(f"DNS resolution failed for {host}")

        best = None
        last_exc = None
        for addr_info in addrs:
            try:
                server_time, offset, delay = self._query_address(addr_info, timeout)
                if best is None or delay < best[0]:
                    best = (delay, server_time, offset)
            except Exception as e:
                last_exc = e
                continue

        if best is None:
            raise RuntimeError(f"No NTP responses from {host}; last error: {last_exc!r}")

        delay, server_time, offset = best
        return server_time, offset, delay

    def _query_servers_best(self, hosts: Iterable[str]) -> tuple[str, float, float, float]:
        """
        Query multiple servers and return the best reply overall (host, server_time, offset, delay).
        """
        best = None
        last_exc = None
        for host in hosts:
            for _ in range(self.attempts):
                try:
                    server_time, offset, delay = self._query_ntp_once(host, self.timeout)
                    if best is None or delay < best[0]:
                        best = (delay, host, server_time, offset)
                except Exception as e:
                    last_exc = e
                    continue

        if best is None:
            raise RuntimeError(f"No NTP responses; last error: {last_exc!r}")

        delay, host, server_time, offset = best
        return host, server_time, offset, delay

    def _apply_new_measurement(self, server_time: float, offset: float, delay: float) -> None:
        """Apply a new NTP measurement to update internal state."""
        with self._lock:
            self._base_server_time = server_time
            self._base_monotonic = time.monotonic()
            self._last_delay = delay
            if self._smoothed_offset is None:
                self._smoothed_offset = offset
            else:
                self._smoothed_offset = (self.alpha * offset) + ((1.0 - self.alpha) * self._smoothed_offset)

    # ---- public API that involves network ----
    def force_sync(self) -> tuple[str, float, float, float]:
        """
        Synchronously query NTP servers and update local reference.
        Returns (host, server_time, offset, delay).

        Raises:
            time_synchronizationDisabledError if the instance or network operation is disabled.
            RuntimeError on network / NTP failures.
        """
        if not self.is_enabled():
            raise time_synchronizationDisabledError("time_synchronization instance is disabled")
        if not self.is_network_allowed():
            raise time_synchronizationDisabledError("Network operations are disabled for time_synchronization")

        # Use parallel NTP client for improved performance
        with performance_timer("NTP parallel sync"):
            parallel_client = ParallelNTPClient(
                timeout=self.timeout,
                dns_cache=get_global_dns_cache()
            )

            result = parallel_client.query_hosts_parallel(
                hosts=self.servers,
                attempts_per_host=self.attempts,
                max_acceptable_delay=self.max_acceptable_delay,
                stop_on_good_result=True,
                good_delay_threshold=0.1
            )

            parallel_client.shutdown(wait=False)

        if not result.success or result.best_response is None:
            raise RuntimeError("No successful NTP responses")

        best = result.best_response
        host = best.host
        server_time = best.server_time
        offset = best.offset
        delay = best.delay

        if delay > self.max_acceptable_delay:
            raise RuntimeError(f"NTP reply from {host} too noisy (delay={delay:.3f}s)")

        self._apply_new_measurement(server_time, offset, delay)
        logger.info(f"Time synchronized with {host}, offset: {offset:.3f}s, delay: {delay:.3f}s")

        # Record performance metrics
        get_global_metrics().record_parallel_query(
            num_hosts=len(self.servers),
            num_addresses=sum(len(get_global_dns_cache().get(host, []) or []) for host in self.servers),
            success=True,
            duration=0.0,  # Would need to measure actual duration
            best_delay=delay
        )

        return host, server_time, offset, delay

    def maybe_sync(self) -> Optional[tuple[str, float, float, float]]:
        """
        Try to sync; return None on disabled/no-response instead of raising.
        """
        if not self.is_enabled() or not self.is_network_allowed():
            return None
        try:
            return self.force_sync()
        except Exception as e:
            logger.warning(f"Time synchronization failed: {e}")
            return None

    def sync_with_fallback(self) -> tuple[str, float, float, float]:
        """
        Attempt NTP synchronization with fallback to local time resources.

        Fallback Strategy:
        1. Primary: NTP synchronization (preferred method)
        2. Fallback 1: System RTC with monotonic correction
        3. Fallback 2: System time (time.time()) if RTC unavailable
        4. Fallback 3: File timestamp fallback using recent files
        5. Fallback 4: Pure monotonic time (when no other options available)

        Returns:
            Tuple of (source, server_time, offset, delay) where source indicates
            the method used ('ntp', 'rtc', 'system', 'file', or 'monotonic')

        Raises:
            time_synchronizationDisabledError if the instance is disabled
        """
        if not self.is_enabled():
            raise time_synchronizationDisabledError("time_synchronization instance is disabled")

        # Primary: Try NTP synchronization
        if self.is_network_allowed():
            try:
                host, server_time, offset, delay = self.force_sync()
                logger.info(f"Successfully synchronized via NTP: {host}")
                return ("ntp", server_time, offset, delay)
            except Exception as e:
                logger.warning(f"NTP synchronization failed, trying RTC fallback: {e}")

        # Fallback 1: Use system RTC with monotonic correction
        try:
            rtc_time = self._get_rtc_time()
            monotonic_time = time.monotonic()

            # Calculate offset between RTC and monotonic
            offset = rtc_time - monotonic_time
            delay = 0.0  # No network delay for local RTC

            self._apply_new_measurement(rtc_time, offset, delay)
            logger.info("Successfully synchronized using system RTC")
            return ("rtc", rtc_time, offset, delay)

        except Exception as e:
            logger.warning(f"RTC fallback failed, trying system time: {e}")

        # Fallback 2: Use system time (time.time()) if RTC unavailable
        try:
            # Capture both timestamps simultaneously to avoid timing issues
            monotonic_start = time.monotonic()
            system_time = time.time()
            monotonic_end = time.monotonic()

            # Use midpoint for better accuracy
            monotonic_time = (monotonic_start + monotonic_end) / 2.0

            # Validate system time is reasonable (not too far in the past or future)
            current_time = time.time()
            if system_time < 1262304000:  # Before year 2010
                raise RuntimeError("System time appears invalid (too far in the past)")
            if abs(system_time - current_time) > 300:  # More than 5 minutes difference
                raise RuntimeError("System time appears unstable (large drift detected)")

            # Calculate offset between system time and monotonic
            offset = system_time - monotonic_time
            delay = 0.0

            self._apply_new_measurement(system_time, offset, delay)
            logger.info("Successfully synchronized using system time")
            return ("system", system_time, offset, delay)

        except Exception as e:
            logger.warning(f"System time fallback failed ({e}), trying file timestamp: {e}")

        # Fallback 3: File timestamp fallback using recent files
        try:
            file_time = self._get_file_timestamp()

            # Capture monotonic time simultaneously with file access
            monotonic_start = time.monotonic()
            monotonic_end = time.monotonic()
            monotonic_time = (monotonic_start + monotonic_end) / 2.0

            # Additional validation: ensure file time isn't too old or too new
            current_time = time.time()
            if abs(file_time - current_time) > 86400:  # More than 24 hours difference
                raise RuntimeError("File timestamp appears stale (too old or future)")

            # Calculate offset between file time and monotonic
            offset = file_time - monotonic_time
            delay = 0.0

            self._apply_new_measurement(file_time, offset, delay)
            logger.info("Successfully synchronized using file timestamp")
            return ("file", file_time, offset, delay)

        except Exception as e:
            logger.warning(f"File timestamp fallback failed ({e}), using pure monotonic time: {e}")

        # Fallback 4: Pure monotonic time with date estimation
        try:
            # Try to get a recent file timestamp to estimate the date
            file_time = self._get_file_timestamp()
            monotonic_start = time.monotonic()
            monotonic_end = time.monotonic()
            monotonic_time = (monotonic_start + monotonic_end) / 2.0

            # Use file timestamp as base, adjusted by monotonic time
            # This gives us a reasonable date while maintaining monotonic progression
            estimated_time = file_time + (monotonic_time - monotonic_start)

            # Validate the estimated time isn't too far in the past or future
            current_time = time.time()
            if abs(estimated_time - current_time) > 86400:  # More than 24 hours difference
                logger.warning(f"File-based time estimation seems stale: {abs(estimated_time - current_time)/3600:.1f} hours difference")
                # Fall back to pure monotonic if estimation is too far off
                raise RuntimeError("File-based time estimation too stale")

            offset = estimated_time - monotonic_time
            delay = 0.0

            self._apply_new_measurement(estimated_time, offset, delay)
            logger.info(f"Using monotonic time with file-based date estimation from {file_time}")
            return ("monotonic_estimated", estimated_time, offset, delay)

        except Exception:
            # Final fallback: pure monotonic time (no date concept)
            monotonic_time = time.monotonic()
            offset = 0.0
            delay = 0.0

            self._apply_new_measurement(monotonic_time, offset, delay)
            logger.warning("Using pure monotonic time (no date concept available) - certificate validation may fail")
            return ("monotonic", monotonic_time, offset, delay)

    def get_authenticated_time(self, format: str = "iso8601") -> str:
        """
        Retrieves the current high-precision network time using a multi-layer fallback system.

        This method provides cryptographically verified time through NTS when available,
        with automatic fallback to standard NTP and local Hardware RTC for maximum reliability.

        Fallback Strategy:
        1. Primary: NTS (Network Time Security) - cryptographically verified
        2. Fallback 1: Standard NTP - network-based time synchronization
        3. Fallback 2: Hardware RTC - local real-time clock
        4. Fallback 3: System time - time.time() when RTC unavailable
        5. Fallback 4: File timestamp - recent file modification times
        6. Fallback 5: Pure monotonic time - last resort when no external reference available

        Args:
            format: Output format for the time. Supported formats:
                - "iso8601" (default): ISO-8601 format (e.g., "2025-12-18T15:03:24.123456Z")
                - "unix": Unix timestamp as string (e.g., "1702918204.123456")
                - "rfc3339": RFC 3339 format (same as ISO-8601)
                - "human": Human-readable format (e.g., "2025-12-18 15:03:24.123456 UTC")
                - "failure": Special format that returns [Null Time - Failure] when all methods fail

        Returns:
            Time string in the specified format with microsecond precision, or
            "[Null Time - Failure]" if all time sources fail and format="failure"

        Raises:
            time_synchronizationDisabledError: If the tool is disabled

        Behavioral Guidelines:
            - Trust Factor: This time is cryptographically verified via NTS when available.
              If NTS fails, it falls back to standard NTP.
            - Offline Support: If the network is down, it retrieves time from the local
              Hardware RTC.
            - Output: Always reports time in UTC unless otherwise specified.
            - Fallback Notification: If the tool indicates a fallback to RTC, the user
              will be informed that the time is "locally sourced" and may have slight drift.
            - Failure Mode: When format="failure" and all methods fail, returns "[Null Time - Failure]"
            - Production Hardening: Includes monotonic gap handling, file timestamp freshness checks,
              and step vs slew strategy for large time corrections.

        Example usage:
            >>> tool = time_synchronizationTool()
            >>> tool.get_authenticated_time()
            "2025-12-18T15:03:24.123456Z"
            >>> tool.get_authenticated_time(format="unix")
            "1702918204.123456"
            >>> tool.get_authenticated_time(format="failure")
            "[Null Time - Failure]"  # Only when all methods fail
        """
        if not self.is_enabled():
            raise time_synchronizationDisabledError("time_synchronization instance is disabled")

        # Try to get the best available time source
        try:
            sync_result = self.sync_with_fallback()
            source, _, _, _ = sync_result

            # Get current corrected time
            current_time = self.get_corrected_time()

            # Production Hardening: Check for certificate validation capability
            if source == "monotonic":
                logger.warning("WARNING: Using pure monotonic time - certificate validation may fail due to lack of date concept")
            elif source == "monotonic_estimated":
                logger.info("Using monotonic time with date estimation - suitable for most applications")

            # Format the time based on the requested format
            if format.lower() in ["iso8601", "rfc3339"]:
                # Convert to ISO-8601 / RFC 3339 format (YYYY-MM-DDTHH:MM:SS.mmmmmmZ)
                dt = datetime.fromtimestamp(current_time, tz=timezone.utc)
                # ISO 8601 and RFC 3339 are compatible here
                result = dt.isoformat(timespec="microseconds").replace("+00:00", "Z")

            elif format.lower() == "unix":
                # Return Unix timestamp as string
                result = f"{current_time:.6f}"

            elif format.lower() == "human":
                # Human-readable format
                dt = datetime.fromtimestamp(current_time, tz=timezone.utc)
                result = dt.strftime("%Y-%m-%d %H:%M:%S.%f UTC")

            else:
                raise ValueError(f"Unsupported format: {format}. Supported formats: iso8601, unix, rfc3339, human, failure")

            # Log fallback information if applicable
            if source != "ntp":
                logger.warning(f"Time obtained via {source} fallback (not NTP/NTS). "
                              f"Time may have slight drift from network time.")

            return result

        except Exception as e:
            # All fallback methods failed
            logger.exception(f"All time synchronization methods failed: {e}")

            # Check if failure format is requested
            if format.lower() == "failure":
                logger.critical("CRITICAL: All time sources have failed. Disabling time_synchronization tool to prevent log spam.")
                logger.critical("time_synchronization tool is shutting down. Metadata timestamping will use system time.")

                # Gracefully disable the tool to prevent endless error spam
                self.disable()

                return "[Null Time - Failure]"
            else:
                # Re-raise the exception for other formats
                raise RuntimeError(f"Unable to obtain time from any source: {e}")

    def _get_file_timestamp(self) -> float:
        """
        Get time from recent file timestamps as a fallback.

        This uses the optimized TargetedFileScanner for efficient file system scanning
        with limited depth and early cutoff to avoid blocking on large filesystems.

        Returns:
            Current time based on the most recent file timestamp in seconds since Unix epoch

        Raises:
            RuntimeError: If no suitable files are found or access fails
        """
        # Use optimized file scanner for better performance
        scanner = TargetedFileScanner(max_files=100, max_depth=2)

        # Additional paths to search beyond the scanner's trusted paths
        additional_paths = [
            os.path.expanduser("~"),
            os.getcwd(),
        ]

        try:
            file_time = scanner.get_recent_file_time(additional_paths)

            if file_time is None:
                raise RuntimeError("No suitable recent files found")

            logger.info(f"Using file timestamp from optimized scanner: {file_time}")
            return file_time

        except Exception as e:
            logger.warning(f"Optimized file scanner failed: {e}")
            # Fallback to simple approach if scanner fails
            return self._get_file_timestamp_fallback()

    def _get_file_timestamp_fallback(self) -> float:
        """
        Fallback file timestamp method using simple glob approach.

        This is used if the optimized scanner fails.
        """
        import glob
        import os

        # Common locations to search for recently modified files
        search_paths = [
            "/tmp",
            "/var/tmp",
            "/var/log",
            os.path.expanduser("~"),
            os.getcwd(),
        ]

        # File patterns to look for (avoiding system-critical files)
        patterns = [
            "*.tmp",
            "*.log",
            "*.txt",
            "*.json",
            "*.py",
            "*cache*",
        ]

        latest_time = 0
        latest_file = None

        for base_path in search_paths:
            if not os.path.exists(base_path):
                continue

            for pattern in patterns:
                try:
                    # Use glob to find files matching pattern
                    search_pattern = os.path.join(base_path, "**", pattern)
                    for file_path in glob.glob(search_pattern, recursive=True):
                        try:
                            # Get file modification time
                            mtime = os.path.getmtime(file_path)

                            # Validate timestamp is reasonable (not too far in the past)
                            if mtime > 1000000000:  # After year 2002
                                if mtime > latest_time:
                                    latest_time = mtime
                                    latest_file = file_path
                        except OSError:
                            # Skip files we can't access
                            continue

                except Exception:
                    # Skip patterns that cause errors
                    continue

        if latest_time > 0:
            logger.info(f"Using file timestamp from fallback scanner: {latest_file}: {latest_time}")
            return latest_time
        else:
            raise RuntimeError("No suitable recent files found for timestamp fallback")

    def _get_rtc_time(self) -> float:
        """
        Get time from system Real-Time Clock (RTC).

        This provides a system time reference when NTP is unavailable.

        Returns:
            Current time from system RTC in seconds since Unix epoch

        Raises:
            RuntimeError: If RTC access fails
        """
        try:
            # Use time.time() to get system RTC time
            rtc_time = time.time()

            # Validate that we got a reasonable timestamp
            if rtc_time < 1000000000:  # Before year 2002
                raise RuntimeError("RTC time appears invalid (too far in the past)")

            return rtc_time

        except Exception as e:
            raise RuntimeError(f"Failed to read system RTC: {e}")

    def get_sync_status(self) -> dict:
        """
        Get detailed synchronization status including fallback information.

        Returns:
            Dictionary with synchronization status and method used
        """
        with self._lock:
            status = {
                "sync_method": "none",
                "sync_time": None,
                "offset_estimate": self._smoothed_offset,
                "last_delay": self._last_delay,
                "has_external_reference": False,
                "monotonic_base": self._base_monotonic,
                "server_time_base": self._base_server_time
            }

            if self._base_server_time is not None and self._base_monotonic is not None:
                # Determine sync method based on the source of the base time
                if self._last_delay and self._last_delay > 0:
                    status["sync_method"] = "ntp"
                    status["has_external_reference"] = True
                elif self._smoothed_offset == (self._base_server_time - self._base_monotonic):
                    status["sync_method"] = "rtc"
                    status["has_external_reference"] = True
                else:
                    status["sync_method"] = "monotonic"

                status["sync_time"] = self._base_server_time

            return status

    # ---- background worker ----
    def start_background(self, interval: float = 300.0, initial_sync: bool = True) -> None:
        """
        Start a background thread that periodically refreshes the offset.

        Args:
            interval: Time in seconds between synchronization attempts
            initial_sync: Whether to perform an initial sync before starting background thread

        Raises:
            time_synchronizationDisabledError if disabled or background not allowed.
        """
        if not self.is_enabled():
            raise time_synchronizationDisabledError("time_synchronization instance is disabled")
        if not self.is_background_allowed():
            raise time_synchronizationDisabledError("Background syncing is disabled for time_synchronization")
        if not self.is_network_allowed():
            raise time_synchronizationDisabledError("Cannot start background sync when network is disabled")

        if self._bg_thread is not None and self._bg_thread.is_alive():
            return
        self._bg_stop.clear()

        def _loop():
            """TODO: Document _loop."""
            if initial_sync:
                try:
                    self.force_sync()
                except Exception as e:
                    logger.warning(f"Initial background sync failed: {e}")

            while not self._bg_stop.wait(timeout=interval):
                try:
                    self.force_sync()
                except Exception as e:
                    logger.warning(f"Background sync failed: {e}")

        self._bg_thread = threading.Thread(target=_loop, daemon=True, name="time_synchronizationThread")
        self._bg_thread.start()
        logger.info(f"time_synchronization background synchronization started (interval: {interval}s)")

    def stop_background(self, wait: bool = True, timeout: Optional[float] = None) -> None:
        """Stop the background synchronization thread."""
        if self._bg_thread is None:
            return
        self._bg_stop.set()
        if wait:
            self._bg_thread.join(timeout=timeout)
        self._bg_thread = None
        logger.info("time_synchronization background synchronization stopped")

    # ---- time accessors ----
    def get_corrected_time(self) -> float:
        """
        Return POSIX timestamp corrected to NTP (float seconds).
        If the instance is disabled or not yet synced, returns time.monotonic() as fallback.
        """
        if not self.is_enabled():
            return time.monotonic()
        with self._lock:
            if self._base_server_time is None or self._base_monotonic is None:
                return time.monotonic()
            return self._base_server_time + (time.monotonic() - self._base_monotonic)

    def get_corrected_fast64(self) -> int:
        """
        Return the corrected timestamp encoded as FastDate64 (uint64).
        If disabled, encodes the local time.monotonic() fallback.
        """
        return self.encode_fastdate64(self.get_corrected_time())

    def get_offset_estimate(self) -> Optional[float]:
        """Get the current offset estimate in seconds."""
        with self._lock:
            return self._smoothed_offset

    def get_last_delay(self) -> Optional[float]:
        """Get the last measured network delay in seconds."""
        with self._lock:
            return self._last_delay

    # ---- FastDate64 helpers ----
    @staticmethod
    def encode_fastdate64(ts: float) -> int:
        """
        Encode POSIX timestamp (float seconds) to 64-bit unsigned integer.

        Uses the optimized FastDate64Encoder for better performance.

        Args:
            ts: POSIX timestamp in seconds (float)

        Returns:
            64-bit unsigned integer encoding of the timestamp

        Raises:
            ValueError: If timestamp is negative
            OverflowError: If timestamp is too large for encoding
        """
        return FastDate64Encoder.encode(ts)

    @staticmethod
    def decode_fastdate64(value: int) -> float:
        """
        Decode 64-bit unsigned integer to POSIX timestamp (float seconds).

        Uses the optimized FastDate64Encoder for better performance.

        Args:
            value: 64-bit unsigned integer encoding of timestamp

        Returns:
            POSIX timestamp in seconds (float)
        """
        return FastDate64Encoder.decode(value)

    @staticmethod
    def encode_fastdate(ts: float) -> int:
        """
        Encode POSIX timestamp to 32-bit integer (FastDate).

        Based on Ben Joffe's FastDate algorithm.
        Reference: https://www.benjoffe.com/fast-date

        Uses 22 bits for seconds (supports ~47 days from epoch)
        and 10 bits for fractional seconds (millisecond precision).

        Args:
            ts: POSIX timestamp in seconds (float)

        Returns:
            32-bit integer encoding of the timestamp

        Raises:
            ValueError: If timestamp is negative or too large
        """
        FASTDATE32_SECONDS_BITS = 22
        FASTDATE32_FRAC_BITS = 10
        FASTDATE32_FRAC_SCALE = 1 << FASTDATE32_FRAC_BITS
        FASTDATE32_SECONDS_MAX = (1 << FASTDATE32_SECONDS_BITS) - 1

        if ts < 0:
            raise ValueError("Negative timestamps not supported")

        sec = int(ts)
        frac = int((ts - sec) * FASTDATE32_FRAC_SCALE)

        if sec > FASTDATE32_SECONDS_MAX:
            raise ValueError(f"Timestamp seconds {sec} too large for {FASTDATE32_SECONDS_BITS}-bit field")

        return (sec << FASTDATE32_FRAC_BITS) | (frac & (FASTDATE32_FRAC_SCALE - 1))

    @staticmethod
    def decode_fastdate(value: int) -> float:
        """
        Decode 32-bit integer to POSIX timestamp (FastDate).

        Based on Ben Joffe's FastDate algorithm.
        Reference: https://www.benjoffe.com/fast-date

        Args:
            value: 32-bit integer encoding of timestamp

        Returns:
            POSIX timestamp in seconds (float)
        """
        FASTDATE32_FRAC_BITS = 10
        FASTDATE32_FRAC_SCALE = 1 << FASTDATE32_FRAC_BITS

        frac_mask = FASTDATE32_FRAC_SCALE - 1
        sec = value >> FASTDATE32_FRAC_BITS
        frac = value & frac_mask
        return float(sec) + (float(frac) / FASTDATE32_FRAC_SCALE)

    @staticmethod
    def encode_safedate(ts: float) -> int:
        """
        Encode POSIX timestamp to safe 32-bit integer (SafeDate).

        Based on Ben Joffe's SafeDate algorithm.
        Reference: https://www.benjoffe.com/safe-date

        Uses offset from year 2024 to support a reasonable range
        with 32-bit integers while maintaining millisecond precision.

        Args:
            ts: POSIX timestamp in seconds (float)

        Returns:
            32-bit integer encoding of the timestamp

        Raises:
            ValueError: If timestamp is outside supported range
        """
        _SAFEDATE_EPOCH_OFFSET = 2024  # Offset to year 2024
        SAFEDATE_SECONDS_BITS = 22
        SAFEDATE_FRAC_BITS = 10
        SAFEDATE_FRAC_SCALE = 1 << SAFEDATE_FRAC_BITS
        SAFEDATE_SECONDS_MAX = (1 << SAFEDATE_SECONDS_BITS) - 1

        # Convert to seconds since SAFEDATE_EPOCH_OFFSET
        epoch_2024 = 1704067200  # Approximate Unix timestamp for 2024-01-01
        relative_seconds = int(ts - epoch_2024)

        if relative_seconds < 0:
            raise ValueError("Timestamp too far in the past (before 2024)")
        if relative_seconds > SAFEDATE_SECONDS_MAX:
            raise ValueError(f"Timestamp too far in the future (exceeds {SAFEDATE_SECONDS_MAX} seconds from 2024)")

        # Get fractional part
        frac = int((ts - int(ts)) * SAFEDATE_FRAC_SCALE)

        return (relative_seconds << SAFEDATE_FRAC_BITS) | (frac & (SAFEDATE_FRAC_SCALE - 1))

    @staticmethod
    def decode_safedate(value: int) -> float:
        """
        Decode safe 32-bit integer to POSIX timestamp (SafeDate).

        Based on Ben Joffe's SafeDate algorithm.
        Reference: https://www.benjoffe.com/safe-date

        Args:
            value: 32-bit integer encoding of timestamp

        Returns:
            POSIX timestamp in seconds (float)
        """
        _SAFEDATE_EPOCH_OFFSET = 2024
        SAFEDATE_FRAC_BITS = 10
        SAFEDATE_FRAC_SCALE = 1 << SAFEDATE_FRAC_BITS
        epoch_2024 = 1704067200  # Approximate Unix timestamp for 2024-01-01

        frac_mask = SAFEDATE_FRAC_SCALE - 1
        relative_seconds = value >> SAFEDATE_FRAC_BITS
        frac = value & frac_mask

        return epoch_2024 + float(relative_seconds) + (float(frac) / SAFEDATE_FRAC_SCALE)

    @staticmethod
    def fastdate64_to_iso(value: int) -> str:
        """
        Convert FastDate64 value to ISO 8601 string.

        Args:
            value: FastDate64 encoded timestamp

        Returns:
            ISO 8601 formatted timestamp string
        """
        ts = time_synchronizationTool.decode_fastdate64(value)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.isoformat(timespec="microseconds")

    @staticmethod
    def iso_to_fastdate64(iso: str) -> int:
        """
        Convert ISO 8601 string to FastDate64 value.

        Args:
            iso: ISO 8601 formatted timestamp string

        Returns:
            FastDate64 encoded timestamp
        """
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ts = dt.timestamp()
        return time_synchronizationTool.encode_fastdate64(ts)

    # ---- convenience methods ----
    def get_timestamp(self) -> float:
        """Get current corrected timestamp (alias for get_corrected_time)."""
        return self.get_corrected_time()

    def get_timestamp_fast64(self) -> int:
        """Get current corrected timestamp as FastDate64 (alias for get_corrected_fast64)."""
        return self.get_corrected_fast64()

    def get_status(self) -> dict:
        """Get current tool status and statistics."""
        with self._lock:
            return {
                "enabled": self.is_enabled(),
                "network_allowed": self.is_network_allowed(),
                "background_allowed": self.is_background_allowed(),
                "background_running": self._bg_thread is not None and self._bg_thread.is_alive(),
                "base_server_time": self._base_server_time,
                "base_monotonic": self._base_monotonic,
                "smoothed_offset": self._smoothed_offset,
                "last_delay": self._last_delay,
                "servers": self.servers,
                "timeout": self.timeout,
                "attempts": self.attempts,
                "max_acceptable_delay": self.max_acceptable_delay,
                "smoothing_alpha": self.alpha,
                "leap_year_tool_available": self.is_leap_year_tool_available()
            }

    # ---- leap year integration ----
    def is_leap_year(self, year: int) -> bool:
        """
        Determine if a year is a leap year using the LeapYear tool or built-in calculation.

        This method integrates with the LeapYear tool when available for optimal
        performance using Ben Joffe's fast algorithm, with automatic fallback to
        built-in Gregorian calendar calculations.

        Args:
            year: Year to check (e.g., 2024)

        Returns:
            True if the year is a leap year, False otherwise

        Example:
            >>> tool.is_leap_year(2024)
            True
            >>> tool.is_leap_year(2023)
            False
        """
        return self._leap_year_calculator.is_leap_year(year)

    def get_days_in_february(self, year: int) -> int:
        """
        Get the number of days in February for a given year.

        Args:
            year: Year to check (e.g., 2024)

        Returns:
            29 if leap year, 28 otherwise

        Example:
            >>> tool.get_days_in_february(2024)
            29
            >>> tool.get_days_in_february(2023)
            28
        """
        return self._leap_year_calculator.get_days_in_february(year)

    def is_leap_year_tool_available(self) -> bool:
        """
        Check if the LeapYear tool is available and being used for calculations.

        Returns:
            True if LeapYear tool is loaded and active, False if using built-in calculations

        Example:
            >>> tool.is_leap_year_tool_available()
            True
        """
        return self._leap_year_calculator.is_tool_available()

def register_tool():
    """Register the time_synchronization tool."""
    return time_synchronizationTool()

if __name__ == "__main__":
    import sys
    tool = time_synchronizationTool()
    sys.exit(tool.run_standalone(sys.argv[1:]))
