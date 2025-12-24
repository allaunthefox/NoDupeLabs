# Scan Plugin API Specification

## Overview

The Scan Plugin provides comprehensive file scanning capabilities with enhanced UUID generation and specific hash type selection functionality. This plugin serves as the primary interface for file scanning operations within the NoDupeLabs ecosystem.

## API Methods

### UUID Generation Methods

#### `generate_scan_uuid(**kwargs) -> Dict[str, Any]`
Generate a UUID for scan operations with comprehensive metadata.

**Parameters:**
- `**kwargs`: Additional parameters for UUID generation

**Returns:**
```json
{
  "uuid": "string (UUID v4)",
  "uuid_version": "int (4)",
  "variant": "string",
  "timestamp": "int (Unix timestamp)",
  "urn_format": "string (URN format)",
  "canonical_format": "string (Canonical format)",
  "generated_at": "float (Unix timestamp with microseconds)",
  "success": "bool (true)"
}
```

**Example:**
```python
result = scan_plugin.api_call('generate_scan_uuid')
print(f"Generated UUID: {result['uuid']}")
```

### Hash Operation Methods

#### `get_available_hash_types(**kwargs) -> Dict[str, Any]`
Retrieve all available hash types supported by the system.

**Parameters:**
- `**kwargs`: Additional parameters (optional)

**Returns:**
```json
{
  "available_hash_types": {
    "algorithm_name": {
      "algorithm": "string",
      "digest_size": "int",
      "block_size": "int", 
      "type": "string (standard|fast|progressive)",
      "description": "string (optional)"
    }
  },
  "count": "int",
  "generated_at": "float"
}
```

**Example:**
```python
hash_types = scan_plugin.api_call('get_available_hash_types')
for alg_name, alg_info in hash_types['available_hash_types'].items():
    print(f"{alg_name}: {alg_info['type']} - {alg_info['digest_size']} bytes")
```

#### `hash_file(file_path: str, algorithm: str = 'sha256', chunk_size: int = 8192) -> Dict[str, Any]`
Hash a file using the specified algorithm.

**Parameters:**
- `file_path`: Path to the file to hash
- `algorithm`: Hash algorithm to use (default: 'sha256')
- `chunk_size`: Size of chunks to read (default: 8192)

**Returns:**
```json
{
  "file_path": "string",
  "algorithm": "string",
  "hash": "string (hexadecimal)",
  "file_size": "int",
  "file_mtime": "float",
  "chunk_size": "int",
  "success": "bool",
  "generated_at": "float"
}
```

**Example:**
```python
result = scan_plugin.api_call('hash_file', 
    file_path='/path/to/file',
    algorithm='blake3',
    chunk_size=16384
)
if result['success']:
    print(f"File hash: {result['hash']}")
```

## Command Line Interface

### Scan Command Extensions

The scan command now supports enhanced UUID generation:

```bash
# Scan with UUID generation for audit trail
nodupe scan /path/to/directory --generate-uuid

# Scan without UUID (traditional behavior preserved)
nodupe scan /path/to/directory

# Verbose output with UUID
nodupe scan /path/to/directory --generate-uuid --verbose
```

## Integration Points

### Plugin System Integration
The enhanced ScanPlugin registers the following capabilities:
- **Commands**: `['scan']`
- **API Calls**: `['generate_scan_uuid', 'hash_file', 'get_available_hash_types']`
- **Events**: `['scan_start', 'scan_complete', 'file_processed']`

### Cascade Integration
Both cascade stages support:
- UUID generation for operation tracking
- Specific hash algorithm selection
- Rich metadata return values

## Error Handling

All API methods return standardized error responses:

```json
{
  "error": "string (error message)",
  "success": false,
  "generated_at": "float"
}
```

## Performance Considerations

- **UUID Generation**: Near-instantaneous, suitable for high-frequency operations
- **Hash Operations**: Chunk-based processing for large files
- **Algorithm Selection**: Choose appropriate algorithms based on security vs. performance needs

## Security Considerations

- UUID v4 generation uses cryptographically secure random number generation
- Hash algorithms follow industry standards
- Progressive hashing provides quick filtering followed by thorough verification

## Backward Compatibility

All existing functionality remains intact. New features are additive and maintain API compatibility.
