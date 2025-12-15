# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

-**MMAP Handler**(`nodupe/core/mmap_handler.py`): Memory-mapped file operations with context manager support
-**Incremental Scanning**(`nodupe/core/incremental.py`): Checkpoint-based resume support for long scans
-**API Management**(`nodupe/core/api.py`): API stability decorators and endpoint validation

### Fixed

-**Database Schema Alignment**: Fixed `FileRepository` row indices to match 14-column schema
-**Memory Database Path**: Fixed `DatabaseConnection` handling of `:memory:` path
-**Test Suite**: Updated `test_main.py` to align with current `CoreLoader` API
-**Test Database Schema**: Updated `test_database.py` to use full schema consistently

### Changed

- Core utilities now 100% implemented (13/13 modules)
- Test suite expanded to 134 passing tests

## [0.1.0] - 2025-12-14

#### Added

- Initial modular architecture with plugin system
- Core command plugins: `scan`, `similarity`, `plan`, `apply`
- BruteForce similarity backend with optional FAISS support
- SQLite database with full schema management
- Plugin hot-reload support
- Platform-specific auto-configuration
- Parallel processing with GIL-aware optimization
