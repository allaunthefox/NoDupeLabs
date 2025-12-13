# NoDupeLabs Project Map - Modular Architecture with Hard Isolation

## Overview

This document outlines the new modular architecture for NoDupeLabs with hard isolation between the core loader/orchestrator and all other functions. The design follows the principle of "fail until it falls back on the standard library for operations."

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
- `plugins/` - Plugin management system
- `deps.py` - Dependency management with graceful fallback

**Dependencies**: Standard library only

### 2. Database Layer (Core)

**Location**: `nodupe/core/plugins/db/`

**Responsibilities**:

- File metadata storage
- Duplicate detection
- Basic indexing
- Transaction management

**Key Components**:

- `connection.py` - SQLite connection management with connection pooling
- `files.py` - File repository with CRUD operations
- `embeddings.py` - Embedding storage with model versioning

**Dependencies**: sqlite3 (standard library)

### 3. File Processing (Core)

**Location**: `nodupe/scan/`

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

**Dependencies**: Standard library + hashlib

### 4. Utilities (Core)

**Location**: `nodupe/utils/`

**Responsibilities**:

- Filesystem operations
- Hashing algorithms
- Compression utilities
- MIME type detection

**Key Components**:

- `filesystem.py` - Path operations and MIME detection
- `hashing.py` - Cryptographic hashing
- `compression.py` - Compression with fallback

**Dependencies**: Standard library only

### 5. AI/ML Backends (Plugin)

**Location**: `nodupe/plugins/ml/`

**Responsibilities**:

- NSFW classification
- Embedding generation
- Model management

**Key Components**:

- `interfaces.py` - Abstract backend contracts
- `cpu_backend.py` - Pure NumPy implementation (always available)
- `onnx_backend.py` - ONNX Runtime CPU backend (optional)

**Dependencies**: Optional (Pillow, ONNX Runtime)

### 6. GPU Acceleration (Plugin)

**Location**: `nodupe/plugins/gpu/`

**Responsibilities**:

- Hardware-accelerated computing
- Large-scale operations
- GPU fallback management

**Key Components**:

- `cuda_backend.py` - NVIDIA CUDA (PyTorch/TensorFlow)
- `onnx_gpu.py` - ONNX Runtime with GPU
- `opencl_backend.py` - AMD/Intel GPUs (pyopencl)
- `metal_backend.py` - Apple Metal (M1/M2/M3)
- `vulkan_backend.py` - Vulkan compute (wgpu-py/Kompute)

**Dependencies**: Highly optional (torch, tensorflow, pyopencl, wgpu)

### 7. Video Processing (Plugin)

**Location**: `nodupe/plugins/video/`

**Responsibilities**:

- Video processing and analysis
- Frame extraction
- Perceptual hashing
- Metadata extraction

**Key Components**:

- `interfaces.py` - Video backend contracts
- `ffmpeg_subprocess.py` - FFmpeg CLI (requires ffmpeg binary)
- `opencv_backend.py` - OpenCV (computer vision library)
- `pyav_backend.py` - PyAV (Pythonic FFmpeg bindings)
- `vidgear_backend.py` - VidGear (multi-threaded framework)
- `analyzer_backend.py` - video-analyzer CLI integration
- `vulkan_video.py` - Vulkan GPU compute for video
- `frame_extractor.py` - Key frame extraction strategies
- `perceptual_hash.py` - Video similarity hashing
- `metadata_extractor.py` - Metadata extraction and normalization

**Dependencies**: Optional (ffmpeg, opencv-python, av, vidgear, wgpu)

### 8. Network Features (Plugin)

**Location**: `nodupe/plugins/network/`

**Responsibilities**:

- Remote storage
- Distributed processing
- Cloud synchronization
- API server

**Key Components**:

- `remote_storage.py` - S3, GCS, Azure blob storage
- `distributed_scan.py` - Multi-machine distributed scanning
- `api_server.py` - REST API server
- `sync_client.py` - Cloud synchronization client

**Dependencies**: Optional (boto3, google-cloud-storage, azure-storage-blob, fastapi, requests)

### 9. Similarity Search (Plugin)

**Location**: `nodupe/plugins/similarity/`

**Responsibilities**:

- Vector similarity search
- Index management
- Near-duplicate detection
- Backend coordination

**Key Components**:

- `interfaces.py` - Similarity search interfaces
- `brute_force.py` - NumPy-based brute-force search (always available)
- `faiss_backend.py` - FAISS vector search (CPU)
- `annoy_backend.py` - Spotify Annoy (optional)
- `similarity_manager.py` - Backend management and coordination

**Dependencies**: Optional (NumPy, FAISS, Annoy)

### 10. Commands (Plugin)

**Location**: `nodupe/plugins/commands/`

**Responsibilities**:

- Command implementations
- Argument validation
- Error handling
- Result formatting

**Key Components**:

- `scan.py` - Scan command with filtering and duplicate detection
- `apply.py` - Apply command with file management actions
- `similarity.py` - Similarity command with multiple metrics
- `export.py` - Export/reporting commands
- `video_scan.py` - Video-specific scanning

**Dependencies**: Core modules only

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

## Implementation Plan

### Phase 1: Core Isolation

1. Extract core loader functionality
2. Implement plugin interface
3. Create dependency injection container
4. Implement graceful degradation system
5. Test core functionality without optional dependencies

### Phase 2: Plugin Conversion

1. Convert AI backends to plugins
2. Convert similarity backends to plugins
3. Convert commands to use plugin system
4. Implement plugin discovery and loading
5. Test plugin isolation and error handling

### Phase 3: Testing and Validation

1. Test core functionality with all plugins disabled
2. Test graceful degradation scenarios
3. Test plugin loading and event system
4. Test error handling and recovery
5. Performance testing with various configurations

## Migration Strategy

### Clean Break Implementation

1. Identify core vs. optional functionality
2. Extract interfaces for plugin boundaries
3. Implement fallback mechanisms with focus on efficiency
4. Convert modules to plugins with resilience focus
5. Test each conversion for isolation and quality

### Hard Break Approach

- New CLI interface optimized for efficiency
- Clean database schema designed for performance
- Streamlined configuration format

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

## Documentation Requirements

1. Plugin Development Guide
2. Dependency Management Guide
3. Error Handling Best Practices
4. Configuration Reference
5. Migration Guide from Legacy

## Future Enhancements

1. Dynamic Plugin Loading: Load plugins at runtime
2. Plugin Marketplace: Discover and install plugins
3. Advanced Fallback Strategies: Machine learning-based fallback selection
4. Performance Optimization: Caching and parallel processing
5. Extended Monitoring: Real-time metrics and alerts
