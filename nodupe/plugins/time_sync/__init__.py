"""
TimeSync Plugin

Provides NTP-based time synchronization and FastDate64 timestamp encoding.
This plugin ensures accurate, monotonic timekeeping for the NoDupeLabs system.

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
    from nodupe.plugins.time_sync import TimeSyncPlugin
    
    plugin = TimeSyncPlugin()
    plugin.enable()
    corrected_time = plugin.get_corrected_time()
    compact_ts = plugin.get_corrected_fast64()
    
    # Get authenticated time with multi-layer fallback
    authenticated_time = plugin.get_authenticated_time()
    unix_timestamp = plugin.get_authenticated_time(format="unix")
    human_readable = plugin.get_authenticated_time(format="human")
"""

from .time_sync import TimeSyncPlugin

__all__ = ["TimeSyncPlugin"]
