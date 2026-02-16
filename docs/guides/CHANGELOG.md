# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-14

### Added
- **Rollback System**: Transaction logging and snapshot capabilities for data safety
  - `SnapshotManager` class for creating/restoring snapshots
  - `TransactionLog` class for logging operations
  - `RollbackManager` for high-level orchestration
  - CLI commands: `create`, `restore`, `delete`, `list`, `undo`
- **Type Safety**: mypy integration in CI pipeline
- **Code Formatting**: black and isort integration in CI pipeline
- **Performance Benchmarks**: Added to CI pipeline
- **Security Scanner**: red_team.py for vulnerability detection

### Changed
- **CI/CD Pipeline**: Enhanced with multiple quality gates
  - mypy type checking
  - black format checking
  - isort import checking
  - Performance benchmarks
  - Rollback tests

### Fixed
- **Test Coverage**: Improved to 80%+
- **Docstrings**: 100% coverage on all functions

## [0.0.0] - 2025-12-17

### Added
- Initial release
- Core deduplication functionality
- Plugin system
- Database support
- CLI commands

[1.0.0]: https://github.com/allaunthefox/NoDupeLabs/releases/tag/v1.0.0
[0.0.0]: https://github.com/allaunthefox/NoDupeLabs/releases/tag/v0.0.0
