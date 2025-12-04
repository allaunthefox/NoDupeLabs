# Changelog

All notable changes to this project will be documented in this file.

## 2025-12-03 — Documentation Updates & Repository Cleanup

- docs: Updated all documentation to use the `nodupe` command instead of `python -m nodupe.cli`
- docs: Fixed Python version requirement (3.9+) across all documentation
- docs: Fixed duplicate lines and markdown formatting issues in AI_BACKEND.md
- repo: Removed e621_downloader submodule from repository

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
