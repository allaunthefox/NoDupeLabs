1. Architecture Principles

Hard isolation
Clear delineation
Graceful degradation
Domain organization

2. Complete Directory Tree

Full structure with explanations for every file
Clear separation: core/ vs core/plugin_system/ vs plugins/
All plugin categories: ML, GPU, Video, Network, Similarity, Commands

3. Component Descriptions

Detailed explanation of each major section
Purpose and key files for each component
Dependency requirements clearly stated

4. Dependency Isolation Levels

Level 0: Core (zero deps)
Level 1: Basic plugins (minimal)
Level 2: Advanced plugins (optional)

5. Installation Strategies

Complete pip install options
Feature-specific combinations
Full extras_require configuration for setup.py

6. Graceful Degradation Patterns

Code examples for ML backend selection
5-tier video fallback chain
GPU/CPU fallback
Network features as optional

7. Configuration Structure

Complete config.toml example
All plugin configuration sections

8. Import Patterns

Safe import with fallback
Plugin availability checking
Error messages for missing features

9. Testing Strategy

Core testing requirements
Plugin isolation testing
Integration testing
Performance benchmarking

10. Additional Sections

Development workflow
Security considerations
Performance optimization
Migration from legacy
Future extensibility
Documentation requirements

This document serves as the definitive reference for the new modular architecture with hard isolation!


# NoDupeLabs - Project Structure Specification

## Overview

This document defines the modular architecture for NoDupeLabs with hard isolation between core functionality and optional plugins. The structure enforces graceful degradation and clear delineation of concerns.

---

## Architecture Principles

### 1. Hard Isolation
- **Core** has ZERO optional dependencies
- **Plugins** can fail completely without affecting core
- **No direct imports** from plugins in core code

### 2. Clear Delineation
- **Core**: Required functionality (database, scanning, hashing)
- **Plugin Infrastructure**: System for loading/managing plugins
- **Feature Plugins**: Optional capabilities organized by domain

### 3. Graceful Degradation
- Multiple backend tiers for each feature
- Automatic fallback to simpler implementations
- System remains functional even with missing dependencies

### 4. Domain Organization
- Plugins grouped by functionality (ML, GPU, Video, Network)
- Each domain has clear interfaces and contracts
- Independent development and testing

---

## Directory Structure

```
nodupe/
├── core/                           # Core System (Required - No Optional Dependencies)
│   ├── __init__.py
│   ├── loader.py                   # Application bootstrap and initialization
│   ├── database.py                 # SQLite database layer with connection pooling
│   ├── config.py                   # Configuration loading and management
│   │
│   ├── plugin_system/              # Plugin Infrastructure (NOT plugins themselves)
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract Plugin base class and contracts
│   │   ├── registry.py             # Plugin registry and lookup
│   │   ├── loader.py               # Dynamic plugin loading/unloading
│   │   ├── discovery.py            # Plugin discovery and metadata parsing
│   │   ├── security.py             # Permission system and sandboxing
│   │   ├── lifecycle.py            # Plugin lifecycle management
│   │   ├── dependencies.py         # Dependency resolution (topological sort)
│   │   ├── compatibility.py        # Version compatibility checking
│   │   └── hot_reload.py           # Hot reload and rollback support
│   │
│   ├── security.py                 # Path sanitization and validation
│   ├── validators.py               # Input validation utilities
│   ├── limits.py                   # Resource limits (memory, file handles)
│   ├── indexing.py                 # Database indexing and optimization
│   ├── incremental.py              # Incremental scanning with checkpoints
│   ├── filesystem.py               # Safe filesystem operations
│   ├── compression.py              # Compression with stdlib fallback
│   ├── mime_detection.py           # MIME type detection
│   ├── errors.py                   # Custom exception hierarchy
│   ├── logging.py                  # Structured logging setup
│   ├── version.py                  # Semantic versioning and API version
│   ├── api.py                      # API stability decorators
│   │
│   ├── cache/                      # Caching Infrastructure
│   │   ├── __init__.py
│   │   ├── hash_cache.py           # File hash cache (path + mtime)
│   │   ├── query_cache.py          # Database query result cache
│   │   └── embedding_cache.py      # Vector embedding cache
│   │
│   ├── parallel.py                 # Parallel processing (multiprocessing/threading)
│   ├── mmap_handler.py             # Memory-mapped file handling
│   └── pools.py                    # Resource pooling (connections, threads)
│
├── plugins/                        # Optional Feature Plugins (Organized by Domain)
│   ├── __init__.py
│   │
│   ├── ml/                         # Machine Learning Backends (CPU)
│   │   ├── __init__.py
│   │   ├── interfaces.py           # Abstract backend contracts
│   │   ├── cpu_backend.py          # Pure NumPy implementation (always available)
│   │   └── onnx_backend.py         # ONNX Runtime CPU backend
│   │
│   ├── gpu/                        # GPU Acceleration
│   │   ├── __init__.py
│   │   ├── cuda_backend.py         # NVIDIA CUDA (PyTorch/TensorFlow)
│   │   ├── onnx_gpu.py             # ONNX Runtime with GPU
│   │   ├── opencl_backend.py       # OpenCL (AMD/Intel GPUs)
│   │   ├── metal_backend.py        # Apple Metal (M1/M2/M3)
│   │   └── vulkan_backend.py       # Vulkan compute (wgpu-py/Kompute)
│   │
│   ├── video/                      # Video Processing and Analysis
│   │   ├── __init__.py
│   │   ├── interfaces.py           # Video backend contracts
│   │   │
│   │   │── Tier 5: Ultimate Fallback (No Python Dependencies)
│   │   ├── ffmpeg_subprocess.py    # FFmpeg CLI (requires ffmpeg binary)
│   │   │
│   │   │── Tier 4: Widely Available
│   │   ├── opencv_backend.py       # OpenCV (computer vision library)
│   │   │
│   │   │── Tier 3: Reliable
│   │   ├── pyav_backend.py         # PyAV (Pythonic FFmpeg bindings)
│   │   │
│   │   │── Tier 1: High-Level Frameworks
│   │   ├── vidgear_backend.py      # VidGear (multi-threaded framework)
│   │   │
│   │   │── Tier 2: ML-Powered
│   │   ├── analyzer_backend.py     # video-analyzer CLI integration
│   │   │
│   │   │── Tier 3: Advanced GPU
│   │   ├── vulkan_video.py         # Vulkan GPU compute for video
│   │   │
│   │   │── Utilities
│   │   ├── frame_extractor.py      # Key frame extraction strategies
│   │   ├── perceptual_hash.py      # Video similarity hashing
│   │   └── metadata_extractor.py   # Metadata extraction and normalization
│   │
│   ├── network/                    # Network and Distributed Features
│   │   ├── __init__.py
│   │   ├── remote_storage.py       # S3, GCS, Azure blob storage
│   │   ├── distributed_scan.py     # Multi-machine distributed scanning
│   │   ├── api_server.py           # REST API server
│   │   └── sync_client.py          # Cloud synchronization client
│   │
│   ├── similarity/                 # Similarity Search Backends
│   │   ├── __init__.py
│   │   ├── brute_force.py          # CPU brute-force (always available)
│   │   ├── faiss_backend.py        # FAISS vector search (CPU)
│   │   └── annoy_backend.py        # Spotify Annoy (optional)
│   │
│   └── commands/                   # Command Plugins
│       ├── __init__.py
│       ├── scan.py                 # File scanning command
│       ├── apply.py                # Apply actions command
│       ├── similarity.py           # Similarity search commands
│       ├── export.py               # Export/reporting commands
│       └── video_scan.py           # Video-specific scanning
│
├── tests/                          # Test Suite (Mirrors Source Structure)
│   ├── core/
│   │   ├── test_database.py
│   │   ├── test_security.py
│   │   ├── test_validators.py
│   │   ├── plugin_system/
│   │   │   ├── test_base.py
│   │   │   ├── test_registry.py
│   │   │   └── test_loader.py
│   │   └── cache/
│   │       ├── test_hash_cache.py
│   │       └── test_query_cache.py
│   │
│   └── plugins/
│       ├── ml/
│       │   ├── test_cpu_backend.py
│       │   └── test_onnx_backend.py
│       ├── video/
│       │   ├── test_interfaces.py
│       │   ├── test_ffmpeg_subprocess.py
│       │   ├── test_opencv_backend.py
│       │   └── test_pyav_backend.py
│       └── similarity/
│           └── test_brute_force.py
│
├── benchmarks/                     # Performance Benchmarks
│   ├── legacy_baseline.py
│   ├── baseline_results.json
│   └── benchmark_suite.py
│
├── docs/                           # Documentation
│   ├── architecture.md
│   ├── plugin_development.md
│   ├── dependencies.md
│   ├── configuration.md
│   ├── error_handling.md
│   └── api_reference.md
│
├── config.toml                     # Default configuration
├── .pylintrc                       # Pylint configuration
├── pyproject.toml                  # PEP 8, project metadata, dependencies
├── .markdownlint.json              # Markdown linting rules
├── setup.py                        # Package setup with extras_require
├── README.md                       # Project overview
├── STANDARDS.md                    # Code quality standards
└── .vscode/
    └── settings.json               # Pylance/IDE configuration
```

---

## Component Descriptions

### Core System (`nodupe/core/`)

**Purpose**: Required functionality that works without any optional dependencies.

**Key Files**:
- `loader.py` - Application bootstrap, initializes core systems
- `database.py` - SQLite operations with connection pooling
- `config.py` - Configuration loading from TOML files
- `security.py` - Path traversal prevention, input sanitization
- `validators.py` - Type-safe input validation
- `limits.py` - Resource limit enforcement (memory, file handles)

**Dependencies**: Python standard library + SQLite (built-in)

### Plugin System (`nodupe/core/plugin_system/`)

**Purpose**: Infrastructure for loading, managing, and securing plugins.

**Key Components**:
- `base.py` - `Plugin` abstract base class, `PluginMetadata`
- `registry.py` - `PluginRegistry` singleton for plugin lookup
- `loader.py` - Dynamic import and instantiation of plugins
- `discovery.py` - Scans directories for plugins
- `security.py` - Permission model and resource quotas
- `lifecycle.py` - Initialize, start, stop, shutdown hooks
- `dependencies.py` - Topological sort for load order
- `compatibility.py` - Semantic version checking
- `hot_reload.py` - File watching and state preservation

**Dependencies**: Python standard library only

### ML Plugins (`nodupe/plugins/ml/`)

**Purpose**: Machine learning backends for embedding generation (CPU-based).

**Backends**:
- `cpu_backend.py` - Pure NumPy (no ML dependencies) - **Always available**
- `onnx_backend.py` - ONNX Runtime CPU - **Optional**

**Graceful Degradation**: ONNX → CPU fallback → Feature disabled

**Dependencies**: 
- Required: None (CPU backend uses stdlib + NumPy)
- Optional: `onnxruntime>=1.14`

### GPU Plugins (`nodupe/plugins/gpu/`)

**Purpose**: Hardware-accelerated computing for large-scale operations.

**Backends**:
- `cuda_backend.py` - NVIDIA GPUs (torch/tensorflow-gpu)
- `onnx_gpu.py` - ONNX Runtime GPU
- `opencl_backend.py` - AMD/Intel GPUs (pyopencl)
- `metal_backend.py` - Apple Silicon M1/M2/M3 (torch MPS)
- `vulkan_backend.py` - Hardware-agnostic (wgpu-py/Kompute)

**Dependencies**: Highly optional, choose one:
- `torch>=2.0` (CUDA or Metal)
- `tensorflow-gpu>=2.12` (CUDA)
- `onnxruntime-gpu>=1.14` (CUDA)
- `pyopencl>=2022.1` (OpenCL)
- `wgpu>=0.9.0` or `kp` (Vulkan)

### Video Plugins (`nodupe/plugins/video/`)

**Purpose**: Video processing with 5-tier graceful degradation.

**Tier System** (Try in order):
1. **Tier 1** - `vidgear_backend.py` - High-level framework (easiest)
2. **Tier 2** - `analyzer_backend.py` - ML-powered analysis
3. **Tier 3** - `pyav_backend.py` - Reliable FFmpeg bindings
4. **Tier 4** - `opencv_backend.py` - Widely available CV library
5. **Tier 5** - `ffmpeg_subprocess.py` - CLI fallback (always works if FFmpeg installed)

**Utilities**:
- `frame_extractor.py` - Extract key frames (uniform, scene-detect)
- `perceptual_hash.py` - Video similarity (phash, dhash, wavelet)
- `metadata_extractor.py` - Duration, codec, resolution, FPS

**Dependencies**:
- Tier 5: `ffmpeg` binary in PATH (not Python package)
- Tier 4: `opencv-python>=4.7.0`
- Tier 3: `av>=10.0.0` (PyAV)
- Tier 1: `vidgear[core]>=0.3.0`
- Tier 2: `video-analyzer` CLI tool
- Advanced GPU: `wgpu>=0.9.0`

### Network Plugins (`nodupe/plugins/network/`)

**Purpose**: Remote storage, distributed processing, cloud sync.

**Components**:
- `remote_storage.py` - S3, Google Cloud Storage, Azure Blob
- `distributed_scan.py` - Multi-machine job coordination
- `api_server.py` - REST API (FastAPI/Flask)
- `sync_client.py` - Cross-machine database sync

**Dependencies**: 
- `boto3>=1.26` (AWS S3)
- `google-cloud-storage>=2.7` (GCS)
- `azure-storage-blob>=12.14` (Azure)
- `fastapi>=0.95` or `flask>=2.3` (API server)
- `requests>=2.28` (sync client)

### Similarity Plugins (`nodupe/plugins/similarity/`)

**Purpose**: Vector similarity search for duplicate detection.

**Backends**:
- `brute_force.py` - NumPy brute-force - **Always available**
- `faiss_backend.py` - FAISS vector search (CPU)
- `annoy_backend.py` - Spotify Annoy (optional)

**Dependencies**:
- Required: None (brute-force uses stdlib)
- Optional: `faiss-cpu>=1.7` or `faiss-gpu>=1.7`
- Optional: `annoy>=1.17`

### Commands Plugins (`nodupe/plugins/commands/`)

**Purpose**: CLI commands that orchestrate features.

**Commands**:
- `scan.py` - File system scanning
- `apply.py` - Apply actions (delete, move, symlink)
- `similarity.py` - Find similar files
- `export.py` - Export results (CSV, JSON)
- `video_scan.py` - Video-specific operations

**Dependencies**: None (uses core + other plugins)

---

## Dependency Isolation Levels

### Level 0: Core (Always Required)
```
nodupe/core/*
├── Python 3.9+ standard library
└── SQLite (built into Python)

Dependencies: ZERO optional packages
```

### Level 1: Basic Plugins (Minimal)
```
nodupe/plugins/ml/cpu_backend.py
nodupe/plugins/similarity/brute_force.py
nodupe/plugins/commands/*

Dependencies: numpy (lightweight)
```

### Level 2: Advanced Plugins (Optional)
```
nodupe/plugins/ml/onnx_backend.py          → onnxruntime
nodupe/plugins/gpu/*                       → torch/tensorflow/pyopencl
nodupe/plugins/video/*                     → opencv/av/vidgear
nodupe/plugins/network/*                   → boto3/requests
nodupe/plugins/similarity/faiss_backend.py → faiss-cpu

Dependencies: Feature-specific packages
```

**Principle**: Each level functions independently of higher levels.

---

## Installation Strategies

### Minimal Installation
```bash
pip install nodupe

# Includes:
# - Core system (zero optional deps)
# - CPU-based ML fallback
# - Brute-force similarity
```

### Feature-Specific Installations
```bash
# Machine Learning
pip install nodupe[ml]              # ONNX CPU backend

# GPU Acceleration
pip install nodupe[gpu]             # PyTorch/TensorFlow GPU
pip install nodupe[gpu-cuda]        # NVIDIA CUDA specific
pip install nodupe[gpu-metal]       # Apple Metal specific

# Video Processing
pip install nodupe[video]           # Basic: OpenCV + PyAV
pip install nodupe[video-vidgear]   # High-level: VidGear
pip install nodupe[video-analyzer]  # ML-powered analysis
pip install nodupe[video-gpu]       # GPU-accelerated
pip install nodupe[video-all]       # All video backends

# Network Features
pip install nodupe[network]         # Cloud storage + API
pip install nodupe[network-s3]      # S3 only
pip install nodupe[network-gcs]     # Google Cloud only

# Similarity Search
pip install nodupe[similarity]      # FAISS CPU
pip install nodupe[similarity-gpu]  # FAISS GPU

# Complete Installation
pip install nodupe[all]

# Custom Combinations
pip install nodupe[ml,video,network]
pip install nodupe[gpu-cuda,similarity-gpu]
```

### setup.py extras_require Configuration
```python
extras_require={
    # ML backends
    'ml': ['onnxruntime>=1.14'],
    
    # GPU acceleration
    'gpu': ['torch>=2.0'],
    'gpu-cuda': ['torch>=2.0', 'onnxruntime-gpu>=1.14'],
    'gpu-metal': ['torch>=2.0'],
    'gpu-opencl': ['pyopencl>=2022.1'],
    'gpu-vulkan': ['wgpu>=0.9.0'],
    
    # Video processing
    'video': ['opencv-python>=4.7.0', 'av>=10.0.0'],
    'video-vidgear': ['vidgear[core]>=0.3.0'],
    'video-analyzer': [],  # CLI tool, not pip package
    'video-gpu': ['wgpu>=0.9.0'],
    'video-all': ['opencv-python', 'av', 'vidgear[core]', 'wgpu'],
    
    # Network features
    'network': ['boto3>=1.26', 'requests>=2.28', 'fastapi>=0.95'],
    'network-s3': ['boto3>=1.26'],
    'network-gcs': ['google-cloud-storage>=2.7'],
    
    # Similarity search
    'similarity': ['faiss-cpu>=1.7'],
    'similarity-gpu': ['faiss-gpu>=1.7'],
    
    # Everything
    'all': [
        'onnxruntime>=1.14',
        'torch>=2.0',
        'opencv-python>=4.7.0',
        'av>=10.0.0',
        'boto3>=1.26',
        'faiss-cpu>=1.7',
    ],
}
```

---

## Graceful Degradation Patterns

### Pattern 1: ML Backend Selection
```python
# Try backends in priority order
try:
    from nodupe.plugins.ml import ONNXBackend
    backend = ONNXBackend()
except ImportError:
    from nodupe.plugins.ml import CPUBackend
    backend = CPUBackend()  # Always works
```

### Pattern 2: Video Backend Selection
```python
# 5-tier fallback chain
for backend_name in ['vidgear', 'pyav', 'opencv', 'ffmpeg']:
    try:
        backend = load_video_backend(backend_name)
        if backend.is_available():
            break
    except ImportError:
        continue
else:
    # All backends failed
    video_features_disabled = True
```

### Pattern 3: GPU Acceleration
```python
# Try GPU, fallback to CPU
if cuda_available():
    backend = CUDABackend()
elif metal_available():
    backend = MetalBackend()
else:
    backend = CPUBackend()  # Always works
```

### Pattern 4: Network Features
```python
# Network features completely optional
try:
    from nodupe.plugins.network import RemoteStorage
    storage = RemoteStorage(backend='s3')
except ImportError:
    storage = None  # Local-only mode
```

---

## Configuration Structure

### config.toml Example
```toml
[core]
database_path = "~/.nodupe/database.db"
log_level = "INFO"
log_file = "~/.nodupe/nodupe.log"

[plugins]
scan_dirs = ["nodupe/plugins"]
auto_load = true

[plugins.ml]
backend = "auto"  # auto, onnx, cpu
backend_priority = ["onnx", "cpu"]

[plugins.gpu]
enabled = true
backend = "auto"  # auto, cuda, metal, opencl, vulkan
device_id = 0
max_memory_mb = 4096

[plugins.video]
enabled = true
backend = "auto"  # auto, vidgear, pyav, opencv, ffmpeg
backend_priority = ["vidgear", "pyav", "opencv", "ffmpeg"]
frames_per_video = 10
hash_algorithm = "phash"
use_gpu = true

[plugins.network]
enabled = false
remote_storage = false

[plugins.similarity]
backend = "faiss"  # faiss, annoy, brute_force
index_type = "ivf"

[cache]
enable_hash_cache = true
enable_query_cache = true
enable_embedding_cache = true
max_cache_size_mb = 1024

[performance]
max_workers = 8
use_mmap_for_large_files = true
large_file_threshold_mb = 100
```

---

## Import Patterns

### Core System (Always Works)
```python
# Core infrastructure - no optional dependencies
from nodupe.core.database import Database
from nodupe.core.config import load_config
from nodupe.core.plugin_system import Plugin, PluginRegistry
```

### Plugin Imports (With Fallback)
```python
# ML Backend - with fallback
try:
    from nodupe.plugins.ml import ONNXBackend as MLBackend
except ImportError:
    from nodupe.plugins.ml import CPUBackend as MLBackend

# Video Processing - with fallback
try:
    from nodupe.plugins.video import VideoAnalyzer
except ImportError:
    VideoAnalyzer = None  # Video features disabled

# GPU Acceleration - completely optional
try:
    from nodupe.plugins.gpu import CUDABackend
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

# Network Features - completely optional
try:
    from nodupe.plugins.network import RemoteStorage
    NETWORK_AVAILABLE = True
except ImportError:
    NETWORK_AVAILABLE = False
```

### Safe Plugin Usage
```python
def process_video(path):
    if VideoAnalyzer is not None:
        analyzer = VideoAnalyzer()
        return analyzer.extract_frames(path)
    else:
        raise RuntimeError("Video features not available. Install with: pip install nodupe[video]")
```

---

## Testing Strategy

### Core Testing (Required - 100% Coverage)
```bash
# Test core without any plugins
pytest tests/core/ --cov=nodupe/core --cov-report=html

# Must achieve >80% coverage
```

### Plugin Testing (Isolated)
```bash
# Test each plugin independently
pytest tests/plugins/ml/
pytest tests/plugins/video/
pytest tests/plugins/network/

# Mock missing dependencies
pytest tests/plugins/video/ --mock-opencv
```

### Integration Testing
```bash
# Test core + plugins together
pytest tests/integration/

# Test graceful degradation
pytest tests/integration/test_fallback.py
```

### Performance Benchmarking
```bash
# Run benchmarks
python benchmarks/benchmark_suite.py

# Compare against baseline
python benchmarks/legacy_baseline.py
```

---

## Development Workflow

### 1. Setup Development Environment
```bash
git clone <repo>
cd nodupe

# Install in editable mode with all features
pip install -e ".[all,dev]"

# Or minimal for core development
pip install -e .
```

### 2. Code Quality Checks
```bash
# Linting
pylint nodupe/

# Type checking (via Pylance in VS Code)
# Or use mypy if configured

# Style checking
pep8 nodupe/

# Markdown linting
markdownlint docs/
```

### 3. Run Tests
```bash
# All tests
pytest

# Specific module
pytest tests/core/test_database.py

# With coverage
pytest --cov=nodupe --cov-report=html
```

### 4. Create New Plugin
```bash
# Follow plugin template
cp -r nodupe/plugins/_template nodupe/plugins/my_plugin

# Edit plugin.json metadata
# Implement Plugin base class
# Add tests in tests/plugins/my_plugin/
```

---

## Security Considerations

### Plugin Sandboxing
- Plugins run with defined permissions (filesystem, network, database)
- Resource quotas enforced (memory, CPU time, file handles)
- Permission manifest in plugin.json

### Path Traversal Prevention
- All paths validated through `nodupe.core.security.sanitize_path()`
- Paths normalized and checked against base directory
- Symlink traversal blocked

### Resource Limits
- Memory limits per plugin
- Maximum file handle limits
- Execution time limits with timeout

---

## Performance Optimization

### Caching Strategy
- **Hash Cache**: Avoid re-hashing unchanged files (path + mtime key)
- **Query Cache**: Cache database query results with TTL
- **Embedding Cache**: Cache ML embeddings on disk (memory-mapped)

### Parallel Processing
- **CPU-bound**: `multiprocessing.Pool` for hashing, ML inference
- **I/O-bound**: `concurrent.futures.ThreadPoolExecutor` for file operations
- **Auto-scaling**: Worker count based on `os.cpu_count()`

### Memory Management
- **Memory-mapped files**: For large videos and index files (>100MB)
- **Streaming processing**: Process files in chunks
- **Resource pools**: Reuse database connections, thread pools

---

## Migration from Legacy

### Data Migration
- Automated migration tool: `nodupe migrate --from legacy.db --to new.db`
- Backup created automatically before migration
- Validation of migrated data
- Rollback capability

### Configuration Migration
- Convert old INI/JSON config to TOML
- Map legacy settings to new structure
- Preserve custom settings

### Gradual Rollout
- Run legacy and new side-by-side during transition
- Compare results for validation
- Switch when confidence high

---

## Future Extensibility

### Adding New Plugin Categories
```
nodupe/plugins/
  ├── ml/
  ├── gpu/
  ├── video/
  ├── network/
  ├── similarity/
  ├── commands/
  └── NEW_CATEGORY/        # Easy to add
      ├── __init__.py
      ├── interfaces.py
      └── backend1.py
```

### Adding New Backends
```python
# Implement interface
from nodupe.plugins.video.interfaces import VideoBackend

class NewVideoBackend(VideoBackend):
    def is_available(self) -> bool:
        # Check dependencies
        pass
    
    # Implement all abstract methods
```

### Plugin Discovery
- Automatic discovery in `nodupe/plugins/`
- Support for external plugins via entry points
- Plugin metadata in `plugin.json`

---

## Documentation Requirements

### Per-Plugin Documentation
- `README.md` - Overview and usage
- `INSTALL.md` - Installation instructions
- `API.md` - Public API reference
- `EXAMPLES.md` - Usage examples

### Core Documentation
- Architecture overview
- Plugin development guide
- Configuration reference
- Error handling guide
- Migration guide

---

## Summary

This structure provides:
- ✅ **Hard isolation** between core and plugins
- ✅ **Clear delineation** of functionality
- ✅ **Graceful degradation** through multiple tiers
- ✅ **Domain organization** for maintainability
- ✅ **Independent development** of plugins
- ✅ **User choice** in features via pip extras
- ✅ **Future extensibility** for new features

**Key Principle**: The core system works perfectly with ZERO optional dependencies. Everything else is an optional enhancement.