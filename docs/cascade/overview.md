# Cascade System Overview

## Introduction

The Cascade System provides modular, extensible processing stages for file operations with enhanced UUID generation and specific hash type selection capabilities. Each stage operates independently while maintaining consistent audit trails and algorithm control.

## Enhanced Features

### UUID Generation Integration
All cascade stages now support RFC 4122 compliant UUID v4 generation for:
- Operation tracking and audit trails
- Distributed processing coordination
- Event correlation and debugging
- Compliance and security auditing

### Specific Hash Type Selection
Cascade stages support algorithm-specific operations:

#### Progressive Hashing Stage
- **Available algorithms**: BLAKE3, SHA256, MD5, and any hashlib algorithm
- **Algorithm selection**: Single algorithm for both phases or separate quick/full algorithms
- **Optimal cascading**: Automatic selection (BLAKE3 → SHA256 → MD5) based on availability
- **Parameters**: `algorithm`, `quick_algorithm`, `full_algorithm`

#### Archive Processing Stage
- **Available algorithms**: SHA256, BLAKE3, MD5, and any hashlib algorithm
- **Content hashing**: Optional file content hashing with specified algorithms
- **Hash options**: Metadata-based or actual content hashing
- **Parameters**: `hash_algorithm`, `hash_contents`, `extract_to_temp`

#### Unified API
- **Consistent interface**: Same parameter names across all stages
- **Backward compatibility**: Existing code continues to work unchanged
- **Enhanced functionality**: New features are optional additions

## Cascade Stages

### 1. Progressive Hashing Stage

The progressive hashing stage implements multi-phase duplicate detection with algorithm flexibility:

#### Features:
- **Quick Filtering**: Fast initial hash comparison
- **Full Verification**: Thorough hash comparison for candidates
- **UUID Generation**: Unique identifiers for each operation
- **Algorithm Selection**: Customizable hash algorithms for both phases

#### API Methods:
- `execute(files, quick_algorithm='sha256', full_algorithm='sha256')`
- Returns UUID, algorithm metadata, and comprehensive results

### 2. Archive Processing Stage

The archive processing stage handles various archive formats with content-specific hashing:

#### Features:
- **Multi-format Support**: ZIP, TAR, 7Z, RAR, and others
- **Content Hashing**: Configurable algorithm for extracted content
- **UUID Tracking**: Unique identifiers for archive operations
- **Progressive Processing**: Quick filtering with full verification

#### API Methods:
- `execute(archive_path, hash_algorithm='sha256')`
- Returns UUID, extraction metadata, and verification results

## API Integration

### Unified API Access
Both cascade stages provide consistent API access through the plugin system:

```python
# Access via plugin container
scan_plugin = container.get_service('scan_plugin')

# UUID generation
uuid_result = scan_plugin.api_call('generate_scan_uuid')

# Available hash types
hash_types = scan_plugin.api_call('get_available_hash_types')

# Stage-specific operations
progressive_result = scan_plugin.api_call('progressive_hash_scan',
    files=file_list,
    quick_algorithm='blake3',
    full_algorithm='sha256'
)

archive_result = scan_plugin.api_call('archive_process',
    archive_path='/path/to/archive.zip',
    hash_algorithm='blake3'
)
```

### Direct Stage Access
```python
from nodupe.core.cascade.stages.progressive_hashing import get_progressive_hashing_stage
from nodupe.core.cascade.stages.archive_processing import get_archive_processing_stage

# Progressive hashing with UUID and specific algorithms
progressive_stage = get_progressive_hashing_stage()
result = progressive_stage.execute(
    files=file_list,
    quick_algorithm='blake3',
    full_algorithm='blake3'
)
print(f"Progressive operation UUID: {result['uuid']}")

# Archive processing with UUID and specific algorithm
archive_stage = get_archive_processing_stage()
result = archive_stage.execute(
    archive_path='/path/to/archive.7z',
    hash_algorithm='blake3'
)
print(f"Archive operation UUID: {result['uuid']}")
```

## Configuration

### Algorithm Selection
Configure default algorithms for each stage:

```python
# Configuration example
cascade_config = {
    'progressive_hashing': {
        'default_quick_algorithm': 'blake3',
        'default_full_algorithm': 'sha256',
        'enable_uuid_generation': True
    },
    'archive_processing': {
        'default_hash_algorithm': 'blake3',
        'enable_uuid_generation': True,
        'supported_formats': ['zip', 'tar', '7z', 'rar']
    }
}
```

### Performance Tuning
- **BLAKE3**: Optimal for performance-sensitive operations
- **SHA256**: Balanced security and performance
- **MD5**: Fastest for non-security-critical operations
- **SHA3**: Highest security requirements

## Error Handling

All cascade operations return standardized responses with UUIDs for tracking:

```json
{
  "success": "bool",
  "error": "string (if applicable)",
  "uuid": "string (unique identifier for tracking)",
  "generated_at": "float"
}
```

## Integration Points

### Plugin System Integration
- **API Calls**: All enhanced features available via plugin API
- **Command Line**: UUID generation accessible via `--generate-uuid` flag
- **Event System**: UUIDs available for audit logging and event tracking
- **Cascade Stages**: Both stages support UUIDs and specific hash types

### Backward Compatibility
All existing cascade functionality remains unchanged. New features are additive enhancements that preserve existing integrations.
