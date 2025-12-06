# Python 3.13+ Features in NoDupeLabs

## Runtime Detection (`nodupe/runtime.py`)

```python
from nodupe.runtime import get_runtime_info, is_gil_disabled, get_optimal_executor

# Check all features
print(get_runtime_info())
# {'python_version': '3.13', 'gil_disabled': False, 'has_zstd': True, ...}

# Check GIL status (free-threaded Python)
if is_gil_disabled():
    print("Running GIL-free - threads can scale!")

# Get best executor for CPU work
executor = get_optimal_executor()  # 'thread' | 'process' | 'interpreter'
```

## Compression (`nodupe/utils/compression.py`)

Uses zstd when available, falls back to gzip:

```python
from nodupe.utils.compression import compress, decompress, has_zstd

data = b"your data here" * 1000
compressed = compress(data)  # Auto-selects best algorithm
original = decompress(compressed)
```

## Features Detected

| Feature | Python | Detection |
|---------|--------|-----------|
| Free-threading (no GIL) | 3.13+ | `sys._is_gil_enabled()` |
| Subinterpreters | 3.14+ | `InterpreterPoolExecutor` |
| zstd stdlib | 3.14+ | `compression.zstd` |
| zstandard (third-party) | any | `pip install zstandard` |

## Integration Points

- **db/connection.py**: Uses `is_gil_disabled()` to choose thread vs process writer
- **Logging**: Can use zstd compression for rotated logs
- **Exports**: Compressed metadata files via `compress_file()`
