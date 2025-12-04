# Changelog

All notable changes to this project will be documented in this file.

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

---

If you'd like, I can also:

- Tag a release and publish release notes once CI is fully green.
- Continue documenting the next modules (I suggest `nodupe/applier.py` and `nodupe/archiver.py`).

See PR #2 for details: https://github.com/allaunthefox/NoDupeLabs/pull/2
