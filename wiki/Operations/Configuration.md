# Configuration

## Config File

NoDupeLabs uses `nodupe.toml` for configuration.

## Location

Searches in order:
1. `./nodupe.toml` (current directory)
2. `~/.nodupe/config`
3. Default values

## Options

### Database

```toml
[database]
path = ".nodupe/database.db"
auto_vacuum = true
```

### Scanning

```toml
[scanning]
threads = 4
hash_size = 8192
follow_symlinks = false
```

### Performance

```toml
[performance]
max_memory = "1GB"
cache_size = 1000
```

### Logging

```toml
[logging]
level = "INFO"
file = "nodupe.log"
```

## Environment Variables

- `NODUPE_CONFIG` - Override config path
- `NODUPE_DB_PATH` - Override database path

## CLI Override

Many options can be passed via CLI:

```bash
nodupe scan --threads 8 /path
```
