"""
TimeSync Tool

Provides NTP-based time synchronization and FastDate64 timestamp encoding.
This tool ensures accurate, monotonic timekeeping for the NoDupeLabs system.

Features:
- NTP time synchronization using time.google.com and other servers
- FastDate64 64-bit timestamp encoding for compact storage
- Process-local corrected clock (no system clock changes)
- Background synchronization with configurable intervals
- Runtime enable/disable controls
- High-precision authenticated time retrieval with multi-layer fallback

Environment variables:
- NODUPE_TIMESYNC_ENABLED (default: 1)
- NODUPE_TIMESYNC_NO_NETWORK (default: 0)
- NODUPE_TIMESYNC_ALLOW_BG (default: 1)

Example usage:
    from nodupe.tools.time_sync import TimeSyncTool

    tool = TimeSyncTool()
    tool.enable()
    corrected_time = tool.get_corrected_time()
    compact_ts = tool.get_corrected_fast64()

    # Get authenticated time with multi-layer fallback
    authenticated_time = tool.get_authenticated_time()
    unix_timestamp = tool.get_authenticated_time(format="unix")
    human_readable = tool.get_authenticated_time(format="human")
"""

import socket as socket
from logging import getLogger

from .time_sync_tool import time_synchronizationTool as _time_sync_impl
from .time_sync_tool import logger as logger

# Backwards-compatible public name expected by tests and external callers
class TimeSyncTool(_time_sync_impl):
    """Compatibility wrapper exposing the historical `TimeSyncTool` name.

    Delegates all behavior to the underlying implementation but provides any
    missing abstract methods required by the `Tool` interface and preserves
    historical defaults expected by the test-suite.
    """

    def __init__(
        self,
        servers: Optional[Iterable[str]] | None = None,
        timeout: float = 3.0,
        attempts: int = 2,
        max_acceptable_delay: float = 0.5,
        smoothing_alpha: float = 0.3,
        **kwargs,
    ) -> None:
        # Historical default server list used by the test-suite
        default_servers = ["time.google.com", "time.cloudflare.com", "pool.ntp.org"]
        if servers is None:
            servers = default_servers
        super().__init__(
            servers=servers,
            timeout=timeout,
            attempts=attempts,
            max_acceptable_delay=max_acceptable_delay,
            smoothing_alpha=smoothing_alpha,
            **kwargs,
        )

    @property
    def name(self) -> str:
        # Historical public name (capitalized) expected by tests
        return "TimeSync"

    def describe_usage(self) -> str:  # concrete implementation required by Tool
        return (
            "TimeSyncTool - NTP-based time synchronization and FastDate64 helpers."
        )


__all__ = ["TimeSyncTool", "socket", "logger"]
