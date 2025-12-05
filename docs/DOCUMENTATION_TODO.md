# NoDupeLabs Documentation Roadmap

This document outlines the comprehensive documentation work required to bring all
modules in the NoDupeLabs project up to professional standards.

## Overview

A thorough audit of the codebase (conducted 2025-12-03) revealed that **76% of
modules lack module-level docstrings**. This roadmap prioritizes documentation
work based on module criticality and usage frequency.

## Progress Summary

- **Total modules reviewed**: 50+
- **Modules fully documented**: 15 (cli.py, config.py, scanner.py, db.py, applier.py, archiver.py, planner.py, rollback.py, exporter.py, categorizer.py, validator.py, utils/hashing.py, utils/filesystem.py, utils/media.py, utils/ffmpeg_progress.py)
- **External docs updated**: 5 (BEGINNERS_GUIDE.md, SIMILARITY.md, AI_BACKEND.md, CHANGELOG.md, docs/CHANGELOG.md entry)
- **Repository releases**: v0.1.1 created and published (includes full changelog as release notes)
- **Modules remaining**: ~35
- **Completion**: ~30% (Priority 1, 2, & 3 completed)
- **Last updated**: 2025-12-03

## Recent work & status (summary)

- **Priority 1, 2, & 3 Documentation (COMPLETED 2025-12-03)**:
  - ✅ **Priority 1 (Critical Infrastructure)**: cli.py, config.py, scanner.py, db.py,
    applier.py, archiver.py - All modules fully documented with comprehensive module
    docstrings and function/method docstrings including Args/Returns/Raises/Example
    sections.
  - ✅ **Priority 2 (Core Functionality)**: planner.py, rollback.py, exporter.py,
    categorizer.py, validator.py - All modules fully documented following the same
    comprehensive standards.
  - ✅ **Priority 3 (Utilities)**: utils/hashing.py, utils/filesystem.py, utils/media.py,
    utils/ffmpeg_progress.py - All utility modules fully documented with detailed
    module docstrings, function docstrings, and comprehensive examples.
  - 15 of 50+ modules now have complete documentation (30% completion)
  - All docstrings follow PEP 8 line length limits and include usage examples

- **Changelog & release**: Updated `docs/CHANGELOG.md` with detailed entries covering
  CI and documentation efforts, then created and published release tag `v0.1.1` with
  the full changelog as release body.

- **CI & vendoring hardening**: Disabled submodule handling in CI checkout and set
  `fetch-depth: 0`. Added/updated vendoring helpers and a `validate-vendored-install`
  CI job that performs offline installs of vendored wheels and smoke-import checks.

- **Scanner & tests**: Implemented ETA / STALL progress messaging, hard `max_idle_time`
  to prevent scanner hangs, and added unit tests exercising timing and progress behavior.

- **Lint fixes**: Resolved flake8 E501 violations by wrapping long docstring lines.

- **Docs site**: Added a lightweight Sphinx site under `docs/sphinx/` and CI job (`docs-build`) that builds it to verify API docs render from docstrings.
- **Doc sanity checks**: Added `scripts/check_docstrings_and_size.py` and a CI `doc-sanity` job to block PRs when public APIs lack docstrings or a module becomes too large.
- **Stress tests**: Added concurrent stress tests for DB and plugin dispatch under `tests/test_concurrency_stress.py` and hooked them into the `slow-tests` CI job (marked as `slow`).

Next steps:

- Priority 4: Commands (9 command modules)
- Priority 5: Supporting modules (10+ modules)

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

**Status**: ✅ Module and function docstrings added

**Notes**: Module-level docstring added explaining three-phase commit
pattern, safety guarantees, and checkpoint format. Complete function
docstring added to `apply_moves()` with Args/Returns/Raises sections
and usage examples. Completed 2025-12-03.

---

### 1.4 Archiver Module

**File**: `nodupe/archiver.py`

**Status**: ✅ Module, class, and method docstrings added

**Notes**: Comprehensive module docstring added covering all supported
formats (zip, tar, 7z, rar), optional dependencies, security features,
and usage examples. ArchiveHandler class fully documented with all
public and private method docstrings including Args/Returns/Raises.
Completed 2025-12-03.

---

## Priority 2: Core Functionality (HIGH)

These modules implement primary user-facing features.

### 2.1 Planner Module

**File**: `nodupe/planner.py`

**Status**: ✅ Module and function docstrings added

**Notes**: Module docstring added covering deduplication strategy,
CSV plan format, and conflict resolution. Complete function docstrings
added for `ensure_unique()` and `write_plan_csv()` with Args/Returns/
Example sections. Completed 2025-12-03.

---

### 2.2 Rollback Module

**File**: `nodupe/rollback.py`

**Status**: ✅ Module and function docstrings added

**Notes**: Module docstring added explaining LIFO rollback strategy,
safety requirements, and validation steps. Complete function docstring
added for `rollback_from_checkpoint()` with Args/Returns/Example
sections. Completed 2025-12-03.

---

### 2.3 Exporter Module

**File**: `nodupe/exporter.py`

**Status**: ✅ Module and function docstrings added

**Notes**: Module docstring added covering nodupe_meta_v1 schema,
idempotent write behavior, safety features (read-only detection,
atomic writes, disk full handling). Complete function docstrings
added for `_iso_now()` and `write_folder_meta()` with Args/Returns/
Raises/Example sections. Completed 2025-12-03.

---

### 2.4 Categorizer Module

**File**: `nodupe/categorizer.py`

**Status**: ✅ Module and function docstrings added

**Notes**: Module docstring added explaining category taxonomy
(image, video, text, archive, other), MIME type mapping, and topic
inference. Complete function docstring added for `categorize_file()`
with Args/Returns/Example sections covering all supported categories.
Completed 2025-12-03.

---

### 2.5 Validator Module

**File**: `nodupe/validator.py`

**Status**: ✅ Module and function docstrings added

**Notes**: Module docstring added covering JSON Schema validation,
fallback structural checks, and validation strategy. Complete function
docstrings added for `get_schema()` and `validate_meta_dict()` with
Args/Returns/Raises/Example sections. Includes documentation of
two-phase validation approach. Completed 2025-12-03.

---

## Priority 3: Utilities (MEDIUM)

### 3.1 Hashing Utilities

**File**: `nodupe/utils/hashing.py`

**Status**: ✅ Module and function docstrings added

**Notes**: Module docstring added covering supported algorithms (SHA-512,
SHA-256, BLAKE2b, SHA-1, MD5), performance characteristics, and incremental
hashing strategy. Complete function docstrings added for `validate_hash_algo()`
and `hash_file()` with Args/Returns/Raises/Example sections. Includes performance
notes comparing algorithm speeds. Completed 2025-12-03.

---

### 3.2 Filesystem Utilities

**File**: `nodupe/utils/filesystem.py`

**Status**: ✅ Module and function docstrings added

**Notes**: Module docstring added explaining modern MIME type support (WebP,
HEIC, AVIF, Matroska), context detection strategy, and permission handling.
Complete function docstrings added for `should_skip()`, `detect_context()`,
`get_mime_safe()`, and `get_permissions()` with Args/Returns/Example sections.
Completed 2025-12-03.

---

### 3.3 Media Utilities

**File**: `nodupe/utils/media.py`

**Status**: ✅ Module and function docstrings added

**Notes**: Module docstring added covering video frame extraction strategy,
FFmpeg integration, frame caching, and metadata sidecar generation. Complete
function docstrings added for `_hash_path()` and `extract_representative_frame()`
with detailed Args/Returns/Raises/Example sections. Includes cache location
and FFmpeg command documentation. Completed 2025-12-03.

---

### 3.4 FFmpeg Progress Helper

**File**: `nodupe/utils/ffmpeg_progress.py`

**Status**: ✅ Module and function docstrings added

**Notes**: Module docstring added explaining progress mode detection (auto/
interactive/quiet), NO_DUPE_PROGRESS environment variable, duration inference,
and timeout handling. Complete function docstrings added for `_parse_time_string()`,
`_parse_ffmpeg_duration_from_cmd()`, and `run_ffmpeg_with_progress()` with
comprehensive Args/Returns/Raises/Example sections. Completed 2025-12-03.

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
