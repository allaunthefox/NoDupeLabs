# Architecture Overview

## System Design

NoDupeLabs uses a plugin-based architecture with a modular core system.

## Core Components

### nodupe/core/

| Module | Purpose |
|--------|---------|
| `loader.py` | File loading and processing |
| `config.py` | Configuration management |
| `database/` | SQLite database operations |
| `plugin_system/` | Plugin lifecycle management |
| `scan/` | File scanning utilities |

### nodupe/plugins/

| Plugin Type | Purpose |
|-------------|---------|
| `database/` | Data persistence |
| `similarity/` | Content comparison |
| `time_sync/` | Timestamp synchronization |
| `commands/` | CLI commands |
| `ml/` | Machine learning |
| `gpu/` | GPU acceleration |

## Data Flow

```
1. User runs CLI command
   ↓
2. Command validates input
   ↓
3. Core system scans files
   ↓
4. Plugins process results
   ↓
5. Database stores metadata
   ↓
6. Results displayed to user
```

## Plugin System

Plugins extend functionality through a standardized interface:

```python
class SimilarityCommandPlugin:
    name: str
    def execute(self, args) -> Result:
        ...
```

## Testing

- pytest-based test suite
- 1023 tests collected
- Coverage: 16.5%
- Docstring coverage: 100%

## See Also

- [Plugin Development](../Development/Plugins.md)
- [API Reference](../API/CLI.md)
