# NoDupeLabs Architecture

**Version:** 1.0
**Last Updated:** 2025-12-05
**Status:** Living Document

---

## Table of Contents

1. [Overview](#overview)
2. [Design Philosophy](#design-philosophy)
3. [System Architecture](#system-architecture)
4. [Module Hierarchy](#module-hierarchy)
5. [Design Patterns](#design-patterns)
6. [Dependency Flow](#dependency-flow)
7. [Extension Points](#extension-points)
8. [Data Flow](#data-flow)
9. [Testing Architecture](#testing-architecture)

---

## Overview

NoDupeLabs is a context-aware file deduplication system built with modularity and extensibility as core principles. The architecture follows a **layered design** with clear separation of concerns, dependency injection for testability, and pluggable backends for AI and similarity search.

### Key Characteristics

- **Modularity Score:** 9/10 (targeting 10/10 with complete documentation)
- **Architecture Style:** Layered + Dependency Injection + Plugin System
- **Language:** Python 3.13+
- **Key Principles:** SOLID, separation of concerns, dependency inversion

### High-Level Components

```text
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│  (Entry points, argument parsing, command dispatch)          │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                     Command Layer                            │
│  (Thin wrappers that coordinate dependencies)                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Container Layer (DI)                        │
│  (Dependency injection, service lifecycle management)        │
└─────┬──────────────┬──────────────┬────────────────┬────────┘
      │              │              │                │
┌─────▼──────┐ ┌────▼─────┐ ┌──────▼───────┐ ┌─────▼────────┐
│Orchestrators│ │  Core    │ │  Subsystems  │ │   Plugins    │
│  (Workflow) │ │ Services │ │ (AI, Search) │ │  (Hooks)     │
└─────┬──────┘ └────┬─────┘ └──────┬───────┘ └─────┬────────┘
      │              │              │                │
      └──────────────┴──────────────┴────────────────┘
                           │
                  ┌────────▼────────┐
                  │   Utilities     │
                  │ (Hash, FS, I/O) │
                  └─────────────────┘
```

---

## Design Philosophy

### 1. Separation of Concerns

Each module has a **single, well-defined responsibility**:

- **Commands** - Thin CLI wrappers (no business logic)
- **Orchestrators** - Coordinate workflows (no implementation details)
- **Services** - Provide core functionality (database, logging, metrics)
- **Utilities** - Low-level operations (no dependencies on higher layers)

### 2. Dependency Inversion

High-level modules don't depend on low-level modules. Both depend on abstractions:

```python
# ❌ BAD: Command directly creates dependencies
def cmd_scan(args):
    db = DB(args.db_path)
    logger = JsonlLogger(args.log_dir)
    # ... business logic

# ✅ GOOD: Command receives dependencies via injection
def cmd_scan(args, cfg):
    container = get_container()
    orchestrator = container.get_scanner()  # DI!
    return orchestrator.scan(...)
```

### 3. Open/Closed Principle

The system is **open for extension, closed for modification**:

- Add new commands without modifying CLI code (command registry)
- Add new AI backends without modifying scan logic (backend factory)
- Add new similarity backends without modifying search code (plugin system)

### 4. Interface Segregation

Modules expose only what's necessary through **explicit `__all__` exports**:

```python
# nodupe/scan/__init__.py
__all__ = [
    "ScanValidator",      # Public API
    "ScanOrchestrator",   # Public API
    "iter_files",         # Public API
    # _internal_helper NOT exported - implementation detail
]
```

---

## System Architecture

### Layer 1: CLI Entry Point

**Location:** `nodupe/cli` (or main entry point)
**Responsibility:** Parse arguments, dispatch to commands
**Dependencies:** `commands` package only

```python
# Pseudocode
def main():
    args = parse_args()
    command_func = COMMANDS[args.command]  # Registry lookup
    return command_func(args, config)
```

### Layer 2: Commands

**Location:** `nodupe/commands/`
**Responsibility:** Thin wrappers that validate inputs and coordinate dependencies
**Key Pattern:** Dependency Injection via Container

**Example Structure:**

```text
commands/
├── __init__.py          # Command registry (COMMANDS dict)
├── scan.py              # Scan command (4 imports only!)
├── plan.py              # Deduplication planning
├── apply.py             # Execute deduplication plan
├── rollback.py          # Revert operations
├── verify.py            # Verify checksums
├── mount.py             # FUSE filesystem
├── archive.py           # Archive operations
└── similarity.py        # Similarity search commands
```

### Layer 3: Dependency Injection Container

**Location:** `nodupe/container.py`
**Responsibility:** Create and manage service lifecycles
**Key Pattern:** Service Locator + Factory

**Services Provided:**

- `get_db()` - Database facade
- `get_telemetry()` - Unified logging + metrics
- `get_scanner()` - Scan orchestrator with all dependencies
- `get_classifier()` - NSFW classifier
- `get_backend()` - AI backend for embeddings
- `get_plugin_manager()` - Plugin event system

### Layer 4: Orchestrators

**Location:** `nodupe/scan/orchestrator.py`, etc.
**Responsibility:** Coordinate complex workflows
**Key Pattern:** Orchestrator Pattern

**Example: ScanOrchestrator**

```python
class ScanOrchestrator:
    def __init__(self, db, telemetry, backend, plugin_manager):
        self.db = db              # Injected
        self.telemetry = telemetry  # Injected
        self.backend = backend      # Injected
        self.pm = plugin_manager    # Injected

    def scan(self, roots, hash_algo, workers, ...):
        # Coordinate: scanning → hashing → embedding → storage
        # But don't implement low-level details
```

### Layer 5: Core Services

**Locations:**

- `nodupe/db/` - Database operations
- `nodupe/telemetry.py` - Unified logging + metrics
- `nodupe/plugins.py` - Plugin manager
- `nodupe/config/` - Configuration management

### Layer 6: Subsystems

**Modular subsystems with clear boundaries:**

#### Scan Subsystem (`nodupe/scan/`)

```text
scan/
├── __init__.py          # Public API
├── orchestrator.py      # Workflow coordination
├── walker.py            # File tree traversal
├── hasher.py            # Hash computation (threaded)
├── processor.py         # File processing
├── progress.py          # Progress tracking
└── validator.py         # Precondition validation
```

#### AI Subsystem (`nodupe/ai/`)

- **Purpose:** NSFW classification and embedding computation
- **Pattern:** Factory + Abstract Backend
- **Backends:** ONNX Runtime, CPU fallback

#### Similarity Subsystem (`nodupe/similarity/`)

- **Purpose:** Vector similarity search for near-duplicates
- **Pattern:** Factory + Plugin System
- **Backends:** FAISS, brute-force

### Layer 7: Utilities

**Location:** `nodupe/utils/`
**Responsibility:** Low-level operations (no business logic)
**Dependencies:** None (or only stdlib)

```text
utils/
├── hashing.py           # File hashing utilities
├── filesystem.py        # File operations, MIME detection
├── media.py             # Video frame extraction
└── compression.py       # Archive handling
```

---

## Module Hierarchy

### Dependency Rules

**One-way flow (no circular dependencies):**

```text
CLI → Commands → Container → Orchestrators → Services → Utilities
                    ↓
                Subsystems (scan, ai, similarity)
                    ↓
                 Utilities
```

**Import Rules:**

1. ✅ **Higher layers CAN import lower layers**
   - `commands/scan.py` can import `container`
   - `orchestrator.py` can import `db`, `telemetry`

2. ❌ **Lower layers CANNOT import higher layers**
   - `utils/hashing.py` CANNOT import `commands`
   - `db/connection.py` CANNOT import `orchestrator`

3. ✅ **Subsystems are isolated**
   - `scan/` doesn't import from `similarity/`
   - `ai/` doesn't import from `scan/`
   - They coordinate through orchestrators

### Package Structure

```text
nodupe/
├── __init__.py              # Public API exports
├── container.py             # DI container
├── cli                      # Entry point (separate package/file)
│
├── commands/                # Layer 2: Commands
│   ├── __init__.py         # COMMANDS registry
│   └── *.py                # Individual commands
│
├── scan/                    # Subsystem: File scanning
│   ├── __init__.py         # Public API
│   ├── orchestrator.py     # Workflow coordinator
│   └── *.py                # Implementation modules
│
├── ai/                      # Subsystem: AI backends
│   ├── __init__.py         # Public API
│   └── backends/           # Pluggable backends
│
├── similarity/              # Subsystem: Similarity search
│   ├── __init__.py         # Public API
│   ├── index.py            # Index operations
│   └── backends/           # Pluggable backends
│
├── db/                      # Core: Database
│   ├── __init__.py
│   ├── connection.py       # DB facade
│   └── files.py            # File operations
│
├── config/                  # Core: Configuration
│   ├── __init__.py
│   └── schema.py           # Validation
│
├── plugins.py               # Core: Plugin system
├── telemetry.py            # Core: Logging + metrics
├── logger.py               # Legacy logger (deprecated)
├── metrics.py              # Legacy metrics (deprecated)
│
├── utils/                   # Utilities (no dependencies)
│   ├── hashing.py
│   ├── filesystem.py
│   └── media.py
│
├── categorizer.py          # File categorization
├── exporter.py             # Metadata export
├── validator.py            # Schema validation
├── nsfw_classifier.py      # NSFW detection
├── mount.py                # FUSE filesystem
├── planner.py              # Deduplication planning
├── applier.py              # Plan execution
├── archiver.py             # Archive operations
└── vendor/                  # Vendored dependencies
```

---

## Design Patterns

### 1. Command Registry Pattern

**Problem:** CLI hardcoded 13 command imports
**Solution:** Central registry for dynamic command discovery

**Implementation:**

```python
# nodupe/commands/__init__.py
COMMANDS = {
    "scan": cmd_scan,
    "plan": cmd_plan,
    "apply": cmd_apply,
    # ...
}

# CLI looks up commands dynamically
command_func = COMMANDS[args.command]
```

**Benefits:**

- Add commands without modifying CLI
- Easy to list available commands
- Plugin system can extend registry

### 2. Dependency Injection (DI)

**Problem:** Commands tightly coupled to service implementations
**Solution:** Service Container injects dependencies

**Implementation:**

```python
# nodupe/container.py
class ServiceContainer:
    def get_scanner(self):
        db = self.get_db()
        telemetry = self.get_telemetry()
        backend = self.get_backend()
        pm = self.get_plugin_manager()
        return ScanOrchestrator(db, telemetry, backend, pm)

# nodupe/commands/scan.py
def cmd_scan(args, cfg):
    container = get_container()
    orchestrator = container.get_scanner()  # All deps injected!
    return orchestrator.scan(...)
```

**Benefits:**

- Testable (inject mocks)
- Flexible (swap implementations)
- Decoupled (commands don't create services)

### 3. Orchestrator Pattern

**Problem:** Complex workflows scattered across modules
**Solution:** Dedicated orchestrator coordinates subsystems

**Implementation:**

```python
class ScanOrchestrator:
    def __init__(self, db, telemetry, backend, pm):
        # Dependencies injected
        pass

    def scan(self, roots, hash_algo, workers, ...):
        # 1. Validate preconditions
        # 2. Scan files (walker)
        # 3. Compute hashes (hasher)
        # 4. Compute embeddings (backend)
        # 5. Store in database (db)
        # 6. Export metadata (exporter)
        # 7. Emit events (plugin_manager)
```

**Benefits:**

- Single place for workflow logic
- Easy to understand sequence
- Can add steps without modifying commands

### 4. Factory Pattern

**Problem:** Need different backend implementations at runtime
**Solution:** Factory selects backend based on availability

**Implementation:**

```python
# nodupe/ai/backends/__init__.py
def choose_backend():
    try:
        return ONNXBackend()  # Fast GPU/CPU backend
    except ImportError:
        return CPUBackend()   # Pure Python fallback

# Usage (injected via container)
backend = choose_backend()
embedding = backend.compute_embedding(image_path)
```

**Benefits:**

- Graceful degradation (ONNX → CPU fallback)
- Easy to add new backends
- Uniform interface (BaseBackend)

### 5. Plugin System (Event Hooks)

**Problem:** Users want to extend behavior without modifying code
**Solution:** Event-driven plugin system with hooks

**Implementation:**

```python
# nodupe/plugins.py
class PluginManager:
    def emit(self, event_name, data):
        # Call all registered hook functions
        pass

# In orchestrator
self.pm.emit('scan:start', {'roots': roots})
self.pm.emit('file:scanned', {'path': path, 'hash': hash_val})
self.pm.emit('scan:complete', {'files_scanned': count})
```

**Benefits:**

- Users can hook into workflow
- No need to modify core code
- Extensible via external plugins

---

## Dependency Flow

### Initialization Flow

```text
1. main() entry point
   ↓
2. Parse CLI arguments
   ↓
3. Load configuration (nodupe.yml)
   ↓
4. Create ServiceContainer (container.py)
   ↓
5. Look up command in COMMANDS registry
   ↓
6. Call command function (e.g., cmd_scan)
   ↓
7. Command gets orchestrator from container
   ↓
8. Orchestrator executes workflow
```

### Scan Workflow (Example)

```text
cmd_scan (commands/scan.py)
  ↓
ServiceContainer.get_scanner()
  ↓
ScanOrchestrator (scan/orchestrator.py)
  ├─→ ScanValidator (scan/validator.py) - Validate inputs
  ├─→ iter_files (scan/walker.py) - Traverse file tree
  ├─→ threaded_hash (scan/hasher.py) - Compute hashes
  ├─→ BaseBackend.compute_embedding (ai/backends/) - AI embeddings
  ├─→ DB.upsert_files (db/connection.py) - Store in database
  ├─→ write_folder_meta (exporter.py) - Export metadata
  └─→ PluginManager.emit (plugins.py) - Notify plugins
```

### Service Dependencies

```text
ScanOrchestrator
  ├─ DB (database facade)
  │   └─ sqlite3 (stdlib)
  │
  ├─ Telemetry (logging + metrics)
  │   ├─ JsonlLogger
  │   └─ Metrics
  │
  ├─ BaseBackend (AI backend)
  │   ├─ ONNXBackend (optional)
  │   └─ CPUBackend (fallback)
  │
  └─ PluginManager (event system)
      └─ asyncio (for async plugins)
```

---

## Extension Points

### 1. Adding a New Command

See [ADDING_COMMANDS.md](ADDING_COMMANDS.md) for detailed guide.

**Quick Overview:**

1. Create `nodupe/commands/my_command.py`
2. Implement `cmd_my_command(args, cfg)` function
3. Add to `COMMANDS` registry in `commands/__init__.py`
4. Add argument parser configuration

**No CLI modification needed!**

### 2. Adding a New AI Backend

See [EXTENDING_BACKENDS.md](EXTENDING_BACKENDS.md) for detailed guide.

**Quick Overview:**

1. Create `nodupe/ai/backends/my_backend.py`
2. Inherit from `BaseBackend`
3. Implement `compute_embedding()` method
4. Add to backend selection logic in `choose_backend()`

### 3. Adding a New Similarity Backend

See [EXTENDING_BACKENDS.md](EXTENDING_BACKENDS.md) for detailed guide.

**Quick Overview:**

1. Create plugin in `nodupe/similarity/backends/my_backend.py`
2. Inherit from base interface
3. Implement `add()`, `search()`, `save()`, `load()` methods
4. Register backend in plugin system

### 4. Adding Plugin Hooks

Users can extend behavior by registering hooks:

```python
# In user's plugin file
from nodupe.plugins import pm

@pm.hook
def on_file_scanned(path, hash_value):
    print(f"File scanned: {path} -> {hash_value}")
```

**Available hooks:**

- `scan:start`, `scan:complete`
- `file:scanned`, `file:duplicated`
- `plan:created`, `plan:applied`
- Custom hooks can be added

---

## Data Flow

### File Scanning Flow

```text
User Invokes: nodupe scan /data

1. CLI parses arguments
   ↓
2. cmd_scan validates inputs
   ↓
3. ScanOrchestrator.scan() begins
   ↓
4. iter_files() walks file tree
   ↓  (yields paths)
5. process_file() gathers metadata
   ↓  (stat, MIME, permissions)
6. threaded_hash() computes checksums
   ↓  (parallel workers)
7. BaseBackend.compute_embedding() (optional)
   ↓  (for images/videos)
8. DB.upsert_files() stores results
   ↓  (SQLite database)
9. write_folder_meta() exports metadata
   ↓  (meta.json per folder)
10. PluginManager.emit() notifies plugins
```

### Database Schema

```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    size INTEGER NOT NULL,
    hash TEXT NOT NULL,
    mime TEXT,
    permissions TEXT,
    mtime REAL,
    embedding BLOB,  -- Optional AI embedding
    -- ... other fields
);

CREATE INDEX idx_hash ON files(hash);
CREATE INDEX idx_size ON files(size);
```

### Configuration Flow

```text
1. Load nodupe.yml (YAML config file)
   ↓
2. Merge with defaults (config/schema.py)
   ↓
3. Validate schema (validator.py)
   ↓
4. Store in ServiceContainer.config
   ↓
5. Commands access via container.config
```

---

## Testing Architecture

### Unit Testing Strategy

**Dependency Injection enables easy mocking:**

```python
def test_scan_orchestrator():
    # Create mocks
    mock_db = Mock(spec=DB)
    mock_telemetry = Mock(spec=Telemetry)
    mock_backend = Mock(spec=BaseBackend)
    mock_pm = Mock(spec=PluginManager)

    # Inject mocks
    orchestrator = ScanOrchestrator(
        db=mock_db,
        telemetry=mock_telemetry,
        backend=mock_backend,
        plugin_manager=mock_pm
    )

    # Test in isolation
    orchestrator.scan(roots=['/tmp'], hash_algo='sha256', ...)

    # Verify interactions
    mock_db.upsert_files.assert_called_once()
```

### Integration Testing Strategy

**Use container overrides for integration tests:**

```python
def test_scan_command_integration(tmp_path):
    # Create test container
    container = ServiceContainer()

    # Override services for testing
    test_db = DB(tmp_path / "test.db")
    container.override('db', test_db)

    # Run actual command
    from nodupe.commands import cmd_scan
    result = cmd_scan(args, cfg)

    # Verify end-to-end behavior
    assert result == 0
    assert test_db.count_files() > 0
```

### Testing Pyramid

```text
           ┌─────────┐
          /  E2E (5%) \     Full CLI tests
         /─────────────\
        / Integration   \   Component tests with real services
       /     (15%)      \
      /───────────────────\
     /    Unit Tests       \  Individual module tests
    /       (80%)          \
   /─────────────────────────\
```

---

## Performance Considerations

### 1. Parallel Scanning

- **File walking:** Single-threaded (limited by filesystem)
- **Hashing:** Multi-threaded pool (configurable workers)
- **Embeddings:** Batch processing (GPU acceleration if available)

### 2. Database Optimization

- **Batch inserts:** Use transactions for bulk operations
- **Indexes:** Hash and size columns indexed
- **Connection pooling:** Reuse connections across operations

### 3. Memory Management

- **Streaming:** Process files one at a time (no full loading)
- **Chunked hashing:** Read files in chunks (default 8MB)
- **Lazy loading:** Load embeddings only when needed

---

## Security Considerations

### 1. Path Traversal Protection

- Validate all paths before operations
- Use `Path.resolve()` to prevent `../` attacks
- Respect filesystem permissions

### 2. SQL Injection Prevention

- Use parameterized queries only
- Never concatenate user input into SQL

### 3. Command Injection Protection

- Use `subprocess` with list arguments (not shell=True)
- Validate all external command inputs
- Timeout mechanisms for external processes

---

## Migration Guide

### From Monolithic to Modular

The codebase has evolved from a monolithic design to the current modular architecture:

**Before (v0.x):**

```python
# Everything in scanner.py (1000+ lines)
def scan_files(roots):
    # Walking + hashing + embedding + storage all mixed
```

**After (v1.0+):**

```python
# Separated into modules
from nodupe.scan import iter_files, threaded_hash
from nodupe.ai import choose_backend
from nodupe.db import DB

# Clear responsibilities
```

---

## Conclusion

NoDupeLabs architecture achieves **9/10 modularity** through:

1. ✅ **Clear Layering** - One-way dependency flow
2. ✅ **Dependency Injection** - Testable, flexible services
3. ✅ **Command Registry** - Extensible without modification
4. ✅ **Orchestrator Pattern** - Coordinated workflows
5. ✅ **Factory Pattern** - Pluggable backends
6. ✅ **Public APIs** - Clear boundaries via `__all__` exports
7. ✅ **Single Responsibility** - Each module has one job
8. ✅ **No Circular Dependencies** - Clean DAG structure

**Next:** See specific guides for common tasks:

- [DEPENDENCY_INJECTION.md](DEPENDENCY_INJECTION.md) - Using the DI container
- [ADDING_COMMANDS.md](ADDING_COMMANDS.md) - Creating new commands
- [EXTENDING_BACKENDS.md](EXTENDING_BACKENDS.md) - Adding AI/similarity backends

---

**Document Version:** 1.0
**Maintainer:** NoDupeLabs Team
**License:** Apache-2.0
