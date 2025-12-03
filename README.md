# NoDupeLabs

**Important!** NoDupeLabs was written by a combination of LLMs and should not be used on production unless you accept what that implies. It works for me, might not work for you. Might delete everything.

NoDupeLabs is a next-generation, context-aware system for cataloging, deduplicating, and organizing files. It builds upon the legacy of DeDupeLab with a completely refactored architecture, enhanced safety features, and environment-aware performance tuning.

It generates self-describing `meta.json` manifests for every folder so that archives remain readable and verifiable even without the original software.

---

## Overview

NoDupeLabs performs recursive directory scans, identifies unique files using configurable hashing (defaulting to SHA-512), and produces metadata that describes each folder’s structure, file types, and inferred categories.

Every directory receives a `meta.json` manifest that follows the `nodupe_meta_v1` schema. These manifests are meant to remain valid and machine-readable indefinitely.

---

## Features

### 🛡️ Enhanced Safety & Integrity
*   **Smart Metadata Updates**: Automatically skips writing `meta.json` if the content hasn't changed, preserving file modification timestamps.
*   **Read-Only Detection**: Proactively checks for read-only directories and files before attempting writes, preventing crash-loops on protected storage.
*   **Verification**: New `verify` command validates checkpoints against the current filesystem state to ensure data integrity before applying changes.

### 🚀 Environment Auto-Tuning
NoDupeLabs automatically detects your deployment environment and optimizes its configuration:
*   **Desktop**: Balances performance with system responsiveness.
*   **NAS**: Optimizes for network I/O and lower CPU availability.
*   **Cloud**: Maximizes throughput for high-speed VM storage.
*   **Container**: Uses conservative defaults for Docker/Kubernetes environments.

### 🔍 Advanced Detection
*   **Contextual Hashing**: Distinguishes between archived (inside zip/tar) and unarchived copies of the same file.
*   **Expanded MIME Support**: Native detection for modern formats like `.webp`, `.heic`, `.mkv`, and `.json`.
*   **NSFW Classification**: Multi-tier detection system (filename patterns, metadata analysis) to flag potential sensitive content.

### 📦 Smart Dependency Management
*   **Auto-Install**: Automatically detects and installs optional dependencies (like `psutil`, `tqdm`, `pillow`) at runtime if they are missing.
*   **Graceful Degradation**: If dependencies cannot be installed, the system falls back to standard library implementations without crashing.

---

## Installation

NoDupeLabs is designed to be installed as a Python package.

```bash
# Clone the repository
git clone https://github.com/allaunthefox/NoDupeLabs.git
cd NoDupeLabs

# Install in editable mode
pip install -e .
```

---

## Usage

### Scanning
The `scan` command walks through the specified directory, computes hashes, and generates validated metadata.

```bash
python3 -m nodupe.cli scan --root /path/to/data
```

### Planning & Deduplication
Generate a deduplication plan based on the scan results.

```bash
# 1. Generate a plan
python3 -m nodupe.cli plan --out plan.csv

# 2. Apply the plan (moves duplicates to a holding area)
python3 -m nodupe.cli apply --plan plan.csv --checkpoint output/checkpoints/checkpoint_latest.json
```

### Verification
Verify that a checkpoint matches the current state of the filesystem.

```bash
python3 -m nodupe.cli verify --checkpoint output/checkpoints/checkpoint_latest.json
```

### Rollback
Undo a deduplication operation using the checkpoint file.

```bash
python3 -m nodupe.cli rollback --checkpoint output/checkpoints/checkpoint_latest.json
```

---

## Configuration

Configuration is handled via `nodupe.yml`. If it doesn't exist, a default one is generated on the first run.

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

## License

NoDupeLabs is distributed under the Apache License 2.0.

```text
SPDX-License-Identifier: Apache-2.0
Copyright (c) 2025 Allaun
```
