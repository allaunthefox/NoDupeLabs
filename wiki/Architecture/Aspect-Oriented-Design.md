# Aspect-Oriented Design (AOD)

NoDupeLabs implements a **minimal-core, plugin-first** architecture based on Aspect-Oriented Design principles. This ensures that the core scanning engine remains lean and portable, while all specialized logic is externalized into swappable plugins.

## Core Interfaces (Contracts)

The system defines formal contracts in `nodupe/core/` that all implementations must follow.

| Aspect | Interface | Standard Implementation |
|--------|-----------|-------------------------|
| **Hashing** | `HasherInterface` | `nodupe/plugins/hashing/` |
| **MIME Detection** | `MIMEDetectionInterface` | `nodupe/plugins/mime/` |
| **Archive Handling** | `ArchiveHandlerInterface` | `nodupe/plugins/archive/` |

## Decoupling Strategy

Core components do not instantiate specific implementations. Instead, they request services from the `ServiceContainer`.

### Example: FileWalker Decoupling
The `FileWalker` previously had a hard dependency on `ArchiveHandler`. It now uses **Dependency Injection**:

```python
# Preferred approach
self._archive_handler = global_container.get_service('archive_handler_service')
if not self._archive_handler:
    self._archive_handler = DefaultFallback()
```

## Benefits

1.  **Zero-Dependency Core:** The core can run in restricted environments with only the Python standard library.
2.  **Hardware Acceleration:** Plugins can provide specialized implementations (e.g., GPU-accelerated hashing) without changing core code.
3.  **Scalability:** New file formats or protocols can be added by dropping in a new plugin directory.
4.  **Persistent Standards:** All interactions across these aspects obey the system-wide [Logging Policy](../Operations/Logging-Policy.md).
