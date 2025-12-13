# NoDupeLabs - Definitive Project Structure

## Complete Directory Layout

```
nodupe/
│
├── core/                                    # REQUIRED - Zero Optional Dependencies
│   ├── __init__.py
│   ├── main.py                              # Application entry point
│   ├── loader.py                            # Bootstrap and initialization
│   ├── container.py                         # Dependency injection container
│   ├── config.py                            # Configuration loading/management
│   │
│   ├── cli/                                 # Core CLI (minimal argument parsing ONLY)
│   │   ├── __init__.py
│   │   ├── parser.py                        # ArgParse setup, no command logic
│   │   └── output.py                        # Output formatting (stdout/stderr)
│   │
│   ├── database/                            # SQLite database layer
│   │   ├── __init__.py
│   │   ├── connection.py                    # Connection pool, context managers
│   │   ├── schema.py                        # Database schema definitions
│   │   ├── repository.py                    # File/hash repository patterns
│   │   ├── transactions.py                  # Transaction management
│   │   └── indexing.py                      # Index creation/optimization
│   │
│   ├── scan/                                # File scanning (stdlib ONLY)
│   │   ├── __init__.py
│   │   ├── walker.py                        # os.walk based file traversal
│   │   ├── file_info.py                     # Basic file info (size, mtime)
│   │   ├── hasher.py                        # Cryptographic hashing
│   │   └── progress.py                      # Progress tracking
│   │
│   ├── plugin_system/                       # Plugin infrastructure (NOT plugins)
│   │   ├── __init__.py
│   │   ├── base.py                          # Abstract Plugin base class
│   │   ├── registry.py                      # Plugin registry singleton
│   │   ├── loader.py                        # Dynamic plugin loading
│   │   ├── discovery.py                     # Plugin discovery/metadata
│   │   ├── security.py                      # Permission system
│   │   ├── lifecycle.py                     # Plugin lifecycle hooks
│   │   ├── dependencies.py                  # Dependency resolution
│   │   ├── compatibility.py                 # Version checking
│   │   └── hot_reload.py                    # Hot reload support
│   │
│   ├── cache/                               # Caching infrastructure
│   │   ├── __init__.py
│   │   ├── hash_cache.py                    # File hash cache (path+mtime)
│   │   ├── query_cache.py                   # DB query result cache
│   │   └── embedding_cache.py               # Vector embedding cache
│   │
│   ├── security.py                          # Path sanitization/validation
│   ├── validators.py                        # Input validation
│   ├── limits.py                            # Resource limits (memory, handles)
│   ├── filesystem.py                        # Safe filesystem operations
│   ├── compression.py                       # Compression with stdlib fallback
│   ├── mime_detection.py                    # MIME type detection (stdlib)
│   ├── incremental.py                       # Incremental scanning
│   ├── parallel.py                          # Parallel processing
│   ├── mmap_handler.py                      # Memory-mapped file handling
│   ├── pools.py                             # Resource pooling
│   ├── errors.py                            # Custom exception hierarchy
│   ├── logging.py                           # Structured logging
│   ├── version.py                           # Version management
│   └── api.py                               # API stability decorators
│
├── plugins/                                 # OPTIONAL - Organized by Domain
│   ├── __init__.py
│   │
│   ├── commands/                            # CLI Command Plugins
│   │   ├── __init__.py
│   │   ├── base.py                          # Command base class
│   │   ├── scan.py                          # Scan command implementation
│   │   ├── apply.py                         # Apply actions command
│   │   ├── similarity.py                    # Similarity commands
│   │   ├── export.py                        # Export/report commands
│   │   └── video_scan.py                    # Video-specific scanning
│   │
│   ├── ml/                                  # ML Backends (CPU)
│   │   ├── __init__.py
│   │   ├── interfaces.py                    # Backend contracts
│   │   ├── cpu_backend.py                   # NumPy CPU (always available)
│   │   ├── onnx_backend.py                  # ONNX Runtime CPU
│   │   └── models/                          # ML model files
│   │       └── .gitkeep
│   │
│   ├── gpu/                                 # GPU Acceleration
│   │   ├── __init__.py
│   │   ├── cuda_backend.py                  # NVIDIA CUDA
│   │   ├── onnx_gpu.py                      # ONNX GPU
│   │   ├── opencl_backend.py                # AMD/Intel OpenCL
│   │   ├── metal_backend.py                 # Apple Metal
│   │   └── vulkan_backend.py                # Vulkan compute
│   │
│   ├── video/                               # Video Processing
│   │   ├── __init__.py
│   │   ├── interfaces.py                    # Video backend contracts
│   │   │
│   │   ├── ffmpeg_subprocess.py             # Tier 5: FFmpeg CLI fallback
│   │   ├── opencv_backend.py                # Tier 4: OpenCV
│   │   ├── pyav_backend.py                  # Tier 3: PyAV
│   │   ├── vidgear_backend.py               # Tier 1: VidGear
│   │   ├── analyzer_backend.py              # Tier 2: video-analyzer
│   │   ├── vulkan_video.py                  # Tier 3: Vulkan GPU
│   │   │
│   │   ├── frame_extractor.py               # Frame extraction utilities
│   │   ├── perceptual_hash.py               # Video similarity hashing
│   │   └── metadata_extractor.py            # Metadata extraction
│   │
│   ├── network/                             # Network/Distributed
│   │   ├── __init__.py
│   │   ├── remote_storage.py                # S3/GCS/Azure storage
│   │   ├── distributed_scan.py              # Multi-machine scanning
│   │   ├── api_server.py                    # REST API server
│   │   └── sync_client.py                   # Cloud sync
│   │
│   └── similarity/                          # Similarity Search
│       ├── __init__.py
│       ├── brute_force.py                   # NumPy brute-force (always)
│       ├── faiss_backend.py                 # FAISS vector search
│       └── annoy_backend.py                 # Spotify Annoy
│
├── tests/                                   # Test Suite (mirrors source)
│   ├── __init__.py
│   │
│   ├── core/                                # Core tests
│   │   ├── test_config.py
│   │   ├── test_loader.py
│   │   ├── test_container.py
│   │   │
│   │   ├── cli/
│   │   │   └── test_parser.py
│   │   │
│   │   ├── database/
│   │   │   ├── test_connection.py
│   │   │   ├── test_schema.py
│   │   │   ├── test_repository.py
│   │   │   └── test_transactions.py
│   │   │
│   │   ├── scan/
│   │   │   ├── test_walker.py
│   │   │   ├── test_hasher.py
│   │   │   └── test_progress.py
│   │   │
│   │   ├── plugin_system/
│   │   │   ├── test_base.py
│   │   │   ├── test_registry.py
│   │   │   ├── test_loader.py
│   │   │   ├── test_discovery.py
│   │   │   └── test_security.py
│   │   │
│   │   ├── cache/
│   │   │   ├── test_hash_cache.py
│   │   │   └── test_query_cache.py
│   │   │
│   │   ├── test_security.py
│   │   ├── test_validators.py
│   │   ├── test_filesystem.py
│   │   └── test_errors.py
│   │
│   ├── plugins/                             # Plugin tests
│   │   ├── commands/
│   │   │   ├── test_scan.py
│   │   │   ├── test_apply.py
│   │   │   └── test_similarity.py
│   │   │
│   │   ├── ml/
│   │   │   ├── test_cpu_backend.py
│   │   │   └── test_onnx_backend.py
│   │   │
│   │   ├── video/
│   │   │   ├── test_interfaces.py
│   │   │   ├── test_ffmpeg_subprocess.py
│   │   │   ├── test_opencv_backend.py
│   │   │   └── test_pyav_backend.py
│   │   │
│   │   ├── network/
│   │   │   └── test_remote_storage.py
│   │   │
│   │   └── similarity/
│   │       ├── test_brute_force.py
│   │       └── test_faiss_backend.py
│   │
│   └── integration/                         # Integration tests
│       ├── test_core_plugin_integration.py
│       ├── test_fallback_chains.py
│       └── test_end_to_end.py
│
├── benchmarks/                              # Performance benchmarks
│   ├── __init__.py
│   ├── legacy_baseline.py                   # Baseline from old system
│   ├── baseline_results.json
│   ├── benchmark_suite.py
│   └── compare.py                           # Compare new vs old
│
├── docs/                                    # Documentation
│   ├── architecture.md                      # System architecture
│   ├── plugin_development.md                # Plugin dev guide
│   ├── dependencies.md                      # Dependency management
│   ├── configuration.md                     # Config reference
│   ├── error_handling.md                    # Error patterns
│   ├── api_reference.md                     # API documentation
│   ├── migration_guide.md                   # Legacy → new
│   └── testing_guide.md                     # Testing strategies
│
├── scripts/                                 # Development/utility scripts
│   ├── setup_dev.sh                         # Dev environment setup
│   ├── run_benchmarks.sh                    # Run all benchmarks
│   └── migrate_legacy.py                    # Migration helper
│
├── .github/                                 # GitHub specific (if using)
│   └── workflows/
│       └── tests.yml                        # CI/CD pipeline
│
├── .vscode/                                 # VS Code settings
│   └── settings.json                        # Pylance, pylint config
│
├── config.toml                              # Default configuration
├── config.example.toml                      # Example config
│
├── .pylintrc                                # Pylint configuration
├── pyproject.toml                           # Project metadata, deps, PEP 8
├── .markdownlint.json                       # Markdown linting
├── .gitignore                               # Git ignore patterns
│
├── setup.py                                 # Package setup with extras
├── MANIFEST.in                              # Package manifest
├── requirements.txt                         # Pinned dependencies
├── requirements-dev.txt                     # Dev dependencies
│
├── README.md                                # Project overview
├── STANDARDS.md                             # Code quality standards
├── CONTRIBUTING.md                          # Contribution guidelines
├── LICENSE                                  # License file
└── CHANGELOG.md                             # Version history
```

---

## Key Principles Applied

### 1. **Core has ZERO optional dependencies**
```
nodupe/core/
├── Only uses Python stdlib
├── SQLite (built into Python)
└── NumPy at most (minimal)
```

### 2. **Plugin System is Infrastructure**
```
nodupe/core/plugin_system/
├── NOT plugins themselves
├── The SYSTEM for managing plugins
└── Required for core to load plugins
```

### 3. **All Features are Plugins**
```
nodupe/plugins/
├── commands/      # Even CLI commands are plugins
├── ml/            # ML backends
├── gpu/           # GPU acceleration
├── video/         # Video processing
├── network/       # Network features
└── similarity/    # Similarity search
```

### 4. **Tests Mirror Source**
```
tests/
├── core/          # Mirrors nodupe/core/
└── plugins/       # Mirrors nodupe/plugins/
```

---

## What Goes Where - Decision Matrix

| Content | Location | Why |
|---------|----------|-----|
| Application bootstrap | `core/main.py`, `core/loader.py` | Entry point, always needed |
| Argument parsing | `core/cli/parser.py` | Basic CLI, no commands |
| Command implementations | `plugins/commands/*.py` | Optional, orchestrate features |
| Database operations | `core/database/*.py` | Core functionality |
| File scanning (stdlib) | `core/scan/*.py` | Core functionality |
| MIME detection (optional) | Move to plugin if uses `python-magic` | Optional dependency |
| Plugin management | `core/plugin_system/*.py` | Infrastructure |
| ML embeddings | `plugins/ml/*.py` | Optional feature |
| GPU acceleration | `plugins/gpu/*.py` | Optional feature |
| Video processing | `plugins/video/*.py` | Optional feature |
| Network features | `plugins/network/*.py` | Optional feature |
| Similarity search | `plugins/similarity/*.py` | Optional feature |
| Path validation | `core/security.py` | Core security |
| Logging | `core/logging.py` | Core infrastructure |
| Tests | `tests/` (top level) | Standard Python pattern |
| Benchmarks | `benchmarks/` (top level) | Performance tracking |
| Documentation | `docs/` (top level) | Standard location |

---

## Component Details

### Core System (`nodupe/core/`)

**Purpose**: Required functionality that works without any optional dependencies.

#### `main.py`
- Application entry point
- Bootstrap the entire system
- Handle top-level exception catching

#### `loader.py`
- Initialize core components
- Load configuration
- Set up dependency injection container
- Initialize plugin system
- Start application

#### `container.py`
- Dependency injection container
- Service registration and resolution
- Lifecycle management

#### `config.py`
- Load configuration from TOML files
- Validate configuration
- Provide configuration access
- Handle environment overrides

---

### Core CLI (`nodupe/core/cli/`)

**Purpose**: Minimal argument parsing without command implementations.

#### `parser.py`
- Set up ArgumentParser
- Define global arguments
- NO command logic (commands are plugins)
- Return parsed arguments

#### `output.py`
- Format output to stdout/stderr
- Handle verbosity levels
- Color output (optional, with fallback)

---

### Core Database (`nodupe/core/database/`)

**Purpose**: SQLite database operations.

#### `connection.py`
- Connection pooling
- Context managers
- Thread-safe access

#### `schema.py`
- Database schema definitions
- Table creation
- Schema migrations

#### `repository.py`
- File repository pattern
- CRUD operations
- Query builders

#### `transactions.py`
- Transaction context managers
- Nested transaction support (savepoints)
- Rollback handling

#### `indexing.py`
- Index creation
- Index optimization
- VACUUM and ANALYZE

---

### Core Scan (`nodupe/core/scan/`)

**Purpose**: File scanning using only standard library.

#### `walker.py`
- os.walk based file traversal
- Respect .gitignore (stdlib only)
- Filter hidden files
- Follow/ignore symlinks

#### `file_info.py`
- Get file size
- Get modification time
- Get file permissions
- Basic metadata (no MIME)

#### `hasher.py`
- Cryptographic hashing (hashlib)
- MD5, SHA256, SHA512
- Streaming hash for large files

#### `progress.py`
- Progress tracking
- ETA calculation
- Files processed count
- Bytes processed count

---

### Plugin System (`nodupe/core/plugin_system/`)

**Purpose**: Infrastructure for managing plugins.

#### `base.py`
```python
class Plugin(ABC):
    name: str
    version: str
    dependencies: List[str]
    
    @abstractmethod
    def initialize(self, container: DependencyContainer):
        pass
    
    @abstractmethod
    def shutdown(self):
        pass
```

#### `registry.py`
- PluginRegistry singleton
- Register/unregister plugins
- Lookup plugins by name or capability

#### `loader.py`
- Dynamic import of plugins
- Instantiate plugin classes
- Handle import errors gracefully

#### `discovery.py`
- Scan plugin directories
- Load plugin metadata (plugin.json)
- Find available plugins

#### `security.py`
- Permission system
- Resource quotas
- Sandboxing

#### `lifecycle.py`
- Plugin lifecycle hooks
- Start/stop plugins
- Handle failures

#### `dependencies.py`
- Resolve plugin dependencies
- Topological sort for load order
- Detect circular dependencies

#### `compatibility.py`
- Semantic version checking
- API compatibility validation
- Conflict detection

#### `hot_reload.py`
- File watching
- State preservation
- Reload plugins

---

### Cache System (`nodupe/core/cache/`)

**Purpose**: Multi-level caching.

#### `hash_cache.py`
- Cache file hashes
- Key: (path, mtime)
- Automatic invalidation on file change

#### `query_cache.py`
- Cache database query results
- TTL-based expiration
- LRU eviction

#### `embedding_cache.py`
- Cache ML embeddings
- Persist to disk
- Memory-mapped for large datasets

---

### Core Utilities

#### `security.py`
- Path sanitization
- Path traversal prevention
- Validate file access

#### `validators.py`
- Input validation
- Type checking
- Range validation

#### `limits.py`
- Resource limit enforcement
- Memory limits
- File handle limits
- CPU time limits

#### `filesystem.py`
- Safe file operations
- Cross-platform path handling
- Hidden file detection

#### `compression.py`
- gzip compression
- Stdlib fallback
- Auto-detect compression

#### `mime_detection.py`
- MIME type detection
- Stdlib mimetypes module
- Fallback to extension-based

#### `incremental.py`
- Incremental scanning
- Checkpoint saving
- Resume from checkpoint

#### `parallel.py`
- Parallel processing
- multiprocessing.Pool
- ThreadPoolExecutor
- Auto worker scaling

#### `mmap_handler.py`
- Memory-mapped file handling
- For large files (>100MB)
- Safe cleanup

#### `pools.py`
- Connection pooling
- Thread pool management
- Resource reuse

#### `errors.py`
```python
class NoDupeError(Exception):
    """Base exception"""
    
class SecurityError(NoDupeError):
    """Security violation"""
    
class ValidationError(NoDupeError):
    """Input validation failed"""
    
class PluginError(NoDupeError):
    """Plugin-related error"""
```

#### `logging.py`
- Structured logging
- Log rotation
- Context injection
- Multiple handlers

#### `version.py`
- Semantic versioning
- API version tracking
- Compatibility checking

#### `api.py`
- @stable_api decorator
- @deprecated decorator
- API registry

---

## Plugin Categories

### Commands (`nodupe/plugins/commands/`)

**Purpose**: CLI command implementations.

#### `base.py`
```python
class Command(ABC):
    name: str
    description: str
    
    @abstractmethod
    def execute(self, args) -> int:
        """Return exit code"""
        pass
```

#### Command Implementations
- `scan.py` - Scan filesystem for files
- `apply.py` - Apply actions (delete, move, symlink)
- `similarity.py` - Find similar files
- `export.py` - Export results (CSV, JSON, HTML)
- `video_scan.py` - Video-specific scanning

---

### ML Plugins (`nodupe/plugins/ml/`)

**Purpose**: Machine learning backends.

#### `interfaces.py`
```python
class MLBackend(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        pass
    
    @abstractmethod
    def generate_embedding(self, data: bytes) -> np.ndarray:
        pass
```

#### Backends
- `cpu_backend.py` - Pure NumPy (always available)
- `onnx_backend.py` - ONNX Runtime CPU

**Dependencies**:
- cpu_backend: numpy (minimal)
- onnx_backend: onnxruntime>=1.14

---

### GPU Plugins (`nodupe/plugins/gpu/`)

**Purpose**: GPU acceleration.

#### Backends
- `cuda_backend.py` - NVIDIA CUDA
- `onnx_gpu.py` - ONNX Runtime GPU
- `opencl_backend.py` - AMD/Intel GPUs
- `metal_backend.py` - Apple Silicon
- `vulkan_backend.py` - Vulkan compute

**Dependencies**:
- CUDA: torch>=2.0 or tensorflow-gpu>=2.12
- OpenCL: pyopencl>=2022.1
- Metal: torch>=2.0
- Vulkan: wgpu>=0.9.0

---

### Video Plugins (`nodupe/plugins/video/`)

**Purpose**: Video processing with 5-tier fallback.

#### `interfaces.py`
```python
class VideoBackend(ABC):
    @abstractmethod
    def extract_frames(self, path: Path, num: int) -> List[np.ndarray]:
        pass
    
    @abstractmethod
    def get_metadata(self, path: Path) -> Dict:
        pass
```

#### Backends (in priority order)
1. `vidgear_backend.py` - High-level framework
2. `analyzer_backend.py` - ML-powered
3. `pyav_backend.py` - FFmpeg bindings
4. `opencv_backend.py` - OpenCV
5. `ffmpeg_subprocess.py` - CLI fallback

#### Utilities
- `frame_extractor.py` - Extract key frames
- `perceptual_hash.py` - Video similarity
- `metadata_extractor.py` - Video metadata

**Dependencies**:
- vidgear: vidgear[core]>=0.3.0
- pyav: av>=10.0.0
- opencv: opencv-python>=4.7.0
- ffmpeg: ffmpeg binary in PATH

---

### Network Plugins (`nodupe/plugins/network/`)

**Purpose**: Network and distributed features.

#### Components
- `remote_storage.py` - S3/GCS/Azure
- `distributed_scan.py` - Multi-machine
- `api_server.py` - REST API
- `sync_client.py` - Cloud sync

**Dependencies**:
- boto3>=1.26 (S3)
- google-cloud-storage>=2.7 (GCS)
- fastapi>=0.95 (API)

---

### Similarity Plugins (`nodupe/plugins/similarity/`)

**Purpose**: Similarity search.

#### Backends
- `brute_force.py` - NumPy (always available)
- `faiss_backend.py` - FAISS vector search
- `annoy_backend.py` - Spotify Annoy

**Dependencies**:
- brute_force: numpy only
- faiss: faiss-cpu>=1.7 or faiss-gpu>=1.7
- annoy: annoy>=1.17

---

## Import Patterns

### Core Imports (Always Work)
```python
# Core functionality - no optional deps
from nodupe.core.config import load_config
from nodupe.core.database import Database
from nodupe.core.scan import FileWalker
from nodupe.core.plugin_system import Plugin, PluginRegistry

# These always work
```

### Plugin Imports (With Fallback)
```python
# Commands - graceful degradation
try:
    from nodupe.plugins.commands import ScanCommand
except ImportError:
    ScanCommand = None  # Commands disabled

# ML - graceful degradation
try:
    from nodupe.plugins.ml import ONNXBackend
except ImportError:
    from nodupe.plugins.ml import CPUBackend as ONNXBackend

# Video - graceful degradation
try:
    from nodupe.plugins.video import VideoAnalyzer
except ImportError:
    VideoAnalyzer = None  # Video features disabled

# GPU - completely optional
try:
    from nodupe.plugins.gpu import CUDABackend
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

# Network - completely optional
try:
    from nodupe.plugins.network import RemoteStorage
except ImportError:
    RemoteStorage = None
```

### Safe Plugin Usage
```python
def process_video(path):
    if VideoAnalyzer is not None:
        analyzer = VideoAnalyzer()
        return analyzer.extract_frames(path)
    else:
        raise RuntimeError(
            "Video features not available. "
            "Install with: pip install nodupe[video]"
        )
```

---

## Configuration Structure

### config.toml
```toml
[core]
database_path = "~/.nodupe/database.db"
log_level = "INFO"
log_file = "~/.nodupe/nodupe.log"

[core.scan]
follow_symlinks = false
ignore_hidden = true
max_file_size_mb = 10000

[core.cache]
enable_hash_cache = true
enable_query_cache = true
max_cache_size_mb = 1024

[plugins]
scan_dirs = ["nodupe/plugins"]
auto_load = true

[plugins.commands]
default_action = "hardlink"

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
```

---

## Testing Strategy

### Test Commands

```bash
# Test core only (no plugins)
pytest tests/core/ --cov=nodupe/core

# Test specific plugin
pytest tests/plugins/video/

# Test specific module
pytest tests/core/database/test_connection.py

# Test everything
pytest tests/

# With coverage report
pytest --cov=nodupe --cov-report=html

# Integration tests
pytest tests/integration/

# Run benchmarks
python benchmarks/benchmark_suite.py
```

### Test Organization

```
tests/
├── core/              # Core tests (must have >80% coverage)
├── plugins/           # Plugin tests (isolated)
└── integration/       # Integration tests
```

### Test Isolation

- Core tests run WITHOUT plugin dependencies
- Plugin tests mock missing dependencies
- Integration tests use real dependencies
- Fixtures for database, file system

---

## Development Workflow

### Initial Setup
```bash
# 1. Clone repository
git clone <repo>
cd nodupe

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install for development
pip install -e ".[all,dev]"

# 4. Set up pre-commit hooks (optional)
pre-commit install
```

### Daily Development
```bash
# 1. Run tests
pytest

# 2. Check code quality
pylint nodupe/
pep8 nodupe/

# 3. Type checking (Pylance in VS Code)
# Or use mypy if configured

# 4. Format markdown docs
markdownlint docs/

# 5. Run specific tests
pytest tests/core/database/
```

### Before Commit
```bash
# 1. Run all tests
pytest

# 2. Check coverage
pytest --cov=nodupe --cov-report=html

# 3. Run benchmarks (if changed performance-critical code)
python benchmarks/benchmark_suite.py

# 4. Update changelog
# Edit CHANGELOG.md
```

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
pip install nodupe[video-all]       # All video backends

# Network Features
pip install nodupe[network]         # Cloud storage + API

# Similarity Search
pip install nodupe[similarity]      # FAISS CPU
pip install nodupe[similarity-gpu]  # FAISS GPU

# Complete Installation
pip install nodupe[all]

# Custom Combinations
pip install nodupe[ml,video,network]
pip install nodupe[gpu-cuda,similarity-gpu]
```

### setup.py extras_require
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
    'video-all': ['opencv-python', 'av', 'vidgear[core]', 'wgpu'],
    
    # Network features
    'network': ['boto3>=1.26', 'requests>=2.28', 'fastapi>=0.95'],
    
    # Similarity search
    'similarity': ['faiss-cpu>=1.7'],
    'similarity-gpu': ['faiss-gpu>=1.7'],
    
    # Development
    'dev': ['pytest>=7.0', 'pytest-cov>=4.0', 'pylint>=2.17'],
    
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

## Dependency Isolation Levels

### Level 0: Core (Required)
```
nodupe/core/*
├── Python 3.9+ standard library
└── SQLite (built into Python)

Dependencies: ZERO optional packages
Can function completely standalone
```

### Level 1: Basic Plugins (Minimal)
```
nodupe/plugins/ml/cpu_backend.py
nodupe/plugins/similarity/brute_force.py
nodupe/plugins/commands/*

Dependencies: numpy only (lightweight)
Basic functionality available
```

### Level 2: Advanced Plugins (Optional)
```
nodupe/plugins/ml/onnx_backend.py          → onnxruntime
nodupe/plugins/gpu/*                       → torch/tensorflow/pyopencl
nodupe/plugins/video/*                     → opencv/av/vidgear
nodupe/plugins/network/*                   → boto3/requests
nodupe/plugins/similarity/faiss_backend.py → faiss-cpu

Dependencies: Feature-specific heavy packages
Enhanced functionality
```

---

## Graceful Degradation Patterns

### Pattern 1: ML Backend Selection
```python
# Try backends in priority order
backend = None

try:
    from nodupe.plugins.ml import ONNXBackend
    backend = ONNXBackend()
    if backend.is_available():
        print("Using ONNX backend")
except ImportError:
    pass

if backend is None:
    from nodupe.plugins.ml import CPUBackend
    backend = CPUBackend()  # Always works
    print("Using CPU fallback backend")
```

### Pattern 2: Video Backend Selection
```python
# 5-tier fallback chain
backends_to_try = [
    'vidgear',      # Tier 1
    'analyzer',     # Tier 2
    'pyav',         # Tier 3
    'opencv',       # Tier 4
    'ffmpeg'        # Tier 5
]

backend = None
for backend_name in backends_to_try:
    try:
        backend = load_video_backend(backend_name)
        if backend.is_available():
            print(f"Using {backend_name} video backend")
            break
    except ImportError:
        continue

if backend is None:
    print("Video features disabled (no backends available)")
    video_features_enabled = False
```

### Pattern 3: GPU Acceleration
```python
# Try GPU, fallback to CPU
from nodupe.plugins.gpu import detect_gpu

gpu_type = detect_gpu()  # returns 'cuda', 'metal', 'opencl', or None

if gpu_type == 'cuda':
    from nodupe.plugins.gpu import CUDABackend
    backend = CUDABackend()
elif gpu_type == 'metal':
    from nodupe.plugins.gpu import MetalBackend
    backend = MetalBackend()
else:
    from nodupe.plugins.ml import CPUBackend
    backend = CPUBackend()  # Always works
```

### Pattern 4: Network Features
```python
# Network features completely optional
network_enabled = False

try:
    from nodupe.plugins.network import RemoteStorage
    storage = RemoteStorage(backend='s3')
    network_enabled = True
except ImportError:
    storage = None  # Local-only mode
    
print(f"Network features: {'enabled' if network_enabled else 'disabled'}")
```

---

## File Organization Best Practices

### Module Size
- Keep modules under 500 lines
- Split large modules into submodules
- One class per file for large classes

### Naming Conventions
- Modules: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case()`
- Constants: `UPPER_SNAKE_CASE`

### Import Order
```python
# 1. Standard library
import os
from pathlib import Path

# 2. Third-party (if any)
import numpy as np

# 3. Local application
from nodupe.core.database import Database
from nodupe.core.plugin_system import Plugin
```

---

## Summary

This structure provides:

✅ **Hard Isolation** - Core has zero optional dependencies  
✅ **Clear Delineation** - `core/` vs `core/plugin_system/` vs `plugins/`  
✅ **Domain Organization** - Plugins grouped by functionality  
✅ **Graceful Degradation** - Multiple fallback tiers  
✅ **Standard Python Layout** - Tests at top level, proper package structure  
✅ **Future Extensibility** - Easy to add new plugins  
✅ **Maintainability** - Clear organization, good separation of concerns  
✅ **Testability** - Isolated testing, high coverage targets  

**Use this exact structure.** It implements all architectural principles with no ambiguity.
