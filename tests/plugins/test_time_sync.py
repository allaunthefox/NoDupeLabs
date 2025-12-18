"""
Tests for TimeSync Plugin

Tests the NTP-based time synchronization and FastDate64 timestamp encoding functionality.
These tests mock network operations to avoid real UDP calls and ensure reliable testing.
"""

import time
import threading
from unittest.mock import patch, MagicMock
import pytest
from datetime import datetime, timezone

from nodupe.plugins.time_sync import TimeSyncPlugin


class TestTimeSyncPlugin:
    """Test suite for TimeSyncPlugin."""

    def test_plugin_metadata(self):
        """Test that plugin metadata is correctly defined."""
        plugin = TimeSyncPlugin()
        metadata = plugin.metadata
        
        assert metadata.name == "TimeSync"
        assert metadata.version == "1.0.0"
        assert "NTP-based" in metadata.description
        assert "FastDate64" in metadata.description
        assert "time" in metadata.tags
        assert "ntp" in metadata.tags

    def test_initialization_defaults(self):
        """Test plugin initialization with default values."""
        plugin = TimeSyncPlugin()
        
        assert plugin.servers == ["time.google.com", "time.cloudflare.com", "pool.ntp.org"]
        assert plugin.timeout == 3.0
        assert plugin.attempts == 2
        assert plugin.max_acceptable_delay == 0.5
        assert plugin.alpha == 0.3

    def test_initialization_custom_values(self):
        """Test plugin initialization with custom values."""
        plugin = TimeSyncPlugin(
            servers=["custom.ntp.com"],
            timeout=5.0,
            attempts=3,
            max_acceptable_delay=1.0,
            smoothing_alpha=0.5
        )
        
        assert plugin.servers == ["custom.ntp.com"]
        assert plugin.timeout == 5.0
        assert plugin.attempts == 3
        assert plugin.max_acceptable_delay == 1.0
        assert plugin.alpha == 0.5

    def test_runtime_flags_initial_state(self):
        """Test initial state of runtime flags."""
        plugin = TimeSyncPlugin()
        
        # These depend on environment variables, so we just check they're booleans
        assert isinstance(plugin.is_enabled(), bool)
        assert isinstance(plugin.is_network_allowed(), bool)
        assert isinstance(plugin.is_background_allowed(), bool)

    def test_enable_disable_plugin(self):
        """Test enabling and disabling the plugin."""
        plugin = TimeSyncPlugin(enabled=False)
        
        assert not plugin.is_enabled()
        
        plugin.enable()
        assert plugin.is_enabled()
        
        plugin.disable()
        assert not plugin.is_enabled()

    def test_network_operations_control(self):
        """Test enabling and disabling network operations."""
        plugin = TimeSyncPlugin(allow_network=False)
        
        assert not plugin.is_network_allowed()
        
        plugin.enable_network()
        assert plugin.is_network_allowed()
        
        plugin.disable_network()
        assert not plugin.is_network_allowed()

    def test_background_sync_control(self):
        """Test enabling and disabling background synchronization."""
        plugin = TimeSyncPlugin(allow_background=False)
        
        assert not plugin.is_background_allowed()
        
        plugin.enable_background()
        assert plugin.is_background_allowed()
        
        plugin.disable_background()
        assert not plugin.is_background_allowed()

    def test_encode_decode_fastdate64_roundtrip(self):
        """Test FastDate64 encoding and decoding roundtrip."""
        # Test with various timestamps
        test_timestamps = [
            1672531200.123456,  # 2023-01-01T00:00:00.123456Z
            0.0,                # Unix epoch
            1000000000.0,       # 2001-09-09T01:46:40Z
            time.time(),        # Current time
        ]
        
        for ts in test_timestamps:
            encoded = TimeSyncPlugin.encode_fastdate64(ts)
            decoded = TimeSyncPlugin.decode_fastdate64(encoded)
            
            # Allow small rounding error due to fractional truncation
            assert abs(decoded - ts) < 1e-6, f"Roundtrip failed for {ts}"

    def test_encode_fastdate64_negative_timestamp(self):
        """Test that negative timestamps raise ValueError."""
        with pytest.raises(ValueError, match="Negative timestamps not supported"):
            TimeSyncPlugin.encode_fastdate64(-1.0)

    def test_encode_fastdate64_overflow(self):
        """Test that timestamps too large for encoding raise OverflowError."""
        # Use a timestamp that would exceed FASTDATE_SECONDS_BITS
        large_ts = (1 << 34)  # Exceeds 34-bit seconds field
        
        with pytest.raises(OverflowError, match="too large for.*bit field"):
            TimeSyncPlugin.encode_fastdate64(large_ts)

    def test_fastdate64_to_iso_conversion(self):
        """Test FastDate64 to ISO 8601 string conversion."""
        ts = 1672531200.123456  # 2023-01-01T00:00:00.123456Z
        encoded = TimeSyncPlugin.encode_fastdate64(ts)
        iso_string = TimeSyncPlugin.fastdate64_to_iso(encoded)
        
        # Parse the ISO string back to timestamp
        dt = datetime.fromisoformat(iso_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        decoded_ts = dt.timestamp()
        
        assert abs(decoded_ts - ts) < 1e-6

    def test_iso_to_fastdate64_conversion(self):
        """Test ISO 8601 string to FastDate64 conversion."""
        iso_string = "2023-01-01T00:00:00.123456+00:00"
        encoded = TimeSyncPlugin.iso_to_fastdate64(iso_string)
        decoded = TimeSyncPlugin.decode_fastdate64(encoded)
        
        # Parse the original ISO string to timestamp
        dt = datetime.fromisoformat(iso_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        original_ts = dt.timestamp()
        
        assert abs(decoded - original_ts) < 1e-6

    def test_disabled_behavior_fallback(self):
        """Test that disabled plugin falls back to time.monotonic()."""
        plugin = TimeSyncPlugin(enabled=False)
        
        # Should not raise and should return a float
        result = plugin.get_corrected_time()
        assert isinstance(result, float)
        
        # Should return a valid FastDate64 encoded timestamp
        fast64 = plugin.get_corrected_fast64()
        assert isinstance(fast64, int)
        
        # Should raise when trying to sync
        with pytest.raises(TimeSyncPlugin._get_exception_class()):
            plugin.force_sync()

    @patch('nodupe.plugins.time_sync.socket.getaddrinfo')
    @patch('nodupe.plugins.time_sync.TimeSyncPlugin._query_address')
    def test_force_sync_success(self, mock_query_address, mock_getaddrinfo):
        """Test successful NTP synchronization."""
        # Mock DNS resolution
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_DGRAM, 17, '', ('1.1.1.1', 123))
        ]
        
        # Mock NTP response
        server_time = 1600000000.5
        offset = 0.25
        delay = 0.01
        mock_query_address.return_value = (server_time, offset, delay)
        
        plugin = TimeSyncPlugin(servers=["test.ntp.com"], enabled=True, allow_network=True)
        
        result = plugin.force_sync()
        
        assert result[0] == "test.ntp.com"
        assert result[1] == server_time
        assert result[2] == offset
        assert result[3] == delay
        
        # Verify that internal state was updated
        assert plugin.get_offset_estimate() is not None
        assert plugin.get_last_delay() == delay

    @patch('nodupe.plugins.time_sync.socket.getaddrinfo')
    def test_force_sync_disabled_network(self, mock_getaddrinfo):
        """Test that force_sync raises when network is disabled."""
        plugin = TimeSyncPlugin(allow_network=False)
        
        with pytest.raises(TimeSyncPlugin._get_exception_class(), match="Network operations are disabled"):
            plugin.force_sync()

    @patch('nodupe.plugins.time_sync.socket.getaddrinfo')
    def test_force_sync_disabled_plugin(self, mock_getaddrinfo):
        """Test that force_sync raises when plugin is disabled."""
        plugin = TimeSyncPlugin(enabled=False)
        
        with pytest.raises(TimeSyncPlugin._get_exception_class(), match="TimeSync instance is disabled"):
            plugin.force_sync()

    @patch('nodupe.plugins.time_sync.socket.getaddrinfo')
    @patch('nodupe.plugins.time_sync.TimeSyncPlugin._query_address')
    def test_force_sync_high_delay(self, mock_query_address, mock_getaddrinfo):
        """Test that force_sync raises when delay exceeds threshold."""
        # Mock DNS resolution
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_DGRAM, 17, '', ('1.1.1.1', 123))
        ]
        
        # Mock NTP response with high delay
        server_time = 1600000000.5
        offset = 0.25
        delay = 1.0  # Exceeds max_acceptable_delay of 0.5
        mock_query_address.return_value = (server_time, offset, delay)
        
        plugin = TimeSyncPlugin(servers=["test.ntp.com"], enabled=True, allow_network=True)
        
        with pytest.raises(RuntimeError, match="too noisy"):
            plugin.force_sync()

    @patch('nodupe.plugins.time_sync.socket.getaddrinfo')
    @patch('nodupe.plugins.time_sync.TimeSyncPlugin._query_address')
    def test_maybe_sync_success(self, mock_query_address, mock_getaddrinfo):
        """Test successful maybe_sync operation."""
        # Mock DNS resolution
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_DGRAM, 17, '', ('1.1.1.1', 123))
        ]
        
        # Mock NTP response
        server_time = 1600000000.5
        offset = 0.25
        delay = 0.01
        mock_query_address.return_value = (server_time, offset, delay)
        
        plugin = TimeSyncPlugin(servers=["test.ntp.com"], enabled=True, allow_network=True)
        
        result = plugin.maybe_sync()
        
        assert result is not None
        assert result[1] == server_time

    def test_maybe_sync_disabled(self):
        """Test maybe_sync returns None when disabled."""
        plugin = TimeSyncPlugin(enabled=False)
        
        result = plugin.maybe_sync()
        assert result is None

    @patch('nodupe.plugins.time_sync.socket.getaddrinfo')
    @patch('nodupe.plugins.time_sync.TimeSyncPlugin._query_address')
    def test_maybe_sync_failure(self, mock_query_address, mock_getaddrinfo):
        """Test maybe_sync returns None on failure."""
        # Mock DNS resolution failure
        mock_getaddrinfo.return_value = []
        
        plugin = TimeSyncPlugin(servers=["test.ntp.com"], enabled=True, allow_network=True)
        
        result = plugin.maybe_sync()
        assert result is None

    @patch('nodupe.plugins.time_sync.socket.getaddrinfo')
    @patch('nodupe.plugins.time_sync.TimeSyncPlugin._query_address')
    def test_background_sync_start_stop(self, mock_query_address, mock_getaddrinfo):
        """Test starting and stopping background synchronization."""
        # Mock DNS resolution and NTP response
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_DGRAM, 17, '', ('1.1.1.1', 123))
        ]
        mock_query_address.return_value = (1600000000.5, 0.25, 0.01)
        
        plugin = TimeSyncPlugin(
            servers=["test.ntp.com"], 
            enabled=True, 
            allow_network=True,
            allow_background=True
        )
        
        # Start background sync
        plugin.start_background(interval=1.0, initial_sync=False)
        
        # Give thread time to start
        time.sleep(0.1)
        
        assert plugin._bg_thread is not None
        assert plugin._bg_thread.is_alive()
        
        # Stop background sync
        plugin.stop_background(wait=True)
        
        assert plugin._bg_thread is None

    def test_background_sync_disabled_network(self):
        """Test that background sync cannot start when network is disabled."""
        plugin = TimeSyncPlugin(allow_network=False, allow_background=True)
        
        with pytest.raises(TimeSyncPlugin._get_exception_class(), match="Cannot start background sync"):
            plugin.start_background()

    def test_background_sync_disabled_background(self):
        """Test that background sync cannot start when background is disabled."""
        plugin = TimeSyncPlugin(allow_network=True, allow_background=False)
        
        with pytest.raises(TimeSyncPlugin._get_exception_class(), match="Background syncing is disabled"):
            plugin.start_background()

    def test_get_corrected_time_no_sync(self):
        """Test get_corrected_time returns fallback when not synced."""
        plugin = TimeSyncPlugin(enabled=True)
        
        # Should return time.monotonic() when not synced
        result = plugin.get_corrected_time()
        assert isinstance(result, float)

    @patch('nodupe.plugins.time_sync.socket.getaddrinfo')
    @patch('nodupe.plugins.time_sync.TimeSyncPlugin._query_address')
    def test_get_corrected_time_after_sync(self, mock_query_address, mock_getaddrinfo):
        """Test get_corrected_time returns corrected time after sync."""
        # Mock DNS resolution
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_DGRAM, 17, '', ('1.1.1.1', 123))
        ]
        
        # Mock NTP response
        server_time = 1600000000.5
        offset = 0.25
        delay = 0.01
        mock_query_address.return_value = (server_time, offset, delay)
        
        plugin = TimeSyncPlugin(servers=["test.ntp.com"], enabled=True, allow_network=True)
        plugin.force_sync()
        
        # Get corrected time
        corrected_time = plugin.get_corrected_time()
        
        # Should be close to server time plus elapsed monotonic time
        assert isinstance(corrected_time, float)
        assert corrected_time > server_time

    def test_get_status(self):
        """Test get_status returns comprehensive status information."""
        plugin = TimeSyncPlugin(
            servers=["test.ntp.com"],
            timeout=5.0,
            attempts=3,
            max_acceptable_delay=1.0,
            smoothing_alpha=0.5,
            enabled=True,
            allow_network=True,
            allow_background=True
        )
        
        status = plugin.get_status()
        
        expected_keys = [
            "enabled", "network_allowed", "background_allowed", "background_running",
            "base_server_time", "base_monotonic", "smoothed_offset", "last_delay",
            "servers", "timeout", "attempts", "max_acceptable_delay", "smoothing_alpha"
        ]
        
        for key in expected_keys:
            assert key in status
        
        assert status["servers"] == ["test.ntp.com"]
        assert status["timeout"] == 5.0
        assert status["attempts"] == 3
        assert status["max_acceptable_delay"] == 1.0
        assert status["smoothing_alpha"] == 0.5

    def test_convenience_methods(self):
        """Test convenience methods work correctly."""
        plugin = TimeSyncPlugin(enabled=False)
        
        # These should work without raising
        timestamp = plugin.get_timestamp()
        fast64 = plugin.get_timestamp_fast64()
        
        assert isinstance(timestamp, float)
        assert isinstance(fast64, int)

    def test_smoothing_alpha_applied(self):
        """Test that smoothing alpha is applied to offset calculations."""
        plugin = TimeSyncPlugin(smoothing_alpha=0.1, enabled=True, allow_network=True)
        
        # Mock multiple syncs with different offsets
        with patch('nodupe.plugins.time_sync.socket.getaddrinfo') as mock_getaddrinfo, \
             patch('nodupe.plugins.time_sync.TimeSyncPlugin._query_address') as mock_query_address:
            
            mock_getaddrinfo.return_value = [
                (socket.AF_INET, socket.SOCK_DGRAM, 17, '', ('1.1.1.1', 123))
            ]
            
            # First sync with offset 1.0
            mock_query_address.return_value = (1600000000.0, 1.0, 0.01)
            plugin.force_sync()
            first_offset = plugin.get_offset_estimate()
            
            # Second sync with offset 2.0
            mock_query_address.return_value = (1600000000.0, 2.0, 0.01)
            plugin.force_sync()
            second_offset = plugin.get_offset_estimate()
            
            # Should be smoothed: 0.1 * 2.0 + 0.9 * 1.0 = 1.1
            expected = 0.1 * 2.0 + 0.9 * 1.0
            assert abs(second_offset - expected) < 1e-6

    def test_plugin_lifecycle(self):
        """Test plugin initialization and shutdown lifecycle."""
        plugin = TimeSyncPlugin(enabled=True)
        
        # Mock successful sync during initialization
        with patch.object(plugin, 'force_sync') as mock_sync:
            plugin.initialize()
            mock_sync.assert_called_once()
        
        # Shutdown should stop background thread
        with patch.object(plugin, 'stop_background') as mock_stop:
            plugin.shutdown()
            mock_stop.assert_called_once_with(wait=False)

    def test_get_authenticated_time_iso8601_format(self):
        """Test get_authenticated_time with ISO-8601 format."""
        plugin = TimeSyncPlugin(enabled=True)
        
        # Mock sync_with_fallback to return a known time
        with patch.object(plugin, 'sync_with_fallback') as mock_sync, \
             patch.object(plugin, 'get_corrected_time') as mock_get_time:
            
            mock_sync.return_value = ("ntp", 1600000000.0, 0.0, 0.01)
            mock_get_time.return_value = 1600000000.123456
            
            result = plugin.get_authenticated_time()
            
            # Should return ISO-8601 format
            assert result == "2020-09-13T12:26:40.123456Z"
            assert isinstance(result, str)

    def test_get_authenticated_time_unix_format(self):
        """Test get_authenticated_time with Unix timestamp format."""
        plugin = TimeSyncPlugin(enabled=True)
        
        # Mock sync_with_fallback to return a known time
        with patch.object(plugin, 'sync_with_fallback') as mock_sync, \
             patch.object(plugin, 'get_corrected_time') as mock_get_time:
            
            mock_sync.return_value = ("ntp", 1600000000.0, 0.0, 0.01)
            mock_get_time.return_value = 1600000000.123456
            
            result = plugin.get_authenticated_time(format="unix")
            
            # Should return Unix timestamp as string
            assert result == "1600000000.123456"
            assert isinstance(result, str)

    def test_get_authenticated_time_rfc3339_format(self):
        """Test get_authenticated_time with RFC-3339 format."""
        plugin = TimeSyncPlugin(enabled=True)
        
        # Mock sync_with_fallback to return a known time
        with patch.object(plugin, 'sync_with_fallback') as mock_sync, \
             patch.object(plugin, 'get_corrected_time') as mock_get_time:
            
            mock_sync.return_value = ("ntp", 1600000000.0, 0.0, 0.01)
            mock_get_time.return_value = 1600000000.123456
            
            result = plugin.get_authenticated_time(format="rfc3339")
            
            # Should return RFC-3339 format (same as ISO-8601)
            assert result == "2020-09-13T12:26:40.123456Z"

    def test_get_authenticated_time_human_format(self):
        """Test get_authenticated_time with human-readable format."""
        plugin = TimeSyncPlugin(enabled=True)
        
        # Mock sync_with_fallback to return a known time
        with patch.object(plugin, 'sync_with_fallback') as mock_sync, \
             patch.object(plugin, 'get_corrected_time') as mock_get_time:
            
            mock_sync.return_value = ("ntp", 1600000000.0, 0.0, 0.01)
            mock_get_time.return_value = 1600000000.123456
            
            result = plugin.get_authenticated_time(format="human")
            
            # Should return human-readable format
            assert result == "2020-09-13 12:26:40.123456 UTC"

    def test_get_authenticated_time_disabled_plugin(self):
        """Test get_authenticated_time raises error when plugin is disabled."""
        plugin = TimeSyncPlugin(enabled=False)
        
        with pytest.raises(TimeSyncPlugin._get_exception_class(), match="TimeSync instance is disabled"):
            plugin.get_authenticated_time()

    def test_get_authenticated_time_unsupported_format(self):
        """Test get_authenticated_time raises error for unsupported formats."""
        plugin = TimeSyncPlugin(enabled=True)
        
        with pytest.raises(ValueError, match="Unsupported format"):
            plugin.get_authenticated_time(format="invalid")

    def test_get_authenticated_time_fallback_warning(self):
        """Test that fallback to RTC triggers appropriate warning."""
        plugin = TimeSyncPlugin(enabled=True, allow_network=False)
        
        # Mock sync_with_fallback to return RTC fallback
        with patch.object(plugin, 'sync_with_fallback') as mock_sync, \
             patch.object(plugin, 'get_corrected_time') as mock_get_time, \
             patch('nodupe.plugins.time_sync.logger') as mock_logger:
            
            mock_sync.return_value = ("rtc", 1600000000.0, 0.0, 0.0)
            mock_get_time.return_value = 1600000000.123456
            
            result = plugin.get_authenticated_time()
            
            # Should return the time
            assert result == "2020-09-13T12:26:40.123456Z"
            
            # Should log warning about fallback
            mock_logger.warning.assert_called_once_with(
                "Time obtained via rtc fallback (not NTP/NTS). Time may have slight drift from network time."
            )

    def test_get_authenticated_time_monotonic_fallback(self):
        """Test get_authenticated_time with monotonic fallback."""
        plugin = TimeSyncPlugin(enabled=True, allow_network=False)
        
        # Mock sync_with_fallback to return monotonic fallback
        with patch.object(plugin, 'sync_with_fallback') as mock_sync, \
             patch.object(plugin, 'get_corrected_time') as mock_get_time, \
             patch('nodupe.plugins.time_sync.logger') as mock_logger:
            
            mock_sync.return_value = ("monotonic", 1600000000.0, 0.0, 0.0)
            mock_get_time.return_value = 1600000000.123456
            
            result = plugin.get_authenticated_time()
            
            # Should return the time
            assert result == "2020-09-13T12:26:40.123456Z"
            
            # Should log warning about fallback
            mock_logger.warning.assert_called_once_with(
                "Time obtained via monotonic fallback (not NTP/NTS). Time may have slight drift from network time."
            )

    def test_get_authenticated_time_precision(self):
        """Test that get_authenticated_time maintains microsecond precision."""
        plugin = TimeSyncPlugin(enabled=True)
        
        # Test with various microsecond values
        test_times = [
            1600000000.000000,  # No fractional part
            1600000000.123456,  # 6-digit fractional
            1600000000.100000,  # 1-digit fractional
            1600000000.000001,  # 1-microsecond
        ]
        
        for test_time in test_times:
            with patch.object(plugin, 'sync_with_fallback') as mock_sync, \
                 patch.object(plugin, 'get_corrected_time') as mock_get_time:
                
                mock_sync.return_value = ("ntp", test_time, 0.0, 0.01)
                mock_get_time.return_value = test_time
                
                result = plugin.get_authenticated_time()
                
                # Parse the ISO string back to timestamp
                dt = datetime.fromisoformat(result.replace("Z", "+00:00"))
                decoded_time = dt.timestamp()
                
                # Should maintain microsecond precision
                assert abs(decoded_time - test_time) < 1e-6

    def test_get_authenticated_time_utc_timezone(self):
        """Test that get_authenticated_time always returns UTC time."""
        plugin = TimeSyncPlugin(enabled=True)
        
        # Mock sync_with_fallback to return a known time
        with patch.object(plugin, 'sync_with_fallback') as mock_sync, \
             patch.object(plugin, 'get_corrected_time') as mock_get_time:
            
            mock_sync.return_value = ("ntp", 1600000000.0, 0.0, 0.01)
            mock_get_time.return_value = 1600000000.123456
            
            result = plugin.get_authenticated_time()
            
            # Should end with Z (UTC indicator)
            assert result.endswith("Z")
            
            # Parse and verify timezone is UTC
            dt = datetime.fromisoformat(result.replace("Z", "+00:00"))
            assert dt.tzinfo is not None
            assert dt.tzinfo.utcoffset(dt).total_seconds() == 0

    def test_get_authenticated_time_network_failure_fallback(self):
        """Test get_authenticated_time handles network failures gracefully."""
        plugin = TimeSyncPlugin(enabled=True, allow_network=True)
        
        # Mock sync_with_fallback to simulate network failure and RTC fallback
        with patch.object(plugin, 'sync_with_fallback') as mock_sync, \
             patch.object(plugin, 'get_corrected_time') as mock_get_time, \
             patch('nodupe.plugins.time_sync.logger') as mock_logger:
            
            # Simulate network failure, fallback to RTC
            mock_sync.return_value = ("rtc", 1600000000.0, 0.0, 0.0)
            mock_get_time.return_value = 1600000000.123456
            
            result = plugin.get_authenticated_time()
            
            # Should still return a valid time
            assert result == "2020-09-13T12:26:40.123456Z"
            
            # Should log warning about fallback
            mock_logger.warning.assert_called_once()

    def test_get_authenticated_time_case_insensitive_formats(self):
        """Test that get_authenticated_time handles case-insensitive format strings."""
        plugin = TimeSyncPlugin(enabled=True)
        
        # Mock sync_with_fallback to return a known time
        with patch.object(plugin, 'sync_with_fallback') as mock_sync, \
             patch.object(plugin, 'get_corrected_time') as mock_get_time:
            
            mock_sync.return_value = ("ntp", 1600000000.0, 0.0, 0.01)
            mock_get_time.return_value = 1600000000.123456
            
            # Test various case combinations
            test_formats = ["ISO8601", "Iso8601", "ISO", "iso", "RFC3339", "Rfc3339", "rfc", "UNIX", "Unix", "unix", "HUMAN", "Human", "human"]
            
            for fmt in test_formats:
                result = plugin.get_authenticated_time(format=fmt)
                
                if fmt.lower() in ["iso8601", "iso", "rfc3339", "rfc"]:
                    assert result == "2020-09-13T12:26:40.123456Z"
                elif fmt.lower() in ["unix", "unix"]:
                    assert result == "1600000000.123456"
                elif fmt.lower() in ["human", "human"]:
                    assert result == "2020-09-13 12:26:40.123456 UTC"


# Helper function to get the actual exception class
def _get_exception_class():
    """Helper to get the actual TimeSyncDisabledError class."""
    return TimeSyncPlugin._get_exception_class()
