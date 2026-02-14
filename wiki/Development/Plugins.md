# Plugin Development

## Overview

NoDupeLabs uses a plugin-based architecture. Plugins extend core functionality through standardized interfaces.

## Plugin Types

| Type | Purpose |
|------|---------|
| `database` | Data persistence |
| `similarity` | Content comparison |
| `time_sync` | Timestamp handling |
| `commands` | CLI extensions |
| `ml` | Machine learning |
| `gpu` | GPU acceleration |
| `network` | Network operations |
| `video` | Video processing |

## Creating a Plugin

### Structure

```python
from nodupe.core.plugins import SimilarityCommandPlugin

class MyPlugin(SimilarityCommandPlugin):
    """Plugin description."""
    
    name: str = "my_plugin"
    version: str = "1.0.0"
    
    def execute(self, args):
        """Execute the plugin."""
        pass
```

### Plugin Interface

Implement the appropriate interface based on plugin type:

- `SimilarityCommandPlugin` - For similarity detection
- `DatabasePlugin` - For database operations
- `CommandPlugin` - For CLI commands

## Registration

Plugins are auto-discovered from the `nodupe/plugins/` directory.

## Example

See existing plugins in `nodupe/plugins/`:
- `database/features.py`
- `similarity/__init__.py`
- `time_sync/time_sync.py`

## Testing

```bash
pytest tests/plugins/ -v
```

## Best Practices

1. Follow existing plugin patterns
2. Add comprehensive docstrings
3. Include tests in `tests/plugins/`
4. Use type annotations
