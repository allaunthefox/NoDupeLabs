# NoDupeLabs

**New to NoDupeLabs?** Check out the [Beginner's Guide](docs/BEGINNERS_GUIDE.md) for step-by-step instructions!

**Important!** NoDupeLabs was written by a combination of LLMs and should not be used on production unless you accept what that implies. It works for me, might not work for you. Might delete everything.

NoDupeLabs is a next-generation, context-aware system for cataloging, deduplicating, and organizing files. It is designed with enhanced safety features and environment-aware performance tuning.

It generates self-describing `meta.json` manifests for every folder so that archives remain readable and verifiable even without the original software.

---

## Overview

NoDupeLabs scans directories recursively, computes content hashes using a configurable hashing algorithm (default: SHA-512), and generates self-describing metadata that captures each folder’s structure, file types, inferred categories, and optional context tags.

Each scanned directory receives a `meta.json` manifest conforming to the `nodupe_meta_v1` schema. These manifests are designed to be stable, machine-readable, and long-lived so archives remain verifiable even without the original toolset.

---

## Features

### 🛡️ Enhanced Safety & Integrity

* **Smart Metadata Updates**: Automatically skips writing `meta.json` if the content hasn't changed, preserving file modification timestamps.
* **Read-Only Detection**: Proactively checks for read-only directories and files before attempting writes, preventing crash-loops on protected storage.
* **Verification**: New `verify` command validates checkpoints against the current filesystem state to ensure data integrity before applying changes.

### 🚀 Environment Auto-Tuning

NoDupeLabs automatically detects your deployment environment and optimizes its configuration:

* **Desktop**: Balances performance with system responsiveness.
* **NAS**: Optimizes for network I/O and lower CPU availability.
* **Cloud**: Maximizes throughput for high-speed VM storage.
* **Container**: Uses conservative defaults for Docker/Kubernetes environments.

### 🔍 Advanced Detection

* **Contextual Hashing**: Distinguishes between archived (inside zip/tar) and unarchived copies of the same file.
* **Expanded MIME Support**: Native detection for modern formats like `.webp`, `.heic`, `.mkv`, and `.json`.
* **NSFW Classification**: Multi-tier detection system (filename patterns, metadata analysis) to flag potential sensitive content.

### Video handling and file formats

NoDupe now supports basic video identification by extracting a representative frame and computing embeddings on that frame. Extracted frames are saved as standard JPEG files and include a human-readable JSON sidecar (same base filename with a .json suffix) containing source path and extraction metadata.

Index files can be persisted in human-readable formats so they can be inspected or processed by plain text tools or an LLM. Supported index formats include:

* `.npz` (numpy compressed) — compact binary format
* `.json` — full JSON object with `dim`, `ids`, and `vectors` entries
* `.jsonl` — JSON lines, one entry per id/vector pair (easy to stream/process)

When converting video files, the project uses widely supported codecs/containers by default, for example:

* MP4 -> H.264 (libx264) + AAC audio
* WebM -> VP9 (libvpx-vp9) + Opus audio
* MKV -> H.264 (libx264) + AAC audio
* AVI -> MPEG4

These formats are chosen for compatibility with common desktop tools and text-based tooling for metadata.

Schema & spec files
-------------------

If you want to validate or inspect the exact format, NoDupe includes JSON Schema files under `nodupe/schemas/`:

* `nodupe/schemas/index.json.schema` — schema for `.json` index files
* `nodupe/schemas/index.jsonl.schema` — schema for each line in `.jsonl` files

The JSONL format follows the industry-standard JSON Lines / NDJSON format (see <https://jsonlines.org/>).

### 📦 Smart Dependency Management

* **Auto-Install**: Automatically detects and installs optional dependencies (like `psutil`, `pillow`) at runtime if they are missing.
* **Graceful Degradation**: If dependencies cannot be installed, the system falls back to standard library implementations without crashing.

### ✨ Code Quality & Reliability

NoDupeLabs enforces automated quality checks so the codebase remains correct
and maintainable across changes:

- **Type-checked**: The project uses mypy for static type checking on
  production code (configured in `pyproject.toml` and run in CI).
- **Docstring coverage**: Docstring coverage is enforced in CI using
  `interrogate` (configured with a high coverage threshold).
- **Style / linting**: PEP 8 checks run with `flake8` as part of CI.
- **Python compatibility**: Requires Python 3.9+ (see `pyproject.toml`).
- **Automated tests**: A comprehensive test suite (unit/integration/slow
  markers) runs on CI to help prevent regressions.
- **CI/CD Quality Gates**: flake8, mypy, docstring coverage and pytest are
  run automatically on pushes and pull requests.

---

## Installation

NoDupeLabs is designed to be installed as a Python package. Follow these clear, reproducible steps:

### Standard Installation

```bash
# 1. Clone the repository
git clone https://github.com/allaunthefox/NoDupeLabs.git
cd NoDupeLabs

# 2. Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# 3. Install in editable mode
pip install -e .
```

### Verify Installation

```bash
# Check that NoDupeLabs is installed correctly
nodupe --help

# You should see the help output with available commands
```

### Minimal/Offline Operation

NoDupeLabs includes vendored copies of essential libraries (`PyYAML`) in `nodupe/vendor/libs`. If the system Python environment lacks these dependencies, the application will automatically use the bundled versions, ensuring basic functionality works out-of-the-box.

#### Offline Installation Steps

```bash
# 1. Install all vendored wheels (includes PyYAML, etc.)
python scripts/install_vendored_wheels.py

# 2. Install specific vendored wheel (e.g., onnxruntime for AI features)
python scripts/install_vendored_wheels.py --pattern onnxruntime

# 3. Alternatively, use pip directly with vendored wheels
python -m pip install --no-index --find-links nodupe/vendor/libs onnxruntime
```

### Development Installation

For contributors who want to work on NoDupeLabs:

```bash
# 1. Clone the repository
git clone https://github.com/allaunthefox/NoDupeLabs.git
cd NoDupeLabs

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install development dependencies
pip install -r dev-requirements.txt

# 4. Install NoDupeLabs in editable mode
pip install -e .

# 5. Verify development setup
make test  # Run fast tests
make lint  # Check code style
```

---

## Command Reference

### `init`

Initialize the configuration file (`nodupe.yml`) with a specific preset.

```bash
nodupe init [--preset default|performance|paranoid|media|ebooks|audiobooks|archives] [--force]
```

* `--preset`: Choose a configuration profile:
  * `default`: Balanced settings (SHA-512, safe defaults).
  * `performance`: Faster hashing (BLAKE2b), less logging, validation disabled.
  * `paranoid`: Maximum safety (SHA-512, strict validation, dry-run enabled).
  * `media`: Optimized for images/video (BLAKE2b, AI enabled, larger similarity index).
  * `ebooks`: Optimized for text/PDFs (SHA-256, AI disabled, pretty metadata).
  * `audiobooks`: Optimized for audio collections (BLAKE2b, AI disabled, extra ignore patterns).
  * `archives`: Optimized for long-term storage (SHA-512, debug logging).
* `--force`: Overwrite existing configuration file.

### `scan`

Walks through specified directories, computes hashes, and populates the database.

* **Incremental Scanning**: Automatically skips re-hashing files that haven't changed (based on size and modification time) since the last scan.
* **Pre-flight Checks**: Verifies input readability and output writability before starting.

```bash
nodupe scan --root /path/to/data [--root /another/path]
```

* `--root`: Directory to scan. Can be specified multiple times.

### `plan`

Analyzes the database for duplicates and generates a CSV action plan.

* **Strategy**: By default, keeps the first file found and marks others for moving to a `.nodupe_duplicates` folder.

```bash
nodupe plan --out plan.csv
```

* `--out`: Path to save the generated CSV plan.

### `apply`

Executes the actions defined in a plan CSV.

* **Safety**: Creates a checkpoint file before moving any files, allowing for rollback.

```bash
nodupe apply --plan plan.csv --checkpoint output/checkpoints/chk_01.json [--force]
```

* `--plan`: Path to the CSV plan generated by `plan`.
* `--checkpoint`: Path to save the rollback checkpoint.
* `--force`: Execute changes immediately (disables dry-run mode).

### `verify`

Validates a checkpoint file against the current filesystem state.

* Ensures that files listed in the checkpoint still exist and haven't been modified before attempting a rollback.

```bash
nodupe verify --checkpoint output/checkpoints/chk_01.json
```

### `rollback`

Undoes a previous `apply` operation using its checkpoint file.

* Moves files back to their original locations.

```bash
nodupe rollback --checkpoint output/checkpoints/chk_01.json
```

### `similarity`

Tools for finding near-duplicates (e.g., resized images) using vector embeddings.

#### `build`

Creates a similarity index from the database.

```bash
nodupe similarity build --out index.npz (or .json/.jsonl) [--dim 16]
```

#### `update`

Incrementally updates an existing index with new files from the database.

```bash
nodupe similarity update --index-file index.npz|index.json|index.jsonl [--rebuild]
```

* `--index-file`: Path to the existing index.
* `--rebuild`: Completely rebuild the index from the DB, removing stale entries.

#### `query`

Finds files similar to a target file.

```bash
nodupe similarity query target.jpg --index-file index.npz|index.json|index.jsonl [-k 5]
```

### `archive`

Utilities for inspecting archive files (zip, tar, etc.) without extracting them.

```bash
nodupe archive list file.zip
nodupe archive extract file.zip --dest /tmp/out
```

### `mount`

Mounts the NoDupeLabs database as a read-only FUSE filesystem (Linux only).

* Allows browsing files by hash, size, or type.

```bash
nodupe mount /mnt/nodupe
```

---

## Configuration

Configuration is handled via `nodupe.yml`. If it doesn't exist, a default one is generated on the first run. Key settings include:

* `db_path`: Location of the SQLite database (default: `output/index.db`).
* `log_dir`: Directory for logs (default: `output/logs`).
* `parallelism`: Number of threads for scanning (0 = auto).
* `ignore_patterns`: List of file/folder patterns to skip (e.g., `.git`, `node_modules`).
* `ai`: Settings for the optional AI backend (ONNX/PyTorch).

```yaml
hash_algo: sha512
dedup_strategy: content_hash
parallelism: 0  # 0 = auto-detect based on environment
dry_run: true
nsfw:
  enabled: false
  threshold: 2
```

---

## Metadata Format

Every directory receives a `meta.json` file describing its contents.

```json
{
  "spec": "nodupe_meta_v1",
  "generated_at": "2025-12-02T12:00:00Z",
  "summary": {
    "files_total": 15,
    "bytes_total": 10485760,
    "categories": {"image": 10, "text": 5},
    "topics": ["vacation", "beach"],
    "keywords": ["2025", "summer"]
  },
  "entries": [
    {
      "name": "photo.jpg",
      "size": 204800,
      "mtime": 1730090400,
      "file_hash": "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e",
      "hash_algo": "sha512",
      "mime": "image/jpeg",
      "category": "image",
      "subtype": "photo",
      "topic": "vacation"
    }
  ]
}
```

---

## Development & Testing

### Quality Tools

NoDupeLabs maintains high code quality standards with automated checks:

```bash
# Linting (PEP 8 compliance)
flake8 nodupe/

# Type checking (Python 3.9+ compatible)
mypy nodupe/

# Docstring coverage (enforced at 100% in CI; configured in pyproject.toml)
interrogate -vv nodupe/ --fail-under 100

# Run tests
pytest tests/ -v

# Run only fast tests (skip slow/integration)
pytest tests/ -v -m "not slow and not integration"
```

### Tool Configuration

All quality tools are configured in `pyproject.toml`:

* **MyPy**: Type checking with Python 3.9 baseline
* **Pytest**: Test markers for unit/integration/slow tests
* **Interrogate**: Docstring coverage enforced (threshold configured in pyproject.toml / CI)
* **Flake8**: PEP 8 compliance (configured in `.flake8`)

### Continuous Integration

Quality checks run automatically on every commit:

* Flake8 linting (must pass)
* MyPy type checking (must pass)
* Interrogate docstring coverage (100% required — enforced in CI)
* Test suite (comprehensive tests covering unit, integration and slow markers; run by CI)

See [.github/workflows/ci.yml](.github/workflows/ci.yml) for details.

---

## Troubleshooting

### Common Issues and Solutions

#### Installation Problems

**Issue**: `pip install -e .` fails with dependency errors

**Solution**:
```bash
# Ensure you have the latest pip and setuptools
pip install --upgrade pip setuptools

# Install dependencies manually first
pip install PyYAML xxhash zstandard py7zr rarfile jsonschema

# Then install NoDupeLabs
pip install -e .
```

**Issue**: Missing optional dependencies (e.g., `pillow`, `psutil`)

**Solution**:
```bash
# Install optional dependencies
pip install pillow psutil

# Or use the development requirements
pip install -r dev-requirements.txt
```

#### Command Execution Issues

**Issue**: `nodupe: command not found`

**Solution**:
```bash
# Ensure you're using the virtual environment
source .venv/bin/activate

# Check Python path
python -c "import nodupe; print(nodupe.__file__)"

# Try running directly with Python
python -m nodupe.cli --help
```

**Issue**: Permission denied errors

**Solution**:
```bash
# Check directory permissions
ls -la /path/to/your/directory

# Fix permissions if needed
chmod -R u+rw /path/to/your/directory
```

#### Scanning Problems

**Issue**: Scanner hangs or is very slow

**Solution**:
```bash
# Reduce parallelism
nodupe scan --root /path/to/data --parallelism 2

# Increase timeout settings
# Edit nodupe.yml and set:
# heartbeat_interval: 30
# stall_timeout: 600
# max_idle_time: 120
```

**Issue**: Files not being detected or processed

**Solution**:
```bash
# Check ignore patterns
cat nodupe.yml | grep ignore_patterns

# Temporarily disable ignore patterns
nodupe scan --root /path/to/data --ignore-patterns ""
```

#### Database Issues

**Issue**: Database corruption or errors

**Solution**:
```bash
# Backup existing database
cp output/index.db output/index.db.backup

# Delete and recreate database
rm output/index.db
nodupe scan --root /path/to/data
```

**Issue**: Database locked errors

**Solution**:
```bash
# Ensure no other NoDupeLabs processes are running
ps aux | grep nodupe

# Wait for processes to complete or kill them
# pkill -f nodupe

# Try again with reduced parallelism
nodupe scan --root /path/to/data --parallelism 1
```

#### AI/Similarity Features

**Issue**: AI backend not available

**Solution**:
```bash
# Install ONNX runtime
pip install onnxruntime

# Or use CPU backend (slower but works without ONNX)
# Edit nodupe.yml and set:
# ai:
#   backend: cpu
```

**Issue**: Similarity search not working

**Solution**:
```bash
# Ensure you have built the similarity index
nodupe similarity build --out index.npz

# Check that the index file exists
ls -la index.npz

# Try with different backend
nodupe similarity build --out index.json
```

### Debugging Techniques

#### Enable Verbose Logging

```bash
# Set environment variable for debug logging
export NO_DUPE_DEBUG=1

# Run command with verbose output
nodupe scan --root /path/to/data --verbose
```

#### Check Configuration

```bash
# View current configuration
cat nodupe.yml

# Reset to default configuration
rm nodupe.yml
nodupe init --preset default
```

#### Manual Database Inspection

```bash
# Connect to SQLite database
sqlite3 output/index.db

# Check tables
.tables

# Query files
SELECT * FROM files LIMIT 10;

# Check schema
.schema files
```

### Getting Help

If you encounter issues not covered here:

1. **Check logs**: Look in `output/logs/` for detailed error information
2. **Review documentation**: Consult the [Beginner's Guide](docs/BEGINNERS_GUIDE.md)
3. **Search issues**: Check GitHub issues for similar problems
4. **Create issue**: Open a new GitHub issue with detailed information

When reporting issues, please include:
- NoDupeLabs version (`nodupe --version`)
- Python version (`python --version`)
- Operating system and version
- Exact command you ran
- Full error message or stack trace
- Relevant log files

## License

NoDupeLabs is distributed under the Apache License 2.0.

```text
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 Allaun
```
