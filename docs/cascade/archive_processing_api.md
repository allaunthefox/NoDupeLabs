# Archive Processing Cascade API

## Overview

The Archive Processing Cascade Stage provides intelligent archive handling with UUID generation and specific hash type selection capabilities. This stage handles various archive formats with optimized processing and comprehensive tracking.

## API Integration

### UUID Generation in Archive Processing

Each archive processing operation now includes UUID generation for audit and tracking:

```python
from nodupe.core.cascade.stages.archive_processing import get_archive_processing_stage

stage = get_archive_processing_stage()
result = stage.execute(archive_path)
print(result['uuid'])  # Unique identifier for this operation
print(result['processing_algorithm'])  # Algorithm used for processing
print(result['extraction_method'])  # Method used for extraction
```

### Specific Hash Type Selection

The archive processing stage supports specific algorithm selection for content hashing:

#### Available Hash Algorithms
- **SHA256**: Balanced security and performance (default)
- **BLAKE3**: Fastest performance, good security (requires `blake3` package)
- **MD5**: Fastest but least secure
- **Any hashlib algorithm**: All algorithms available in `hashlib.algorithms_available`

#### Content Hashing Options
- **Enable content hashing**: Use `hash_contents=True` parameter
- **Specify algorithm**: Use `hash_algorithm` parameter (default: 'sha256')
- **Hash extraction**: When `extract_to_temp=True`, hashes actual extracted file contents
- **Hash metadata**: When `extract_to_temp=False`, hashes based on archive metadata and file information

## API Methods

### `execute(archive_path, hash_algorithm='sha256', **kwargs)`
Execute archive processing with UUID generation and algorithm selection.

**Parameters:**
- `archive_path`: Path to archive file to process
- `hash_algorithm`: Algorithm for content hashing (default: 'sha256')
- `**kwargs`: Additional parameters including UUID metadata

**Returns:**
```json
{
  "archive_path": "string",
  "extraction_results": "List[Dict]",
  "successful_method": "string",
  "total_files": "int", 
  "execution_time": "float",
  "uuid": "string (unique operation identifier)",
  "hash_algorithm": "string",
  "extracted_content_uuid": "string (UUID for extracted content)",
  "content_verification_results": "List[Dict]"
}
```

## Integration Examples

### With UUID and Specific Algorithm
```python
stage = get_archive_processing_stage()

# Use BLAKE3 for content hashing with UUID tracking
result = stage.execute(
    archive_path='/path/to/archive.zip',
    hash_algorithm='blake3'
)

print(f"Operation UUID: {result['uuid']}")
print(f"Content hash algorithm: {result['hash_algorithm']}")
print(f"Files extracted: {result['total_files']}")
print(f"Successful method: {result['successful_method']}")
```

### API Access Pattern
```python
# Access via plugin system
scan_plugin = container.get_service('scan_plugin')

# Get available hash types for archive processing
hash_types = scan_plugin.api_call('get_available_hash_types')

# Execute archive processing with specific algorithm
archive_result = scan_plugin.api_call('archive_process',
    archive_path='/path/to/archive.7z',
    hash_algorithm='blake3'
)
```

## Supported Archive Formats

### Extraction Methods
- **ZIP**: Native Python zipfile module
- **TAR**: Native Python tarfile module  
- **7Z**: py7zr library (if available)
- **RAR**: rarfile library (if available)
- **Other**: Generic extraction support

### Content Hashing
Each extracted file can be hashed using the specified algorithm:
- **Individual file hashing**: Each extracted file gets hashed
- **Archive-level hash**: Composite hash of all content
- **Progressive hashing**: Quick filtering followed by full verification

## Performance Optimization

### Algorithm Selection Impact
- **BLAKE3**: Fastest performance for content hashing
- **SHA256**: Balanced security and performance
- **MD5**: Fastest but least secure for content verification
- **SHA3**: Highest security, slower performance

### UUID Overhead
- UUID generation adds minimal overhead (< 0.1ms per operation)
- UUIDs enable comprehensive archive processing audit trails
- UUIDs support distributed archive processing tracking

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

Existing archive processing functionality remains unchanged. New features are optional enhancements that preserve all existing behavior.
