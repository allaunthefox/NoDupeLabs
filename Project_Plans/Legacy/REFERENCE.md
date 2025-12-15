<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright (c) 2025 Allaun -->

# NoDupeLabs Legacy System Reference

## Overview

This document provides comprehensive information about the legacy NoDupeLabs system for reference during migration and feature restoration. It serves as a historical record of how the legacy system worked.

## Legacy System Architecture

### Monolithic Structure

The legacy NoDupeLabs was organized as a monolithic application with these characteristics:

1. **Tight Coupling**: Core functionality was tightly coupled with optional features
1. **Direct Imports**: Modules directly imported from each other without clear boundaries
1. **Limited Isolation**: No clear separation between core and plugin functionality
1. **Dependency Management**: Optional dependencies were not gracefully handled

### Directory Structure

```yaml
NoDupeLabs-Legacy/
├── nodupe/
│   ├──__init__.py
│   ├── main.py              # Entry point
│   ├── scanner.py           # File scanning
│   ├── planner.py           # Duplicate detection
│   ├── applier.py           # Action execution
│   ├── nsfw_classifier.py   # NSFW detection
│   ├── similarity/          # Vector search
│   ├── ai/                  # AI/ML backends
│   ├── db/                  # Database management
│   ├── cli/                 # CLI interface
│   ├── plugins/             # Plugin system
│   └── vendor/              # Vendored libraries
├── plugins/
│   ├── nsfw_logger.py
│   ├── scan_reporter.py
│   └── startup_logger.py
├── docs/
├── tests/
└── scripts/
```

## Legacy Plugin System

### Plugin Architecture

The legacy plugin system provided basic event-based integration:

### Plugin Manager Interface
```python
class LegacyPluginManager:
```

def register(self, event: str, callback: Callable):

```text
"""Register callback for event"""
pass
```

```text

```

def emit(self, event: str,**kwargs):

```text
"""Emit event to all registered callbacks"""
pass
```

```text

```

def load_plugins(self, paths: List[str]):

```python
"""Load plugins from specified paths"""
pass
```

```text
```

### Legacy Plugins

#### 1. NSFW Logger Plugin

**File**: `plugins/nsfw_logger.py`

**Capabilities**:

- Post-scan NSFW content analysis
- Sample-based classification
- Graceful error handling
- Reporting of flagged content

**Implementation Example**:

```python
def on_scan_complete(records=None,**kwargs):
```

try:

```python
from nodupe.nsfw_classifier import NSFWClassifier
from nodupe.utils.filesystem import get_mime_safe
from pathlib import Path
c = NSFWClassifier(threshold=2)
# Sample up to 20 files for classification
sample = []
if records:
```

for r in records[:20]:
    sample.append((r[0], r[4]))

```text
```

```text

```

```text
res = c.batch_classify([(Path(p), m) for p, m in sample])
flagged = [p for p, v in res.items() if v['flagged']]
print(f"[plugins.nsfw_logger] sample flagged: {len(flagged)} / {len(sample)}")
```

except Exception as e:

```text
print(f"[plugins.nsfw_logger] plugin failed gracefully: {e}")
```

```text

pm.register("scan_complete", on_scan_complete)
```

## 2. Scan Reporter Plugin

**File**: `plugins/scan_reporter.py`

**Capabilities**:

- Scan progress reporting
- Statistics collection
- Performance metrics
- Event-based reporting

### 3. Startup Logger Plugin

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
- File management operations
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

### Command Reference

#### 1. `init` - Configuration Initialization

- Initialize configuration with presets
- Configuration file generation
- Preset selection (default, performance, paranoid, media, etc.)

#### 2. `scan` - Directory Scanning

- Directory scanning
- Metadata extraction
- Hash computation
- Database population

#### 3. `plan` - Duplicate Planning ✅ RESTORED IN MODERN

- Duplicate detection
- Action planning
- CSV generation
- Strategy configuration

#### 4. `apply` - Action Execution

- Action execution
- File management
- Checkpoint creation
- Change application

#### 5. `verify` - Checkpoint Validation ✅ IMPLEMENTED

- Checkpoint validation
- Filesystem verification
- Integrity checking
- Pre-rollback validation

#### 6. `rollback` - Change Reversal ⚠️ MISSING IN MODERN

- Change reversal
- File restoration
- Checkpoint-based recovery
- State restoration

#### 7. `similarity` - Similarity Search

- Similarity index management
- Vector search
- Near-duplicate finding
- Index persistence

#### 8. `archive` - Archive Management ⚠️ MISSING IN MODERN

- Archive inspection
- Archive extraction
- Archive management
- Format support (ZIP, TAR, etc.)

#### 9. `mount` - Virtual Filesystem ⚠️ MISSING IN MODERN

- FUSE filesystem mounting
- Database browsing
- Virtual filesystem
- Read-only access

## Legacy Configuration System

### Configuration File Format**File**: `nodupe.yml`**Structure**:

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

1.**Hash Algorithm Selection**: SHA-512, BLAKE2b, SHA-256
1.**Parallelism Control**: Auto-detection or manual configuration
1.**Dry Run Mode**: Safe testing without changes
1.**NSFW Detection**: Configurable sensitivity
1.**Ignore Patterns**: File/directory exclusion
1.**Environment Auto-Tuning**: Desktop, NAS, Cloud, Container

### Environment Presets

-**default**: Balanced settings
-**performance**: Speed-optimized
-**paranoid**: Maximum safety
-**media**: Media file optimized
-**desktop**: Desktop environment
-**nas**: NAS/server optimized
-**cloud**: Cloud storage optimized
-**container**: Containerized deployment

## Legacy Metadata Format

### Meta.json Structure

```json
{
  "spec": "nodupe_meta_v1",
  "generated_at": "2025-12-02T12:00:00Z",
 "summary": {
```

"files_total": 15,
"bytes_total": 10485760,
"categories": {"image": 10, "text": 5},
"topics": ["vacation", "beach"],
"keywords": ["2025", "summer"]

```text
  },
  "entries": [
```

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

```text
  ]
}
```

### Metadata Features

1.**Self-Describing**: Contains schema version and generation timestamp
1.**Comprehensive**: File details, hashes, categories, and topics
1.**Machine-Readable**: Standard JSON format
1.**Long-Lived**: Designed for archive preservation
1.**Verifiable**: Hash-based integrity checking

## Legacy Quality and Testing

### Quality Standards

1.**Type Checking**: MyPy with Python 3.9+ compatibility
1.**Linting**: Flake8 for PEP 8 compliance
1.**Docstring Coverage**: 100% enforced with Interrogate
1.**Testing**: Comprehensive test suite with unit/integration/slow markers

### Testing Commands

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

## Legacy Dependencies and Vendoring

### Dependency Management

1.**Auto-Install**: Automatic dependency installation at runtime
1.**Graceful Degradation**: Fallback to standard library
1.**Vendoring**: Bundled libraries for offline operation

### Vendored Libraries**Location**: `nodupe/vendor/libs`**Contents**:

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

## Legacy System Strengths

### Robust Features

1.**Comprehensive File Processing**: Advanced scanning and metadata extraction
1.**Sophisticated Duplicate Detection**: Multiple strategies and algorithms
1.**Powerful Similarity Search**: Vector-based near-duplicate detection
1.**Flexible Configuration**: Environment-aware auto-tuning
1.**Self-Describing Metadata**: Long-lived archive preservation
1.**Extensive Testing**: High code quality standards

### Proven Capabilities

1.**Large-Scale Processing**: Handles thousands of files efficiently
1.**Multi-Format Support**: Images, videos, archives, documents
1.**Advanced Detection**: NSFW classification, MIME type detection
1.**Safety Features**: Read-only detection, integrity verification
1.**Recovery Mechanisms**: Checkpoint-based rollback system
1.**Cross-Platform**: Works on desktop, NAS, cloud, and containers

## Legacy System Limitations

### Architectural Challenges

1.**Tight Coupling**: Difficult to modify or extend components
1.**Limited Isolation**: Plugin failures could affect core system
1.**Dependency Management**: Complex dependency resolution
1.**Testing Complexity**: Hard to test components in isolation
1.**Documentation Maintenance**: Manual documentation updates
1.**Performance Bottlenecks**: Limited optimization opportunities

### Technical Debt

1.**Monolithic Codebase**: Large, complex modules
1.**Global State**: Shared variables and state
1.**Direct Imports**: Circular dependency risks
1.**Limited Extensibility**: Hard to add new features
1.**Maintenance Challenges**: Complex refactoring required
1.**Scalability Issues**: Performance limitations at scale

## Migration Insights

### Features to Preserve

1.**Planner Module**: Critical for duplicate detection
1.**Rollback System**: Essential safety feature
1.**Verify Command**: Integrity checking capability
1.**Archive Support**: Handle compressed files
1.**Environment Auto-tuning**: Optimize for different deployments

### Features to Modernize

1.**Plugin Architecture**: Implement hard isolation
1.**Dependency Injection**: Replace direct imports
1.**Configuration Format**: YAML → TOML migration
1.**Error Handling**: Enhanced graceful degradation
1.**Testing Infrastructure**: Better isolation and coverage

### Features to Deprecate

1.**Virtual Filesystem (FUSE)**: Low usage, high complexity
1.**Vendored Dependencies**: Use modern package management
1.**Global State**: Replace with service containers
1.**Direct Module Imports**: Use dependency injection

## Conclusion

The legacy NoDupeLabs system provided a robust, feature-rich foundation for file deduplication and organization. While its monolithic architecture presented maintenance challenges, it included several critical features (planner, verify, rollback, archive support) that must be restored in the modern system to achieve feature parity.

This reference document serves as a guide for understanding legacy behavior and informing the restoration of missing features in the modern modular architecture.
