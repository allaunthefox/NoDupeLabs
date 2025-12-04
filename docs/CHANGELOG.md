# Changelog

All notable changes to this project will be documented in this file.

## 2025-12-03 — Documentation Improvements (Phase 1)

### Module Documentation

- **nodupe/cli.py**: Added comprehensive module docstring covering CLI architecture,
  plugin system, available commands, exit codes, and key features
- **nodupe/config.py**: Added detailed module docstring including all configuration
  presets, configuration keys, dependencies, and usage examples
- Added detailed function docstrings with Args/Returns sections to config module
- Fixed line length issues to comply with PEP 8 standards

### Documentation Review

- Conducted comprehensive audit of 50+ Python modules in nodupe package
- Identified 38 modules (76%) lacking module-level docstrings
- Created detailed documentation requirements roadmap (see DOCUMENTATION_TODO.md)
- Prioritized documentation work into 5 tiers based on criticality

### External Documentation

- Updated all documentation to use the `nodupe` command instead of `python -m nodupe.cli`
- Fixed Python version requirement (3.9+) across all documentation files
- Fixed duplicate lines and markdown formatting issues in AI_BACKEND.md
- Updated BEGINNERS_GUIDE.md, SIMILARITY.md with correct command syntax

### Repository

- Removed e621_downloader submodule from repository

### Next Steps

See docs/DOCUMENTATION_TODO.md for the complete documentation roadmap and
prioritized list of modules requiring documentation.

## 2025-12-03 — ci/fix-mypy-and-validate-job (merged via PR #2)

- scanner: threaded_hash now emits ETA/STALL messages when worker queues stall and supports a hard
  idle timeout (`max_idle_time`) to avoid hangs. Backwards-compatible alias `stalled_timeout` is
  supported. Added tests to validate timing/timeout behaviors.
- tests: added/updated unit tests for scanner timing, timeouts and progress messages; fixed importer
  locations for a few utils used by tests so CI collects and runs tests reliably.
- convert_videos: prefer internal ffmpeg helper at call-time so tests that monkeypatch the helper
  behave reliably.
- cli & commands: exported `check_scan_requirements` and made `validate_hash_algo` available from
  `nodupe.scanner` for tests and backwards compatibility.
- tooling & CI: vendoring helpers and offline validation flow improved; validate-vendored-install job
  was added and hardened to avoid failing in empty-vendor checkouts.

See PR #2 for details: https://github.com/allaunthefox/NoDupeLabs/pull/2
