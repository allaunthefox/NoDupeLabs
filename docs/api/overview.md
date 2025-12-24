# NoDupeLabs API Overview

## Core API Services

The NoDupeLabs system provides several core API services, with enhanced capabilities for UUID generation and specific hash type selection.

### Scan Plugin API (Enhanced)

The Scan Plugin now includes advanced UUID generation and hash type selection capabilities:

#### New API Methods:
- `generate_scan_uuid()` - Generate UUIDs for scan operations
- `get_available_hash_types()` - Get supported hash algorithms
- `hash_file(file_path, algorithm, chunk_size)` - Hash files with specific algorithms

#### Enhanced Capabilities:
- **UUID Generation**: RFC 4122 compliant UUID v4 generation with metadata
- **Hash Type Selection**: Support for multiple algorithms (MD5, SHA, BLAKE, BLAKE3, progressive hashing)
- **API Accessibility**: All new features available via plugin API calls
- **Command Integration**: `--generate-uuid` flag for scan command
- **Cascade Integration**: Both progressive hashing and archive processing stages support UUIDs and specific hash types

### Progressive Hashing Cascade API

The progressive hashing cascade stage now supports:
- **UUID Generation**: Each operation gets a unique identifier for audit trails
- **Algorithm Selection**: Specific hash algorithms for quick and full hashing
- **Rich Metadata**: Comprehensive return values with timing and algorithm information

### Archive Processing Cascade API

The archive processing cascade stage includes:
- **UUID Tracking**: Unique identifiers for archive operations
- **Hash Algorithm Control**: Specific algorithm selection for archive content
- **Progressive Processing**: Support for progressive hashing within archives

## API Usage Examples

### UUID Generation
```python
# Generate UUID via API
scan_plugin = container.get_service('scan_plugin')
uuid_result = scan_plugin.api_call('generate_scan_uuid')
print(f"Operation UUID: {uuid_result['uuid']}")

# Get available hash types
hash_types = scan_plugin.api_call('get_available_hash_types')
print(f"Available algorithms: {list(hash_types['available_hash_types'].keys())}")
```

### Specific Hash Type Usage
```python
# Hash file with specific algorithm
result = scan_plugin.api_call('hash_file',
    file_path='/path/to/file',
    algorithm='blake3',
    chunk_size=16384
)
print(f"BLAKE3 hash: {result['hash']}")
```

### Command Line Usage
```bash
# Scan with UUID generation
nodupe scan /path/to/directory --generate-uuid

# Traditional scan (preserved functionality)
nodupe scan /path/to/directory
```

## Plugin Integration

The enhanced ScanPlugin capabilities are available through:
- **Plugin System**: API calls via `plugin.api_call(method, **kwargs)`
- **Command Line**: Enhanced scan command with `--generate-uuid` flag
- **Cascade Stages**: Integrated into progressive and archive processing
- **Event System**: UUIDs available for audit logging and event tracking

## Backward Compatibility

All existing functionality remains unchanged. The new features are additive enhancements that do not affect existing integrations.
