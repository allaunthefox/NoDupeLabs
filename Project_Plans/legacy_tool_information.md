# NoDupeLabs Legacy Tool Information

## Overview

This document provides a comprehensive analysis of the legacy NoDupeLabs system, documenting all its capabilities, plugins, architecture, and implementation details. It serves as a reference for understanding how the legacy system worked before the modular refactoring.

## Legacy System Architecture

### Monolithic Structure

The legacy NoDupeLabs was organized as a monolithic application with the following key characteristics:

1. **Tight Coupling**: Core functionality was tightly coupled with optional features
2. **Direct Imports**: Modules directly imported from each other without clear boundaries
3. **Limited Isolation**: No clear separation between core and plugin functionality
4. **Dependency Management**: Optional dependencies were not gracefully handled

### Core Components

The legacy system consisted of these main components:

1. **Core Engine**: File processing, hashing, and duplicate detection
2. **Database Layer**: SQLite-based file metadata storage
3. **Command System**: CLI interface and command processing
4. **Plugin System**: Basic plugin architecture with limited isolation
5. **Similarity Search**: Vector-based similarity detection
6. **AI/ML Backends**: Image processing and embedding generation

## Legacy System Structure

### Directory Structure

```
NoDupeLabs-Legacy/
├── nodupe/
│   ├── __init__.py
│   ├── main.py
│   ├── scanner.py
│   ├── planner.py
│   ├── applier.py
│   ├── nsfw_classifier.py
│   ├── similarity/
│   ├── ai/
│   ├── db/
│   ├── cli/
│   ├── plugins/
│   ├── vendor/
│   └── ...
├── plugins/
│   ├── nsfw_logger.py
│   ├── scan_reporter.py
│   └── startup_logger.py
├── docs/
├── tests/
├── scripts/
└── ...
```

### Key Modules

1. **main.py**: Entry point and CLI orchestration
2. **scanner.py**: File scanning and metadata extraction
3. **planner.py**: Duplicate detection and action planning
4. **applier.py**: Action execution and file management
5. **nsfw_classifier.py**: NSFW content detection
6. **similarity/**: Vector similarity search functionality
7. **ai/**: AI/ML backend implementations
8. **db/**: Database management and operations

## Legacy Plugin System

### Plugin Architecture

The legacy plugin system had the following characteristics:

1. **Basic Plugin Interface**: Simple registration and event system
2. **Limited Isolation**: Plugins could directly import from core modules
3. **Event System**: Basic hook mechanism for plugin integration
4. **Dependency Injection**: Minimal support for service injection

### Plugin Loading Process

1. Core system discovered plugin modules in the `plugins/` directory
2. Plugins were imported directly using Python's import system
3. Plugin manager instance was injected as global variable `pm`
4. Plugins registered callbacks for events using `pm.register()`
5. Core system emitted events during execution using `pm.emit()`

### Plugin Manager Interface

```python
class LegacyPluginManager:
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

### Legacy Plugins

#### 1. NSFW Logger Plugin

**File**: `plugins/nsfw_logger.py`

**Capabilities**:
- Post-scan NSFW content analysis
- Sample-based classification
- Graceful error handling
- Reporting of flagged content

**Implementation**:
```python
def on_scan_complete(records=None, **kwargs):
    try:
        from nodupe.nsfw_classifier import NSFWClassifier
        from nodupe.utils.filesystem import get_mime_safe
        from pathlib import Path
        c = NSFWClassifier(threshold=2)
        # Sample up to 20 files for classification
        sample = []
        if records:
            for r in records[:20]:
                sample.append((r[0], r[4]))

        res = c.batch_classify([(Path(p), m) for p, m in sample])
        flagged = [p for p, v in res.items() if v['flagged']]
        print(f"[plugins.nsfw_logger] sample flagged: {len(flagged)} / {len(sample)}")
    except Exception as e:
        print(f"[plugins.nsfw_logger] plugin failed gracefully: {e}")

pm.register("scan_complete", on_scan_complete)
```

#### 2. Scan Reporter Plugin

**File**: `plugins/scan_reporter.py`

**Capabilities**:
- Scan progress reporting
- Statistics collection
- Performance metrics
- Event-based reporting

#### 3. Startup Logger Plugin

**File**: `plugins/startup_logger.py`

**Capabilities**:
- System initialization logging
- Environment detection
- Configuration reporting
- Startup diagnostics

## Legacy Core Functionality

### File Scanning and Processing

**Module**: `nodupe/scanner.py`

**Capabilities**:
- Recursive directory traversal
- File metadata extraction
- Content hashing (SHA-512, BLAKE2b)
- MIME type detection
- Incremental scanning
- Progress tracking

**Key Features**:
- Multi-threaded scanning
- File filtering and exclusion
- Change detection
- Error handling and recovery

### Duplicate Detection and Planning

**Module**: `nodupe/planner.py`

**Capabilities**:
- Duplicate identification
- Action planning
- Conflict resolution
- Strategy configuration

**Key Features**:
- Content-based duplicate detection
- Multiple resolution strategies
- CSV action plan generation
- Dry-run mode

### Action Execution

**Module**: `nodupe/applier.py`

**Capabilities**:
- Action plan execution
- File management
- Checkpoint creation
- Rollback support

**Key Features**:
- Safe file operations
- Transaction-like behavior
- Checkpoint-based rollback
- Progress reporting

### NSFW Classification

**Module**: `nodupe/nsfw_classifier.py`

**Capabilities**:
- NSFW content detection
- Multi-tier classification
- Batch processing
- Threshold configuration

**Key Features**:
- Filename pattern matching
- Metadata analysis
- AI-based classification
- Configurable sensitivity

### Similarity Search

**Module**: `nodupe/similarity/`

**Capabilities**:
- Vector similarity search
- Index management
- Near-duplicate detection
- Multiple backend support

**Key Features**:
- Brute-force search
- FAISS integration
- Index persistence
- Similarity thresholding

## Legacy Command System

### Command Structure

The legacy system used a comprehensive CLI interface with the following commands:

#### 1. `init`
- Initialize configuration with presets
- Configuration file generation
- Preset selection (default, performance, paranoid, media, etc.)

#### 2. `scan`
- Directory scanning
- Metadata extraction
- Hash computation
- Database population

#### 3. `plan`
- Duplicate detection
- Action planning
- CSV generation
- Strategy configuration

#### 4. `apply`
- Action execution
- File management
- Checkpoint creation
- Change application

#### 5. `verify`
- Checkpoint validation
- Filesystem verification
- Integrity checking
- Pre-rollback validation

#### 6. `rollback`
- Change reversal
- File restoration
- Checkpoint-based recovery
- State restoration

#### 7. `similarity`
- Similarity index management
- Vector search
- Near-duplicate finding
- Index persistence

#### 8. `archive`
- Archive inspection
- Archive extraction
- Archive management
- Format support

#### 9. `mount`
- FUSE filesystem mounting
- Database browsing
- Virtual filesystem
- Read-only access

## Legacy Configuration System

### Configuration File

**File**: `nodupe.yml`

**Structure**:
```yaml
hash_algo: sha512
dedup_strategy: content_hash
parallelism: 0  # 0 = auto-detect
dry_run: true
nsfw:
  enabled: false
  threshold: 2
ignore_patterns:
  - .git
  - node_modules
  - .DS_Store
```

### Configuration Features

1. **Hash Algorithm Selection**: SHA-512, BLAKE2b, SHA-256
2. **Parallelism Control**: Auto-detection or manual configuration
3. **Dry Run Mode**: Safe testing without changes
4. **NSFW Detection**: Configurable sensitivity
5. **Ignore Patterns**: File/directory exclusion
6. **Environment Auto-Tuning**: Desktop, NAS, Cloud, Container

## Legacy Metadata Format

### Meta.json Structure

```json
{
  "spec": "nodupe_meta_v1",
  "generated_at": "2025-12-02T12:00:00Z",
  "summary": {
    "files_total": 15,
    "bytes_total": 10485760,
    "categories": {"image": 10, "text": 5},
    "topics": ["vacation", "beach"],
    "keywords": ["2025", "summer"]
  },
  "entries": [
    {
      "name": "photo.jpg",
      "size": 204800,
      "mtime": 1730090400,
      "file_hash": "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e",
      "hash_algo": "sha512",
      "mime": "image/jpeg",
      "category": "image",
      "subtype": "photo",
      "topic": "vacation"
    }
  ]
}
```

### Metadata Features

1. **Self-Describing**: Contains schema version and generation timestamp
2. **Comprehensive**: File details, hashes, categories, and topics
3. **Machine-Readable**: Standard JSON format
4. **Long-Lived**: Designed for archive preservation
5. **Verifiable**: Hash-based integrity checking

## Legacy Quality and Testing

### Quality Standards

1. **Type Checking**: MyPy with Python 3.9+ compatibility
2. **Linting**: Flake8 for PEP 8 compliance
3. **Docstring Coverage**: 100% enforced with Interrogate
4. **Testing**: Comprehensive test suite with unit/integration/slow markers

### Testing Architecture

```bash
# Run all tests
pytest tests/ -v

# Run fast tests only
pytest tests/ -v -m "not slow and not integration"

# Run quality checks
flake8 nodupe/
mypy nodupe/
interrogate -vv nodupe/ --fail-under 100
```

### CI/CD Pipeline

1. **Automated Testing**: Runs on every commit
2. **Quality Gates**: Flake8, MyPy, Interrogate must pass
3. **Coverage Monitoring**: Test coverage tracking
4. **Regression Prevention**: Comprehensive test suite

## Legacy Dependencies and Vendoring

### Dependency Management

1. **Auto-Install**: Automatic dependency installation at runtime
2. **Graceful Degradation**: Fallback to standard library
3. **Vendoring**: Bundled libraries for offline operation

### Vendored Libraries

**Location**: `nodupe/vendor/libs`

**Purpose**: Ensure basic functionality without external dependencies

**Contents**:
- PyYAML
- ONNX Runtime
- Other essential libraries

### Offline Installation

```bash
# Install vendored wheels
python scripts/install_vendored_wheels.py

# Install specific vendored wheel
python scripts/install_vendored_wheels.py --pattern onnxruntime
```

## Legacy vs. Modern Architecture Comparison

### Key Differences

| Feature | Legacy System | Modern System |
|---------|--------------|---------------|
| **Architecture** | Monolithic | Modular |
| **Plugin Isolation** | Limited | Hard Isolation |
| **Dependency Management** | Direct imports | Dependency Injection |
| **Error Handling** | Basic | Graceful Degradation |
| **Testing** | Comprehensive | Enhanced with CI/CD |
| **Configuration** | YAML-based | TOML-based |
| **Documentation** | Manual | Automated |
| **Performance** | Environment-tuned | Optimized with benchmarks |

### Migration Benefits

1. **Improved Maintainability**: Clear module boundaries
2. **Enhanced Safety**: Hard isolation prevents crashes
3. **Better Testing**: Comprehensive test coverage
4. **Modern Tooling**: Automated documentation and CI/CD
5. **Performance Optimization**: Benchmark-driven improvements
6. **Future-Proof**: Plugin marketplace and ecosystem expansion

## Legacy System Strengths

### Robust Features

1. **Comprehensive File Processing**: Advanced scanning and metadata extraction
2. **Sophisticated Duplicate Detection**: Multiple strategies and algorithms
3. **Powerful Similarity Search**: Vector-based near-duplicate detection
4. **Flexible Configuration**: Environment-aware auto-tuning
5. **Self-Describing Metadata**: Long-lived archive preservation
6. **Extensive Testing**: High code quality standards

### Proven Capabilities

1. **Large-Scale Processing**: Handles thousands of files efficiently
2. **Multi-Format Support**: Images, videos, archives, documents
3. **Advanced Detection**: NSFW classification, MIME type detection
4. **Safety Features**: Read-only detection, integrity verification
5. **Recovery Mechanisms**: Checkpoint-based rollback system
6. **Cross-Platform**: Works on desktop, NAS, cloud, and containers

## Legacy System Limitations

### Architectural Challenges

1. **Tight Coupling**: Difficult to modify or extend components
2. **Limited Isolation**: Plugin failures could affect core system
3. **Dependency Management**: Complex dependency resolution
4. **Testing Complexity**: Hard to test components in isolation
5. **Documentation Maintenance**: Manual documentation updates
6. **Performance Bottlenecks**: Limited optimization opportunities

### Technical Debt

1. **Monolithic Codebase**: Large, complex modules
2. **Global State**: Shared variables and state
3. **Direct Imports**: Circular dependency risks
4. **Limited Extensibility**: Hard to add new features
5. **Maintenance Challenges**: Complex refactoring required
6. **Scalability Issues**: Performance limitations at scale

## Conclusion

The legacy NoDupeLabs system provided a robust foundation for file deduplication and organization with comprehensive features for scanning, duplicate detection, similarity search, and metadata management. However, its monolithic architecture and limited plugin isolation presented challenges for maintainability, testing, and extensibility.

The modern refactored system addresses these limitations through modular architecture, hard isolation between components, dependency injection, and enhanced testing infrastructure while preserving the core functionality and strengths of the legacy system.
