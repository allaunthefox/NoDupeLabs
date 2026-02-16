# Import Path Mapping for NoDupeLabs Project

## Overview

This document maps the old import paths to the new import paths after the project restructuring.

## Path Mapping

### Database Module
- **Old**: `nodupe.core.database.connection` → **New**: `nodupe.tools.databases.connection`
- **Old**: `nodupe.core.database.files` → **New**: `nodupe.tools.databases.files`
- **Old**: `nodupe.core.database.repository_interface` → **New**: `nodupe.tools.databases.repository_interface`
- **Old**: `nodupe.core.database.schema` → **New**: `nodupe.tools.databases.schema`
- **Old**: `nodupe.core.database.query` → **New**: `nodupe.tools.databases.query`
- **Old**: `nodupe.core.database.database` → **New**: `nodupe.tools.databases.database`

### Hashing Module
- **Old**: `nodupe.core.hasher` → **New**: `nodupe.tools.hashing.hasher_logic`
- **Old**: `nodupe.core.hasher_interface` → **New**: `nodupe.tools.hashing.hasher_logic`

### Archive Module
- **Old**: `nodupe.core.archive_interface` → **New**: `nodupe.tools.archive.archive_logic`

### MIME Module
- **Old**: `nodupe.core.mime_interface` → **New**: `nodupe.tools.mime.mime_logic`

### Compression Module
- **Old**: `nodupe.core.compression` → **New**: `nodupe.tools.compression_standard.engine_logic`

### Time Sync Module
- **Old**: `nodupe.core.time_sync` → **New**: `nodupe.tools.time_sync.time_sync_logic`

### File System Module
- **Old**: `nodupe.core.filesystem` → **New**: `nodupe.tools.os_filesystem.fs_logic`

### Scanner Engine Module
- **Old**: `nodupe.core.scan.processor` → **New**: `nodupe.tools.scanner_engine.processor`
- **Old**: `nodupe.core.scan.walker` → **New**: `nodupe.tools.scanner_engine.walker`
- **Old**: `nodupe.core.scan.hasher` → **New**: `nodupe.tools.hashing.hasher_logic`
- **Old**: `nodupe.core.scan.progress` → **New**: `nodupe.tools.scanner_engine.progress`
- **Old**: `nodupe.core.scan.file_info` → **New**: `nodupe.tools.scanner_engine.file_info`
- **Old**: `nodupe.core.incremental` → **New**: `nodupe.tools.scanner_engine.incremental`

### Cache Modules
- **Old**: `nodupe.core.cache.embedding_cache` → **New**: `nodupe.tools.ml.embedding_cache`
- **Old**: `nodupe.core.cache.hash_cache` → **New**: `nodupe.tools.hashing.hash_cache`
- **Old**: `nodupe.core.cache.query_cache` → **New**: `nodupe.tools.databases.query_cache`

### Security Module
- **Old**: `nodupe.core.security` → **New**: `nodupe.tools.security_audit.security_logic`

### Maintenance Module
- **Old**: `nodupe.core.maintenance` → **New**: `nodupe.tools.maintenance.manager_logic`

### API Modules
- **Old**: `nodupe.core.api.validation` → **New**: `nodupe.core.api.validation`
- **Old**: `nodupe.core.api.codes` → **New**: `nodupe.core.api.codes`
- **Old**: `nodupe.core.api.ipc` → **New**: `nodupe.core.api.ipc`

### Tool System Modules
- **Old**: `nodupe.core.tool_system.registry` → **New**: `nodupe.core.tool_system.registry`
- **Old**: `nodupe.core.tool_system.loader` → **New**: `nodupe.core.tool_system.loader`
- **Old**: `nodupe.core.tool_system.discovery` → **New**: `nodupe.core.tool_system.discovery`
- **Old**: `nodupe.core.tool_system.lifecycle` → **New**: `nodupe.core.tool_system.lifecycle`
- **Old**: `nodupe.core.tool_system.base` → **New**: `nodupe.core.tool_system.base`
- **Old**: `nodupe.core.tool_system.accessible_base` → **New**: `nodupe.core.tool_system.accessible_base`

### Core Modules (Unchanged)
- `nodupe.core.config`
- `nodupe.core.container`
- `nodupe.core.loader`
- `nodupe.core.main`
- `nodupe.core.errors`
- `nodupe.core.version`
- `nodupe.core.deps`
- `nodupe.core.limits`
- `nodupe.core.logging_system`

## Fixes Applied

### Test File Import Fixes
The following test files have been updated to use the new import paths:

1. **Cache Tests** (tests/core/cache/):
   - `test_embedding_cache.py` → `nodupe.tools.ml.embedding_cache`
   - `test_hash_cache.py` → `nodupe.tools.hashing.hash_cache`
   - `test_query_cache.py` → `nodupe.tools.databases.query_cache`

2. **Scanner Tests** (tests/core/):
   - `test_file_walker.py` → `nodupe.tools.scanner_engine.walker`, `nodupe.tools.scanner_engine.file_info`
   - `test_file_processor.py` → `nodupe.tools.scanner_engine.processor`, `nodupe.tools.scanner_engine.walker`
   - `test_file_hasher.py` → `nodupe.tools.hashing.hasher_logic`
   - `test_file_info.py` → `nodupe.tools.scanner_engine.file_info`
   - `test_progress_tracker.py` → `nodupe.tools.scanner_engine.progress`
   - `test_incremental.py` → `nodupe.tools.scanner_engine.incremental`

### Module Import Fixes
The following module files have been fixed to resolve broken imports:

1. **nodupe/tools/ml/__init__.py** - Removed broken `from .ml_tool import register_tool` import
2. **nodupe/tools/scanner_engine/__init__.py** - Fixed imports to include proper exports
3. **nodupe/tools/archive/archive_logic.py** - Fixed imports to use correct paths:
   - `nodupe.tools.compression_standard.engine_logic`
   - `nodupe.tools.mime.mime_logic`
   - `nodupe.core.archive_interface`
   - `nodupe.core.container`
4. **nodupe/tools/mime/mime_logic.py** - Fixed import to use `nodupe.core.mime_interface`

## Current Status

- **Initial State**: 36 errors, 734 tests collected
- **Current State**: 33 errors, 794 tests collected
- **Tests Resolved**: 60 more tests now collecting successfully
- **Errors Reduced**: 3 fewer errors

## Remaining Work

The following test files still have import errors that need to be resolved:
- test_plugins.py
- test_progress_tracker.py (may need re-check)
- test_rollback.py
- test_rollback_idempotent.py
- test_security.py
- test_time_sync_failure_rules.py
- test_time_sync_utils.py
- test_validators.py
- Various integration and performance tests
