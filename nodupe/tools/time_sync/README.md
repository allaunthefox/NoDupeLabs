# TimeSync Plugin

The TimeSync plugin provides NTP-based time synchronization and FastDate64 timestamp encoding for the NoDupeLabs system. It ensures accurate, monotonic timekeeping that is immune to system clock changes.

**Algorithm Attribution:**
- FastDate64 encoding/decoding based on Ben Joffe's work
- Reference: https://www.benjoffe.com/fast-date-64

## Features

- **NTP Time Synchronization**: Query multiple NTP servers (Google, Cloudflare, pool) for accurate time
- **FastDate64 Encoding**: Compact 64-bit timestamp encoding for efficient storage and sorting
- **Monotonic Timekeeping**: Process-local corrected clock immune to system clock jumps
- **Background Synchronization**: Automatic periodic time synchronization
- **Runtime Controls**: Enable/disable network operations and background sync
- **Environment Configuration**: Configurable via environment variables

## Installation

The TimeSync plugin is included with NoDupeLabs and requires no additional dependencies.

## Usage

### Basic Usage

```python
from nodupe.plugins.time_sync import TimeSyncPlugin

# Create and initialize the plugin
plugin = TimeSyncPlugin()
plugin.initialize()

# Get corrected timestamp
corrected_time = plugin.get_corrected_time()
print(f"Corrected time: {corrected_time}")

# Get compact 64-bit timestamp
compact_ts = plugin.get_corrected_fast64()
print(f"FastDate64: {compact_ts}")
```

### Advanced Configuration

```python
# Custom configuration
plugin = TimeSyncPlugin(
    servers=["custom.ntp.com", "pool.ntp.org"],
    timeout=5.0,              # Socket timeout in seconds
    attempts=3,               # Number of attempts per server
    max_acceptable_delay=1.0, # Maximum network delay in seconds
    smoothing_alpha=0.3       # Offset smoothing factor (0.0-1.0)
)

# Enable the plugin
plugin.enable()

# Perform initial synchronization
try:
    host, server_time, offset, delay = plugin.force_sync()
    print(f"Synchronized with {host}")
    print(f"Offset: {offset:.3f}s, Delay: {delay:.3f}s")
except Exception as e:
    print(f"Synchronization failed: {e}")
```

### Background Synchronization

```python
# Start background synchronization (every 5 minutes)
plugin.start_background(interval=300.0)

# Check status
status = plugin.get_status()
print(f"Background running: {status['background_running']}")

# Stop background synchronization
plugin.stop_background()
```

### Runtime Controls

```python
# Control plugin state
plugin.enable()   # Enable the plugin
plugin.disable()  # Disable the plugin

# Control network operations
plugin.enable_network()   # Allow network queries
plugin.disable_network()  # Block network queries

# Control background synchronization
plugin.enable_background()   # Allow background sync
plugin.disable_background()  # Stop and disable background sync
```

### Fallback Synchronization

The plugin provides automatic fallback when NTP network is unavailable:

```python
# Primary method: NTP synchronization (preferred)
try:
    host, server_time, offset, delay = plugin.force_sync()
    print(f"Synchronized via NTP: {host}")
except Exception as e:
    print(f"NTP failed: {e}")
    
    # Fallback: Use automatic fallback strategy
    source, server_time, offset, delay = plugin.sync_with_fallback()
    print(f"Synchronized via {source}: offset={offset:.3f}s, delay={delay:.3f}s")
    
    # Check synchronization status
    status = plugin.get_sync_status()
    print(f"Sync method: {status['sync_method']}")
    print(f"Has external reference: {status['has_external_reference']}")
```

**Fallback Strategy:**
1. **Primary (Preferred)**: NTP synchronization via network
2. **Fallback 1**: System RTC with monotonic correction
3. **Fallback 2**: Pure monotonic time (when RTC unavailable)

**When to Use Fallback:**
- Network connectivity issues
- Firewall blocking UDP port 123
- NTP server unavailability
- Restricted environments without internet access

**Benefits:**
- **Graceful Degradation**: Continues working even without network
- **Monotonic Guarantee**: Always provides monotonic time progression
- **Best Available Reference**: Uses the most accurate local time source
- **Transparent Operation**: Same API regardless of sync method

### FastDate64 Utilities

```python
from nodupe.plugins.time_sync import TimeSyncPlugin

# Encode timestamp to 64-bit integer (Ben Joffe's FastDate64)
# Reference: https://www.benjoffe.com/fast-date-64
ts = time.time()
encoded = TimeSyncPlugin.encode_fastdate64(ts)

# Decode back to timestamp
decoded = TimeSyncPlugin.decode_fastdate64(encoded)

# Convert to ISO 8601 string
iso_string = TimeSyncPlugin.fastdate64_to_iso(encoded)

# Convert from ISO 8601 string
encoded_from_iso = TimeSyncPlugin.iso_to_fastdate64(iso_string)
```

### FastDate Utilities (32-bit)

```python
# Encode timestamp to 32-bit integer (Ben Joffe's FastDate)
# Reference: https://www.benjoffe.com/fast-date
# Supports ~47 days from Unix epoch with millisecond precision
ts = time.time()
encoded = TimeSyncPlugin.encode_fastdate(ts)

# Decode back to timestamp
decoded = TimeSyncPlugin.decode_fastdate(encoded)
```

### SafeDate Utilities (32-bit with 2024 epoch)

```python
# Encode timestamp to safe 32-bit integer (Ben Joffe's SafeDate)
# Reference: https://www.benjoffe.com/safe-date
# Uses 2024 as epoch offset for reasonable range with millisecond precision
ts = time.time()
encoded = TimeSyncPlugin.encode_safedate(ts)

# Decode back to timestamp
decoded = TimeSyncPlugin.decode_safedate(encoded)
```

### Algorithm Comparison

| Algorithm | Bits | Range | Precision | Use Case |
|-----------|------|-------|-----------|----------|
| FastDate64 | 64 | ~544 years | Sub-microsecond | General purpose, high precision |
| FastDate | 32 | ~47 days | Millisecond | Short-term, compact storage |
| SafeDate | 32 | 2024±~24 days | Millisecond | Modern applications, safe range |

### Leap Year Integration

The TimeSync plugin integrates with the LeapYear plugin for optimal leap year calculations:

```python
# Check if leap year (uses LeapYear plugin if available, falls back to built-in)
is_leap = plugin.is_leap_year(2024)  # True
is_leap = plugin.is_leap_year(2023)  # False

# Get days in February for a year
feb_days = plugin.get_days_in_february(2024)  # 29 (leap year)
feb_days = plugin.get_days_in_february(2023)  # 28 (non-leap year)

# Check if LeapYear plugin is available
plugin_available = plugin.is_leap_year_plugin_available()
print(f"LeapYear plugin available: {plugin_available}")

# Performance comparison:
# - With LeapYear plugin: ~2-5 nanoseconds per calculation (Ben Joffe's algorithm)
# - Without plugin: ~10-20 nanoseconds per calculation (built-in algorithm)
```

**Integration Benefits:**
- **Automatic Plugin Detection**: Loads LeapYear plugin if available
- **Seamless Fallback**: Uses built-in calculations if plugin unavailable
- **Error Resilience**: Falls back to built-in if plugin encounters errors
- **Performance Optimization**: Uses Ben Joffe's fast bitwise algorithm when possible

## Environment Variables

Configure the plugin behavior using environment variables:

- `NODUPE_TIMESYNC_ENABLED` (default: `1`): Enable/disable the plugin
- `NODUPE_TIMESYNC_NO_NETWORK` (default: `0`): Disable network operations
- `NODUPE_TIMESYNC_ALLOW_BG` (default: `1`): Allow background synchronization

Example:
```bash
export NODUPE_TIMESYNC_ENABLED=1
export NODUPE_TIMESYNC_NO_NETWORK=0
export NODUPE_TIMESYNC_ALLOW_BG=1
```

## FastDate64 Format

FastDate64 encodes timestamps into a 64-bit unsigned integer:

- **34 bits** for seconds (supports ~544 years from Unix epoch)
- **30 bits** for fractional seconds (nanosecond precision)

This format provides:
- **Compact storage**: 8 bytes vs 8+ bytes for float/double
- **Fast sorting**: Integer comparison is faster than float
- **Precision**: Sub-microsecond accuracy
- **Range**: Sufficient for most applications

## Error Handling

The plugin provides several error conditions:

```python
from nodupe.plugins.time_sync import TimeSyncPlugin

try:
    plugin.force_sync()
except TimeSyncPlugin._get_exception_class() as e:
    if "disabled" in str(e):
        print("Plugin or network is disabled")
    elif "noisy" in str(e):
        print("Network delay too high")
    else:
        print(f"Sync failed: {e}")

# Use maybe_sync() for non-throwing alternative
result = plugin.maybe_sync()
if result is None:
    print("Sync not available")
else:
    host, server_time, offset, delay = result
```

## Integration with NoDupeLabs

The TimeSync plugin integrates seamlessly with the NoDupeLabs plugin system:

```python
from nodupe.core.plugin_system import PluginManager

# The plugin will be automatically discovered and loaded
manager = PluginManager()
timesync_plugin = manager.get_plugin("TimeSync")

if timesync_plugin:
    corrected_time = timesync_plugin.get_corrected_time()
```

## Performance Considerations

- **Network overhead**: NTP queries are lightweight (single UDP packet)
- **CPU overhead**: FastDate64 encoding/decoding is very fast
- **Memory overhead**: Minimal (plugin stores only a few float values)
- **Background sync**: Runs in separate thread, configurable interval

## Security Notes

- Uses standard NTP protocol over UDP port 123
- No system clock modifications (process-local only)
- DNS resolution uses system resolver
- Consider firewall rules if network access is restricted

## Troubleshooting

### Plugin won't sync
- Check network connectivity to NTP servers
- Verify UDP port 123 is not blocked
- Check DNS resolution for NTP servers
- Review plugin status: `plugin.get_status()`

### High network delay
- Try different NTP servers
- Check network congestion
- Increase `max_acceptable_delay` if needed

### Background sync not working
- Verify `allow_background` is enabled
- Check that network operations are allowed
- Review thread status in plugin status

## Examples

### File Metadata with Accurate Timestamps

```python
from nodupe.plugins.time_sync import TimeSyncPlugin
import os

plugin = TimeSyncPlugin()
plugin.initialize()

# Get file creation time with NTP correction
file_path = "/path/to/file"
stat = os.stat(file_path)
file_time = stat.st_mtime

# Encode with FastDate64 for compact storage
metadata_timestamp = plugin.encode_fastdate64(file_time)
creation_timestamp = plugin.get_corrected_fast64()

print(f"File time (FastDate64): {metadata_timestamp}")
print(f"Creation time (FastDate64): {creation_timestamp}")
```

### Database Timestamps

```python
from nodupe.plugins.time_sync import TimeSyncPlugin

plugin = TimeSyncPlugin()
plugin.initialize()

# Get current time for database record
current_time = plugin.get_corrected_fast64()

# Store in database as integer
# INSERT INTO events (timestamp, data) VALUES (?, ?)
# cursor.execute("INSERT INTO events (timestamp, data) VALUES (?, ?)", 
#                (current_time, "event_data"))

# Query and decode
# cursor.execute("SELECT timestamp FROM events ORDER BY timestamp")
# for row in cursor.fetchall():
#     ts = TimeSyncPlugin.decode_fastdate64(row[0])
#     print(f"Event time: {ts}")
```

## API Reference

### TimeSyncPlugin Class

#### Constructor
```python
TimeSyncPlugin(
    servers: Optional[Iterable[str]] = None,
    timeout: float = 3.0,
    attempts: int = 2,
    max_acceptable_delay: float = 0.5,
    smoothing_alpha: float = 0.3,
    *,
    enabled: Optional[bool] = None,
    allow_network: Optional[bool] = None,
    allow_background: Optional[bool] = None,
)
```

#### Methods
- `initialize()`: Initialize the plugin
- `shutdown()`: Shutdown the plugin
- `force_sync() -> Tuple[str, float, float, float]`: Force synchronization
- `maybe_sync() -> Optional[Tuple[str, float, float, float]]`: Try synchronization
- `start_background(interval: float = 300.0, initial_sync: bool = True)`: Start background sync
- `stop_background(wait: bool = True, timeout: Optional[float] = None)`: Stop background sync
- `get_corrected_time() -> float`: Get corrected timestamp
- `get_corrected_fast64() -> int`: Get corrected timestamp as FastDate64
- `get_status() -> dict`: Get plugin status

#### Static Methods
- `encode_fastdate64(ts: float) -> int`: Encode timestamp
- `decode_fastdate64(value: int) -> float`: Decode timestamp
- `fastdate64_to_iso(value: int) -> str`: Convert to ISO string
- `iso_to_fastdate64(iso: str) -> int`: Convert from ISO string

#### Runtime Control Methods
- `is_enabled() -> bool`: Check if enabled
- `enable()`: Enable plugin
- `disable()`: Disable plugin
- `is_network_allowed() -> bool`: Check network access
- `enable_network()`: Enable network
- `disable_network()`: Disable network
- `is_background_allowed() -> bool`: Check background sync
- `enable_background()`: Enable background sync
- `disable_background()`: Disable background sync
