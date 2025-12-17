<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright (c) 2025 Allaun -->
<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to NoDupeLabs will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Comprehensive CHANGELOG.md for tracking project changes
- Enhanced README.md with status badges for type safety and test coverage
- Detailed "What's New" section in README.md
- Complete implementation of DatabaseRepository with full CRUD operations
- Additional repository methods: read_all, count, exists
- **CONTRIBUTING.md**: Comprehensive contribution guidelines with development setup, coding standards, testing requirements, and community guidelines
- **Documentation Updates**: Updated all core documentation files with current project status and implementation details
- **December 17 Documentation Update**: Comprehensive update to all documentation files including PROJECT_STATUS.md, CHANGELOG.md, and other project planning documents

### Changed

- Updated all project documentation to reflect Pylance error fixes and current status
- Improved PROJECT_SUMMARY.md with date-stamped change history and documentation updates
- Enhanced TODOS.md with type safety completion status and documentation progress
- Updated PROJECT_SUMMARY.md to reflect 100% completion of Core Scanning, Database modules, and documentation
- Updated Project_Plans/README.md with current project status including documentation completion
- Updated Project_Plans/Architecture/ARCHITECTURE.md with latest implementation details
- Updated Project_Plans/Implementation/ROADMAP.md with accurate phase completion (Phase 8 now 60% complete)
- Updated Project_Plans/Features/COMPARISON.md with current feature status (85% migration complete)
- Updated Project_Plans/Quality/IMPROVEMENT_PLAN.md with latest quality metrics and documentation progress
- Updated output/ci_artifacts/README.md with current project status including documentation completion
- **December 17 Documentation Update**: Updated PROJECT_STATUS.md to reflect current date (2025-12-17) and added comprehensive documentation update entry

### Fixed

- DatabaseRepository now fully implemented (previously had NotImplementedError stubs)
- Type safety issue in repository_interface.py (lastrowid None handling)
- Documentation consistency issues across all project files
- Missing CONTRIBUTING.md file created with comprehensive guidelines
- **Import Errors**: Fixed SimilarityPlugin and Database class import errors in test files
- **CI/CD Documentation**: Updated CI_FIX_SUMMARY.md to reflect completed documentation and import error fixes

## [0.9.5] - 2025-12-15

### Fixed

- **Type Safety Improvements**: Resolved all Pylance type checking errors
  - `nodupe/core/database/indexing.py` (line 234): Added explicit type annotation `List[Dict[str, Any]]` for columns list in `get_index_info()` method
  - `nodupe/core/plugin_system/compatibility.py`:
    - Added `cast` import from typing module for proper type casting
    - Line 194: Used `cast(Dict[Any, Any], deps)` for proper dictionary type casting
    - Lines 196-197: Added explicit type annotations `key_str: str` and `value_str: str`
    - Line 401: Added type annotation `parts: List[int] = []` in `_parse_version()` method
    - Removed unnecessary `# type: ignore` comments
  - Improved type inference for complex nested data structures
  - Enhanced type safety for list comprehensions and dict operations

### Changed

- Updated Project_Plans/Quality/IMPROVEMENT_PLAN.md:
  - Marked "Type Safety Enforcement" as "✅ IN PROGRESS"
  - Added detailed changelog of Pylance fixes
  - Updated current status from "Partial hints" to "Pylance errors fixed"
- Updated PROJECT_SUMMARY.md:
  - Added "Recent Critical Fixes" section with detailed type safety improvements
  - Separated December 15 changes from December 14 changes
- Updated Project_Plans/TODOS.md:
  - Updated Type Safety section with completed Pylance error fixes
  - Added Recent Updates subsection with detailed accomplishments

## [0.9.4] - 2025-12-14

### Added

- Unified Core Loader system for better modularity
- Complete Similarity System with BruteForce backend integration
- Full Plan Command implementation
- Comprehensive Verify Command with integrity checking

### Fixed

- Core loader refactoring to use unified loader.py
- Similarity backend connection to CLI
- Plugin validation issues
- Legacy plugin structure issues in scan.py and apply.py

### Changed

- Improved main entry point architecture
- Enhanced plugin system reliability
- Better error handling in core modules

## [0.9.3] - 2025-12-13

### Added

- Hash autotuning functionality for optimal algorithm selection
- Verify command implementation
- Comprehensive test suite expansion

### Fixed

- Hash autotuning algorithm selection logic
- Database transaction handling
- Plugin discovery and loading issues

### Changed

- Updated test coverage metrics (144 tests collected)
- Improved documentation accuracy across all planning documents

## [0.9.2] - 2025-12-12

### Added

- Complete plugin system with lifecycle management
- Plugin security and isolation features
- Plugin dependency resolution
- Cache system (hash_cache, query_cache, embedding_cache)

### Changed

- Enhanced plugin architecture with hard isolation
- Improved plugin discovery mechanism
- Better error handling in plugin system

## [0.9.1] - 2025-12-11

### Added

- Core database layer with SQLite
- File scanning and hashing system
- Basic command structure (scan, apply)
- Configuration management with TOML

### Changed

- Restructured core architecture for better modularity
- Improved file processing pipeline
- Enhanced database schema

## [0.9.0] - 2025-12-10

### Added

- Initial project structure
- Basic file scanning capabilities
- Database foundation
- Plugin system foundation
- Documentation framework

### Changed

- Migrated from legacy codebase
- Modernized Python code structure
- Updated dependencies

## Types of Changes

- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` in case of vulnerabilities

## Version Guidelines

- **Major version** (X.0.0): Incompatible API changes
- **Minor version** (0.X.0): New features, backwards compatible
- **Patch version** (0.0.X): Bug fixes, backwards compatible

## Contributing

When adding changes to this CHANGELOG:

1. Add entries to the `[Unreleased]` section as you work
2. Follow the established format and categories
3. Be specific about what changed and where
4. Include file paths and line numbers for code changes
5. Link to issues or PRs when applicable
6. Move entries to a version section when releasing

## Links

- [Project Repository](https://github.com/allaunthefox/NoDupeLabs)
- [Documentation](Project_Plans/README.md)
- [Contributing Guidelines](Project_Plans/TODOS.md)
- [Architecture Overview](Project_Plans/Architecture/ARCHITECTURE.md)
