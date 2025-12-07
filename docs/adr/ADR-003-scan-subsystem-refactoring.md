# ADR-003: Scan Subsystem Refactoring

**Status:** ✅ Accepted
**Date:** 2025-12-05
**Deciders:** Architecture Team
**Context:** Phase 4 of Modularity Improvement Plan

---

## Context

The original `scanner.py` was a monolithic module (1000+ lines) that mixed multiple concerns:
- File tree traversal
- Hash computation (with threading)
- File metadata extraction
- Embedding computation
- Database operations
- Progress tracking
- Error handling

**Problems:**
- Single Responsibility Principle violations
- Hard to test individual components
- Difficult to understand the full workflow
- Changes to one concern affected others
- Hard to reuse components (e.g., just hashing)

---

## Decision

**Refactor the monolithic `scanner.py` into a modular `scan/` subsystem** with clear separation of concerns and orchestration pattern.

**New Structure:**

```
scan/
├── __init__.py          # Public API exports
├── orchestrator.py      # Workflow coordination
├── walker.py            # File tree traversal
├── hasher.py            # Hash computation (threaded)
├── processor.py         # File metadata extraction
├── progress.py          # Progress tracking
└── validator.py         # Precondition validation
```

**Design Pattern:** **Orchestrator Pattern**

The orchestrator coordinates all subsystems without implementing low-level details:

```python
class ScanOrchestrator:
    def __init__(self, db, telemetry, backend, plugin_manager):
        # Dependencies injected (enables testing)
        pass

    def scan(self, roots, hash_algo, workers, ...):
        # 1. Validate preconditions (validator)
        # 2. Walk file tree (walker)
        # 3. Compute hashes (hasher)
        # 4. Extract metadata (processor)
        # 5. Compute embeddings (backend)
        # 6. Store results (db)
        # 7. Track progress (progress)
        # 8. Emit events (plugin_manager)
```

---

## Module Responsibilities

### 1. `orchestrator.py` - Workflow Coordination
**Responsibility:** Coordinate the complete scan workflow
**Dependencies:** All other modules (via DI)
**No Implementation:** Delegates to specialized modules

### 2. `walker.py` - File Tree Traversal
**Responsibility:** Traverse filesystem, yield paths
**Dependencies:** None (pure utility)
**Key Function:** `iter_files(roots, ignore_patterns, follow_symlinks)`

### 3. `hasher.py` - Hash Computation
**Responsibility:** Compute file hashes with parallelism
**Dependencies:** None (pure utility)
**Key Function:** `threaded_hash(files, hash_algo, workers)`

### 4. `processor.py` - File Metadata
**Responsibility:** Extract file metadata (MIME, size, permissions)
**Dependencies:** Filesystem utilities
**Key Function:** `process_file(path)`

### 5. `progress.py` - Progress Tracking
**Responsibility:** Display progress, ETA, throughput
**Dependencies:** None (self-contained)
**Key Class:** `ProgressTracker`

### 6. `validator.py` - Precondition Validation
**Responsibility:** Validate inputs before scan starts
**Dependencies:** None (pure validation)
**Key Class:** `ScanValidator`

---

## Consequences

### Positive

- ✅ **Single Responsibility** - Each module has one clear job
- ✅ **Testability** - Can test each module independently
- ✅ **Reusability** - Can use hasher/walker in other contexts
- ✅ **Maintainability** - Changes isolated to one module
- ✅ **Clarity** - Workflow visible in orchestrator
- ✅ **Extensibility** - Easy to add new processing steps

### Negative

- ⚠️ **More Files** - 7 files instead of 1 monolith
- ⚠️ **Indirection** - Must navigate multiple files
- ⚠️ **Import Complexity** - More imports to manage

### Mitigations

- Clear `__init__.py` with public API exports
- Comprehensive documentation for each module
- Architecture diagram showing relationships
- Type hints on all public functions

---

## Alternatives Considered

### 1. Keep Monolithic Scanner
**Approach:** Accept large file, use comments for sections
**Rejected:** Doesn't solve SRP violations, hard to test

### 2. Pipeline Pattern
**Approach:** Chain of filters/transformers
**Rejected:** Too abstract, harder to understand

### 3. Event-Driven Architecture
**Approach:** Events for each processing stage
**Rejected:** Overkill for current needs, harder to debug

### 4. Microservices (Separate Processes)
**Approach:** Each component as separate process
**Rejected:** Massive complexity increase, no benefits for local tool

---

## Design Decisions

### Orchestrator as Coordinator

The orchestrator is a "dumb" coordinator - it knows the workflow but doesn't implement details:

```python
# Orchestrator doesn't know HOW to hash, just WHEN
files = iter_files(roots, ignore_patterns)
hashes = threaded_hash(files, hash_algo, workers)
```

**Benefits:**
- Workflow visible in one place
- Easy to modify sequence
- Each step independently testable

### Functional Core, Imperative Shell

- **Core modules** (walker, hasher, processor) are pure functions
- **Orchestrator** handles side effects (DB, logging, events)

This makes core logic easy to test without mocks.

### Dependency Injection for Orchestrator

Orchestrator receives all services via constructor:
```python
ScanOrchestrator(
    db=db,                    # Injected
    telemetry=telemetry,      # Injected
    backend=backend,          # Injected
    plugin_manager=pm         # Injected
)
```

**Benefits:**
- Testable (inject mocks)
- Flexible (swap implementations)
- Clear dependencies

---

## Migration Path

### Phase 1: Extract Utilities
- Move `iter_files` to `walker.py`
- Move `threaded_hash` to `hasher.py`
- Keep everything else in `scanner.py`

### Phase 2: Extract Orchestrator
- Create `ScanOrchestrator` class
- Move workflow logic from `cmd_scan` to orchestrator
- Update `cmd_scan` to use orchestrator

### Phase 3: Extract Supporting Modules
- Create `processor.py` for metadata extraction
- Create `progress.py` for progress tracking
- Create `validator.py` for validation

### Phase 4: Cleanup
- Remove old `scanning/` package
- Update all imports
- Update tests to use new structure

---

## Related

- **Pattern:** Orchestrator Pattern, Separation of Concerns
- **References:**
  - [Orchestration vs Choreography](https://camunda.com/blog/2023/02/orchestration-vs-choreography/)
  - [Clean Architecture - Robert Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- **Related ADRs:**
  - ADR-002: Dependency Injection Container (enables this refactoring)
  - ADR-001: Command Registry Pattern (used by scan command)

---

## Implementation

- **PR:** #7 - Architecture documentation
- **Files Created:**
  - `nodupe/scan/orchestrator.py`
  - `nodupe/scan/walker.py`
  - `nodupe/scan/hasher.py`
  - `nodupe/scan/processor.py`
  - `nodupe/scan/progress.py`
  - `nodupe/scan/validator.py`
  - `nodupe/scan/__init__.py`
- **Files Removed:**
  - `nodupe/scanning/__init__.py`
  - `nodupe/scanning/file_processor.py`
  - `nodupe/scanning/progress.py`
- **Files Modified:**
  - `nodupe/commands/scan.py` - Uses orchestrator pattern
- **Impact:** Modularity score: 9/10 → 9/10 (maintained excellent structure)

---

## Metrics

### Before Refactoring
- **scanner.py:** 1000+ lines
- **Imports in scan.py:** 8
- **Test Complexity:** High (must mock everything)

### After Refactoring
- **Largest module:** ~200 lines (orchestrator.py)
- **Imports in scan.py:** 4 (reduced!)
- **Test Complexity:** Low (test each module independently)

### Code Reduction
```
scan.py: 4 imports (vs 8 before) ✅
Avg module size: 150 lines (vs 1000+ before) ✅
Test isolation: 100% (vs mixed before) ✅
```

---

## Notes

This refactoring demonstrates the power of the Orchestrator pattern for complex workflows. Each module now has a single, clear responsibility, making the codebase easier to understand, test, and maintain.

The scan subsystem serves as a template for refactoring other monolithic modules in the codebase.

Key lesson: **Separate "what" (orchestrator) from "how" (specialized modules)**

Future enhancements:
- Add retry logic per module
- Support alternative implementations (e.g., async walker)
- Add performance profiling per stage
- Support pipeline cancellation

---

**Last Updated:** 2025-12-05
