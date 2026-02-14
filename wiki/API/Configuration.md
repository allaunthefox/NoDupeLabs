# Configuration API

## ConfigManager

Manages application configuration.

### Constructor

```python
from nodupe.core.config import ConfigManager

config = ConfigManager()
```

### Methods

#### load_config

```python
def load_config(self, config_path: Optional[str] = None) -> dict[str, Any]
```

Load configuration from file or defaults.

**Parameters:**
- `config_path`: Path to config file (optional)

**Returns:** Configuration dictionary

#### get

```python
def get(self, key: str, default: Any = None) -> Any
```

Get configuration value.

**Parameters:**
- `key`: Configuration key
- `default`: Default value if key not found

**Returns:** Configuration value

#### set

```python
def set(self, key: str, value: Any) -> None
```

Set configuration value.

**Parameters:**
- `key`: Configuration key
- `value`: Configuration value

### Configuration File Format

TOML format:

```toml
[database]
path = ".nodupe/database.db"
timeout = 30

[deduplication]
hash_algorithm = "sha256"
chunk_size = 8192

[performance]
max_workers = 4
cache_size = 1000

[rollback]
enabled = true
backup_dir = ".nodupe/backups"
max_snapshots = 10
```
