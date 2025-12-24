# Scan Plugin API Reference

This document provides comprehensive documentation for the Scan Plugin API, including the enhanced UUID generation and hash type selection capabilities.

## API Endpoints

### 1. UUID Generation

#### `generate_scan_uuid(**kwargs)`
Generate a UUID for scan operations via API.

**Parameters:**
- `**kwargs`: Additional parameters (optional)

**Response:**
```json
{
  "uuid": "string",
  "uuid_version": 4,
  "variant": "string",
  "timestamp": "int",
  "urn_format": "string",
  "canonical_format": "string",
  "generated_at": "float",
  "success": true
}
```

**Usage Example:**
```python
# Via plugin system
scan_plugin = container.get_service('scan_plugin')
result = scan_plugin.api_call('generate_scan_uuid')
print(result['uuid'])  # Get the generated UUID
```

### 2. Hash Type Selection

#### `get_available_hash_types(**kwargs)`
Get available hash types supported by the system.

**Parameters:**
- `**kwargs`: Additional parameters (optional)

**Response:**
```json
{
  "available_hash_types": {
    "algorithm_name": {
      "algorithm": "string",
      "digest_size": "int",
      "block_size": "int",
      "type": "string",
      "description": "string (optional)"
    }
  },
  "count": "int",
  "generated_at": "float"
}
```

**Usage Example:**
```python
# Get available hash types
result = scan_plugin.api_call('get_available_hash_types')
print(result['available_hash_types'])  # List all supported algorithms
```

#### `hash_file(file_path, algorithm='sha256', chunk_size=8192)`
Hash a file using the specified algorithm.

**Parameters:**
- `file_path`: Path to the file to hash (required)
- `algorithm`: Hash algorithm to use (default: 'sha256')
- `chunk_size`: Size of chunks to read (default: 8192)

**Response:**
```json
{
  "file_path": "string",
  "algorithm": "string",
  "hash": "string",
  "file_size": "int",
  "file_mtime": "float",
  "chunk_size": "int",
  "success": true,
  "generated_at": "float"
}
```

**Usage Example:**
```python
# Hash a file with specific algorithm
result = scan_plugin.api_call('hash_file', 
    file_path='/path/to/file',
    algorithm='sha256',
    chunk_size=8192
)
print(result['hash'])  # Get the computed hash
```

## Command-Line Interface

### Scan Command with UUID Generation

The scan command now supports UUID generation:

```bash
# Generate UUID during scan
nodupe scan /path/to/directory --generate-uuid

# Regular scan without UUID
nodupe scan /path/to/directory
```

## Plugin Capabilities

The enhanced ScanPlugin exposes the following capabilities:

```python
{
  'commands': ['scan'],
  'api_calls': [
    'generate_scan_uuid',
    'hash_file', 
    'get_available_hash_types'
  ]
}
```

## Integration Examples

### API Integration
```python
# Get the scan plugin from the container
scan_plugin = container.get_service('scan_plugin')

# Generate UUID via API
uuid_result = scan_plugin.api_call('generate_scan_uuid')
scan_uuid = uuid_result['uuid']

# Get available hash types
hash_types = scan_plugin.api_call('get_available_hash_types')

# Hash a specific file
hash_result = scan_plugin.api_call('hash_file', 
    file_path='/path/to/file',
    algorithm='blake3'
)
```

### Cascade Integration

Both progressive hashing and archive processing cascade stages now support:
- UUID generation for traceability
- Specific hash type selection
- Rich metadata return values

## Supported Hash Algorithms

The system supports multiple hash algorithms including:
- **Standard**: MD5, SHA1, SHA256, SHA384, SHA512
- **SHA3 Variants**: SHA3-224, SHA3-256, SHA3-384, SHA3-512
- **Blake Algorithms**: BLAKE2b, BLAKE2s, BLAKE3
- **Progressive**: Quick filtering hashes, full file hashes

## Error Handling

All API calls return structured error responses:
```json
{
  "error": "string",
  "success": false
}
```

## Backward Compatibility

All existing functionality remains unchanged. The new features are additive and do not break existing integrations.
