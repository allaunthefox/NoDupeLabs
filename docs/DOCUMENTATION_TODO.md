# NoDupeLabs Documentation Roadmap

This document outlines the comprehensive documentation work required to bring all
modules in the NoDupeLabs project up to professional standards.

## Overview

A thorough audit of the codebase (conducted 2025-12-03) revealed that **76% of
modules lack module-level docstrings**. This roadmap prioritizes documentation
work based on module criticality and usage frequency.

## Progress Summary

- **Total modules reviewed**: 50+
- **Modules fully documented**: 4 (cli.py, config.py, scanner.py, db.py)
- **External docs updated**: 5 (BEGINNERS_GUIDE.md, SIMILARITY.md, AI_BACKEND.md, CHANGELOG.md, docs/CHANGELOG.md entry)
- **Repository releases**: v0.1.1 created and published (includes full changelog as release notes)
- **Modules remaining**: ~48
- **Completion**: ~10% (Phase 1 completed for scanner + db; next phase ready)
- **Last updated**: 2025-12-03

## Recent work & status (summary)

- Documentation: Completed module-level and function docstrings for `nodupe/scanner.py` and
  `nodupe/db.py` (Phase 1) with notes and follow-ups in-place. Examples and longer how-to
  snippets remain as follow-up work.
- Changelog & release: Updated `docs/CHANGELOG.md` with detailed entries covering the recent
  CI and documentation efforts, then created and published a release tag `v0.1.1` with the
  full changelog as the release body.
- CI & vendoring hardening: Disabled submodule handling in CI checkout and set `fetch-depth: 0`.
  Added/updated vendoring helpers and a `validate-vendored-install` CI job that performs offline
  installs of vendored wheels and smoke-import checks; this protects CI from network-dependent
  failures and removed-history artifacts (e.g. previously-removed submodules).
- Scanner & tests: Implemented ETA / STALL progress messaging, a hard `max_idle_time` to prevent
  scanner hangs, and added unit tests exercising timing and progress behavior. Adjusted tests to
  import repo source reliably (PYTHONPATH usage) and made helpers easier to monkeypatch where needed.
- Lint fixes: Resolved a flake8 E501 docstring-length violation introduced during documentation
  work by wrapping the offending `nodupe/cli.py` docstring to satisfy line-length checks.

If you'd like, I can now:

- Start Phase 2 documentation (priority: `nodupe/applier.py`, `nodupe/archiver.py`).
- Continue adding usage examples and migration notes to the `nodupe/db.py` docs.
- Review CI runs and address any remaining failing jobs.

## Priority 1: Critical Infrastructure (IMMEDIATE)

These modules form the core of the application and are used by almost every
other module. They require immediate, comprehensive documentation.

### 1.1 Database Layer

**File**: `nodupe/db.py`

**Status**: ✅ Module and method docstrings added

**Notes**: Module-level docstring added and the `DB` class and public
methods (initialization, migrations, upsert/get helpers, embedding
helpers) were documented. Follow-up: add usage examples to docs and a
short migration guide for maintainers.

**Required Documentation**:
- Module docstring explaining:
  - SQLite database schema and WAL mode
  - Schema versioning and migration strategy
  - Thread safety considerations
  - Performance characteristics
- DB class docstring with:
  - Usage examples
  - Connection lifecycle
  - Context manager support
- Method docstrings for:
  - `__init__()` - Parameters: db_path, connection options
  - `_init_schema()` - Schema creation and migration logic
  - `upsert()` - Insert/update file records with conflict resolution
  - `get_duplicates()` - Duplicate detection query logic
  - `get_all()` - Full table scan considerations
  - `iter_files()` - Generator pattern for large datasets
  - `get_known_files()` - Incremental scan optimization
  - `upsert_embedding()` - Embedding storage for similarity search
  - `get_embedding()` - Embedding retrieval
  - `get_all_embeddings()` - Bulk embedding export
  - `close()` - Cleanup and connection management

**Estimated Effort**: 2-3 hours

---


### 1.2 Scanner Module

**File**: `nodupe/scanner.py`

**Status**: ✅ Module and function-level docstrings added

**Required Documentation**:
- Module docstring explaining:
  - Parallel scanning architecture
  - Queue-based work distribution
  - ETA calculation mechanism
  - Timeout and stall detection
  - Incremental scanning strategy
- Function docstrings:
  - `iter_files()` - File discovery with ignore patterns
  - `process_file()` - Single file processing pipeline
  - `threaded_hash()` - **Critical**: Document all parameters:
    - `known_files` - Dict for incremental scanning
    - `heartbeat_interval` - Progress reporting frequency
    - `stall_timeout` / `max_idle_time` - Worker timeout detection
    - `show_eta` - ETA display toggle
    - `collect` - List collection vs. generator mode
  - `validate_hash_algo()` - Hash algorithm validation (re-exported)

**Notes**: Module-level docstring and detailed function docstrings for
`iter_files`, `process_file` and `threaded_hash` were added on 2025-12-03.
Remaining work: add usage examples and expand architecture diagram in docs.

**Estimated Effort**: 0.5-1 hour (follow-ups)

---

### 1.3 Applier Module

**File**: `nodupe/applier.py`

**Status**: ❌ No module docstring, incomplete function docstrings

**Required Documentation**:
- Module docstring explaining:
  - Three-phase commit pattern (Prepare/Execute/Commit)
  - Rollback safety guarantees
  - Checkpoint file format
  - Atomic operation requirements
- Function docstrings:
  - `apply_moves()` - Add detailed Args/Returns/Raises sections
  - Document error handling and rollback triggers
  - Explain checkpoint JSON structure

**Estimated Effort**: 1-2 hours

---

### 1.4 Archiver Module

**File**: `nodupe/archiver.py`

**Status**: ❌ No module docstring, no class/method docstrings

**Required Documentation**:
- Module docstring with:
  - Supported archive formats (zip, tar, 7z, rar, etc.)
  - Optional dependencies and graceful degradation
  - Password-protected archive handling
  - Path traversal attack prevention
- ArchiveHandler class:
  - Usage examples
  - Format detection logic
  - All method docstrings (_detect_type, list_contents, extract, etc.)

**Estimated Effort**: 2 hours

---

## Priority 2: Core Functionality (HIGH)

These modules implement primary user-facing features.

### 2.1 Planner Module

**File**: `nodupe/planner.py`

**Status**: ❌ No module docstring, no function docstrings

**Required Documentation**:
- Module docstring explaining:
  - Deduplication strategy (keep first, move rest)
  - CSV plan format
  - Conflict resolution for filename collisions
- Function docstrings:
  - `ensure_unique()` - Filename collision handling
  - `write_plan_csv()` - CSV generation with columns specification

**Estimated Effort**: 1 hour

---

### 2.2 Rollback Module

**File**: `nodupe/rollback.py`

**Status**: ❌ No module docstring, no function docstrings

**Required Documentation**:
- Module docstring explaining:
  - Rollback safety requirements
  - Checkpoint validation
  - Destination availability checks
- Function docstrings:
  - `rollback_from_checkpoint()` - Full Args/Returns/Raises documentation

**Estimated Effort**: 1 hour

---

### 2.3 Exporter Module

**File**: `nodupe/exporter.py`

**Status**: ❌ No module docstring, incomplete function docstrings

**Required Documentation**:
- Module docstring explaining:
  - `nodupe_meta_v1` schema compliance
  - Idempotent writes (skip unchanged meta.json)
  - Read-only filesystem detection
- Function docstrings:
  - `_iso_now()` - ISO 8601 timestamp generation
  - `write_folder_meta()` - Full parameter documentation

**Estimated Effort**: 1 hour

---

### 2.4 Categorizer Module

**File**: `nodupe/categorizer.py`

**Status**: ❌ No module docstring, no function docstrings

**Required Documentation**:
- Module docstring explaining:
  - Category taxonomy (image, video, text, archive, etc.)
  - MIME type to category mapping
  - Subtype and topic inference
- Function docstrings:
  - `categorize_file()` - Full parameter and return value documentation

**Estimated Effort**: 45 minutes

---

### 2.5 Validator Module

**File**: `nodupe/validator.py`

**Status**: ❌ No module docstring, incomplete function docstrings

**Required Documentation**:
- Module docstring explaining:
  - JSON Schema validation integration
  - Fallback validation when jsonschema unavailable
  - `nodupe_meta_v1` spec enforcement
- Function docstrings:
  - `get_schema()` - Schema retrieval
  - `validate_meta_dict()` - Complete Args/Raises documentation

**Estimated Effort**: 1 hour

---

## Priority 3: Utilities (MEDIUM)

### 3.1 Hashing Utilities

**File**: `nodupe/utils/hashing.py`

**Status**: ❌ No module docstring, incomplete function docstrings

**Required Documentation**:
- Module docstring with:
  - Supported hash algorithms
  - Performance characteristics
  - Incremental hashing strategy
- Function docstrings:
  - `validate_hash_algo()` - Algorithm validation
  - `hash_file()` - Complete Args/Returns/Raises documentation

**Estimated Effort**: 45 minutes

---

### 3.2 Filesystem Utilities

**File**: `nodupe/utils/filesystem.py`

**Status**: ❌ No module docstring, no function docstrings

**Required Documentation**:
- Module docstring explaining utility purpose
- Function docstrings:
  - `should_skip()` - Ignore pattern matching
  - `detect_context()` - Archive/temp folder detection
  - `get_mime_safe()` - MIME detection with overrides
  - `get_permissions()` - ACL/permission capture

**Estimated Effort**: 1 hour

---

### 3.3 Media Utilities

**File**: `nodupe/utils/media.py`

**Status**: ❌ No module docstring, no function docstrings

**Required Documentation**:
- Module docstring explaining:
  - Video frame extraction
  - Image embedding computation
  - Supported media formats
- All function docstrings with full parameter documentation

**Estimated Effort**: 1 hour

---

### 3.4 FFmpeg Progress Helper

**File**: `nodupe/utils/ffmpeg_progress.py`

**Status**: ❌ No module docstring, no function docstrings

**Required Documentation**:
- Module docstring explaining:
  - Progress mode detection (auto/quiet/interactive)
  - Environment variable (NO_DUPE_PROGRESS) handling
  - FFmpeg output parsing
- All function and class docstrings

**Estimated Effort**: 1 hour

---

## Priority 4: Command Modules (MEDIUM)

All command modules lack docstrings. Each should have:
- Module docstring explaining command purpose
- Function docstrings with Args/Returns documentation

**Files** (9 modules):
- `nodupe/commands/init.py`
- `nodupe/commands/scan.py`
- `nodupe/commands/plan.py`
- `nodupe/commands/apply.py`
- `nodupe/commands/rollback.py`
- `nodupe/commands/verify.py`
- `nodupe/commands/mount.py`
- `nodupe/commands/archive.py`
- `nodupe/commands/similarity.py`

**Estimated Effort**: 4-5 hours (30 minutes per module)

---

## Priority 5: Supporting Modules (LOW)

### 5.1 Logger Module

**File**: `nodupe/logger.py`

**Status**: ❌ No module docstring, no class/method docstrings

**Required Documentation**:
- Module docstring explaining JSONL logging format
- JsonlLogger class with rotation/cleanup documentation
- All method docstrings

**Estimated Effort**: 45 minutes

---

### 5.2 Metrics Module

**File**: `nodupe/metrics.py`

**Status**: ❌ No module docstring, no class/method docstrings

**Required Documentation**:
- Module docstring explaining metrics collection
- Metrics class with JSON format documentation
- All method docstrings

**Estimated Effort**: 30 minutes

---

### 5.3 Mount Module

**File**: `nodupe/mount.py`

**Status**: ❌ Minimal docstring, no method docstrings

**Required Documentation**:
- Enhanced module docstring with FUSE filesystem structure
- NoDupeFS class method docstrings (getattr, readdir, open, read, release)

**Estimated Effort**: 1 hour

---

### 5.4 Plugin Manager

**File**: `nodupe/plugins/manager.py`

**Status**: ❌ Basic class docstring, no method docstrings

**Required Documentation**:
- Enhanced module docstring explaining plugin architecture
- Method docstrings with Args/Returns (register, emit, load_plugins)

**Estimated Effort**: 45 minutes

---

### 5.5 AI Backend Modules

**Files**:
- `nodupe/ai/backends/base.py`
- `nodupe/ai/backends/cpu.py`
- `nodupe/ai/backends/onnx.py`

**Status**: Vary by file, generally underdocumented

**Required Documentation**:
- Module docstrings explaining backend architecture
- Class/method docstrings with complete parameters
- Usage examples

**Estimated Effort**: 2 hours total

---

### 5.6 Similarity Backend Modules

**Files**:
- `nodupe/similarity/backends/bruteforce_backend.py`
- `nodupe/similarity/backends/faiss_backend.py`
- `nodupe/similarity/cli.py`
- `nodupe/similarity/index.py`

**Status**: Some have docstrings, but classes/methods underdocumented

**Required Documentation**:
- Complete class docstrings for BruteForceIndex, FaissIndex
- Method docstrings with Args/Returns
- Index persistence format documentation

**Estimated Effort**: 2 hours total

---

## Documentation Standards

All documentation should follow these standards:

### Module Docstrings

```python
"""Brief one-line summary.

Detailed description spanning multiple paragraphs if needed. Explain
the module's purpose, key concepts, and architecture.

Key Features:
    - Feature 1
    - Feature 2

Dependencies:
    - Required dependency
    - Optional dependency (optional, falls back to X)

Example:
    >>> from nodupe import module
    >>> result = module.function()
"""
```

### Function/Method Docstrings

```python
def function(param1: str, param2: int = 0) -> bool:
    """Brief one-line summary.

    Detailed explanation of what the function does, including any
    important behavior, side effects, or usage notes.

    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2 (default: 0)

    Returns:
        Description of return value

    Raises:
        ExceptionType: When and why this exception is raised

    Example:
        >>> result = function("test", 5)
        True
    """
```

### Class Docstrings

```python
class ClassName:
    """Brief one-line summary.

    Detailed description of the class purpose, usage patterns,
    and important attributes.

    Attributes:
        attr1: Description of attribute 1
        attr2: Description of attribute 2

    Example:
        >>> obj = ClassName()
        >>> obj.method()
    """
```

---

## Estimated Total Effort

| Priority | Modules | Estimated Hours |
|----------|---------|-----------------|
| Priority 1 (Critical) | 4 | 8-11 hours |
| Priority 2 (Core) | 5 | 5-6 hours |
| Priority 3 (Utilities) | 4 | 4 hours |
| Priority 4 (Commands) | 9 | 4-5 hours |
| Priority 5 (Supporting) | 10+ | 7-8 hours |
| **TOTAL** | **32+** | **28-34 hours** |

---

## Next Steps

1. **Phase 2**: Document Priority 1 modules (db, scanner, applier, archiver)
2. **Phase 3**: Document Priority 2 modules (planner, rollback, exporter, categorizer, validator)
3. **Phase 4**: Document Priority 3 utilities
4. **Phase 5**: Document command modules
5. **Phase 6**: Document supporting modules
6. **Phase 7**: Final review and consistency check

---

## Completed Work

### Phase 1 (Completed 2025-12-03)

#### Module Documentation

- ✅ **nodupe/cli.py** - Comprehensive module docstring added
  - CLI architecture and plugin system explained
  - All available commands documented
  - Exit codes documented
  - Key features outlined
- ✅ **nodupe/config.py** - Complete module documentation added
  - All 7 configuration presets documented
  - Configuration keys explained with types
  - Dependencies and graceful degradation documented
  - Usage examples added
  - Function docstrings with Args/Returns sections
  - PEP 8 line length compliance

#### External Documentation Updates

- ✅ **docs/BEGINNERS_GUIDE.md**
  - Updated all commands from `python -m nodupe.cli` to `nodupe`
  - Fixed Python version requirement (3.8+ → 3.9+)
  - 5 command examples updated
- ✅ **docs/SIMILARITY.md**
  - Updated command examples to use `nodupe` command
- ✅ **docs/AI_BACKEND.md**
  - Removed duplicate lines
  - Fixed markdown formatting (blank lines around headings/lists)
  - Fixed malformed code blocks
- ✅ **docs/CHANGELOG.md**
  - Added comprehensive Phase 1 entry
  - Documented all changes in this phase

#### Project Documentation

- ✅ Conducted full codebase documentation audit (50+ modules)
- ✅ Created this roadmap document (DOCUMENTATION_TODO.md)
- ✅ Identified documentation gaps (38 modules / 76% lacking docstrings)
- ✅ Prioritized work into 5 tiers
- ✅ Estimated effort for remaining work (28-34 hours)

#### Repository Maintenance

- ✅ Removed e621_downloader submodule
- ✅ All changes committed and pushed to origin/main
- ✅ CI/CD pipeline updated with submodule handling

---

## Maintenance

This document should be updated as documentation work progresses. Mark items as
complete (✅) and update the progress summary and completion percentage.

Last Updated: 2025-12-03
