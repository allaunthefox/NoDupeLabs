# NoDupeLabs Module Specifications

This document provides detailed technical specifications for each module in the `nodupe` package. It is designed to assist in the reassembly, maintenance, or isolated usage of individual components.

---

## 1. `applier.py`
**Purpose**: Executes the physical file operations defined in a deduplication plan.
**Key Features**:
- **Three-Phase Commit**: Validates all moves (Prepare), executes them (Execute), and saves a checkpoint (Commit).
- **Safety Checks**: Verifies source existence and destination vacancy before moving.
- **Checkpointing**: Generates a JSON manifest of all moves to enable rollback.
**Dependencies**: `shutil`, `json`, `pathlib`.

## 2. `archiver.py`
**Purpose**: Abstraction layer for handling various archive formats.
**Key Features**:
- **Unified Interface**: `ArchiveHandler` class provides a consistent API for Zip, Tar, 7z, RAR, etc.
- **Optional Dependencies**: Gracefully handles missing libraries (`py7zr`, `rarfile`, `zstandard`).
- **Content Listing**: Can list contents of archives without full extraction (where supported).
**Dependencies**: `zipfile`, `tarfile`, `gzip`, `bz2`, `lzma`. Optional: `py7zr`, `rarfile`, `zstandard`.

## 3. `bootstrap.py`
**Purpose**: Self-validation and integrity checking.
**Key Features**:
- **Lint Tree**: `lint_tree()` compiles all Python files in the package to catch syntax errors at startup.
**Dependencies**: `pathlib`.

## 4. `categorizer.py`
**Purpose**: Classifies files into high-level categories (Image, Video, Archive, Text) based on MIME type and extension.
**Key Features**:
- **Deterministic**: Pure function `categorize_file(mime, name)` returns category, subtype, and topic.
- **Fallback**: Defaults to "other/unknown" for unrecognized types.
**Dependencies**: None (Pure Python).

## 5. `cli.py`
**Purpose**: The command-line entry point for the application.
**Key Features**:
- **Command Dispatch**: Handles `scan`, `plan`, `apply`, `verify`, `rollback` subcommands.
- **Orchestration**: Glues together the scanner, database, and exporter modules.
- **Error Handling**: Catches top-level exceptions and ensures clean exit codes.
**Dependencies**: `argparse`, `sys`, `json`, `pathlib`, and all other internal modules.

## 6. `config.py`
**Purpose**: Configuration management.
**Key Features**:
- **YAML/JSON Support**: Uses `PyYAML` if available, falls back to a JSON shim.
- **Defaults**: Contains the `DEFAULTS` dictionary defining the system's baseline behavior.
- **Auto-Generation**: Creates `nodupe.yml` if missing.
**Dependencies**: `yaml` (optional), `json`, `pathlib`.

## 7. `db.py`
**Purpose**: Persistence layer for the file index.
**Key Features**:
- **SQLite Backend**: Uses a local `index.db` file.
- **Schema Management**: Automatically initializes and migrates the database schema (e.g., adding `permissions` column).
- **Upsert Logic**: Efficiently inserts or updates file records using `ON CONFLICT` clauses.
**Dependencies**: `sqlite3`, `textwrap`, `pathlib`.

## 8. `deps.py`
**Purpose**: Runtime dependency management.
**Key Features**:
- **Graceful Degradation**: Allows the system to run with reduced functionality if libraries (like `pandas` or `pillow`) are missing.
- **Auto-Install**: Can attempt to `pip install` missing optional dependencies at runtime.
**Dependencies**: `subprocess`, `importlib`.

## 9. `environment.py`
**Purpose**: Environment-aware performance tuning.
**Key Features**:
- **Detection**: Identifies if running in a Container, Cloud VM, NAS, or Desktop.
- **Optimization**: Adjusts parallelism, I/O buffer sizes, and logging verbosity based on the detected environment.
**Dependencies**: `platform`, `os`, `pathlib`.

## 10. `exporter.py`
**Purpose**: Generates metadata manifests (`meta.json`).
**Key Features**:
- **Schema Compliance**: Produces JSON matching `nodupe_meta_v1`.
- **Safety**: Checks for read-only filesystems before writing.
- **Idempotency**: Skips writing if the metadata hasn't changed to preserve mtime.
**Dependencies**: `json`, `pathlib`, `collections`.

## 11. `logger.py`
**Purpose**: Structured logging.
**Key Features**:
- **JSONL Format**: Logs events as newline-delimited JSON objects for easy parsing.
- **Rotation**: Automatically rotates logs based on size (`rotate_mb`).
**Dependencies**: `json`, `pathlib`, `datetime`.

## 12. `metrics.py`
**Purpose**: Telemetry and statistics.
**Key Features**:
- **Tracking**: Records files scanned, bytes processed, and operation durations.
- **Persistence**: Saves metrics to `metrics.json`.
**Dependencies**: `json`, `pathlib`, `datetime`.

## 13. `nsfw_classifier.py`
**Purpose**: Content safety analysis.
**Key Features**:
- **Multi-Tier Detection**: Uses filename keywords (Tier 1) and image analysis (Tier 2, via Pillow).
- **Privacy**: Runs entirely offline.
- **ML Backend**: Optional Tier-3 ML inference via ONNX Runtime with a CPU fallback; place runtime model files under `nodupe/models/`.
**Dependencies**: `re`, `pathlib`. Optional: `Pillow`.

## 14. `planner.py`
**Purpose**: Decision engine for deduplication.
**Key Features**:
- **CSV Generation**: Outputs a human-readable plan (`src`, `dst`, `op`, `reason`).
- **Conflict Resolution**: `ensure_unique()` handles filename collisions during moves.
**Dependencies**: `csv`, `pathlib`.

## 15. `rollback.py`
**Purpose**: Disaster recovery.
**Key Features**:
- **Reverse Operation**: Reads a checkpoint JSON and moves files back to their original locations.
- **Validation**: Ensures the target location is free before restoring.
**Dependencies**: `shutil`, `json`, `pathlib`.

## 16. `scanner.py`
**Purpose**: File discovery and hashing.
**Key Features**:
- **Robust Traversal**: Uses `os.walk` with error handling for network drives and symlinks.
- **Threading**: Parallel hashing using `ThreadPoolExecutor`.
- **Context Awareness**: Detects if files are inside archives or temporary folders.
- **Permission Tracking**: Captures file permissions (ACLs).
**Dependencies**: `os`, `hashlib`, `concurrent.futures`, `mimetypes`.

## 17. `validator.py`
**Purpose**: Data integrity verification.
**Key Features**:
- **Schema Validation**: Uses `jsonschema` if available, falls back to manual assertions.
- **Spec Enforcement**: Ensures `meta.json` files meet the version 1 specification.
**Dependencies**: `json`, `pathlib`. Optional: `jsonschema`.
