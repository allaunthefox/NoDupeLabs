# NoDupeLabs Architecture

## Overview

This document outlines the modular architecture for NoDupeLabs with hard isolation between the core loader/orchestrator and all other functions.

## Core Architecture Principles

1. **Hard Isolation**: Core loader must be completely isolated from optional functionality
2. **Graceful Degradation**: All optional features must fail gracefully and fall back to standard library
3. **Plugin-Based**: Non-core functionality implemented as plugins with clear interfaces
4. **Dependency Injection**: Core services injected rather than hard-coded
5. **Standard Library Fallback**: When all else fails, use pure Python standard library

## Module Structure

### 1. Core Loader/Orchestrator (Mandatory)

**Location**: `nodupe/core/`

**Responsibilities**:
- CLI entry point and argument parsing
- Basic configuration loading
- Core command routing
- Plugin management
- Dependency injection container
- Error handling and graceful degradation

**Key Components**:
- `main.py` - Entry point with minimal dependencies
- `cli/` - CLI parsing and routing
- `container.py` - Service container for DI
- `plugin_system/` - Plugin management system
- `deps.py` - Dependency management with graceful fallback
- `config.py` - Configuration loading
- `loader.py` - Core loader

**Dependencies**: Standard library only

### 2. Database Layer (Core)

**Location**: `nodupe/core/database/`

**Responsibilities**:
- File metadata storage
- Duplicate detection
- Basic indexing
- Transaction management

**Key Components**:
- `connection.py` - SQLite connection management with connection pooling
- `files.py` - File repository with CRUD operations
- `embeddings.py` - Embedding storage with model versioning
- `schema.py` - Database schema management
- `repository.py` - Repository pattern implementation
- `transactions.py` - Transaction management
- `indexing.py` - Indexing strategies

**Dependencies**: sqlite3 (standard library)

### 3. File Processing (Core)

**Location**: `nodupe/core/scan/`

**Responsibilities**:
- File discovery and walking
- Hashing and metadata extraction
- Progress tracking
- Incremental scanning

**Key Components**:
- `walker.py` - File system traversal with filtering and error handling
- `processor.py` - File metadata extraction with duplicate detection
- `hasher.py` - Cryptographic hashing with multiple algorithms
- `progress.py` - Progress tracking with time estimation
- `file_info.py` - File information utilities

**Dependencies**: Standard library + hashlib

### 4. Utilities (Core)

**Location**: `nodupe/core/`

**Responsibilities**:
- Filesystem operations
- Hashing algorithms
- Compression utilities
- MIME type detection
- Security and validation
- Resource management

**Key Components**:
- `filesystem.py` - Path operations and MIME detection
- `compression.py` - Compression with fallback
- `mime_detection.py` - MIME type detection
- `security.py` - Security utilities
- `validators.py` - Validation utilities
- `limits.py` - Resource limit management
- `incremental.py` - Incremental processing
- `parallel.py` - Parallel processing
- `mmap_handler.py` - Memory-mapped file handling
- `pools.py` - Resource pooling
- `errors.py` - Error handling
- `logging.py` - Logging utilities
- `version.py` - Version management
- `api.py` - Stable API definitions

**Dependencies**: Standard library only

### 5. Cache System (Core)

**Location**: `nodupe/core/cache/`

**Responsibilities**:
- Hash caching
- Query caching
- Embedding caching
- Cache management

**Key Components**:
- `hash_cache.py` - Hash cache implementation
- `query_cache.py` - Query cache implementation
- `embedding_cache.py` - Embedding cache implementation

**Dependencies**: Standard library only

## Plugin Architecture

### Plugin Interface

```python
class PluginInterface:
    def register(self, event: str, callback: Callable):
        """Register callback for event"""
        pass

    def emit(self, event: str, **kwargs):
        """Emit event to all registered callbacks"""
        pass

    def load_plugins(self, paths: List[str]):
        """Load plugins from specified paths"""
        pass
```

### Plugin Categories

#### AI/ML Backends (Plugin)
**Location**: `nodupe/plugins/ml/`
- NSFW classification
- Embedding generation
- Model management
- Dependencies: Optional (Pillow, ONNX Runtime)

#### GPU Acceleration (Plugin)
**Location**: `nodupe/plugins/gpu/`
- Hardware-accelerated computing
- Large-scale operations
- GPU fallback management
- Dependencies: Highly optional (torch, tensorflow, pyopencl, wgpu)

#### Video Processing (Plugin)
**Location**: `nodupe/plugins/video/`
- Video processing and analysis
- Frame extraction
- Perceptual hashing
- Metadata extraction
- Dependencies: Optional (ffmpeg, opencv-python, av, vidgear, wgpu)

#### Network Features (Plugin)
**Location**: `nodupe/plugins/network/`
- Remote storage
- Distributed processing
- Cloud synchronization
- API server
- Dependencies: Optional (boto3, google-cloud-storage, fastapi, requests)

#### Similarity Search (Plugin)
**Location**: `nodupe/plugins/similarity/`
- Vector similarity search
- Index management
- Near-duplicate detection
- Backend coordination
- Dependencies: Optional (NumPy, FAISS, Annoy)

#### Commands (Plugin)
**Location**: `nodupe/plugins/commands/`
- Command implementations
- Argument validation
- Error handling
- Result formatting
- Dependencies: Core modules only

### Plugin Loading Process

1. Core loader discovers plugin directories
2. Loads Python modules from plugin directories
3. Injects plugin manager instance as `pm`
4. Plugins register callbacks for events
5. Core emits events during execution

### Event System

**Core Events**:
- `startup` - Emitted when application starts
- `shutdown` - Emitted when application exits
- `scan_start` - Emitted when scan begins
- `scan_complete` - Emitted when scan finishes
- `file_processed` - Emitted for each processed file

## Dependency Management

### Dependency Categories

1. **Core Dependencies**: Required for basic functionality
   - Standard library modules
   - SQLite (included with Python)

2. **Optional Dependencies**: Enhance functionality but not required
   - Pillow (image processing)
   - ONNX Runtime (AI inference)
   - NumPy (vector operations)
   - FAISS (similarity search)
   - PyTorch/TensorFlow (GPU acceleration)
   - OpenCV (video processing)
   - FFmpeg (video processing)
   - Boto3 (AWS S3)
   - FastAPI (API server)

### Graceful Degradation Strategy

1. **Check availability** of optional dependency
2. **Attempt installation** if auto-install enabled
3. **Fallback to alternative** implementation
4. **Use standard library** as last resort
5. **Log warnings** but continue execution

## Error Handling

### Error Categories

1. **Fatal Errors**: Cannot continue execution
   - Database corruption
   - Configuration errors
   - Critical file system errors

2. **Recoverable Errors**: Continue with degraded functionality
   - Missing optional dependencies
   - Plugin loading failures
   - Partial scan failures

3. **Transient Errors**: Retry or skip
   - Network timeouts
   - Temporary file access issues
   - Resource constraints

### Error Handling Strategy

```python
try:
    # Attempt operation with best available implementation
    result = best_implementation()
except ImportError:
    try:
        # Fallback to alternative implementation
        result = fallback_implementation()
    except Exception:
        # Final fallback to standard library
        result = stdlib_fallback()
        log.warning("Using standard library fallback")
```

## Configuration

### Configuration Structure

```toml
# Core configuration (required)
[core]
database_path = "~/.nodupe/database.db"
log_level = "INFO"
log_file = "~/.nodupe/nodupe.log"

# Plugin configuration
[plugins]
scan_dirs = ["nodupe/plugins"]
auto_load = true

# ML configuration
[plugins.ml]
backend = "auto"  # auto, onnx, cpu
backend_priority = ["onnx", "cpu"]

# GPU configuration
[plugins.gpu]
enabled = true
backend = "auto"  # auto, cuda, metal, opencl, vulkan
device_id = 0
max_memory_mb = 4096

# Video configuration
[plugins.video]
enabled = true
backend = "auto"  # auto, vidgear, pyav, opencv, ffmpeg
backend_priority = ["vidgear", "pyav", "opencv", "ffmpeg"]
frames_per_video = 10
hash_algorithm = "phash"
use_gpu = true

# Network configuration
[plugins.network]
enabled = false
remote_storage = false

# Similarity configuration
[plugins.similarity]
backend = "faiss"  # faiss, annoy, brute_force
index_type = "ivf"

# Cache configuration
[cache]
enable_hash_cache = true
enable_query_cache = true
enable_embedding_cache = true
max_cache_size_mb = 1024

# Performance configuration
[performance]
max_workers = 8
use_mmap_for_large_files = true
large_file_threshold_mb = 100
```

## Code Quality Standards

All contributions must adhere to the following standards:

1. **Strict Linting**: The codebase must maintain a **10/10** Pylint score
2. **Naming Conventions**:
   - Global constants: `UPPER_CASE` (e.g., `VIDEO_MANAGER`)
   - Classes: `PascalCase`
   - Functions/Variables: `snake_case`
3. **Line Length**: Maximum line length is **120 characters**
4. **Type Hinting**: Full type hinting required for all function signatures

## Testing Architecture

### Test Organization Structure

```text
tests/
├── core/              # Core tests (must have >80% coverage)
├── plugins/           # Plugin tests (isolated)
│   ├── commands/
│   ├── gpu/
│   ├── ml/
│   ├── network/
│   ├── similarity/
│   └── video/
└── integration/       # Integration tests
```

### Test Isolation Strategy

1. **Core Tests**: Run WITHOUT plugin dependencies
2. **Plugin Tests**: Mock missing dependencies
3. **Integration Tests**: Use real dependencies
4. **Fixtures**: Provide database and file system isolation

## Monitoring and Metrics

### Core Metrics

- Plugin load success/failure rates
- Fallback usage statistics
- Dependency availability tracking
- Error rates by category
- Performance impact of fallback modes

### Monitoring Strategy

```python
metrics = {
    "plugins_loaded": 0,
    "plugins_failed": 0,
    "fallbacks_used": 0,
    "dependencies_missing": [],
    "errors_by_type": defaultdict(int)
}
```

## Plugin Isolation Enforcement

### Dependency Isolation Requirements

1. `nodupe/core` must NEVER import from `nodupe/plugins`
2. Plugins can only import from `nodupe/core`
3. Plugins must NOT import from other plugins
4. All dependencies must go through the DI container

### Import Verification

- Automated import boundary checking in CI/CD
- Dependency graph visualization
- Pre-commit hooks to prevent violations

## Documentation Requirements

1. Plugin Development Guide
2. Dependency Management Guide
3. Error Handling Best Practices
4. Configuration Reference
5. Migration Guide from Legacy
