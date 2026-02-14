# Core Module Refactor Plan

**Version:** 5.0  
**Created:** 2026-02-14  
**Status:** Planning Phase  

---

## Overview

This document outlines the comprehensive refactoring plan for all core modules in `nodupe/core/`. This is a **clean break** approach where each replaced module is archived for historical reference.

---

## Critical Rule: Test Coverage Gate

> **IMPORTANT:** Test coverage must be **100% complete** before continuing to the next phase.

Each phase has a mandatory test coverage gate that must pass before proceeding:
- **100% test pass rate** required for the relevant test file(s)
- **Zero failing tests** allowed
- No proceeding to next phase until current phase tests pass

---

## Refactor Approach

### Clean Break Strategy
- Each module being refactored will be **archived** to `archive/refactor_YYYY-MM-DD/<module>/`
- New clean implementations will **replace** the old code
- Any breakage will be **fixed immediately** during the refactoring period
- **No backward compatibility** is required (breaking changes allowed)

### Documentation Requirements
All new code MUST include:
- Module-level docstrings
- License header (SPDX identifier)
- Copyright notice
- Class docstrings with attributes, examples
- Method/function docstrings with Args, Returns, Raises, Example
- Complete type annotations

---

## Current Issues Summary

### Database Module
| Issue | Count | Severity |
|-------|-------|----------|
| Dual-purpose `self.transaction` conflict | 9 | HIGH |
| Component dependency mismatch | 5+ | HIGH |
| Missing attributes (logging, cache, locking, session) | 9 | HIGH |
| Total mypy errors | 42 | HIGH |

### API Module
| Issue | Count | Severity |
|-------|-------|----------|
| Missing API versioning | 1 | HIGH |
| Missing OpenAPI generation | 1 | HIGH |
| Missing rate limiting | 1 | HIGH |
| Missing schema validation | 1 | HIGH |

### Other Modules
| Module | Issues | Priority |
|--------|--------|----------|
| time_sync_utils.py | Missing return types, Any returns | MEDIUM |
| plugin_system/*.py | Missing return type annotations | MEDIUM |
| scan/*.py | Minor type mismatches | LOW |

---

## Phase 1: Database Module Refactor

**Goal:** Fix architectural issues in `database.py` and create a clean, type-safe implementation.

**Achievement Metrics:**
1. `mypy nodupe/core/database --config-file mypy.ini` returns **0 errors**
2. `pytest tests/core/test_database.py -v` shows **100% pass rate** (GATE: Must pass before Phase 2)
3. Test coverage for database module: **100%**

### Step 1.1: Archive Current Database Module
- **Action:** Move `nodupe/core/database/database.py` to `archive/refactor_2026-02-14/database/database.py`
- **Verification:** File exists in archive, original removed from nodupe/core/database/
- **Metric:** `ls archive/refactor_2026-02-14/database/` shows database.py

### Step 1.2: Create New Database Package Structure
- **Action:** Create `nodupe/core/database/` package with:
  - `__init__.py` - Exports (DOCUMENTED)
  - `wrapper.py` - Main Database class (DOCUMENTED)
  - `connection.py` - Connection management (DOCUMENTED)
  - `transaction.py` - Transaction handling (DOCUMENTED)
  - `query.py` - Query execution (DOCUMENTED)
  - `schema.py` - Schema management (DOCUMENTED)
  - `indexing.py` - Index management (DOCUMENTED)
  - `security.py` - Security validation (DOCUMENTED)
  - `files.py` - File repository (DOCUMENTED)
  - `embeddings.py` - Embeddings handling (DOCUMENTED)
  - `repository_interface.py` - Repository interface (DOCUMENTED)
  - `backup.py` - Backup functionality (DOCUMENTED)
- **Verification:** All files exist with complete docstrings
- **Metric:** 12 new files created; `grep -r "def " nodupe/core/database/*.py | wc -l` shows all functions

### Step 1.3: Add Module-Level Docstrings
- **Action:** Add module docstrings to all 12 database files
- **Verification:** Each file starts with triple-quote docstring
- **Metric:** `python -c "import nodupe.core.database"` imports without ImportError

### Step 1.4: Add Class Docstrings
- **Action:** Add Google-style docstrings to all classes
- **Verification:** All classes have docstrings with Attributes, Example sections
- **Metric:** `grep -c "Attributes:" nodupe/core/database/*.py` counts classes

### Step 1.5: Add Method/Function Docstrings
- **Action:** Add docstrings to all methods with Args, Returns, Raises, Example
- **Verification:** All public methods documented
- **Metric:** No "TODO" or undocumented public methods remain

### Step 1.6: Fix Dual-Purpose Attribute Conflict
- **Action:** Rename `self.transaction` object to `self.transaction_manager`
- **Verification:** Context manager works, no method-assign errors
- **Metric:** `mypy nodupe/core/database/wrapper.py --config-file mypy.ini | grep -c "method-assign"` returns 0

### Step 1.7: Add Missing Components
- **Action:** Add logging, cache, locking, session, compression, serialization, cleanup
- **Verification:** Components accessible on Database instance
- **Metric:** `db.logging`, `db.cache`, `db.locking`, `db.session` all accessible

### Step 1.8: Fix Component Dependencies
- **Action:** Pass Connection not Database to components
- **Verification:** Components receive correct type
- **Metric:** `mypy nodupe/core/database/ --config-file mypy.ini` returns 0 errors

### Step 1.9: Run Database Tests - GATE CHECK
- **Action:** Execute test suite
- **Verification:** All database tests pass - **100% required**
- **Metric:** `pytest tests/core/test_database.py -v` shows **100% pass rate**
- **GATE:** Must pass before Phase 2 - if tests fail, fix and re-run until 100% passes

### Step 1.10: Update Imports Across Codebase
- **Action:** Update all files importing from database module
- **Verification:** No import errors
- **Metric:** `python -c "from nodupe.core import *"` imports without errors

---

## Phase 2: API Module - Enhanced Implementation

**Goal:** Create a comprehensive API system with versioning, OpenAPI generation, rate limiting, and schema validation.

**Achievement Metrics:**
1. `mypy nodupe/core/api/ --config-file mypy.ini` returns **0 errors**
2. `pytest tests/core/test_api.py -v` shows **100% pass rate** (GATE: Must pass before Phase 3)
3. All 4 new API features functional (versioning, OpenAPI, rate limiting, validation)
4. Test coverage for API module: **100%**

### Step 2.1: Archive Current API Module
- **Action:** Move `nodupe/core/api.py` to `archive/refactor_2026-02-14/api/api.py`
- **Verification:** File exists in archive
- **Metric:** `ls archive/refactor_2026-02-14/api/` shows api.py

### Step 2.2: Create New API Package Structure
- **Action:** Create `nodupe/core/api/` package with:
  - `__init__.py` - Exports (DOCUMENTED)
  - `versioning.py` - API versioning system (DOCUMENTED)
  - `openapi.py` - OpenAPI spec generation (DOCUMENTED)
  - `ratelimit.py` - Rate limiting (DOCUMENTED)
  - `validation.py` - Schema validation (DOCUMENTED)
  - `decorators.py` - API decorators (DOCUMENTED)
- **Verification:** 6 new files created
- **Metric:** 6 files in nodupe/core/api/

### Step 2.3: Add Module-Level Docstrings
- **Action:** Add module docstrings to all 6 API files
- **Verification:** Each file starts with docstring
- **Metric:** All 6 files have module docstrings

### Step 2.4: Add Class Docstrings
- **Action:** Add docstrings to APIVersion, OpenAPIGenerator, RateLimiter, SchemaValidator
- **Verification:** All classes documented
- **Metric:** 4+ classes with full docstrings

### Step 2.5: Implement APIVersion Class
- **Action:** Create APIVersion with @versioned decorator
- **Verification:** Decorator marks functions with version
- **Metric:** `@versioned("v2")` decorator functional; `APIVersion.get_version()` returns version

### Step 2.6: Implement OpenAPIGenerator Class
- **Action:** Create OpenAPIGenerator for OpenAPI 3.1.2 spec generation
- **Verification:** Generates valid OpenAPI spec
- **Metric:** `generator.generate_spec()` returns valid dict; `generator.to_yaml()` outputs valid YAML

### Step 2.7: Implement RateLimiter Class
- **Action:** Create RateLimiter with sliding window algorithm
- **Verification:** Rate limiting works correctly
- **Metric:** `limiter.check_rate_limit()` returns bool; `limiter.throttle()` returns wait time

### Step 2.8: Implement @rate_limited Decorator
- **Action:** Create @rate_limited decorator
- **Verification:** Decorator applies rate limiting
- **Metric:** `@rate_limited(requests_per_minute=60)` functional

### Step 2.9: Implement SchemaValidator Class
- **Action:** Create SchemaValidator for JSON schema validation
- **Verification:** Validates request/response against schemas
- **Metric:** `validator.validate_request()` and `validator.validate_response()` return bool

### Step 2.10: Implement Validation Decorators
- **Action:** Create @validate_request and @validate_response decorators
- **Verification:** Decorators validate data
- **Metric:** `@validate_request(schema)` and `@validate_response(schema)` functional

### Step 2.11: Add Complete Type Annotations
- **Action:** Add type hints to all functions
- **Verification:** No type errors
- **Metric:** `mypy nodupe/core/api/ --config-file mypy.ini` returns 0 errors

### Step 2.12: Run API Tests - GATE CHECK
- **Action:** Execute API test suite
- **Verification:** All API tests pass - **100% required**
- **Metric:** `pytest tests/core/test_api.py -v` shows **100% pass rate**
- **GATE:** Must pass before Phase 3 - if tests fail, fix and re-run until 100% passes

### Step 2.13: Update Wiki/API Documentation
- **Action:** Document new API features in wiki/
- **Verification:** Documentation exists
- **Metric:** wiki/API/ has updated documentation

---

## Phase 3: Type Annotation Improvements

**Goal:** Fix type errors in remaining core modules using clean break approach.

**Achievement Metrics:**
1. `mypy nodupe/core/ --config-file mypy.ini` returns **0 errors**
2. All affected module tests pass **100%** (GATE: Must pass before Phase 4)
3. Test coverage for affected modules: **100%**

### Step 3.1: Archive and Refactor time_sync_utils.py
- **Action:** Move to archive, create clean version with full docstrings
- **Verification:** File archived, new file created
- **Metric:** `mypy nodupe/core/time_sync_utils.py --config-file mypy.ini` returns 0 errors

### Step 3.2: Archive and Refactor filesystem.py
- **Action:** Move to archive, create clean version with full docstrings
- **Verification:** File archived, new file created
- **Metric:** `mypy nodupe/core/filesystem.py --config-file mypy.ini` returns 0 errors

### Step 3.3: Archive and Refactor compression.py
- **Action:** Move to archive, create clean version with full docstrings
- **Verification:** File archived, new file created
- **Metric:** `mypy nodupe/core/compression.py --config-file mypy.ini` returns 0 errors

### Step 3.4: Archive and Refactor loader.py
- **Action:** Move to archive, create clean version with full docstrings
- **Verification:** File archived, new file created
- **Metric:** `mypy nodupe/core/loader.py --config-file mypy.ini` returns 0 errors

### Step 3.5: Run mypy on Each Module - GATE CHECK
- **Action:** Verify type correctness
- **Verification:** All modules pass mypy - **0 errors required**
- **Metric:** `mypy nodupe/core/ --config-file mypy.ini 2>&1 | grep -c "error:"` returns **0**
- **GATE:** Must pass before Phase 4 - if errors exist, fix and re-run until 0 errors

---

## Phase 4: Plugin System Refactor

**Goal:** Create a clean, well-documented plugin system with complete type annotations.

**Achievement Metrics:**
1. `mypy nodupe/core/plugin_system/ --config-file mypy.ini` returns **0 errors**
2. `pytest tests/plugins/ -v` shows **100% pass rate** (GATE: Must pass before Phase 5)
3. Test coverage for plugin system: **100%**

### Step 4.1: Archive plugin_system/ Directory
- **Action:** Move `nodupe/core/plugin_system/` to `archive/refactor_2026-02-14/plugin_system/`
- **Verification:** All 12 files archived
- **Metric:** `ls archive/refactor_2026-02-14/plugin_system/` shows all files

### Step 4.2: Create New plugin_system/
- **Action:** Recreate with full documentation
- **Verification:** 12 new files with docstrings
- **Metric:** All files have module/class/method docstrings

### Step 4.3: Add Complete Type Annotations
- **Action:** Add type hints to all functions
- **Verification:** No type errors
- **Metric:** `mypy nodupe/core/plugin_system/ --config-file mypy.ini` returns 0 errors

### Step 4.4: Run Plugin Tests - GATE CHECK
- **Action:** Execute plugin test suite
- **Verification:** All tests pass - **100% required**
- **Metric:** `pytest tests/plugins/ -v` shows **100% pass rate**
- **GATE:** Must pass before Phase 5 - if tests fail, fix and re-run until 100% passes

---

## Phase 5: Scan Module Refactor

**Goal:** Clean up scan modules with proper type safety and documentation.

**Achievement Metrics:**
1. `mypy nodupe/core/scan/ --config-file mypy.ini` returns **0 errors**
2. Scan-related tests pass **100%** (GATE: Must pass before Phase 6)
3. Test coverage for scan module: **100%**

### Step 5.1: Archive scan/ Directory
- **Action:** Move `nodupe/core/scan/` to `archive/refactor_2026-02-14/scan/`
- **Verification:** All 7 files archived
- **Metric:** `ls archive/refactor_2026-02-14/scan/` shows all files

### Step 5.2: Create New scan/ with Documentation
- **Action:** Recreate with full docstrings
- **Verification:** 7 new files with documentation
- **Metric:** All files have complete docstrings

### Step 5.3: Fix Type Issues
- **Action:** Add type annotations
- **Verification:** No type errors
- **Metric:** `mypy nodupe/core/scan/ --config-file mypy.ini` returns 0 errors

### Step 5.4: Run Scan Tests - GATE CHECK
- **Action:** Execute scan test suite
- **Verification:** All tests pass - **100% required**
- **Metric:** Relevant tests show **100% pass rate**
- **GATE:** Must pass before Phase 6 - if tests fail, fix and re-run until 100% passes

---

## Phase 6: Other Core Modules

**Goal:** Refactor remaining core modules with full documentation.

**Achievement Metrics:**
1. All refactored modules pass mypy with **0 errors**
2. All module tests pass **100%** (GATE: Must pass before Phase 7)
3. Test coverage for all modules: **100%**

### Step 6.1: Archive and Refactor config.py
- **Action:** Archive, recreate with docstrings
- **Verification:** File archived, new file works
- **Metric:** `mypy nodupe/core/config.py --config-file mypy.ini` returns 0 errors

### Step 6.2: Archive and Refactor incremental.py
- **Action:** Archive, recreate with docstrings
- **Verification:** File archived, new file works
- **Metric:** `mypy nodupe/core/incremental.py --config-file mypy.ini` returns 0 errors

### Step 6.3: Archive and Refactor security.py
- **Action:** Archive, recreate with docstrings
- **Verification:** File archived, new file works
- **Metric:** `mypy nodupe/core/security.py --config-file mypy.ini` returns 0 errors

### Step 6.4: Archive and Refactor validators.py
- **Action:** Archive, recreate with docstrings
- **Verification:** File archived, new file works
- **Metric:** `mypy nodupe/core/validators.py --config-file mypy.ini` returns 0 errors

### Step 6.5: Archive and Refactor pools.py
- **Action:** Archive, recreate with docstrings
- **Verification:** File archived, new file works
- **Metric:** `mypy nodupe/core/pools.py --config-file mypy.ini` returns 0 errors

### Step 6.6: Archive and Refactor parallel.py
- **Action:** Archive, recreate with docstrings
- **Verification:** File archived, new file works
- **Metric:** `mypy nodupe/core/parallel.py --config-file mypy.ini` returns 0 errors

### Step 6.7: Archive and Refactor logging.py
- **Action:** Archive, recreate with docstrings
- **Verification:** File archived, new file works
- **Metric:** `mypy nodupe/core/logging.py --config-file mypy.ini` returns 0 errors

### Step 6.8: Archive and Refactor errors.py
- **Action:** Archive, recreate with docstrings
- **Verification:** File archived, new file works
- **Metric:** `mypy nodupe/core/errors.py --config-file mypy.ini` returns 0 errors

---

## Phase 7: Verification & Cleanup

**Goal:** Ensure full compliance and update documentation.

**Achievement Metrics:**
1. `mypy nodupe/ --config-file mypy.ini` returns **0 errors**
2. `pytest tests/ --tb=short` shows **100% pass rate** (FINAL GATE)
3. Test coverage for entire project: **100%**

### Step 7.1: Run Full mypy Check - GATE CHECK
- **Action:** Execute mypy on entire codebase
- **Verification:** Zero type errors required
- **Metric:** `mypy nodupe/ --config-file mypy.ini 2>&1 | grep -c "error:"` returns **0**
- **GATE:** Must pass before final completion

### Step 7.2: Run Full pytest Suite - FINAL GATE CHECK
- **Action:** Execute all tests
- **Verification:** 100% pass rate required
- **Metric:** `pytest tests/ --tb=short` shows **100% pass rate**
- **FINAL GATE:** Project complete only when 100% tests pass

### Step 7.3: Update TYPE_FIX_PLAN.md
- **Action:** Document completion status
- **Verification:** Document updated
- **Metric:** File shows completion status

### Step 7.4: Update PROJECT_PLAN.md
- **Action:** Update with new refactor status
- **Verification:** Document updated
- **Metric:** File reflects completed refactor

### Step 7.5: Create ARCHIVE_REFACTOR_LOG.md
- **Action:** Document all changes
- **Verification:** Log created
- **Metric:** File exists in archive/

---

## Phase Gate Summary

| Phase | Gate Check | Required | Next Phase |
|-------|------------|----------|-------------|
| 1 | `pytest tests/core/test_database.py -v` | 100% pass | Phase 2 |
| 2 | `pytest tests/core/test_api.py -v` | 100% pass | Phase 3 |
| 3 | `mypy nodupe/core/ --config-file mypy.ini` | 0 errors | Phase 4 |
| 4 | `pytest tests/plugins/ -v` | 100% pass | Phase 5 |
| 5 | Scan tests | 100% pass | Phase 6 |
| 6 | Module tests | 100% pass | Phase 7 |
| 7 | `pytest tests/ --tb=short` | 100% pass | COMPLETE |

---

## Success Metrics Summary

| Phase | Metric | Target | Verification Command |
|-------|--------|--------|---------------------|
| 1 | mypy errors | 0 | `mypy nodupe/core/database/ --config-file mypy.ini \| grep -c "error:"` |
| 1 | test pass rate | **100%** | `pytest tests/core/test_database.py -v` |
| 1 | test coverage | **100%** | Coverage report |
| 2 | mypy errors | 0 | `mypy nodupe/core/api/ --config-file mypy.ini` |
| 2 | test pass rate | **100%** | `pytest tests/core/test_api.py -v` |
| 2 | API features | 4/4 | Manual verification |
| 3 | mypy errors | 0 | `mypy nodupe/core/ --config-file mypy.ini` |
| 4 | mypy errors | 0 | `mypy nodupe/core/plugin_system/` |
| 4 | test pass rate | **100%** | `pytest tests/plugins/ -v` |
| 5 | mypy errors | 0 | `mypy nodupe/core/scan/` |
| 5 | test pass rate | **100%** | Scan tests |
| 6 | mypy errors | 0 | Per-file mypy checks |
| 6 | test pass rate | **100%** | Module tests |
| 7 | full mypy | 0 | `mypy nodupe/ --config-file mypy.ini` |
| 7 | full pytest | **100%** | `pytest tests/ --tb=short` |

---

## Documentation Standards

All new files MUST include:

```python
"""
Module Name - Brief Description.

Extended description of what this module does, its purpose,
and key functionalities it provides.

Classes:
    ClassName: Description of the class.

Functions:
    function_name: Description of what the function does.

Example:
    >>> from nodupe.core.module import ClassName
    >>> obj = ClassName()
    >>> obj.method()
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun
```

---

## Implementation Order

```
Phase 1: Database Module (START HERE)
├── 1.1 Archive database.py → Metric: file in archive/
├── 1.2 Create package → Metric: 12 files created
├── 1.3 Module docstrings → Metric: 12 files documented
├── 1.4 Class docstrings → Metric: classes documented
├── 1.5 Method docstrings → Metric: methods documented
├── 1.6 Fix conflict → Metric: 0 method-assign errors
├── 1.7 Add components → Metric: components accessible
├── 1.8 Fix deps → Metric: 0 type errors
├── 1.9 Run tests [GATE] → Metric: 100% pass ← CANNOT PROCEED WITHOUT THIS
└── 1.10 Update imports → Metric: no import errors

Phase 2: API Module
├── 2.1 Archive api.py
├── 2.2 Create package (6 files)
├── 2.3-2.5 Documentation
├── 2.6-2.10 Implement features
├── 2.11 Type annotations
├── 2.12 Run tests [GATE] → Metric: 100% pass ← CANNOT PROCEED WITHOUT THIS
└── 2.13 Update wiki

Phase 3: Type Fixes
├── 3.1-3.4 Archive and refactor modules
└── 3.5 mypy check [GATE] → 0 errors ← CANNOT PROCEED WITHOUT THIS

Phase 4: Plugin System
├── 4.1-4.3 Archive, create, annotate
└── 4.4 Run tests [GATE] → 100% pass ← CANNOT PROCEED WITHOUT THIS

Phase 5: Scan Module
├── 5.1-5.3 Archive, create, fix types
└── 5.4 Run tests [GATE] → 100% pass ← CANNOT PROCEED WITHOUT THIS

Phase 6: Other Modules
├── 6.1-6.8 Archive and refactor
└── All tests [GATE] → 100% pass ← CANNOT PROCEED WITHOUT THIS

Phase 7: Verification [FINAL]
├── 7.1 mypy [GATE] → 0 errors
└── 7.2 pytest [FINAL GATE] → 100% pass ← PROJECT COMPLETE
```

---

**Document Status:** Ready for Implementation  
**Next Step:** "Toggle to Act mode" to begin Phase 1 implementation

---

*Previous versions:*
- *v1.0 - Original database.py issues identified*
- *v2.0 - TYPE_FIX_PLAN.md created*
- *v3.0 - Clean break approach, full documentation, API enhancements*
- *v4.0 - Explicit achievement metrics for each step*
- *v5.0 - This plan (100% test coverage gate before each phase)*
