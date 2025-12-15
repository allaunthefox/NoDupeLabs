<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright (c) 2025 Allaun -->

# NoDupeLabs Architecture

## Overview

This document outlines the modular architecture for NoDupeLabs with hard isolation between the core loader/orchestrator and all other functions.**IMPORTANT**: This document reflects the**actual current implementation**as of 2025-12-13, not aspirational goals.

## Core Architecture Principles

1. **Hard Isolation**: Core loader must be completely isolated from optional functionality
1. **Graceful Degradation**: All optional features must fail gracefully and fall back to the standard library
1. **Plugin-Based**: Non-core functionality implemented as plugins with clear interfaces
1. **Dependency Injection**: Core services injected rather than hard-coded
1. **Standard Library Fallback**: When all else fails, use the Python standard library

## Current Implementation Status

### Legend

- ✅**IMPLEMENTED**- Fully functional with complete implementation
- ⚠️**PARTIAL**- Some functionality implemented, some stubbed
- ❌**STUBBED**- File exists but raises NotImplementedError
- 🚧**IN PROGRESS**- Active development

## Module Structure

### 1. Core Loader/Orchestrator (Mandatory)

**Location**: `nodupe/core/`

**Status**: ✅ IMPLEMENTED (Full functionality working)

**Responsibilities**:

- CLI entry point and argument parsing
- Basic configuration loading
- Core command routing
- Plugin management (discovery, loading, lifecycle)
- Dependency injection container
- Error handling and graceful degradation
**System Resource Auto-tuning** (CPU/RAM/Drive detection)

**Key Components**:

- `main.py` - ✅ Entry point using unified `loader.bootstrap()` (fully implemented)
- `cli/` - ✅ CLI parsing and routing
- `container.py` - ✅ Service container for DI
- `config.py` - ✅ Configuration loading (TOML support + graceful fallback)
- `loader.py` - ✅**IMPLEMENTED**(Unified Core Loader with system resource detection) (fully implemented)
- `plugins.py` - ✅ Plugin integration
- `deps.py` - ✅ Dependency management with graceful fallback
- `errors.py` - ✅ Error handling utilities
`plugin_system/` - ✅ IMPLEMENTED (Full plugin infrastructure complete)
  - `base.py` - ✅ Abstract plugin interface
  - `registry.py` - ✅ Plugin registry (fully implemented)
  - `loader.py` - ✅ IMPLEMENTED (Plugin loading with security and validation)
  - `lifecycle.py` - ✅ IMPLEMENTED (Plugin lifecycle management with dependency resolution)
  - `discovery.py` - ✅ IMPLEMENTED (Recursive plugin discovery)
  - `hot_reload.py` - ✅ IMPLEMENTED (Polling-based hot reload)
  - `security.py` - ✅ IMPLEMENTED (Plugin security validation with AST analysis)
  - `dependencies.py` - ✅ IMPLEMENTED (Dependency resolution with circular detection)
  - `compatibility.py` - ✅ IMPLEMENTED (Compatibility checking with version validation)

**Dependencies**: Standard library only

**Notes**: Core loader is now unified (`main.py` uses `loader.py`), robust (graceful degradation), and feature-complete (auto-tuning enabled).

### 2. Database Layer (Core)**Location**: `nodupe/core/database/`**Status**: ✅**IMPLEMENTED**(Complete database layer with schema, transactions, indexing)**Responsibilities**:

- File metadata storage
- Duplicate detection
- Basic indexing
- Transaction management**Key Components**:

- `connection.py` - ✅ SQLite connection management with pooling (fully implemented)
- `files.py` - ✅ File repository with CRUD operations (fully implemented)
- `embeddings.py` - ✅ Embedding storage with model versioning (fully implemented)
- `schema.py` - ✅**IMPLEMENTED**(Complete schema management, 7 tables, 22 indexes) (fully implemented)
- `indexing.py` - ✅**IMPLEMENTED**(Query optimization, index management) (fully implemented)
- `transactions.py` - ✅**IMPLEMENTED**(ACID transactions with savepoints) (fully implemented)
- `repository.py` - ⚠️**UNUSED**(Interface only - `files.py` implements repository pattern)**Dependencies**: sqlite3 (standard library)**Notes**: ✅**Database layer complete!**Schema, transactions, and indexing fully implemented.

### 3. File Processing (Core)**Location**: `nodupe/core/scan/`**Status**: ✅**IMPLEMENTED**(Fully functional)**Responsibilities**:

- File discovery and walking
- Hashing and metadata extraction
- Progress tracking
- Incremental scanning**Key Components**:

- `walker.py` - ✅ File system traversal (fully implemented)
- `processor.py` - ✅ File metadata extraction (fully implemented)
- `hasher.py` - ✅ Cryptographic hashing (multiple algorithms) (fully implemented)
- `progress.py` - ✅ Progress tracking with time estimation (fully implemented)
- `file_info.py` - ✅ File information utilities (fully implemented)**Dependencies**: Standard library + hashlib**Notes**: Fully functional scanning system.

### 4. Core Utilities**Location**: `nodupe/core/`**Status**: ✅**FULLY IMPLEMENTED**(13/13 utilities implemented)**Responsibilities**:

- Filesystem operations
- Hashing algorithms
- Compression utilities
- MIME type detection
- Security and validation
- Resource management**Key Components**:

- `filesystem.py` - ✅**IMPLEMENTED**(Safe file operations, atomic writes) (fully implemented)
- `logging.py` - ✅**IMPLEMENTED**(Structured logging with rotation) (fully implemented)
- `validators.py` - ✅**IMPLEMENTED**(Comprehensive validation) (fully implemented)
- `mime_detection.py` - ✅**IMPLEMENTED**(Magic number detection) (fully implemented)
- `security.py` - ✅**IMPLEMENTED**(Path sanitization, security validation) (fully implemented)
- `compression.py` - ✅**IMPLEMENTED**(gzip/bz2/lzma/zip/tar support) (fully implemented)
- `limits.py` - ✅**IMPLEMENTED**(Rate limiting, resource monitoring) (fully implemented)
- `parallel.py` - ✅**IMPLEMENTED**(Thread/process pools, map-reduce) (fully implemented)
- `pools.py` - ✅**IMPLEMENTED**(Object/connection/worker pools) (fully implemented)
- `version.py` - ✅**IMPLEMENTED**(Version management with compatibility checking) (fully implemented)
- `incremental.py` - ✅**IMPLEMENTED**(Incremental processing with checkpoint management) (fully implemented)
- `mmap_handler.py` - ✅**IMPLEMENTED**(Memory-mapped file operations with context manager) (fully implemented)
- `api.py` - ✅**IMPLEMENTED**(API management with stability decorators and registration) (fully implemented)**Dependencies**: Standard library only**Notes**: ✅**MAJOR PROGRESS**- 13/13 core utilities fully implemented.

### 5. Cache System (Core)**Location**: `nodupe/core/cache/`**Status**: ✅**IMPLEMENTED**(Complete cache system)**Responsibilities**:

- File hash caching
- Query result caching
- Embedding vector caching
- TTL expiration and eviction**Key Components**:

- `hash_cache.py` - ✅**IMPLEMENTED**(File hash caching with TTL) (fully implemented)
- `query_cache.py` - ✅**IMPLEMENTED**(Query result caching) (fully implemented)
- `embedding_cache.py` - ✅**IMPLEMENTED**(Embedding vector caching) (fully implemented)**Dependencies**: Standard library only

### Notes**: ✅**Cache system complete
## Plugin Architecture

### Plugin Categories

#### Commands Plugin (Implemented)**Location**: `nodupe/plugins/commands/`**Status**: ✅**IMPLEMENTED**(4 commands working)

- `__init__.py` - ✅ Command manager (fully implemented)
- `scan.py` - ✅ Scan command (Wired to Core) (fully implemented)
- `apply.py` - ✅ Apply command (Wired to Core) (fully implemented)
- `similarity.py` - ✅ Similarity command (Wired to Core) (fully implemented)
- `plan.py` - ✅**IMPLEMENTED**(Wired to Core - Strategies Active) (fully implemented)**Dependencies**: Core modules only**Notes**: Commands work via plugin manager integration.

#### Other Plugins (Empty/Stubbed)

-**AI/ML**: Empty
-**GPU**: Empty
-**Video**: Empty
-**Network**: Empty
-**Similarity Backend**: ✅**Implemented**(BruteForce, Faiss)

## Actual vs Documented Status

### What Actually Works

1. ✅**Core loader and CLI**- Unified, auto-tuning, robust
1. ✅**Configuration**- TOML config loading with fallback
1. ✅**File scanning**- FileWalker and FileProcessor
1. ✅**File hashing**- Multiple hash algorithms
1. ✅**Database CRUD**- File metadata storage + Transactions/Schema
1. ✅**Command plugins**- Scan, Apply, Plan, Similarity
1. ✅**Cache System**- Hash, Query, Embeddings
1. ✅**Plugin System**- Discovery, Loading, Lifecycle, Security

### What Needs Implementation

1. ❌**ML/AI/GPU/Video/Network plugins**- Empty directories
1. ✅**Core utilities**- All implemented (13/13 completed)
1. ✅**Similarity backend**- Fully implemented

### Reality Check**Previous Documentation Claimed**:

- "Core architecture 95% complete"**Actual Status**:

- ✅**Commands**: 100% (All core commands functional)
- ❌**Advanced Plugins**: 0%**Honest Assessment**: Core architecture is stable and robust. Advanced features are next.

## Priority Implementation Needs

### Critical (Blocking Basic Functionality)

1. ✅ ~~Implement plugin loader~~ - COMPLETED
1. ✅ ~~Implement database transactions~~ - COMPLETED
1. ✅ ~~Implement basic utilities~~ - COMPLETED
1. ✅ ~~Implement cache system~~ - COMPLETED
1. ✅ ~~Implement Plan command~~ - COMPLETED
1. ✅ ~~Unified Core Loader~~ - COMPLETED

### High Priority (Needed for Production)

1. ✅ ~~Implement Similarity Backend~~ - COMPLETED
1. ✅ Fill in remaining utility stubs (`mmap`, `incremental`, `api`) - COMPLETED

### Medium Priority (Enhanced Features)

1. ML/AI backends
1. Video processing
1. Network features

## CI/CD Pipeline

### CI/CD Overview

The project includes a comprehensive automated CI/CD pipeline implemented with GitHub Actions.

### Pipeline Components**Location**: `.github/workflows/test.yml`**Status**: ✅**IMPLEMENTED**(Complete automated pipeline)**Features**:

-**Multi-Python Testing**: Tests run on Python 3.8, 3.9, 3.10, 3.11, 3.12, and 3.13
-**Code Quality Gates**:
  - Pylint with 10.0 threshold (current: 9.97/10)
  - Mypy strict type checking
  - Black formatting validation
  - isort import sorting validation
  - flake8 linting
-**Coverage Reporting**:
  - pytest with XML, HTML, and terminal coverage reports
  - Codecov integration for coverage tracking
-**Security Scanning**: Automated security checks with bandit and safety
-**Dependency Management**: Automated updates via Dependabot
-**Additional Checks**: Formatting, import sorting, and code style validation

### Configuration Files

- `.github/workflows/test.yml` - Main CI/CD workflow
- `.github/dependabot.yml` - Automated dependency updates
- `.codecov.yml` - Codecov configuration

### Pipeline Triggers

- Runs on every push to `main` and `develop` branches
- Runs on every pull request to `main` branch
- Automated dependency updates weekly

## Architecture Conclusion

The NoDupeLabs architecture now has a**complete and robust core**. The initial "Infrastructure Hell" has been resolved with the unification of the Core Loader and the completion of the Plugin System. The system is ready for the implementation of advanced features.**Last Updated**: 2025-12-15**Status**: Active Development - Phase 6 Complete - Core Functional
