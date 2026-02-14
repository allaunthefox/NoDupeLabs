# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- 100% docstring coverage
- Wiki documentation structure

### Changed
- Tool reorganization to `tools/` directory

## [0.1.0] - 2025-12

### Added
- Core deduplication system
- Plugin architecture
- SQLite database support
- CLI interface
- Similarity detection
- Test suite (1000+ tests)

### Features
- File scanning with multiple threads
- Content-based hashing
- Plugin-based extensibility
- Database file tracking
- CLI commands (scan, apply, similarity, verify, version)

### Plugin Types
- database
- similarity
- time_sync
- commands
- ml
- gpu
- network
- video
