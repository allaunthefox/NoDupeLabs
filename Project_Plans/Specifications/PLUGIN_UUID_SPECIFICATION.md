# Plugin UUID Specification

## Overview

This specification defines the UUID-based naming convention for NoDupeLabs plugins and modules to prevent filename corruption, enable accurate marketplace categorization, and avoid name collisions.

## Purpose

- **Prevent File Corruption**: UUID-based naming prevents issues with special characters, encoding problems, or filesystem limitations
- **Marketplace Categorization**: Enables precise identification and categorization in plugin marketplaces
- **Name Collision Avoidance**: Eliminates conflicts between plugins with similar names
- **Version Tracking**: Facilitates tracking of plugin versions and updates
- **Security**: Provides tamper-evident plugin identification

## UUID Format

### Plugin UUID Structure

```
{plugin_name}_{uuid_v4}.{version}.py
```

**Example:**
```
scan_enhanced_550e8400-e29b-41d4-a716-446655440000.v1.2.3.py
```

### Components

1. **Plugin Name**: Human-readable identifier (2-50 characters)
   - Lowercase letters, numbers, and underscores only
   - Must start with a letter
   - Examples: `scan_enhanced`, `security_checker`, `ml_classifier`

2. **UUID**: Version 4 UUID (Universally Unique Identifier)
   - Format: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`
   - Generated using cryptographically secure random number generator
   - Ensures global uniqueness

3. **Version**: Semantic versioning format
   - Format: `v{major}.{minor}.{patch}`
   - Examples: `v1.0.0`, `v2.1.3`, `v0.5.1`

## UUID Generation Requirements

### Generation Algorithm (ISO/IEC 9834-8 Compliant)
- Use UUID version 4 (random-based) as per RFC 9562
- Use Python's standard library `uuid.uuid4()` function
- Generated UUIDs must have version field set to 0x4
- Generated UUIDs must have variant field set to 0x8, 0x9, 0xA, or 0xB
- No namespace or name-based UUIDs (versions 3 or 5)
- No time-based UUIDs (version 1) for security reasons

### Validation Rules (RFC 9562 Compliant)
- Must be valid UUID v4 format according to RFC 9562
- Must pass Python's standard library `uuid.UUID()` validation
- Must have version field equal to 4
- Must have variant field indicating RFC 9562 compliance
- Cannot be nil UUID (`00000000-0000-0000-0000-000000000000`)
- Cannot be reserved UUIDs (namespace UUIDs, nil UUID, etc.)
- Must be exactly 36 characters in canonical string representation

## Plugin Metadata Schema

### Required Metadata

```python
# Plugin metadata must be included at the top of each plugin file
PLUGIN_METADATA = {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "name": "scan_enhanced",
    "display_name": "Enhanced File Scanner",
    "version": "1.2.3",
    "description": "Advanced file scanning with ML integration",
    "author": "NoDupeLabs Team",
    "category": "scanning",
    "dependencies": ["numpy>=1.20.0", "scikit-learn>=1.0.0"],
    "compatibility": {
        "python": ">=3.9",
        "nodupe_core": ">=1.0.0"
    },
    "tags": ["scanning", "ml", "performance"],
    "marketplace_id": "scan_enhanced_550e8400-e29b-41d4-a716-446655440000"
}
```

### UTF-8 Encoding Requirement

**CRITICAL**: The `marketplace_id` field MUST be UTF-8 encoded and contain only UTF-8 valid characters.

- Marketplace IDs must be valid UTF-8 strings
- No non-UTF-8 characters, control characters, or invalid byte sequences
- Must be safely representable in UTF-8 encoding
- Length must not exceed 255 characters when UTF-8 encoded
- Must not contain null bytes (\x00) or other invalid UTF-8 sequences

### Metadata Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `uuid` | string | Yes | UUID v4 identifier |
| `name` | string | Yes | Internal plugin name |
| `display_name` | string | Yes | User-facing name |
| `version` | string | Yes | Semantic version |
| `description` | string | Yes | Plugin description |
| `author` | string | Yes | Plugin author |
| `category` | string | Yes | Plugin category |
| `dependencies` | list | No | Python package dependencies |
| `compatibility` | dict | Yes | Compatibility requirements |
| `tags` | list | No | Search tags |
| `marketplace_id` | string | Yes | Marketplace identifier (UTF-8 encoded) |

## Plugin Categories

### Standard Categories

- `scanning` - File scanning and detection plugins
- `ml` - Machine learning and AI integration
- `security` - Security analysis and validation
- `performance` - Performance optimization plugins
- `ui` - User interface enhancements
- `integration` - External system integrations
- `utility` - General utility plugins

### Custom Categories

Plugin authors can define custom categories following these rules:
- Lowercase letters and hyphens only
- 3-20 characters
- Must be unique within the marketplace
- Must include description in metadata

## File Naming Conventions

### Valid Examples

```
scan_enhanced_550e8400-e29b-41d4-a716-446655440000.v1.2.3.py
security_checker_a1b2c3d4-e5f6-7890-abcd-ef1234567890.v0.5.1.py
ml_classifier_98765432-10ba-dcfe-9876-543210abcdef.v2.0.0.py
```

### Invalid Examples

```
scan_enhanced.py                    # Missing UUID and version
scan_enhanced_v1.0.0.py            # Missing UUID
scan_enhanced_uuid.v1.0.0.py       # Invalid UUID format
scan-enhanced_550e8400.v1.0.0.py   # Invalid name format
```

## Implementation Requirements

### Plugin Base Class Updates

```python
from uuid import UUID, uuid4
from typing import Dict, Any, Optional
import re

class PluginBase:
    """Base class for all NoDupeLabs plugins with UUID support."""
    
    def __init__(self, metadata: Dict[str, Any]):
        self._validate_metadata(metadata)
        self.uuid: UUID = UUID(metadata["uuid"])
        self.name: str = metadata["name"]
        self.display_name: str = metadata["display_name"]
        self.version: str = metadata["version"]
        self.description: str = metadata["description"]
        self.author: str = metadata["author"]
        self.category: str = metadata["category"]
        self.dependencies: list = metadata.get("dependencies", [])
        self.tags: list = metadata.get("tags", [])
        self.marketplace_id: str = metadata["marketplace_id"]
    
    @staticmethod
    def _validate_metadata(metadata: Dict[str, Any]) -> None:
        """Validate plugin metadata according to specification."""
        required_fields = [
            "uuid", "name", "display_name", "version", 
            "description", "author", "category", "compatibility",
            "marketplace_id"
        ]
        
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Missing required metadata field: {field}")
        
        # Validate UUID
        try:
            uuid_obj = UUID(metadata["uuid"])
            if uuid_obj.version != 4:
                raise ValueError("Plugin UUID must be version 4")
        except ValueError as e:
            raise ValueError(f"Invalid UUID format: {e}")
        
        # Validate name format
        if not re.match(r'^[a-z][a-z0-9_]{1,49}$', metadata["name"]):
            raise ValueError("Plugin name must be 2-50 characters, lowercase letters, numbers, and underscores only")
        
        # Validate version format
        if not re.match(r'^v\d+\.\d+\.\d+$', metadata["version"]):
            raise ValueError("Version must follow semantic versioning format (v1.2.3)")
    
    @classmethod
    def generate_uuid(cls) -> UUID:
        """Generate a new UUID v4 for plugin identification."""
        return uuid4()
    
    @classmethod
    def generate_filename(cls, name: str, version: str) -> str:
        """Generate a UUID-based filename for the plugin."""
        plugin_uuid = cls.generate_uuid()
        return f"{name}_{plugin_uuid}.v{version}.py"
```

### Plugin Discovery Updates

```python
import re
from pathlib import Path
from typing import List, Dict, Any

class PluginDiscovery:
    """Enhanced plugin discovery with UUID-based identification."""
    
    PLUGIN_FILENAME_PATTERN = re.compile(
        r'^(?P<name>[a-z][a-z0-9_]{1,49})_'  # Plugin name
        r'(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})'  # UUID v4
        r'\.v(?P<version>\d+\.\d+\.\d+)\.py$'  # Version
    )
    
    @classmethod
    def discover_plugins(cls, plugin_dir: Path) -> List[Dict[str, Any]]:
        """Discover and validate plugins in the specified directory."""
        plugins = []
        
        for plugin_file in plugin_dir.glob("*.py"):
            match = cls.PLUGIN_FILENAME_PATTERN.match(plugin_file.name)
            if not match:
                continue  # Skip files that don't match UUID naming convention
            
            try:
                plugin_data = cls._load_plugin_metadata(plugin_file)
                plugins.append({
                    "file_path": plugin_file,
                    "metadata": plugin_data,
                    "name": match.group("name"),
                    "uuid": match.group("uuid"),
                    "version": match.group("version")
                })
            except Exception as e:
                # Log error but continue with other plugins
                print(f"Failed to load plugin {plugin_file.name}: {e}")
        
        return plugins
    
    @staticmethod
    def _load_plugin_metadata(plugin_file: Path) -> Dict[str, Any]:
        """Load and validate plugin metadata from file."""
        # Implementation to extract PLUGIN_METADATA from plugin file
        # This would typically use AST parsing or import inspection
        pass
```

## Security Considerations

### UUID Security

- UUIDs must be generated using cryptographically secure methods
- UUIDs should not contain predictable patterns
- UUIDs should not be derived from plugin names or other predictable data

### Plugin Validation

- All plugins must be validated against the UUID specification
- Invalid plugins should be rejected during discovery
- Plugin metadata must be validated before loading
- Dependencies should be verified for security vulnerabilities

### Marketplace Security

- Marketplace should validate UUID format before accepting plugins
- Plugin updates must maintain the same UUID
- Version changes should be tracked for security updates

## Migration Strategy

### Phase 1: Specification Implementation
1. Update plugin base classes with UUID support
2. Implement plugin discovery with UUID validation
3. Add UUID generation utilities

### Phase 2: Plugin Updates
1. Update existing plugins to use UUID naming
2. Add metadata validation to plugin loading
3. Update plugin discovery mechanisms

### Phase 3: Marketplace Integration
1. Update marketplace to require UUID naming
2. Implement plugin categorization based on metadata
3. Add version tracking and update mechanisms

## Backward Compatibility

### Legacy Plugin Support
- Legacy plugins (without UUIDs) will be supported during transition
- Legacy plugins will be assigned temporary UUIDs
- Legacy plugins will be marked for migration

### Deprecation Timeline
- **Phase 1**: UUID specification available, legacy plugins supported
- **Phase 2**: New plugins must use UUID specification
- **Phase 3**: Legacy plugin support deprecated
- **Phase 4**: Legacy plugin support removed

## Testing Requirements

### Unit Tests
- UUID generation and validation
- Plugin metadata validation
- File naming convention validation
- Plugin discovery with UUID support

### Integration Tests
- Plugin loading with UUID metadata
- Marketplace integration with UUID plugins
- Version tracking and updates
- Security validation of UUID-based plugins

### Performance Tests
- Plugin discovery performance with UUID validation
- Metadata loading performance
- UUID generation performance under load

## Examples

### Complete Plugin Example

```python
# scan_enhanced_550e8400-e29b-41d4-a716-446655440000.v1.2.3.py

from uuid import UUID
from nodupe.core.plugin_system.base import PluginBase

PLUGIN_METADATA = {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "name": "scan_enhanced",
    "display_name": "Enhanced File Scanner",
    "version": "1.2.3",
    "description": "Advanced file scanning with ML integration",
    "author": "NoDupeLabs Team",
    "category": "scanning",
    "dependencies": ["numpy>=1.20.0", "scikit-learn>=1.0.0"],
    "compatibility": {
        "python": ">=3.9",
        "nodupe_core": ">=1.0.0"
    },
    "tags": ["scanning", "ml", "performance"],
    "marketplace_id": "scan_enhanced_550e8400-e29b-41d4-a716-446655440000"
}

class ScanEnhancedPlugin(PluginBase):
    """Enhanced file scanning plugin with UUID-based identification."""
    
    def __init__(self):
        super().__init__(PLUGIN_METADATA)
    
    def scan(self, file_path: str) -> Dict[str, Any]:
        """Perform enhanced file scanning."""
        # Implementation here
        pass
```

This specification ensures that all NoDupeLabs plugins follow a consistent, secure, and collision-free naming convention while enabling advanced marketplace features and preventing file corruption issues.
