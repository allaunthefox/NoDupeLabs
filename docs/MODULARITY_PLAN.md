# NoDupeLabs Modularity Improvement Plan

**Document Version:** 1.0
**Date:** 2025-12-04
**Status:** DRAFT
**Current Modularity Score:** 7/10
**Target Score:** 9/10

---

## Executive Summary

This document outlines a phased approach to improve the modularity of NoDupeLabs from "Good" (7/10) to "Exemplary" (9/10). The improvements focus on reducing coupling, establishing clear API boundaries, and ensuring that changes to one module don't require changes to others.

**Total Estimated Effort:** 13-18 hours
**Implementation Phases:** 3
**Risk Level:** Low (mostly structural changes, minimal logic changes)

---

## Current State Assessment

### Strengths
- ✅ No circular dependencies (proper DAG)
- ✅ Clean layering (CLI → Commands → Core → Utils)
- ✅ Well-isolated subpackages (similarity/, ai/)
- ✅ 100% docstring coverage
- ✅ 47 modules with clear responsibilities

### Issues Identified
1. **CLI imports all 13 commands directly** → tight coupling
2. **commands/scan.py has 8 imports** → hub module, SRP violation
3. **No public API exports** → internal structure exposed
4. **Missing ai/__init__.py** → opaque backend selection
5. **Mixed concerns in some modules** → reduced testability

---

## Phase 1: Critical - Decouple CLI from Commands

**Priority:** URGENT
**Effort:** 2-3 hours
**Impact:** HIGH
**Risk:** LOW

### Problem

Currently, `cli.py` directly imports all 13 command functions:

```python
# cli.py (CURRENT - BAD)
from .commands.init import cmd_init
from .commands.scan import cmd_scan
from .commands.plan import cmd_plan
from .commands.apply import cmd_apply
from .commands.rollback import cmd_rollback
from .commands.verify import cmd_verify
from .commands.mount import cmd_mount
from .commands.archive import cmd_archive_list, cmd_archive_extract
from .commands.similarity import (
    cmd_similarity_build,
    cmd_similarity_query,
    cmd_similarity_update
)
```

**Impact:** Every time a command is added, removed, or renamed, `cli.py` must be modified.

### Solution: Command Registry Pattern

Create a centralized command registry in `commands/__init__.py`.

#### Implementation Steps

**Step 1.1: Update commands/__init__.py**

```python
# nodupe/commands/__init__.py
"""Command registry for dynamic command discovery.

This module provides a centralized registry of all available commands,
enabling CLI to discover commands without direct imports.
"""

from .init import cmd_init
from .scan import cmd_scan
from .plan import cmd_plan
from .apply import cmd_apply
from .rollback import cmd_rollback
from .verify import cmd_verify
from .mount import cmd_mount
from .archive import cmd_archive_list, cmd_archive_extract
from .similarity import (
    cmd_similarity_build,
    cmd_similarity_query,
    cmd_similarity_update
)

# Command registry - single source of truth
COMMANDS = {
    'init': cmd_init,
    'scan': cmd_scan,
    'plan': cmd_plan,
    'apply': cmd_apply,
    'rollback': cmd_rollback,
    'verify': cmd_verify,
    'mount': cmd_mount,
    'archive-list': cmd_archive_list,
    'archive-extract': cmd_archive_extract,
    'similarity-build': cmd_similarity_build,
    'similarity-query': cmd_similarity_query,
    'similarity-update': cmd_similarity_update,
}

__all__ = [
    'COMMANDS',
    # Still export individual commands for backwards compatibility
    'cmd_init',
    'cmd_scan',
    'cmd_plan',
    'cmd_apply',
    'cmd_rollback',
    'cmd_verify',
    'cmd_mount',
    'cmd_archive_list',
    'cmd_archive_extract',
    'cmd_similarity_build',
    'cmd_similarity_query',
    'cmd_similarity_update',
]
```

**Step 1.2: Update cli.py**

```python
# nodupe/cli.py (SIMPLIFIED)
"""CLI entry point and command dispatcher."""

import sys
from pathlib import Path

from .bootstrap import lint_tree
from .deps import init_deps
from .config import load_config
from .plugins import pm
from .commands import COMMANDS  # ← Single import instead of 13!


def main():
    """Main CLI entry point."""
    args = parse_arguments()

    # ... (setup code unchanged) ...

    # Command dispatch using registry
    command_func = COMMANDS.get(args.command)
    if not command_func:
        print(f"Error: Unknown command '{args.command}'", file=sys.stderr)
        print(f"Available commands: {', '.join(sorted(COMMANDS.keys()))}")
        return 1

    # Execute command
    try:
        return command_func(args, ctx) or 0
    except KeyboardInterrupt:
        print("\n[CLI] Interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"[CLI][ERROR] {e}", file=sys.stderr)
        return 1
```

#### Testing Strategy

1. **Verify all commands still work:**
   ```bash
   nodupe init --help
   nodupe scan --help
   nodupe plan --help
   # ... test all 12 commands
   ```

2. **Run existing test suite:**
   ```bash
   pytest tests/test_cli_requirements.py -v
   pytest tests/test_commands_structure.py -v
   ```

3. **Test error handling:**
   ```bash
   nodupe invalid-command  # Should show available commands
   ```

#### Success Criteria

- ✅ All 12 commands work as before
- ✅ CLI module no longer imports individual commands
- ✅ Adding new commands only requires editing `commands/__init__.py`
- ✅ All tests pass

#### Benefits

- **Loose Coupling:** CLI doesn't depend on individual command modules
- **Easy Extension:** Add commands by updating registry only
- **Plugin System Ready:** Can extend registry from external plugins
- **Better Error Messages:** Can list available commands from registry

---

## Phase 2: Critical - Establish Public API Boundaries

**Priority:** URGENT
**Effort:** 2-3 hours
**Impact:** HIGH
**Risk:** LOW

### Problem

Users must import from internal modules with no clear API contract:

```python
# Current usage (BAD - internal imports)
from nodupe.db import DB
from nodupe.scanner import threaded_hash
from nodupe.similarity.index import make_index
```

No `__all__` exports mean:
- No clear distinction between public and private
- Users depend on internal structure
- Refactoring breaks user code
- IDE autocomplete shows everything

### Solution: Define Public API Exports

Create clear API boundaries with `__all__` exports.

#### Implementation Steps

**Step 2.1: Create nodupe/__init__.py Public API**

```python
# nodupe/__init__.py
"""NoDupeLabs - Context-aware file deduplication system.

Public API for programmatic usage.

Example:
    >>> from nodupe import DB, threaded_hash, make_index
    >>>
    >>> # Scan files
    >>> for file_info in threaded_hash(['/data'], [], collect=True):
    ...     print(file_info)
    >>>
    >>> # Use database
    >>> db = DB('output/index.db')
    >>> files = db.get_all()
    >>>
    >>> # Build similarity index
    >>> index = make_index(dim=16)
"""

# Core database interface
from .db import DB

# Scanning functions
from .scanner import iter_files, threaded_hash, process_file

# Similarity search
from .similarity import (
    make_index,
    save_index_to_file,
    load_index_from_file,
    update_index_from_db
)

# Configuration
from .config import load_config, ensure_config, get_available_presets

# File categorization
from .categorizer import categorize_file

# Metadata export
from .exporter import write_folder_meta

# Validation
from .validator import validate_meta_dict, get_schema

# Version information
__version__ = "0.1.0"
__author__ = "Allaun"
__license__ = "Apache-2.0"

__all__ = [
    # Database
    'DB',

    # Scanning
    'iter_files',
    'threaded_hash',
    'process_file',

    # Similarity
    'make_index',
    'save_index_to_file',
    'load_index_from_file',
    'update_index_from_db',

    # Configuration
    'load_config',
    'ensure_config',
    'get_available_presets',

    # Classification
    'categorize_file',

    # Export
    'write_folder_meta',

    # Validation
    'validate_meta_dict',
    'get_schema',

    # Metadata
    '__version__',
    '__author__',
    '__license__',
]
```

**Step 2.2: Create ai/__init__.py**

```python
# nodupe/ai/__init__.py
"""AI backend abstraction for embeddings and classification.

Provides pluggable backends for computing image/video embeddings.
Automatically selects best available backend (ONNX Runtime or CPU fallback).

Example:
    >>> from nodupe.ai import choose_backend, list_backends
    >>>
    >>> # List available backends
    >>> backends = list_backends()
    >>> print(backends)  # ['onnx', 'cpu']
    >>>
    >>> # Get best backend
    >>> backend = choose_backend()
    >>> embedding = backend.compute_embedding(image_path)
"""

from .backends import choose_backend, list_backends
from .backends.base import BaseBackend

__all__ = [
    'choose_backend',
    'list_backends',
    'BaseBackend',
]
```

**Step 2.3: Update similarity/__init__.py**

```python
# nodupe/similarity/__init__.py (ENHANCED)
"""Similarity search subsystem with pluggable backends.

Supports multiple index formats (NPZ, JSON, JSONL) and backends
(FAISS, brute-force) for finding near-duplicate files based on
perceptual embeddings.

Example:
    >>> from nodupe.similarity import make_index, save_index_to_file
    >>>
    >>> # Create index
    >>> index = make_index(dim=16, backend='bruteforce')
    >>>
    >>> # Add vectors
    >>> index.add(['file1', 'file2'], [[0.1, 0.2, ...], [0.3, 0.4, ...]])
    >>>
    >>> # Search
    >>> ids, distances = index.search([[0.15, 0.25, ...]], k=5)
    >>>
    >>> # Save to disk
    >>> save_index_to_file(index, 'index.npz', format='npz')
"""

from .index import (
    make_index,
    save_index_to_file,
    load_index_from_file,
    update_index_file_from_vectors,
    update_index_from_db
)
from .backends import list_backends, default_backend_name, get_factory

__all__ = [
    # Index operations
    'make_index',
    'save_index_to_file',
    'load_index_from_file',
    'update_index_file_from_vectors',
    'update_index_from_db',

    # Backend discovery
    'list_backends',
    'default_backend_name',
    'get_factory',
]
```

**Step 2.4: Update utils/__init__.py**

```python
# nodupe/utils/__init__.py
"""Utility functions for hashing, filesystem operations, and media processing.

Low-level utilities with no internal dependencies.
"""

from .hashing import hash_file, validate_hash_algo
from .filesystem import should_skip, detect_context, get_mime_safe, get_permissions
from .media import extract_representative_frame

__all__ = [
    # Hashing
    'hash_file',
    'validate_hash_algo',

    # Filesystem
    'should_skip',
    'detect_context',
    'get_mime_safe',
    'get_permissions',

    # Media
    'extract_representative_frame',
]
```

#### Testing Strategy

1. **Test public API imports:**
   ```python
   # Test in Python REPL
   from nodupe import DB, threaded_hash, make_index
   from nodupe.ai import choose_backend
   from nodupe.similarity import list_backends

   # Should work without errors
   ```

2. **Verify __all__ completeness:**
   ```bash
   python -c "import nodupe; print(nodupe.__all__)"
   python -c "import nodupe.ai; print(nodupe.ai.__all__)"
   ```

3. **Check IDE autocomplete:**
   - Type `from nodupe import ` in IDE
   - Should show only public API exports

4. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

#### Success Criteria

- ✅ All public APIs importable from top-level packages
- ✅ `__all__` defined in all package `__init__.py` files
- ✅ IDE autocomplete shows only public APIs
- ✅ All existing tests pass
- ✅ Documentation updated with new import patterns

#### Benefits

- **Clear API Contract:** Users know what's stable vs internal
- **Better IDE Support:** Autocomplete shows only relevant functions
- **Refactoring Safety:** Can change internals without breaking users
- **Professional Library:** Standard Python packaging practice

---

## Phase 3: Important - Extract EmbeddingProcessor

**Priority:** HIGH (but can wait until Phase 1 & 2 complete)
**Effort:** 4-6 hours
**Impact:** MEDIUM-HIGH
**Risk:** MEDIUM (requires refactoring scan.py logic)

### Problem

`commands/scan.py` has too many responsibilities (SRP violation):

1. Orchestrate file scanning
2. Compute AI embeddings
3. Batch database operations
4. Export folder metadata
5. Emit plugin events
6. Track metrics

**Current imports (8 total):**
```python
from ..db import DB
from ..scanner import threaded_hash
from ..ai.backends import choose_backend
from ..exporter import write_folder_meta
from ..logger import JsonlLogger
from ..metrics import Metrics
from ..plugins import pm
from ..utils.hashing import validate_hash_algo
```

### Solution: Extract EmbeddingProcessor Class

Create dedicated `nodupe/embedding_processor.py` module to handle AI embedding orchestration.

#### Implementation Steps

**Step 3.1: Create embedding_processor.py**

```python
# nodupe/embedding_processor.py (NEW FILE)
"""AI embedding computation orchestration.

This module orchestrates the computation of AI embeddings for files,
separating this concern from the main scanning workflow. Supports
batching, error handling, and progress tracking.

Example:
    >>> from nodupe.embedding_processor import EmbeddingProcessor
    >>> from nodupe.ai import choose_backend
    >>>
    >>> backend = choose_backend()
    >>> processor = EmbeddingProcessor(backend, batch_size=100)
    >>>
    >>> embeddings = processor.process_files(file_records, root_path)
    >>> for file_id, embedding in embeddings:
    ...     print(f"{file_id}: {embedding.shape}")
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .ai.backends.base import BaseBackend


class EmbeddingProcessor:
    """Orchestrates AI embedding computation for file batches.

    Separates embedding logic from scanning workflow, enabling:
    - Independent testing of embedding computation
    - Reuse across different commands
    - Better error handling and retry logic
    - Progress tracking for embedding operations

    Args:
        backend: AI backend instance (ONNX, CPU, etc.)
        batch_size: Number of files to process before yielding
        supported_mimes: MIME types to compute embeddings for
    """

    DEFAULT_SUPPORTED_MIMES = ('image/', 'video/')

    def __init__(
        self,
        backend: BaseBackend,
        batch_size: int = 100,
        supported_mimes: Optional[Tuple[str, ...]] = None
    ):
        """Initialize embedding processor."""
        self.backend = backend
        self.batch_size = batch_size
        self.supported_mimes = supported_mimes or self.DEFAULT_SUPPORTED_MIMES
        self.stats = {
            'processed': 0,
            'skipped': 0,
            'errors': 0
        }

    def should_process(self, mime: str) -> bool:
        """Check if file MIME type should have embedding computed.

        Args:
            mime: File MIME type (e.g., 'image/jpeg', 'video/mp4')

        Returns:
            True if embedding should be computed
        """
        return any(mime.startswith(prefix) for prefix in self.supported_mimes)

    def process_files(
        self,
        file_records: List[Dict[str, Any]],
        root_path: Path
    ) -> List[Tuple[str, Any]]:
        """Process files and compute embeddings.

        Args:
            file_records: List of file metadata dicts with keys:
                - path: File path (str)
                - mime: MIME type (str)
                - size: File size in bytes (int)
            root_path: Root directory for relative paths

        Returns:
            List of (file_path, embedding) tuples

        Example:
            >>> records = [
            ...     {'path': '/data/photo.jpg', 'mime': 'image/jpeg', 'size': 1024},
            ...     {'path': '/data/doc.txt', 'mime': 'text/plain', 'size': 512}
            ... ]
            >>> embeddings = processor.process_files(records, Path('/data'))
            >>> len(embeddings)  # Only image processed
            1
        """
        embeddings = []

        for record in file_records:
            # Skip files that shouldn't be processed
            if not self.should_process(record.get('mime', '')):
                self.stats['skipped'] += 1
                continue

            # Compute embedding with error handling
            try:
                file_path = Path(record['path'])
                embedding = self._compute_embedding(file_path)

                if embedding is not None:
                    embeddings.append((str(file_path), embedding))
                    self.stats['processed'] += 1
                else:
                    self.stats['skipped'] += 1

            except Exception as e:
                print(f"[embedding] Failed for {record['path']}: {e}")
                self.stats['errors'] += 1

        return embeddings

    def _compute_embedding(self, file_path: Path) -> Optional[Any]:
        """Compute embedding for a single file.

        Args:
            file_path: Path to file

        Returns:
            Embedding vector or None if computation failed
        """
        if not file_path.exists():
            return None

        try:
            return self.backend.compute_embedding(file_path)
        except Exception:
            # Let caller handle logging
            raise

    def get_statistics(self) -> Dict[str, int]:
        """Get processing statistics.

        Returns:
            Dict with keys: processed, skipped, errors
        """
        return self.stats.copy()

    def reset_statistics(self):
        """Reset processing statistics."""
        self.stats = {
            'processed': 0,
            'skipped': 0,
            'errors': 0
        }
```

**Step 3.2: Refactor commands/scan.py**

```python
# nodupe/commands/scan.py (REFACTORED)
"""Scan command implementation."""

from pathlib import Path
from typing import Dict, Any

from ..db import DB
from ..scanner import threaded_hash
from ..ai.backends import choose_backend
from ..embedding_processor import EmbeddingProcessor  # ← NEW
from ..exporter import write_folder_meta
from ..logger import JsonlLogger
from ..metrics import Metrics
from ..plugins import pm
from ..utils.hashing import validate_hash_algo


def cmd_scan(args, ctx) -> int:
    """Execute scan command."""
    # ... (setup code unchanged) ...

    # Initialize embedding processor if AI enabled
    embedding_processor = None
    if ctx['config'].get('ai', {}).get('enabled', False):
        try:
            backend = choose_backend()
            embedding_processor = EmbeddingProcessor(
                backend,
                batch_size=ctx['config'].get('ai', {}).get('batch_size', 100)
            )
            print(f"[scan] AI backend: {backend.__class__.__name__}")
        except Exception as e:
            print(f"[scan][WARN] AI backend unavailable: {e}")
            embedding_processor = None

    # Scan files
    file_records = threaded_hash(
        roots=args.paths,
        ignore=ctx['config'].get('ignore_patterns', []),
        workers=ctx['config'].get('parallelism', 0),
        hash_algo=ctx['config'].get('hash_algo', 'sha512'),
        collect=True
    )

    # Store files in database
    db = DB(ctx['db_path'])
    db.upsert_files(file_records)

    # Compute embeddings (now cleanly separated!)
    if embedding_processor:
        embeddings = embedding_processor.process_files(
            file_records,
            Path(args.paths[0])
        )
        db.upsert_embeddings(embeddings)

        # Log statistics
        stats = embedding_processor.get_statistics()
        print(f"[scan] Embeddings: {stats['processed']} processed, "
              f"{stats['skipped']} skipped, {stats['errors']} errors")

    # Export metadata
    for folder, records in group_by_folder(file_records):
        write_folder_meta(folder, records, Path(args.paths[0]))

    # ... (rest unchanged) ...

    return 0
```

**Step 3.3: Write tests**

```python
# tests/test_embedding_processor.py (NEW FILE)
"""Tests for EmbeddingProcessor."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from nodupe.embedding_processor import EmbeddingProcessor


class TestEmbeddingProcessor:
    """Test embedding processor functionality."""

    def test_should_process_image(self):
        """Test that images are processed."""
        backend = Mock()
        processor = EmbeddingProcessor(backend)

        assert processor.should_process('image/jpeg')
        assert processor.should_process('image/png')
        assert processor.should_process('video/mp4')

    def test_should_not_process_text(self):
        """Test that text files are skipped."""
        backend = Mock()
        processor = EmbeddingProcessor(backend)

        assert not processor.should_process('text/plain')
        assert not processor.should_process('application/pdf')

    def test_process_files_success(self, tmp_path):
        """Test successful embedding processing."""
        # Create mock backend
        backend = Mock()
        backend.compute_embedding.return_value = [0.1, 0.2, 0.3]

        processor = EmbeddingProcessor(backend)

        # Create test image
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"fake image")

        records = [
            {'path': str(test_image), 'mime': 'image/jpeg', 'size': 1024}
        ]

        embeddings = processor.process_files(records, tmp_path)

        assert len(embeddings) == 1
        assert embeddings[0][0] == str(test_image)
        assert embeddings[0][1] == [0.1, 0.2, 0.3]

    def test_statistics_tracking(self):
        """Test that statistics are tracked correctly."""
        backend = Mock()
        backend.compute_embedding.return_value = [0.1, 0.2]

        processor = EmbeddingProcessor(backend)

        records = [
            {'path': '/fake.jpg', 'mime': 'image/jpeg', 'size': 1024},
            {'path': '/fake.txt', 'mime': 'text/plain', 'size': 512},
        ]

        # Process (will error on non-existent files, but stats still tracked)
        try:
            processor.process_files(records, Path('/'))
        except:
            pass

        stats = processor.get_statistics()
        assert stats['skipped'] >= 1  # Text file skipped
```

#### Testing Strategy

1. **Unit test embedding_processor.py:**
   ```bash
   pytest tests/test_embedding_processor.py -v
   ```

2. **Integration test scan command:**
   ```bash
   pytest tests/test_commands_structure.py::test_cmd_scan -v
   ```

3. **Manual test:**
   ```bash
   nodupe scan /test/data --dry-run
   ```

4. **Verify import count reduced:**
   ```python
   # Should go from 8 to ~6 imports
   grep "^from" nodupe/commands/scan.py | wc -l
   ```

#### Success Criteria

- ✅ `scan.py` imports reduced from 8 to ~6
- ✅ Embedding logic isolated in separate module
- ✅ All scan tests pass
- ✅ New embedding processor tests pass
- ✅ Can reuse EmbeddingProcessor in other commands

#### Benefits

- **Single Responsibility:** scan.py focuses on orchestration
- **Testability:** Can test embedding logic independently
- **Reusability:** Can use EmbeddingProcessor in other commands
- **Better Error Handling:** Embedding errors don't crash scan

---

## Phase 4: Documentation - Architecture Guide

**Priority:** MEDIUM
**Effort:** 2-3 hours
**Impact:** MEDIUM
**Risk:** NONE (documentation only)

### Objective

Create comprehensive architecture documentation to help developers understand module boundaries and design decisions.

#### Implementation Steps

**Step 4.1: Create ARCHITECTURE.md**

```markdown
# docs/ARCHITECTURE.md

# NoDupeLabs Architecture

## Overview

NoDupeLabs follows a layered architecture with clear separation of concerns...

## Module Structure

[Detailed module diagram and descriptions]

## Dependency Rules

1. CLI → Commands → Core → Utils (one direction)
2. No circular dependencies
3. Subpackages are isolated

## Design Patterns

- Command Registry (CLI dispatching)
- Factory Pattern (AI backends, similarity backends)
- Three-Phase Commit (applier.py)
- Plugin System (event hooks)

## Adding New Features

[Guidelines for extending each layer]
```

**Step 4.2: Create OPTIONAL_DEPENDENCIES.md**

```markdown
# docs/OPTIONAL_DEPENDENCIES.md

# Optional Dependencies

## AI Backends

NoDupeLabs supports multiple AI backends with graceful fallback...

[Details on ONNX, CPU, etc.]

## Similarity Backends

[Details on FAISS, brute-force]

## Graceful Degradation

[How the system behaves when dependencies are missing]
```

**Step 4.3: Update CHANGELOG.md**

Document modularity improvements in changelog.

#### Success Criteria

- ✅ ARCHITECTURE.md created and comprehensive
- ✅ OPTIONAL_DEPENDENCIES.md explains backend selection
- ✅ CHANGELOG.md updated with modularity improvements
- ✅ README.md links to architecture docs

---

## Phase 5: Optional Enhancements

**Priority:** LOW
**Effort:** 6-8 hours total
**Impact:** MEDIUM
**Risk:** MEDIUM

These are nice-to-have improvements that can be done over time.

### Enhancement 5.1: Extract Categorization Pipeline

Create `nodupe/categorization_pipeline.py` to separate categorization from metadata export.

**Effort:** 3-4 hours
**Benefit:** Cleaner separation of concerns in exporter.py

### Enhancement 5.2: Create Test Doubles

Extract interfaces for DB, Scanner, Backend to enable easier mocking in tests.

**Effort:** 2-3 hours
**Benefit:** Better unit test isolation

### Enhancement 5.3: Add Architecture Decision Records

Document architectural decisions in `docs/adr/` folder.

**Effort:** 1-2 hours
**Benefit:** Historical record of design rationale

---

## Implementation Timeline

### Week 1: Critical Improvements
- **Days 1-2:** Phase 1 - Command Registry (2-3 hours)
- **Days 3-4:** Phase 2 - Public API Boundaries (2-3 hours)
- **Day 5:** Testing and validation

### Week 2: Important Improvements
- **Days 1-3:** Phase 3 - Extract EmbeddingProcessor (4-6 hours)
- **Days 4-5:** Phase 4 - Documentation (2-3 hours)

### Future: Optional Enhancements
- Implement as needed or during refactoring sessions

---

## Risk Assessment

### Low Risk Items
- ✅ Command Registry (only changes dispatch mechanism)
- ✅ Public API Exports (purely additive)
- ✅ Documentation (no code changes)

### Medium Risk Items
- ⚠️ EmbeddingProcessor extraction (requires refactoring scan.py logic)
  - **Mitigation:** Comprehensive test coverage before and after
  - **Rollback:** Easy to revert if issues found

### No Breaking Changes
- All improvements are backwards compatible
- Existing code continues to work
- Only internal structure changes

---

## Testing Strategy

### Before Each Phase
1. Run full test suite and record baseline
2. Document current behavior
3. Create branch for changes

### During Implementation
1. Write tests for new code first (TDD)
2. Run tests frequently
3. Check imports with dependency analysis tools

### After Each Phase
1. Run full test suite
2. Test CLI commands manually
3. Check performance hasn't regressed
4. Verify documentation accuracy
5. Get code review if working with team

---

## Success Metrics

### Quantitative Metrics

| Metric | Before | After Phase 1 | After Phase 2 | After Phase 3 | Target |
|--------|--------|---------------|---------------|---------------|--------|
| CLI Imports | 13 | 1 | 1 | 1 | 1 |
| scan.py Imports | 8 | 8 | 8 | 6 | 5-6 |
| Public API Exports | 2/5 | 2/5 | 5/5 | 5/5 | 5/5 |
| Modularity Score | 7/10 | 8/10 | 8.5/10 | 9/10 | 9/10 |

### Qualitative Metrics

- ✅ Can add commands without modifying cli.py
- ✅ Users can import from top-level packages
- ✅ Clear distinction between public and private APIs
- ✅ Embedding logic testable independently
- ✅ Architecture well-documented

---

## Rollback Plan

If any phase causes issues:

1. **Stop implementation immediately**
2. **Git revert to previous working state**
3. **Document what went wrong**
4. **Adjust plan based on lessons learned**
5. **Re-attempt with more testing**

Each phase is independent and can be rolled back without affecting others.

---

## Conclusion

This plan provides a structured approach to improving NoDupeLabs modularity from 7/10 to 9/10. The improvements are:

- **Low risk** (mostly structural changes)
- **High value** (better maintainability)
- **Incremental** (can be done one phase at a time)
- **Backwards compatible** (no breaking changes)

**Recommended Approach:** Implement Phase 1 and Phase 2 first (4-6 hours total) for immediate high-impact improvements. Phase 3 can wait until you have time for deeper refactoring.

**Total Estimated Effort:** 10-15 hours for Phases 1-4
**Expected Outcome:** Modularity score of 9/10, making changes to one module rarely affect others

---

## Appendix: Dependency Graph (Before/After)

### Before (Current)

```
cli.py (13 command imports)
├─ commands/init.py
├─ commands/scan.py (8 imports)
├─ commands/plan.py
├─ commands/apply.py
├─ commands/rollback.py
├─ commands/verify.py
├─ commands/mount.py
├─ commands/archive.py (2 functions)
└─ commands/similarity.py (3 functions)
```

### After (Phase 1 Complete)

```
cli.py (1 import)
└─ commands/__init__.py (COMMANDS registry)
   ├─ commands/init.py
   ├─ commands/scan.py (8 imports)
   ├─ ...
```

### After (Phase 3 Complete)

```
cli.py (1 import)
└─ commands/__init__.py (COMMANDS registry)
   ├─ commands/init.py
   ├─ commands/scan.py (6 imports) ← reduced!
   │  ├─ embedding_processor.py ← new module
   │  └─ ...
```

---

**Document End**
