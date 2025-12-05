# NoDupeLabs Modularity Improvement Plan v2.0
## Path to 10/10 Modularity Score

**Document Version:** 2.0
**Date:** 2025-12-04
**Status:** ACTIVE
**Current Modularity Score:** 7.5/10
**Target Score:** 10/10
**Phases Completed:** 2/6

---

## Executive Summary

This comprehensive plan provides a **complete roadmap** to achieve **world-class modularity** (10/10) for NoDupeLabs. Based on deep analysis of 35 core modules, we've identified **32 distinct issues** across 6 phases.

**Completed:**
- ✅ Phase 1: Command Registry Pattern (2 hours)
- ✅ Phase 2: Public API Boundaries (2 hours)

**Remaining Effort:** 8-10 weeks (320-400 hours) for 10/10 score

**Key Insights:**
1. **Hub Module Problem**: scan.py imports 9 modules (should import ≤3)
2. **God Module Problem**: db.py imported by 10+ modules (should be ≤5)
3. **No Dependency Injection**: All modules use direct imports
4. **Tight I/O Coupling**: Hard to test without filesystem/DB
5. **Global State**: config.py and plugins use module-level singletons

---

## Quick Reference - Phases Overview

| Phase | Priority | Effort | Score Gain | Status |
|-------|----------|--------|------------|--------|
| Phase 1 | URGENT | 2 hrs | +0.2 | ✅ COMPLETE |
| Phase 2 | URGENT | 2 hrs | +0.3 | ✅ COMPLETE |
| Phase 3 | CRITICAL | 3-4 weeks | +1.0 | 🔴 TODO |
| Phase 4 | HIGH | 2-3 weeks | +0.5 | 🔴 TODO |
| Phase 5 | MEDIUM | 2 weeks | +0.5 | 🔴 TODO |
| Phase 6 | POLISH | 1 week | +0.2 | 🔴 TODO |

**Current Score:** 7.5/10
**After Phase 3:** 8.5/10
**After Phase 4:** 9.0/10
**After Phase 5:** 9.5/10
**After Phase 6:** 10.0/10

---

## Phase 1: Command Registry Pattern ✅ COMPLETE

**Status:** ✅ Completed 2025-12-04
**Commit:** `3718f40`
**Score:** 7.0 → 7.2

### What Was Done
- Created COMMANDS registry in `nodupe/commands/__init__.py`
- Replaced 13 direct command imports in CLI with registry lookup
- CLI now uses `COMMANDS[name]` pattern
- Added `__all__` exports to commands package

### Benefits Achieved
- Reduced CLI coupling to commands
- Easier to add new commands
- Cleaner separation of concerns

---

## Phase 2: Public API Boundaries ✅ COMPLETE

**Status:** ✅ Completed 2025-12-04
**Commit:** `3718f40`
**Score:** 7.2 → 7.5

### What Was Done
- Added `__all__` exports to 5 key packages:
  - `nodupe/__init__.py`: Main package API
  - `nodupe/utils/__init__.py`: Utility functions
  - `nodupe/ai/__init__.py`: AI subsystem (NEW)
  - `nodupe/ai/backends/__init__.py`: Backend selection
  - `nodupe/commands/__init__.py`: Command registry

### Benefits Achieved
- Clear API contracts for all packages
- Better encapsulation
- Improved IDE autocomplete
- Explicit public interfaces

---

## Phase 3: Critical Refactoring (Target 8.5/10) 🔴 TODO

**Priority:** CRITICAL
**Effort:** 3-4 weeks (120-160 hours)
**Impact:** Massive reduction in coupling, enables testing
**Risk:** MEDIUM (requires careful refactoring)

### Overview

Phase 3 addresses the 5 **most critical** modularity violations that prevent the codebase from being "excellent":

1. Hub module (scan.py with 9 imports)
2. God module (db.py imported by 10+)
3. Global config state
4. Hidden AI dependencies
5. God function (scanner.py's threaded_hash)

---

### Task 3.1: Extract ScanOrchestrator (Critical Priority)

**Problem:** `nodupe/commands/scan.py` (474 lines, 9 imports)

Current scan.py is doing **4 different jobs**:
```python
# 1. Validation
def check_scan_requirements(args, cfg):
    # Validates CLI args, checks paths, etc.

# 2. Orchestration
def cmd_scan(args, cfg):
    db = DB(...)           # Creates DB
    logger = JsonlLogger(...)  # Creates logger
    metrics = Metrics(...)     # Creates metrics
    backend = choose_backend() # Creates AI backend
    # ... orchestrates everything

# 3. Execution
    results = threaded_hash(...)  # Runs scan

# 4. Post-processing
    write_folder_meta(...)  # Exports results
```

**Solution:** Split into 4 focused classes

#### Step 3.1.1: Create nodupe/scan/validator.py

```python
# nodupe/scan/validator.py
"""Scan argument validation.

Validates scan command arguments and configuration before execution.
Ensures all preconditions are met (paths exist, DB writable, etc.).
"""
from pathlib import Path
from typing import Dict, List, Tuple


class ScanValidator:
    """Validates scan command preconditions."""

    def validate(
        self,
        roots: List[str],
        db_path: Path,
        log_dir: Path
    ) -> Tuple[bool, List[str]]:
        """Validate scan preconditions.

        Args:
            roots: Root directories to scan
            db_path: Database file path
            log_dir: Log directory path

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # Validate roots exist
        for root in roots:
            p = Path(root)
            if not p.exists():
                errors.append(f"Root path does not exist: {root}")
            if not p.is_dir():
                errors.append(f"Root path is not a directory: {root}")

        # Validate DB path writable
        if db_path.exists() and not os.access(db_path, os.W_OK):
            errors.append(f"Database not writable: {db_path}")

        # Validate log dir writable
        log_dir.mkdir(parents=True, exist_ok=True)
        if not os.access(log_dir, os.W_OK):
            errors.append(f"Log directory not writable: {log_dir}")

        return (len(errors) == 0, errors)
```

#### Step 3.1.2: Create nodupe/scan/orchestrator.py

```python
# nodupe/scan/orchestrator.py
"""Scan workflow orchestration.

Coordinates all subsystems involved in a scan operation:
- Database persistence
- Event logging
- Metrics collection
- File scanning
- Metadata export
- Plugin notifications
"""
from pathlib import Path
from typing import Any, Dict, List

from ..db import DB
from ..logger import JsonlLogger
from ..metrics import Metrics
from ..scanner import threaded_hash
from ..ai.backends import BaseBackend
from ..exporter import write_folder_meta
from ..plugins import pm


class ScanOrchestrator:
    """Orchestrates a complete scan operation.

    This class coordinates all subsystems without directly depending
    on their creation. All dependencies are injected via constructor,
    making the class testable and loosely coupled.
    """

    def __init__(
        self,
        db: DB,
        logger: JsonlLogger,
        metrics: Metrics,
        backend: BaseBackend,
        plugin_manager: Any  # Type: PluginManager
    ):
        """Initialize orchestrator with dependencies.

        Args:
            db: Database for persistence
            logger: Event logger
            metrics: Metrics collector
            backend: AI backend for embeddings
            plugin_manager: Plugin event dispatcher
        """
        self.db = db
        self.logger = logger
        self.metrics = metrics
        self.backend = backend
        self.pm = plugin_manager

    def scan(
        self,
        roots: List[str],
        hash_algo: str,
        workers: int,
        progress_mode: str
    ) -> Dict[str, Any]:
        """Execute complete scan workflow.

        Args:
            roots: Root directories to scan
            hash_algo: Hash algorithm (sha256, sha512, etc.)
            workers: Number of worker threads
            progress_mode: Progress display mode

        Returns:
            Scan results summary
        """
        # Emit scan start event
        self.pm.emit("scan_start", roots=roots)

        # Get known files for incremental scan
        known = self.db.get_known_files()

        # Execute threaded scan
        results, duration, total = threaded_hash(
            roots=roots,
            ignore=[],
            workers=workers,
            hash_algo=hash_algo,
            known_files=known,
            collect=True
        )

        # Persist to database
        self.db.upsert_files(results)

        # Record metrics
        self.metrics.record("scan_files", total)
        self.metrics.record("scan_duration_sec", duration)
        self.metrics.save()

        # Log events
        for record in results:
            self.logger.log({
                "event": "file_scanned",
                "path": record[0],
                "size": record[1],
                "hash": record[3]
            })

        # Generate folder metadata
        for root in roots:
            records = [r for r in results if r[0].startswith(root)]
            write_folder_meta(
                folder_path=Path(root),
                file_records=records,
                backend=self.backend
            )

        # Emit scan complete event
        self.pm.emit("scan_complete",
                     total=total,
                     duration=duration)

        return {
            "files_scanned": total,
            "duration_sec": duration,
            "files_per_sec": total / duration if duration > 0 else 0
        }
```

#### Step 3.1.3: Create nodupe/scan/__init__.py

```python
# nodupe/scan/__init__.py
"""Scan subsystem.

Provides file scanning functionality with validation, orchestration,
and result export.

Public API:
    - ScanValidator: Validates scan preconditions
    - ScanOrchestrator: Coordinates scan workflow
"""

from .validator import ScanValidator
from .orchestrator import ScanOrchestrator

__all__ = ["ScanValidator", "ScanOrchestrator"]
```

#### Step 3.1.4: Refactor nodupe/commands/scan.py (SIMPLIFIED)

```python
# nodupe/commands/scan.py (AFTER - 150 lines, 4 imports)
"""Scan command implementation.

Thin CLI wrapper that creates dependencies and delegates to
ScanOrchestrator for actual work.
"""
from pathlib import Path
from typing import Any, Dict

from ..db import DB
from ..logger import JsonlLogger
from ..metrics import Metrics
from ..ai.backends import choose_backend
from ..plugins import pm
from ..scan import ScanValidator, ScanOrchestrator


def check_scan_requirements(args, cfg: Dict) -> int:
    """Validate scan preconditions.

    Args:
        args: Parsed CLI arguments
        cfg: Configuration dict

    Returns:
        0 if valid, 1 if errors
    """
    validator = ScanValidator()

    is_valid, errors = validator.validate(
        roots=args.root,
        db_path=Path(cfg["db_path"]),
        log_dir=Path(cfg["log_dir"])
    )

    if not is_valid:
        for error in errors:
            print(f"[ERROR] {error}")
        return 1

    return 0


def cmd_scan(args, cfg: Dict) -> int:
    """Execute scan command.

    Args:
        args: Parsed CLI arguments
        cfg: Configuration dict

    Returns:
        Exit code (0 = success)
    """
    # Validate preconditions
    if check_scan_requirements(args, cfg) != 0:
        return 1

    # Create dependencies
    db = DB(Path(cfg["db_path"]))
    logger = JsonlLogger(Path(cfg["log_dir"]))
    metrics = Metrics()
    backend = choose_backend()

    # Create orchestrator (dependency injection!)
    orchestrator = ScanOrchestrator(
        db=db,
        logger=logger,
        metrics=metrics,
        backend=backend,
        plugin_manager=pm
    )

    # Execute scan
    try:
        results = orchestrator.scan(
            roots=args.root,
            hash_algo=cfg["hash_algo"],
            workers=cfg.get("workers", 4),
            progress_mode=args.progress or "auto"
        )

        # Print summary
        print(f"Scanned {results['files_scanned']} files "
              f"in {results['duration_sec']:.1f}s "
              f"({results['files_per_sec']:.0f} files/sec)")

        return 0

    except KeyboardInterrupt:
        print("\n[SCAN] Interrupted by user")
        return 130

    except Exception as e:
        print(f"[SCAN][ERROR] {e}")
        return 1
```

#### Benefits of This Refactor

**Before:**
- 474 lines, 9 imports
- Mixed 4 responsibilities
- Hard to test (needs DB + filesystem + AI)
- Cannot mock any dependencies

**After:**
- `validator.py`: 60 lines, 0 external imports (pure validation)
- `orchestrator.py`: 120 lines, 7 imports (all injected!)
- `commands/scan.py`: 80 lines, 5 imports (thin wrapper)
- **Total: 260 lines** (45% reduction)

**Testing improvements:**
```python
# Can now test validation independently
def test_scan_validator_rejects_missing_path():
    validator = ScanValidator()
    is_valid, errors = validator.validate(
        roots=["/nonexistent"],
        db_path=Path("/tmp/test.db"),
        log_dir=Path("/tmp/logs")
    )
    assert not is_valid
    assert "does not exist" in errors[0]

# Can test orchestration with mocks
def test_scan_orchestrator_emits_events():
    mock_pm = Mock()
    orchestrator = ScanOrchestrator(
        db=Mock(),
        logger=Mock(),
        metrics=Mock(),
        backend=Mock(),
        plugin_manager=mock_pm
    )

    orchestrator.scan(roots=["/tmp"], ...)

    mock_pm.emit.assert_any_call("scan_start", roots=["/tmp"])
    mock_pm.emit.assert_any_call("scan_complete", ...)
```

#### Testing Strategy

1. **Unit Tests:**
   - `test_scan_validator.py`: Test all validation cases
   - `test_scan_orchestrator.py`: Test with mocked dependencies
   - `test_scan_command.py`: Test CLI integration

2. **Integration Tests:**
   - `test_scan_integration.py`: Test full workflow with real DB

3. **Verification:**
   ```bash
   # All commands still work
   nodupe scan --root /tmp --progress quiet

   # Tests pass
   pytest tests/test_scan* -v
   ```

#### Success Criteria

- ✅ scan.py reduced from 474 → 80 lines
- ✅ Imports reduced from 9 → 5
- ✅ All dependencies injected via constructor
- ✅ Each class has single responsibility
 - ✅ Test coverage target: high coverage achievable (CI validates coverage thresholds)
- ✅ Can mock all dependencies in tests
- ✅ Existing tests still pass

---

### Task 3.2: Split Database God Module (Critical Priority)

**Problem:** `nodupe/db.py` (327 lines) imported by 10+ modules

Currently db.py does **everything**:
- Schema management
- File queries
- Embedding queries
- Migrations
- Connection management

**Impact:** Changing DB breaks 10+ modules, cannot swap SQLite for Postgres

**Solution:** Split into 4 focused modules

#### Step 3.2.1: Create nodupe/db/connection.py

```python
# nodupe/db/connection.py
"""Database connection management.

Handles SQLite connection lifecycle, schema setup, and migrations.
Provides low-level query execution.
"""
import sqlite3
from pathlib import Path
from typing import Any, List, Optional, Tuple


class DatabaseConnection:
    """SQLite connection manager."""

    def __init__(self, db_path: Path):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Open database connection and initialize schema."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def execute(
        self,
        query: str,
        params: Tuple = ()
    ) -> sqlite3.Cursor:
        """Execute SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Cursor with results
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        return self.conn.execute(query, params)

    def executemany(
        self,
        query: str,
        params_list: List[Tuple]
    ):
        """Execute query with multiple parameter sets.

        Args:
            query: SQL query string
            params_list: List of parameter tuples
        """
        if not self.conn:
            raise RuntimeError("Database not connected")
        self.conn.executemany(query, params_list)
        self.conn.commit()

    def _init_schema(self):
        """Initialize database schema."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                size INTEGER,
                mtime INTEGER,
                hash TEXT,
                mime TEXT,
                perms TEXT,
                context TEXT,
                parent TEXT
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                path TEXT PRIMARY KEY,
                embedding BLOB,
                dim INTEGER,
                FOREIGN KEY(path) REFERENCES files(path)
            )
        """)

        self.conn.commit()
```

#### Step 3.2.2: Create nodupe/db/files.py

```python
# nodupe/db/files.py
"""File repository for database operations.

Handles all file-related queries and persistence operations.
Abstracts SQL details from business logic.
"""
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .connection import DatabaseConnection


# Type alias for file records
FileRecord = Tuple[str, int, int, str, str, str, str, str]


class FileRepository:
    """Repository for file operations."""

    def __init__(self, connection: DatabaseConnection):
        """Initialize repository.

        Args:
            connection: Database connection
        """
        self.conn = connection

    def upsert_files(self, records: Iterable[FileRecord]):
        """Insert or update file records.

        Args:
            records: Iterable of (path, size, mtime, hash,
                     mime, perms, context, parent) tuples
        """
        self.conn.executemany("""
            INSERT INTO files (path, size, mtime, hash, mime, perms, context, parent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                size=excluded.size,
                mtime=excluded.mtime,
                hash=excluded.hash,
                mime=excluded.mime,
                perms=excluded.perms,
                context=excluded.context,
                parent=excluded.parent
        """, list(records))

    def get_duplicates(self) -> List[Tuple[str, List[str]]]:
        """Find duplicate files by hash.

        Returns:
            List of (hash, [path1, path2, ...]) tuples
        """
        cursor = self.conn.execute("""
            SELECT hash, GROUP_CONCAT(path, '|') as paths
            FROM files
            WHERE hash != ''
            GROUP BY hash
            HAVING COUNT(*) > 1
        """)

        return [(row["hash"], row["paths"].split("|"))
                for row in cursor.fetchall()]

    def get_all(self) -> List[Dict]:
        """Get all file records.

        Returns:
            List of file record dicts
        """
        cursor = self.conn.execute("SELECT * FROM files")
        return [dict(row) for row in cursor.fetchall()]

    def get_known_files(self) -> Dict[str, str]:
        """Get known files for incremental scanning.

        Returns:
            Dict mapping path → hash
        """
        cursor = self.conn.execute("SELECT path, hash FROM files")
        return {row["path"]: row["hash"] for row in cursor.fetchall()}

    def iter_files(self):
        """Iterate over all file records.

        Yields:
            File record dicts
        """
        cursor = self.conn.execute("SELECT * FROM files")
        for row in cursor:
            yield dict(row)
```

#### Step 3.2.3: Create nodupe/db/embeddings.py

```python
# nodupe/db/embeddings.py
"""Embedding repository for vector storage.

Handles storage and retrieval of file embeddings for similarity search.
"""
import io
import numpy as np
from typing import Dict, Iterable, List, Optional, Tuple

from .connection import DatabaseConnection


class EmbeddingRepository:
    """Repository for embedding operations."""

    def __init__(self, connection: DatabaseConnection):
        """Initialize repository.

        Args:
            connection: Database connection
        """
        self.conn = connection

    def upsert_embedding(self, path: str, embedding: np.ndarray):
        """Insert or update single embedding.

        Args:
            path: File path
            embedding: Embedding vector
        """
        buf = io.BytesIO()
        np.save(buf, embedding, allow_pickle=False)
        blob = buf.getvalue()

        self.conn.execute("""
            INSERT INTO embeddings (path, embedding, dim)
            VALUES (?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                embedding=excluded.embedding,
                dim=excluded.dim
        """, (path, blob, len(embedding)))

    def upsert_embeddings(
        self,
        records: Iterable[Tuple[str, np.ndarray]]
    ):
        """Insert or update multiple embeddings.

        Args:
            records: Iterable of (path, embedding) tuples
        """
        data = []
        for path, emb in records:
            buf = io.BytesIO()
            np.save(buf, emb, allow_pickle=False)
            data.append((path, buf.getvalue(), len(emb)))

        self.conn.executemany("""
            INSERT INTO embeddings (path, embedding, dim)
            VALUES (?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                embedding=excluded.embedding,
                dim=excluded.dim
        """, data)

    def get_embedding(self, path: str) -> Optional[np.ndarray]:
        """Get embedding for file.

        Args:
            path: File path

        Returns:
            Embedding array or None
        """
        cursor = self.conn.execute(
            "SELECT embedding FROM embeddings WHERE path = ?",
            (path,)
        )
        row = cursor.fetchone()

        if row:
            buf = io.BytesIO(row["embedding"])
            return np.load(buf, allow_pickle=False)
        return None

    def get_all_embeddings(self) -> List[Tuple[str, np.ndarray]]:
        """Get all embeddings.

        Returns:
            List of (path, embedding) tuples
        """
        cursor = self.conn.execute(
            "SELECT path, embedding FROM embeddings"
        )

        results = []
        for row in cursor.fetchall():
            buf = io.BytesIO(row["embedding"])
            emb = np.load(buf, allow_pickle=False)
            results.append((row["path"], emb))

        return results
```

#### Step 3.2.4: Create nodupe/db/__init__.py (PUBLIC API)

```python
# nodupe/db/__init__.py
"""Database subsystem.

Provides abstracted database operations for files and embeddings.
Hides SQLite implementation details behind repository interfaces.

Public API:
    - DB: Main database facade (backwards compatible)
    - DatabaseConnection: Low-level connection manager
    - FileRepository: File operations
    - EmbeddingRepository: Embedding operations
"""
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np

from .connection import DatabaseConnection
from .files import FileRepository, FileRecord
from .embeddings import EmbeddingRepository


class DB:
    """Database facade providing backwards-compatible API.

    This class maintains the same interface as the old monolithic
    DB class, but delegates to specialized repositories internally.
    """

    def __init__(self, db_path: Path):
        """Initialize database.

        Args:
            db_path: Path to database file
        """
        self.connection = DatabaseConnection(db_path)
        self.connection.connect()

        self.files = FileRepository(self.connection)
        self.embeddings = EmbeddingRepository(self.connection)

    def close(self):
        """Close database connection."""
        self.connection.close()

    # File operations (delegate to repository)
    def upsert_files(self, records: Iterable[FileRecord]):
        """Insert or update file records."""
        self.files.upsert_files(records)

    def get_duplicates(self) -> List[Tuple[str, List[str]]]:
        """Find duplicate files."""
        return self.files.get_duplicates()

    def get_all(self) -> List[Dict]:
        """Get all files."""
        return self.files.get_all()

    def iter_files(self):
        """Iterate over files."""
        return self.files.iter_files()

    def get_known_files(self) -> Dict[str, str]:
        """Get known files for incremental scan."""
        return self.files.get_known_files()

    # Embedding operations (delegate to repository)
    def upsert_embedding(self, path: str, embedding: np.ndarray):
        """Insert or update embedding."""
        self.embeddings.upsert_embedding(path, embedding)

    def upsert_embeddings(self, records: Iterable[Tuple[str, np.ndarray]]):
        """Insert or update embeddings."""
        self.embeddings.upsert_embeddings(records)

    def get_embedding(self, path: str) -> Optional[np.ndarray]:
        """Get embedding for file."""
        return self.embeddings.get_embedding(path)

    def get_all_embeddings(self) -> List[Tuple[str, np.ndarray]]:
        """Get all embeddings."""
        return self.embeddings.get_all_embeddings()


__all__ = [
    "DB",  # Backwards-compatible facade
    "DatabaseConnection",
    "FileRepository",
    "FileRecord",
    "EmbeddingRepository"
]
```

#### Benefits of This Refactor

**Before:**
- 327 lines, 1 monolithic module
- Mixed files + embeddings + connection
- Hard to swap SQLite
- Cannot test queries without DB

**After:**
- `connection.py`: 85 lines (connection management)
- `files.py`: 95 lines (file operations)
- `embeddings.py`: 110 lines (embedding operations)
- `__init__.py`: 80 lines (facade for backwards compatibility)
- **Total: 370 lines** (13% larger BUT much better organized)

**Key improvements:**
- ✅ **Testability**: Can test each repository independently
- ✅ **Swappability**: Can create PostgresConnection, implement same interface
- ✅ **Separation of Concerns**: Files ≠ Embeddings ≠ Connection
- ✅ **Backwards Compatible**: Existing code using `DB()` still works
- ✅ **Type Safety**: FileRecord type alias for 8-tuple

#### Migration Strategy

**Step 1:** Create new structure (connection, files, embeddings)
**Step 2:** Create DB facade that delegates
**Step 3:** Run full test suite (should pass, same interface)
**Step 4:** Gradually migrate callers to use repositories directly
**Step 5:** Eventually deprecate DB facade

#### Testing Strategy

```python
# Test connection independently
def test_database_connection():
    conn = DatabaseConnection(Path(":memory:"))
    conn.connect()
    cursor = conn.execute("SELECT 1")
    assert cursor.fetchone()[0] == 1

# Test files repository with mock connection
def test_file_repository_upsert():
    mock_conn = Mock()
    repo = FileRepository(mock_conn)

    repo.upsert_files([
        ("/tmp/test.txt", 100, 123456, "abc123", "text/plain", "rw", "", "/tmp")
    ])

    mock_conn.executemany.assert_called_once()

# Test embeddings repository
def test_embedding_repository_roundtrip():
    conn = DatabaseConnection(Path(":memory:"))
    conn.connect()
    repo = EmbeddingRepository(conn)

    emb = np.array([1.0, 2.0, 3.0])
    repo.upsert_embedding("/test.txt", emb)

    retrieved = repo.get_embedding("/test.txt")
    np.testing.assert_array_equal(emb, retrieved)
```

---

### Task 3.3: Eliminate Config Global State (Critical Priority)

**Problem:** `nodupe/config.py` uses module-level dicts (global mutable state)

Current problems:
```python
# config.py (CURRENT - BAD)
DEFAULTS: Dict[str, Any] = {
    "hash_algo": "sha512",
    # ... 20+ keys
}

PRESETS = {
    "default": DEFAULTS,
    "performance": {**DEFAULTS, "workers": 8},  # Dict spreading
    # ...
}

def load_config():
    """Returns mutable dict - can be modified anywhere!"""
    cfg = DEFAULTS.copy()
    cfg.update(...)  # Side effects!
    return cfg
```

**Issues:**
1. **Global mutable state** - can be modified anywhere
2. **No validation** - typos in keys silently ignored
3. **No type safety** - any value can go in any key
4. **Preset inheritance brittle** - dict spreading loses structure
5. **Hard to test** - globals persist across tests

**Solution:** Create immutable Config dataclass with validation

#### Step 3.3.1: Create nodupe/config/schema.py

```python
# nodupe/config/schema.py
"""Configuration schema definition.

Defines the structure and validation rules for NoDupeLabs configuration.
Uses dataclasses for immutability and attrs for validation.
"""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class HashAlgorithm(Enum):
    """Supported hash algorithms."""
    SHA256 = "sha256"
    SHA512 = "sha512"
    BLAKE2B = "blake2b"


class DedupStrategy(Enum):
    """Deduplication strategies."""
    CONTENT_HASH = "content_hash"
    PERCEPTUAL_HASH = "perceptual_hash"
    MTIME = "mtime"


@dataclass(frozen=True)  # Immutable!
class ScanConfig:
    """Scan operation configuration."""
    workers: int = 4
    hash_algo: HashAlgorithm = HashAlgorithm.SHA512
    follow_symlinks: bool = False
    ignore_patterns: List[str] = field(default_factory=list)
    heartbeat_interval_sec: float = 10.0
    stall_timeout_sec: Optional[float] = 300.0

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.workers < 1:
            raise ValueError("workers must be >= 1")
        if self.heartbeat_interval_sec <= 0:
            raise ValueError("heartbeat_interval_sec must be > 0")


@dataclass(frozen=True)
class PlanConfig:
    """Deduplication planning configuration."""
    strategy: DedupStrategy = DedupStrategy.CONTENT_HASH
    min_size_bytes: int = 0
    max_size_bytes: Optional[int] = None
    keep_newest: bool = True
    dry_run: bool = True

    def __post_init__(self):
        if self.min_size_bytes < 0:
            raise ValueError("min_size_bytes must be >= 0")
        if self.max_size_bytes and self.max_size_bytes < self.min_size_bytes:
            raise ValueError("max_size_bytes must be >= min_size_bytes")


@dataclass(frozen=True)
class ExportConfig:
    """Metadata export configuration."""
    enabled: bool = True
    format_version: str = "nodupe_meta_v1"
    include_thumbnails: bool = False


@dataclass(frozen=True)
class Config:
    """Main NoDupeLabs configuration.

    Immutable configuration object validated on construction.
    Cannot be modified after creation (frozen dataclass).
    """
    # Core paths
    db_path: Path = Path("output/index.db")
    log_dir: Path = Path("output/logs")

    # Subsystem configs
    scan: ScanConfig = field(default_factory=ScanConfig)
    plan: PlanConfig = field(default_factory=PlanConfig)
    export: ExportConfig = field(default_factory=ExportConfig)

    # Plugin configuration
    plugins_dir: Optional[Path] = None

    def __post_init__(self):
        """Validate configuration."""
        # Convert string paths to Path objects if needed
        object.__setattr__(self, 'db_path', Path(self.db_path))
        object.__setattr__(self, 'log_dir', Path(self.log_dir))
        if self.plugins_dir:
            object.__setattr__(self, 'plugins_dir', Path(self.plugins_dir))

    def with_overrides(self, **kwargs) -> 'Config':
        """Create new config with overrides.

        Since config is frozen, this creates a new instance with
        specified values changed.

        Args:
            **kwargs: Fields to override

        Returns:
            New Config instance with overrides
        """
        from dataclasses import replace
        return replace(self, **kwargs)
```

#### Step 3.3.2: Create nodupe/config/presets.py

```python
# nodupe/config/presets.py
"""Configuration presets.

Provides pre-configured settings for common use cases.
"""
from typing import Dict

from .schema import Config, ScanConfig, PlanConfig, HashAlgorithm


def get_preset(name: str) -> Config:
    """Get configuration preset by name.

    Args:
        name: Preset name (default, performance, quality, minimal)

    Returns:
        Config instance for preset

    Raises:
        ValueError: If preset name unknown
    """
    presets: Dict[str, Config] = {
        "default": Config(),

        "performance": Config(
            scan=ScanConfig(
                workers=8,
                hash_algo=HashAlgorithm.BLAKE2B,  # Faster
                heartbeat_interval_sec=30.0
            )
        ),

        "quality": Config(
            scan=ScanConfig(
                workers=2,
                hash_algo=HashAlgorithm.SHA512,  # More thorough
                heartbeat_interval_sec=5.0
            )
        ),

        "minimal": Config(
            scan=ScanConfig(
                workers=1,
                hash_algo=HashAlgorithm.SHA256
            ),
            export=ExportConfig(enabled=False)
        )
    }

    if name not in presets:
        available = ", ".join(sorted(presets.keys()))
        raise ValueError(
            f"Unknown preset '{name}'. Available: {available}"
        )

    return presets[name]


def list_presets() -> list[str]:
    """Get list of available preset names."""
    return ["default", "performance", "quality", "minimal"]
```

#### Step 3.3.3: Create nodupe/config/loader.py

```python
# nodupe/config/loader.py
"""Configuration loading from various sources.

Loads configuration from:
1. Built-in presets
2. YAML/JSON files
3. Environment variables
4. Command-line overrides
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .schema import Config, ScanConfig, PlanConfig, ExportConfig, HashAlgorithm
from .presets import get_preset


class ConfigLoader:
    """Loads and merges configuration from multiple sources."""

    def load(
        self,
        preset: str = "default",
        config_file: Optional[Path] = None,
        overrides: Optional[Dict[str, Any]] = None
    ) -> Config:
        """Load configuration with precedence:

        1. Start with preset (lowest priority)
        2. Apply config file settings
        3. Apply environment variables
        4. Apply explicit overrides (highest priority)

        Args:
            preset: Base preset name
            config_file: Optional config file (YAML/JSON)
            overrides: Explicit overrides dict

        Returns:
            Loaded configuration
        """
        # Start with preset
        cfg = get_preset(preset)

        # Apply config file if provided
        if config_file and config_file.exists():
            file_data = self._load_file(config_file)
            cfg = self._merge_config(cfg, file_data)

        # Apply environment variables
        env_data = self._load_environment()
        cfg = self._merge_config(cfg, env_data)

        # Apply explicit overrides
        if overrides:
            cfg = self._merge_config(cfg, overrides)

        return cfg

    def _load_file(self, path: Path) -> Dict[str, Any]:
        """Load config from YAML or JSON file."""
        with open(path) as f:
            if path.suffix in ('.yaml', '.yml'):
                return yaml.safe_load(f)
            elif path.suffix == '.json':
                return json.load(f)
            else:
                raise ValueError(f"Unsupported config format: {path.suffix}")

    def _load_environment(self) -> Dict[str, Any]:
        """Load config from environment variables.

        Environment variables like NO_DUPE_SCAN_WORKERS=8 are mapped to
        config fields like scan.workers.
        """
        prefix = "NO_DUPE_"
        data = {}

        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue

            # NO_DUPE_SCAN_WORKERS → scan.workers
            config_key = key[len(prefix):].lower()

            # Simple type coercion
            if value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)

            # Nested config (scan_workers → scan.workers)
            parts = config_key.split('_')
            if len(parts) == 2:
                section, field = parts
                if section not in data:
                    data[section] = {}
                data[section][field] = value
            else:
                data[config_key] = value

        return data

    def _merge_config(
        self,
        base: Config,
        overrides: Dict[str, Any]
    ) -> Config:
        """Merge overrides into base config.

        Creates new Config instance (immutable) with overrides applied.
        """
        # Convert dict to nested dataclass structure
        kwargs = {}

        if 'db_path' in overrides:
            kwargs['db_path'] = Path(overrides['db_path'])
        if 'log_dir' in overrides:
            kwargs['log_dir'] = Path(overrides['log_dir'])

        if 'scan' in overrides:
            scan_data = overrides['scan']
            kwargs['scan'] = ScanConfig(
                workers=scan_data.get('workers', base.scan.workers),
                hash_algo=HashAlgorithm(
                    scan_data.get('hash_algo', base.scan.hash_algo.value)
                ),
                follow_symlinks=scan_data.get(
                    'follow_symlinks',
                    base.scan.follow_symlinks
                ),
                # ... other fields
            )

        # Similar for plan, export sections...

        return base.with_overrides(**kwargs)
```

#### Step 3.3.4: Create nodupe/config/__init__.py

```python
# nodupe/config/__init__.py
"""Configuration subsystem.

Provides immutable, validated configuration objects.

Public API:
    - Config: Main configuration dataclass
    - ConfigLoader: Loads config from multiple sources
    - get_preset: Get predefined preset
    - list_presets: List available presets
"""

from .schema import Config, ScanConfig, PlanConfig, ExportConfig
from .loader import ConfigLoader
from .presets import get_preset, list_presets


# Convenience function for backwards compatibility
def load_config(
    preset: str = "default",
    config_file: Optional[Path] = None,
    **overrides
) -> Config:
    """Load configuration (backwards compatible function).

    Args:
        preset: Preset name
        config_file: Optional config file path
        **overrides: Explicit overrides

    Returns:
        Loaded Config instance
    """
    loader = ConfigLoader()
    return loader.load(preset, config_file, overrides)


__all__ = [
    "Config",
    "ScanConfig",
    "PlanConfig",
    "ExportConfig",
    "ConfigLoader",
    "get_preset",
    "list_presets",
    "load_config"
]
```

#### Benefits of This Refactor

**Before:**
```python
# MUTABLE - can be changed anywhere!
cfg = load_config()
cfg["workers"] = 100  # Typo? Silent failure!
cfg["wrokers"] = 100  # <- typo, creates NEW key

# No validation
cfg["workers"] = -5  # <- nonsensical value accepted
```

**After:**
```python
# IMMUTABLE - cannot be changed after creation
cfg = load_config(preset="performance")
cfg.scan.workers = 100  # TypeError: cannot assign to frozen dataclass

# Validated on construction
Config(scan=ScanConfig(workers=-5))  # ValueError: workers must be >= 1

# Type-safe access
cfg.scan.hash_algo  # IDE knows this is HashAlgorithm enum

# Safe overrides create new instance
cfg2 = cfg.with_overrides(scan=ScanConfig(workers=16))
assert cfg.scan.workers == 8  # Original unchanged
assert cfg2.scan.workers == 16  # New instance
```

**Key improvements:**
- ✅ **Immutable**: Cannot be accidentally modified
- ✅ **Validated**: Invalid values rejected immediately
- ✅ **Type-safe**: IDE autocomplete, mypy checking
- ✅ **Testable**: Each test gets fresh config
- ✅ **Clear structure**: Scan/Plan/Export subsections
- ✅ **Backwards compatible**: `load_config()` function still works

---

### Task 3.4: Inject AI Backend (High Priority)

**Problem:** `nodupe/nsfw_classifier.py` creates hidden AI backend dependency

Current code:
```python
class NSFWClassifier:
    def __init__(self, threshold: int = 2):
        # Hidden dependency - hard to test!
        try:
            from .ai.backends import choose_backend
            self.backend = choose_backend()
        except Exception:
            self.backend = None  # Silent failure
```

**Issues:**
1. **Hidden dependency**: Cannot see backend requirement from signature
2. **Hard to test**: Must have real AI backend available
3. **Silent failures**: Exception swallowing hides problems
4. **Cannot mock**: Backend choice happens in __init__

**Solution:** Dependency injection pattern

#### Step 3.4.1: Refactor nsfw_classifier.py

```python
# nodupe/nsfw_classifier.py (AFTER)
"""NSFW content classification.

Multi-tier classification system:
- Tier 1: Filename regex patterns (fast, no ML)
- Tier 2: File metadata analysis (fast, no ML)
- Tier 3: ML-based image analysis (slow, requires backend)
"""
from pathlib import Path
from typing import Any, Dict, Optional

from .ai.backends import BaseBackend


class NSFWClassifier:
    """Multi-tier NSFW content classifier.

    Uses 3-tier system with increasingly sophisticated (and expensive)
    classification methods. Tiers can be tested independently.
    """

    def __init__(
        self,
        threshold: int = 2,
        backend: Optional[BaseBackend] = None  # INJECTED!
    ):
        """Initialize classifier.

        Args:
            threshold: Classification threshold (1=strict, 3=lenient)
            backend: Optional AI backend for Tier 3 (ML) classification.
                     If None, only Tiers 1-2 are used.
        """
        self.threshold = threshold
        self.backend = backend  # May be None - that's OK!

        # Compile regex patterns (Tier 1)
        self._filename_regex = self._compile_patterns(self.NSFW_PATTERNS)
        self._safe_regex = self._compile_patterns(self.SAFE_PATTERNS)

    def classify(self, path: Path, mime: str) -> Dict[str, Any]:
        """Classify file for NSFW content.

        Uses multi-tier approach:
        1. Filename analysis (always)
        2. Metadata analysis (if image/video)
        3. ML analysis (if backend available)

        Args:
            path: File path
            mime: MIME type

        Returns:
            Classification result dict with:
            - score: NSFW score (0=safe, 100=explicit)
            - confidence: Confidence level (0-100)
            - tier: Which tier made the decision
            - reasoning: Human-readable explanation
        """
        # Tier 1: Filename patterns (fast, always available)
        filename_result = self._classify_filename(path)
        if filename_result['confidence'] >= 80:
            return filename_result

        # Tier 2: Metadata analysis (fast, no ML needed)
        if mime.startswith(('image/', 'video/')):
            metadata_result = self._classify_metadata(path, mime)
            if metadata_result['confidence'] >= 70:
                return metadata_result

        # Tier 3: ML analysis (slow, requires backend)
        if self.backend and mime.startswith('image/'):
            ml_result = self._classify_ml(path)
            if ml_result['confidence'] >= 60:
                return ml_result

        # Default: Merge all signals
        return self._merge_results(
            filename_result,
            metadata_result if mime.startswith(('image/', 'video/')) else None,
            None  # No ML result
        )

    def _classify_filename(self, path: Path) -> Dict[str, Any]:
        """Tier 1: Filename-based classification (no I/O, no ML)."""
        name_lower = path.name.lower()

        # Check NSFW patterns
        nsfw_score = 0
        for pattern, weight in self._filename_regex:
            if pattern.search(name_lower):
                nsfw_score += weight

        # Check safe patterns
        safe_score = 0
        for pattern, weight in self._safe_regex:
            if pattern.search(name_lower):
                safe_score += weight

        # Determine result
        if nsfw_score > safe_score:
            return {
                'score': min(100, nsfw_score * 10),
                'confidence': 85,
                'tier': 1,
                'reasoning': 'Filename matches NSFW patterns'
            }
        elif safe_score > 0:
            return {
                'score': 0,
                'confidence': 75,
                'tier': 1,
                'reasoning': 'Filename matches safe patterns'
            }
        else:
            return {
                'score': 50,
                'confidence': 30,
                'tier': 1,
                'reasoning': 'Filename inconclusive'
            }

    def _classify_metadata(
        self,
        path: Path,
        mime: str
    ) -> Dict[str, Any]:
        """Tier 2: Metadata-based classification (fast I/O, no ML)."""
        # Check file size, dimensions, aspect ratio, etc.
        # (Implementation details omitted for brevity)
        pass

    def _classify_ml(self, path: Path) -> Dict[str, Any]:
        """Tier 3: ML-based classification (slow, requires backend)."""
        if not self.backend:
            return {
                'score': 50,
                'confidence': 0,
                'tier': 3,
                'reasoning': 'No ML backend available'
            }

        try:
            # Use injected backend
            prediction = self.backend.predict(path)

            return {
                'score': int(prediction['nsfw_score'] * 100),
                'confidence': int(prediction['confidence'] * 100),
                'tier': 3,
                'reasoning': 'ML classification'
            }
        except Exception as e:
            # Don't fail hard - degrade gracefully
            return {
                'score': 50,
                'confidence': 0,
                'tier': 3,
                'reasoning': f'ML classification failed: {e}'
            }
```

#### Step 3.4.2: Update callers to inject backend

```python
# nodupe/commands/scan.py (AFTER)
def cmd_scan(args, cfg):
    # ...

    # Create backend explicitly
    backend = choose_backend()

    # Inject into classifier
    classifier = NSFWClassifier(
        threshold=cfg.scan.nsfw_threshold,
        backend=backend  # INJECTED!
    )

    # Use classifier...
```

#### Benefits

**Before:**
```python
# Cannot test without real AI backend
def test_nsfw_classifier():
    clf = NSFWClassifier()  # Creates backend internally
    # Must have ONNX model file available!
```

**After:**
```python
# Can test each tier independently
def test_nsfw_classifier_filename_tier():
    # No backend needed for Tier 1!
    clf = NSFWClassifier(backend=None)
    result = clf._classify_filename(Path("explicit_content.jpg"))
    assert result['tier'] == 1
    assert result['score'] > 50

def test_nsfw_classifier_with_mock_backend():
    # Mock backend for Tier 3 testing
    mock_backend = Mock()
    mock_backend.predict.return_value = {
        'nsfw_score': 0.9,
        'confidence': 0.95
    }

    clf = NSFWClassifier(backend=mock_backend)
    result = clf.classify(Path("test.jpg"), "image/jpeg")

    assert result['tier'] == 3
    assert result['score'] == 90
```

---

### Task 3.5: Extract Classes from scanner.py (High Priority)

**Problem:** `nodupe/scanner.py` has 275-line god function `threaded_hash()`

Current function does **everything**:
- File discovery (recursively walk directories)
- Threading (manage worker pool)
- Progress reporting (tqdm integration)
- Timeout handling (stall detection, heartbeat)
- Result collection

**Solution:** Extract 4 focused classes

#### Step 3.5.1: Create nodupe/scanner/discovery.py

```python
# nodupe/scanner/discovery.py
"""File discovery for scanning.

Walks directory trees and discovers scannable files.
"""
from pathlib import Path
from typing import Iterable, List

from ..utils.filesystem import should_skip


class FileDiscoverer:
    """Discovers files for scanning."""

    def __init__(
        self,
        roots: List[str],
        ignore_patterns: List[str],
        follow_symlinks: bool = False
    ):
        """Initialize discoverer.

        Args:
            roots: Root directories to scan
            ignore_patterns: Patterns to ignore
            follow_symlinks: Whether to follow symlinks
        """
        self.roots = [Path(r) for r in roots]
        self.ignore_patterns = ignore_patterns
        self.follow_symlinks = follow_symlinks

    def discover(self) -> Iterable[Path]:
        """Discover all scannable files.

        Yields:
            Path objects for files to scan
        """
        for root in self.roots:
            yield from self._walk(root)

    def _walk(self, root: Path) -> Iterable[Path]:
        """Recursively walk directory tree."""
        try:
            for entry in root.iterdir():
                # Skip ignored patterns
                if should_skip(entry, self.ignore_patterns):
                    continue

                # Handle symlinks
                if entry.is_symlink() and not self.follow_symlinks:
                    continue

                # Recurse into directories
                if entry.is_dir():
                    yield from self._walk(entry)

                # Yield files
                elif entry.is_file():
                    yield entry

        except PermissionError:
            # Skip directories we can't read
            pass
```

#### Step 3.5.2: Create nodupe/scanner/worker_pool.py

```python
# nodupe/scanner/worker_pool.py
"""Worker pool for parallel file hashing."""
import concurrent.futures as futures
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

# Type alias for file records
FileRecord = Tuple[str, int, int, str, str, str, str, str]


class HashWorkerPool:
    """Manages parallel file hashing with worker threads."""

    def __init__(
        self,
        workers: int,
        hash_fn: Callable[[Path], FileRecord],
        known_files: Optional[Dict[str, str]] = None
    ):
        """Initialize worker pool.

        Args:
            workers: Number of worker threads
            hash_fn: Function to hash a single file
            known_files: Dict of known files (path → hash) for incremental
        """
        self.workers = workers
        self.hash_fn = hash_fn
        self.known_files = known_files or {}

    def process(
        self,
        files: List[Path],
        on_result: Callable[[FileRecord], None]
    ) -> Tuple[int, float]:
        """Process files in parallel.

        Args:
            files: List of files to process
            on_result: Callback for each result

        Returns:
            (total_processed, duration_seconds)
        """
        import time
        start = time.time()

        total = 0
        with futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            # Submit all tasks
            future_to_path = {}
            for path in files:
                # Skip if already known (incremental)
                if str(path) in self.known_files:
                    continue

                future = executor.submit(self.hash_fn, path)
                future_to_path[future] = path

            # Collect results as they complete
            for future in futures.as_completed(future_to_path):
                try:
                    result = future.result()
                    on_result(result)
                    total += 1
                except Exception as e:
                    path = future_to_path[future]
                    # Log error but continue processing
                    print(f"Error processing {path}: {e}")

        duration = time.time() - start
        return (total, duration)
```

#### Step 3.5.3: Create nodupe/scanner/progress.py

```python
# nodupe/scanner/progress.py
"""Progress reporting abstraction."""
from abc import ABC, abstractmethod
from typing import Optional


class ProgressReporter(ABC):
    """Abstract progress reporter interface."""

    @abstractmethod
    def start(self, total: Optional[int] = None):
        """Start progress tracking.

        Args:
            total: Total items to process (if known)
        """
        pass

    @abstractmethod
    def update(self, n: int = 1):
        """Update progress.

        Args:
            n: Number of items completed
        """
        pass

    @abstractmethod
    def finish(self):
        """Finish progress tracking."""
        pass


class TqdmProgressReporter(ProgressReporter):
    """Progress reporter using tqdm."""

    def __init__(self):
        """Initialize reporter."""
        self.pbar = None

    def start(self, total: Optional[int] = None):
        """Start tqdm progress bar."""
        try:
            from tqdm import tqdm
            self.pbar = tqdm(total=total, unit='files')
        except ImportError:
            self.pbar = None

    def update(self, n: int = 1):
        """Update progress bar."""
        if self.pbar:
            self.pbar.update(n)

    def finish(self):
        """Close progress bar."""
        if self.pbar:
            self.pbar.close()


class SilentProgressReporter(ProgressReporter):
    """Progress reporter that does nothing (for tests)."""

    def start(self, total: Optional[int] = None):
        pass

    def update(self, n: int = 1):
        pass

    def finish(self):
        pass
```

#### Step 3.5.4: Refactor nodupe/scanner.py (SIMPLIFIED)

```python
# nodupe/scanner.py (AFTER - 150 lines, was 440)
"""File scanning coordinator.

Provides high-level threaded_hash() function using modular components.
"""
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .scanner.discovery import FileDiscoverer
from .scanner.worker_pool import HashWorkerPool, FileRecord
from .scanner.progress import ProgressReporter, TqdmProgressReporter
from .utils.hashing import hash_file


def process_file(
    path: Path,
    hash_algo: str,
    known_hash: Optional[str] = None
) -> FileRecord:
    """Process single file (UNCHANGED - still needed)."""
    # ... (existing implementation)
    pass


def threaded_hash(
    roots: Iterable[str],
    ignore: List[str],
    workers: int = 4,
    hash_algo: str = "sha512",
    follow_symlinks: bool = False,
    known_files: Optional[Dict] = None,
    progress_reporter: Optional[ProgressReporter] = None,
    collect: bool = False
) -> Tuple[List[FileRecord], float, int]:
    """Hash files in parallel (SIMPLIFIED).

    Args:
        roots: Root directories to scan
        ignore: Patterns to ignore
        workers: Number of worker threads
        hash_algo: Hash algorithm
        follow_symlinks: Follow symlinks
        known_files: Known files for incremental
        progress_reporter: Progress reporter (or None for default tqdm)
        collect: Whether to collect results

    Returns:
        (results, duration_sec, total_count)
    """
    # Use default progress reporter if none provided
    if progress_reporter is None:
        progress_reporter = TqdmProgressReporter()

    # Step 1: Discover files
    discoverer = FileDiscoverer(
        roots=list(roots),
        ignore_patterns=ignore,
        follow_symlinks=follow_symlinks
    )
    files = list(discoverer.discover())

    # Step 2: Process in parallel
    results = []

    def hash_fn(path: Path) -> FileRecord:
        """Hash function for worker pool."""
        return process_file(path, hash_algo)

    def on_result(record: FileRecord):
        """Result callback."""
        if collect:
            results.append(record)
        progress_reporter.update(1)

    progress_reporter.start(total=len(files))

    pool = HashWorkerPool(
        workers=workers,
        hash_fn=hash_fn,
        known_files=known_files
    )

    total, duration = pool.process(files, on_result)

    progress_reporter.finish()

    return (results, duration, total)
```

#### Benefits

**Before:**
- 440 lines, 1 god function
- Mixed 5 concerns in one function
- Hard to test (tqdm hardcoded)
- Hard to replace any component

**After:**
- `discovery.py`: 60 lines (file discovery)
- `worker_pool.py`: 80 lines (threading)
- `progress.py`: 70 lines (progress reporting)
- `scanner.py`: 150 lines (coordinator)
- **Total: 360 lines** (18% reduction)

**Key improvements:**
- ✅ Each class has single responsibility
- ✅ Can test discovery without threading
- ✅ Can test threading without file I/O
- ✅ Can test progress reporting separately
- ✅ Can inject silent progress reporter for tests

---

## Phase 3 Success Criteria

At the end of Phase 3, we should achieve:

### Coupling Metrics
- ✅ scan.py: 9 imports → 5 imports
- ✅ db.py: 10+ dependents → 5 direct dependents
- ✅ config.py: Mutable dict → Immutable dataclass
- ✅ nsfw_classifier.py: Hidden dep → Injected dep
- ✅ scanner.py: 275-line function → 4 classes

### Testability Metrics
- ✅ scan.py: 8 mocks needed → 0 mocks (pure DI)
- ✅ config tests: Shared global → Isolated configs
- ✅ nsfw tests: Need AI backend → Mock backend
- ✅ scanner tests: Need filesystem → In-memory

### Code Quality Metrics
- ✅ Flake8: Linting enforced by CI (goal: no violations)
- ✅ MyPy: Static type checking enforced by CI
- ✅ Interrogate: Docstring coverage enforced by CI (targeting full coverage)
- ✅ Tests: Comprehensive test suite validated in CI
- ✅ Modularity: Score improved compared to earlier phases

### Documentation
- ✅ Update CHANGELOG.md for Phase 3
- ✅ Create ARCHITECTURE.md (overview)
- ✅ Update README.md (new structure)

---

## Phase 4: High Priority Fixes (Target 9.0/10) 🔴 TODO

**Priority:** HIGH
**Effort:** 2-3 weeks (80-120 hours)
**Score:** 8.5 → 9.0

### Overview

Phase 4 addresses high-priority issues that further reduce coupling and improve testability:

1. CLI mixed concerns (bootstrap + parsing + dispatch)
2. Exporter tight filesystem coupling
3. Applier non-atomic operations
4. Implement service container (full DI)
5. Remove plugin manager singleton

---

### Task 4.1: Extract CLI Classes

**Problem:** `cli.py` mixes 5 concerns

**Solution:**
- `CLIBootstrapper` (deps + linting)
- `ArgumentParser` (pure argparse)
- `CommandRouter` (dispatch)
- `main()` becomes 10-line coordinator

**Effort:** 1 week

---

### Task 4.2: Inject FileWriter into Exporter

**Problem:** `exporter.py` does direct file I/O (hard to test)

**Solution:**
```python
class FileWriter(ABC):
    @abstractmethod
    def write(self, path: Path, content: str):
        pass

class RealFileWriter(FileWriter):
    def write(self, path: Path, content: str):
        # Actual I/O
        pass

class MemoryFileWriter(FileWriter):
    def __init__(self):
        self.files: Dict[str, str] = {}

    def write(self, path: Path, content: str):
        self.files[str(path)] = content

# Inject writer
def write_folder_meta(
    folder: Path,
    records: List[Dict],
    writer: FileWriter  # INJECTED!
):
    # ...
    writer.write(meta_path, json.dumps(meta))
```

**Benefits:**
- Can test without filesystem
- Can test idempotency logic
- Can test error handling

**Effort:** 3 days

---

### Task 4.3: Fix Applier Atomicity

**Problem:** `applier.py` does partial moves (not atomic)

**Current (BAD):**
```python
for src, dst in moves:
    shutil.move(src, dst)  # If this fails halfway, partial state!
    checkpoint["moves"].append(...)  # Written AFTER move
```

**Solution (GOOD):**
```python
# Step 1: Write checkpoint BEFORE any moves
write_checkpoint(checkpoint)

# Step 2: Move to staging directory first
staging_dir = Path("/tmp/nodupe_staging")
for src, dst in moves:
    staging_path = staging_dir / dst.name
    shutil.copy2(src, staging_path)  # Copy, don't move yet

# Step 3: Verify all copies succeeded
verify_all_copies(staging_dir)

# Step 4: NOW do the actual moves atomically
for src, dst in moves:
    staging_path = staging_dir / dst.name
    staging_path.rename(dst)  # Atomic rename!
    src.unlink()  # Delete original
```

**Benefits:**
- Atomic operations (all or nothing)
- Can rollback from checkpoint
- No partial states

**Effort:** 1 week

---

### Task 4.4: Implement Service Container

**Problem:** Every module creates its own dependencies

**Solution:** Centralized dependency injection

```python
# nodupe/container.py
"""Service container for dependency injection."""
from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .db import DB, DatabaseConnection, FileRepository, EmbeddingRepository
from .logger import JsonlLogger
from .metrics import Metrics
from .ai.backends import BaseBackend, choose_backend
from .plugins import PluginManager


@dataclass
class ServiceContainer:
    """Container for all application services.

    All services are created once at startup and injected
    where needed. No module creates its own dependencies.
    """
    config: Config
    db_connection: DatabaseConnection
    file_repo: FileRepository
    embedding_repo: EmbeddingRepository
    logger: JsonlLogger
    metrics: Metrics
    ai_backend: BaseBackend
    plugin_manager: PluginManager

    @classmethod
    def create(cls, config: Config) -> 'ServiceContainer':
        """Create container from configuration.

        Args:
            config: Application configuration

        Returns:
            Initialized service container
        """
        # Create database services
        db_conn = DatabaseConnection(config.db_path)
        db_conn.connect()
        file_repo = FileRepository(db_conn)
        embedding_repo = EmbeddingRepository(db_conn)

        # Create other services
        logger = JsonlLogger(config.log_dir)
        metrics = Metrics()
        ai_backend = choose_backend()
        plugin_manager = PluginManager()

        return cls(
            config=config,
            db_connection=db_conn,
            file_repo=file_repo,
            embedding_repo=embedding_repo,
            logger=logger,
            metrics=metrics,
            ai_backend=ai_backend,
            plugin_manager=plugin_manager
        )

    def cleanup(self):
        """Clean up resources."""
        self.db_connection.close()


# Usage in cli.py
def main():
    cfg = load_config()
    container = ServiceContainer.create(cfg)

    # Commands receive container
    cmd_scan(args, container)

    container.cleanup()

# Usage in commands
def cmd_scan(args, container: ServiceContainer):
    orchestrator = ScanOrchestrator(
        db=container.file_repo,
        logger=container.logger,
        metrics=container.metrics,
        backend=container.ai_backend,
        plugin_manager=container.plugin_manager
    )

    orchestrator.scan(...)
```

**Benefits:**
- ✅ Single source of truth for dependencies
- ✅ Easy to swap implementations
- ✅ Perfect for testing (create test container)
- ✅ Lifecycle management (cleanup)

**Effort:** 1 week

---

### Task 4.5: Remove Plugin Manager Singleton

**Problem:** `pm = PluginManager()` is global singleton

**Solution:** Inject plugin manager via container

```python
# Before (BAD)
from .plugins import pm  # Global singleton

def cmd_scan(args, cfg):
    pm.emit("scan_start")  # Uses global

# After (GOOD)
def cmd_scan(args, container: ServiceContainer):
    container.plugin_manager.emit("scan_start")  # Injected
```

**Benefits:**
- Can test with isolated plugin managers
- Can have multiple plugin contexts
- No global state

**Effort:** 3 days

---

## Phase 5: Medium Priority (Target 9.5/10) 🔴 TODO

**Priority:** MEDIUM
**Effort:** 2 weeks (80 hours)
**Score:** 9.0 → 9.5

### Task List

1. **M-1:** Create FileCategory dataclass (vs dict)
2. **M-2:** Fix ensure_unique() race condition (atomic file creation)
3. **M-3:** Merge logger + metrics into Telemetry
4. **M-4:** Extract validator schemas to files
5. **M-5:** Reorganize utils package (filesystem, hashing, media as packages)
6. **M-6:** Create MountAdapter interface (platform abstraction)
7. **M-7:** Integrate archiver into scanner workflow

**Effort:** 2 weeks

---

## Phase 6: Polish (Target 10/10) 🔴 TODO

**Priority:** LOW (Polish)
**Effort:** 1 week (40 hours)
**Score:** 9.5 → 10.0

### Task List

1. **L-1:** Standardize error handling (custom exception hierarchy)
2. **L-2:** Add ABC interfaces for all abstractions
3. **L-3:** Standardize on Path objects (no mixed string/Path)
4. **L-4:** Create parameter objects (reduce long parameter lists)
5. **L-5:** Add type aliases for complex types (FileRecord, etc.)

**Effort:** 1 week

---

## Implementation Timeline

### Week 1-4: Phase 3 (Critical)
- Week 1: Task 3.1 (ScanOrchestrator)
- Week 2: Task 3.2 (Split DB) + Task 3.3 (Config)
- Week 3: Task 3.4 (Inject AI) + Task 3.5 (Scanner classes)
- Week 4: Testing + documentation

### Week 5-7: Phase 4 (High Priority)
- Week 5: Tasks 4.1-4.2 (CLI + Exporter)
- Week 6: Tasks 4.3-4.4 (Applier + Container)
- Week 7: Task 4.5 + testing

### Week 8-9: Phase 5 (Medium Priority)
- Week 8: Tasks M-1 through M-4
- Week 9: Tasks M-5 through M-7

### Week 10: Phase 6 (Polish)
- Week 10: All polish tasks + final testing

---

## Expected Modularity Scores

| Metric | Current | Phase 3 | Phase 4 | Phase 5 | Phase 6 |
|--------|---------|---------|---------|---------|---------|
| **Coupling** | 4/10 | 7/10 | 8/10 | 9/10 | 10/10 |
| **Cohesion** | 7/10 | 8/10 | 9/10 | 10/10 | 10/10 |
| **Interface** | 8/10 | 9/10 | 9/10 | 10/10 | 10/10 |
| **Testability** | 5/10 | 8/10 | 9/10 | 10/10 | 10/10 |
| **Change Impact** | 6/10 | 8/10 | 9/10 | 9/10 | 10/10 |
| **Overall** | **7.5/10** | **8.5/10** | **9.0/10** | **9.5/10** | **10.0/10** |

---

## Risk Mitigation

### High-Risk Changes
1. **Database split** - Affects 10+ modules
   - Mitigation: Keep DB facade for backwards compatibility
   - Migration: Gradual, test at each step

2. **Config refactor** - All commands use config
   - Mitigation: Keep load_config() function working
   - Migration: Update commands one at a time

3. **Service container** - Affects all commands
   - Mitigation: Commands can still create deps directly initially
   - Migration: Move to container gradually

### Testing Strategy
- Unit tests for each new class
- Integration tests for workflows
- Regression tests (all existing tests must pass)
- Performance tests (no slowdown)

### Rollback Plan
- Each task is its own commit
- Can revert individual tasks if issues
- All changes backward compatible initially

---

## Conclusion

This comprehensive plan provides a **complete roadmap to 10/10 modularity**:

**Phases 1-2:** ✅ **COMPLETE** (Command registry + Public APIs)
**Phase 3:** 🔴 **TODO** - Critical refactoring (3-4 weeks)
**Phase 4:** 🔴 **TODO** - High priority (2-3 weeks)
**Phase 5:** 🔴 **TODO** - Medium priority (2 weeks)
**Phase 6:** 🔴 **TODO** - Polish (1 week)

**Total Remaining Effort:** 8-10 weeks for 10/10 score

The plan is **achievable**, **low-risk**, and delivers **immediate value** at each phase. Phase 3 alone will dramatically improve testability and reduce coupling, justifying the investment.
