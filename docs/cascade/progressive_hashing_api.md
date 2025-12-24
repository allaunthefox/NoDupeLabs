# Progressive Hashing Cascade API

## Overview

The Progressive Hashing Cascade Stage provides intelligent file hashing with UUID generation and specific hash type selection capabilities. This stage implements a multi-phase approach to duplicate detection with performance optimization.

## API Integration

### UUID Generation in Progressive Hashing

Each progressive hashing operation now includes UUID generation for audit and tracking:

```python
from nodupe.core.cascade.stages.progressive_hashing import get_progressive_hashing_stage

stage = get_progressive_hashing_stage()
result = stage.execute(files)
print(result['uuid'])  # Unique identifier for this operation
print(result['quick_hash_algorithm'])  # Algorithm used for quick hashing
print(result['full_hash_algorithm'])  # Algorithm used for full hashing
```

### Specific Hash Type Selection

The progressive hashing stage supports specific algorithm selection:

#### Available Hash Algorithms
- **BLAKE3**: Fastest performance, good security (requires `blake3` package)
- **SHA256**: Balanced security and performance (default)
- **MD5**: Fastest but least secure (fallback option)
- **Any hashlib algorithm**: All algorithms available in `hashlib.algorithms_available`

#### Algorithm Selection Options
- **Single algorithm**: Use same algorithm for both quick and full hashing via `algorithm` parameter
- **Separate algorithms**: Use different algorithms for quick and full hashing via `quick_algorithm` and `full_algorithm` parameters
- **Automatic selection**: Optimal algorithm cascade (BLAKE3 → SHA256 → MD5) based on availability

## API Methods

### `execute(files, **kwargs)`
Execute progressive hashing with UUID generation and specific hash type selection.

**Parameters:**
- `files`: List of file paths to process
- `**kwargs`: Additional parameters including:
  - `algorithm`: Specific hash algorithm to use for both quick and full hashing (optional)
  - `quick_algorithm`: Specific quick hash algorithm (optional)
  - `full_algorithm`: Specific full hash algorithm (optional)
  - `chunk_size`: Size for chunked reading (default 4096)

**Returns:**
```json
{
  "duplicates": "List[Dict]",
  "quick_hash_algorithm": "string",
  "full_hash_algorithm": "string", 
  "files_processed": "int",
  "duplicate_groups": "int",
  "execution_time": "float",
  "algorithm_selection_reason": "string",
  "uuid": "string (unique operation identifier)",
  "hash_type": "string (progressive, specific, etc.)"
}
```

## Integration Examples

### With UUID and Specific Algorithms
```python
stage = get_progressive_hashing_stage()

# Use BLAKE3 for both quick and full hashing with UUID tracking
result = stage.execute(
    files=file_list,
    quick_algorithm='blake3',
    full_algorithm='blake3'
)

print(f"Operation UUID: {result['uuid']}")
print(f"Quick hash algorithm: {result['quick_hash_algorithm']}")
print(f"Files processed: {result['files_processed']}")
print(f"Duplicates found: {result['duplicate_groups']}")
```

### API Access Pattern
```python
# Access via plugin system
scan_plugin = container.get_service('scan_plugin')

# Get available hash types
hash_types = scan_plugin.api_call('get_available_hash_types')

# Execute progressive hashing with specific algorithms
progressive_result = scan_plugin.api_call('progressive_hash_scan',
    files=file_list,
    quick_algorithm='blake3',
    full_algorithm='sha256'
)
```

## Performance Optimization

### Algorithm Selection Impact
- **BLAKE3**: Fastest performance, good security
- **SHA256**: Balanced security and performance
- **MD5**: Fastest but least secure
- **SHA3**: Highest security, slower performance

### UUID Overhead
- UUID generation adds minimal overhead (< 0.1ms per operation)
- UUIDs enable comprehensive audit trails
- UUIDs support distributed processing tracking

## Error Handling

All operations return standardized responses:

```json
{
  "success": "bool",
  "error": "string (if applicable)",
  "uuid": "string (even on error for tracking)",
  "generated_at": "float"
}
```

## Backward Compatibility

Existing progressive hashing functionality remains unchanged. New features are optional enhancements.
