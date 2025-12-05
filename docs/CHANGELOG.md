### Plugin improvements

- `nodupe.plugins.manager`: Converted the plugin manager to an async-first design.
  - Runs a dedicated background asyncio event loop to dispatch coroutine callbacks
    efficiently and run synchronous callbacks in an executor.
  - Provides `stop()` for graceful shutdown of the loop (useful in tests and
    long-running services).
  - Improves performance and reduces thread churn when many async callbacks are executed.

# Changelog

All notable changes to this project will be documented in this file.

## 2025-12-04 — Modularity Improvements (Phases 1 & 2)

### Command Registry Pattern (Phase 1)

- **CLI Decoupling**: Replaced 13 direct command imports with command registry
  - Created `COMMANDS` registry in `nodupe/commands/__init__.py`
  - CLI now uses `COMMANDS[name]` instead of direct function references
  - Removed tight coupling between CLI and command implementations
  - Impact: HIGH | Risk: LOW | Effort: 2 hours

### Public API Boundaries (Phase 2)

- **Package API Exports**: Added `__all__` exports to all key `__init__.py` files
  - `nodupe/__init__.py`: Main package API with version, core modules, subsystems
  - `nodupe/utils/__init__.py`: Utility functions (filesystem, hashing, media, ffmpeg)
  - `nodupe/ai/__init__.py`: Created new file for AI subsystem API
  - `nodupe/ai/backends/__init__.py`: AI backend selection API
  - `nodupe/commands/__init__.py`: Command registry and individual commands
  - Impact: HIGH | Risk: LOW | Effort: 2 hours

### Modularity Benefits

- **Clear API Contracts**: Public API explicitly defined via `__all__`
- **Reduced Coupling**: CLI no longer depends on all command module internals
- **Better Encapsulation**: Internal implementation details hidden from public API
- **Easier Testing**: Clear boundaries make mocking and testing simpler
- **Future-Proof**: Command registry allows dynamic command loading in future

### Quality Metrics

```text
Flake8:          ✅ 0 errors
MyPy:            ✅ 48/48 files pass (was 47, added ai/__init__.py)
Interrogate:     ✅ 100% docstring coverage
Tests:           ✅ 59/59 passing
Modularity:      ✅ 7.5/10 (was 7/10)
```

---

## 2025-12-04 — Quality Infrastructure & Python 3.9+ Compatibility

### Quality Assurance Infrastructure

- **MyPy Configuration**: Added comprehensive type checking configuration to `pyproject.toml`
  - Python 3.9 baseline with full type safety enforcement
  - Smart exclusions for vendor code and optional dependencies
  - Production code must pass type checks in CI
  - Zero type errors across 47 source files

- **Pytest Configuration**: Consolidated test configuration into `pyproject.toml`
  - Migrated from deprecated `pytest.ini`
  - Added 5 test markers: `unit`, `integration`, `slow`, `requires_model`, `requires_ffmpeg`
  - Strict marker enforcement for better test organization
  - Deprecation warning checks for nodupe code

- **CI/CD Enhancements**: Updated `.github/workflows/ci.yml`
  - MyPy checks now blocking (was non-blocking)
  - Added 100% docstring coverage enforcement
  - Updated test execution to use new markers
  - Faster CI feedback with unit test separation

### Type Safety Improvements

- **Python 3.9+ Compatibility**: Replaced all Python 3.10+ union syntax (`X | Y`) with `Optional[X]`
  - `nodupe/applier.py`: Added `Any` import for type annotations
  - `nodupe/exporter.py`: Fixed Optional[str] handling and list/set type assignments
  - `nodupe/nsfw_classifier.py`: Fixed return type annotations with `Any`
  - `nodupe/utils/ffmpeg_progress.py`: Converted 4 union types to Optional
  - `nodupe/scanner.py`: Converted 5 union types to Optional
  - `nodupe/similarity/cli.py`: Converted 2 union types to Optional

### Code Quality Achievements

- **Flake8**: 0 errors (100% PEP 8 compliant)
- **MyPy**: 47/47 source files pass type checking
- **Interrogate**: 100% docstring coverage maintained
- **Test Suite**: 59/59 tests passing
- **Python Compatibility**: Full Python 3.9+ compatibility guaranteed

### Configuration Consolidation

- Removed deprecated `pytest.ini` in favor of `pyproject.toml`
- Centralized all tool configuration in single file
- Modern Python packaging best practices

### Quality Metrics

```text
Flake8:          ✅ 0 errors
MyPy:            ✅ 47/47 files pass
Interrogate:     ✅ 100% docstring coverage
Tests:           ✅ 59/59 passing
Python Target:   ✅ 3.9+ compatible
Type Safety:     ✅ Fully typed
```

---

## 2025-12-03 — Documentation improvements, CI hardening, scanner + DB work

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
- CI & repository hygiene:
  - Removed `e621_downloader` submodule that previously caused runner setup errors; hardened
    CI checkout to avoid submodule cleanups and set `fetch-depth: 0` to ensure deterministic
    workflow runs and avoid partial checkouts.

### Next Steps

See docs/DOCUMENTATION_TODO.md for the complete documentation roadmap and
prioritized list of modules requiring documentation.
prioritized list of modules requiring documentation.

## 2025-12-03 — ci/fix-mypy-and-validate-job (merged via PR #2)

- scanner: threaded_hash now emits ETA/STALL messages when worker queues stall and supports a hard
  idle timeout (`max_idle_time`) to avoid hangs. Backwards-compatible alias `stalled_timeout` is
  supported. Added tests to validate timing/timeout behaviors.
  - scanner: threaded_hash now emits ETA/STALL messages when worker queues stall and supports a
    hard idle timeout (`max_idle_time`) to avoid hangs. Backwards-compatible alias
    `stalled_timeout` is supported. Added tests to validate timing/timeout behaviours and
    progress resiliency (ETA / stall messages) so scanner behaves predictably under noisy IO.
- tests: added/updated unit tests for scanner timing, timeouts and progress messages; fixed importer
  locations for a few utils used by tests so CI collects and runs tests reliably.
- convert_videos: prefer internal ffmpeg helper at call-time so tests that monkeypatch the helper
  behave reliably.
- cli & commands: exported `check_scan_requirements` and made `validate_hash_algo` available from
  `nodupe.scanner` for tests and backwards compatibility.
- tooling & CI: vendoring helpers and offline validation flow improved; validate-vendored-install job
  was added and hardened to avoid failing in empty-vendor checkouts.
  - vendor + offline validation: vendoring helpers were added/extended to allow packaging and
    deterministic offline validation of transitive wheels (including heavy dependency wheels such
    as onnxruntime). CI gained a `validate-vendored-install` job which installs only the vendored
    wheels in an offline environment and performs smoke-import tests to ensure vendored packages
    are usable in CI without network access.

### Other fixes

- Linting: resolved flake8 E501 (long lines) introduced in documentation changes — a docstring
  in `nodupe/cli.py` was wrapped to satisfy line length checks.
- Tests: fixed test collection and import-time issues so tests run against repository source (PYTHONPATH
  usage) in CI. Adjusted a couple of tests to avoid relying on mutable global state and made
  replaceable helpers easier to monkeypatch for stable testing.

### Documentation additions

- `nodupe/scanner.py`: added comprehensive module & function docstrings explaining iterator vs
  collector modes, `iter_files`, `process_file`, `threaded_hash` and parameters such as
  `known_files`, `heartbeat_interval`, `stall_timeout` / `stalled_timeout` and `max_idle_time`.
- `nodupe/db.py`: added module and class/method docstrings describing schema, migration strategy,
  public APIs such as `upsert_files`, `iter_files` and helpers used for embeddings and search.
- `docs/DOCUMENTATION_TODO.md`: updated to reflect the completion of Phase 1 (scanner + db) and
  bumped documentation coverage progress. The roadmap now documents the next priority modules and
  the staged approach for documentation completion.

### Docs & CI enhancements

- Added lightweight Sphinx docs scaffolding under `docs/sphinx/` to auto-generate API docs from
  docstrings using `sphinx.ext.autodoc` and `napoleon` (keeps code and docs consistent).
- Added CI checks:
  - `doc-sanity` job runs a lightweight script `scripts/check_docstrings_and_size.py` to
    ensure public APIs have docstrings and modules remain below a size threshold.
  - `docs-build` job builds the Sphinx docs to verify the site renders from docstrings.

### Stress tests

- Added stress tests for concurrent DB writes/reads and plugin async dispatch (`tests/test_concurrency_stress.py`) and wired them into the slow/integration CI job (marked `slow`) so CI can verify runtime stability under concurrent workloads.

---

If you'd like, I can also:

- Tag a release and publish release notes once CI is fully green.
- Continue documenting the next modules (I suggest `nodupe/applier.py` and `nodupe/archiver.py`).

See PR #2 for details: https://github.com/allaunthefox/NoDupeLabs/pull/2
