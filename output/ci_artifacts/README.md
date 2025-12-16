<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright (c) 2025 Allaun -->

# NoDupeLabs

>**A Modern, Modular, and Robust File Deduplication and Organization Framework.**

![Status](https://img.shields.io/badge/Status-Active-success)
![Completion](https://img.shields.io/badge/Completion-95%25-green)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-Apache--2.0-blue)
![Pylint](https://img.shields.io/badge/Pylint-9.97%2F10.0-brightgreen)
![Type Safety](https://img.shields.io/badge/Type%20Safety-Pylance%20Clean-success)
![Tests](https://img.shields.io/badge/Tests-144%20Passing-brightgreen)
![Coverage](https://img.shields.io/badge/Coverage-31%25-yellow)

NoDupeLabs is a sophisticated tool for scanning, analyzing, and organizing large file collections. It detects duplicates, identifies near-matches using vector similarity, and helps you clean up your digital life with confidence.

## 🎉 What's New (December 2025)

### Recent Updates - December 15, 2025

- ✅ **Type Safety Improvements**: Fixed all Pylance type checking errors
  - Enhanced type annotations in database indexing module
  - Improved type casting in plugin compatibility system
  - Better type inference for complex data structures
  - Zero Pylance errors across the codebase

### Recent Updates - December 14, 2025

- ✅ **Unified Core Loader**: Refactored main entry point for better modularity
- ✅ **Similarity System**: Fully integrated BruteForce backend with CLI
- ✅ **Plan Command**: Complete implementation of duplicate planning system
- ✅ **Verify Command**: Comprehensive file and database integrity verification

## 🚀 Status: 100% Core Complete

The Core Refactor is complete. The system is robust, modular, and ready for use.

-**Core System**: ✅ 100% (Loader, Configuration, DI, Logging)
-**Core Utilities**: ✅ 100% (13/13 modules fully implemented)
-**Scanning**: ✅ 100% (FileWalker, FileProcessor, FileHasher, ProgressTracker, HashAutotuner)
-**Database**: ✅ 100% (CRUD, Schema, Transactions, Indexing, Repository - ALL COMPLETE)
-**Similarity**: ✅ 100% (Vector-based backend & CLI)
-**Planning**: ✅ 100% (Duplicate detection & resolution strategies)
-**Plugins**: ✅ 100% (Isolated, secure, auto-discovering)
-**Commands**: ✅ 100% (Scan, Apply, Plan, Similarity, Verify, Version all implemented)
-**Testing**: ⚠️ 31% coverage (144 tests collected, 134+ passing, target: 60%+)

## ✨ Key Features

-**Blazing Fast Scanning**: optimized file walker with multiple hashing algorithms (MD5, SHA256, SHAKE, BLAKE2, xxHash, etc.) with automatic algorithm selection.
-**Smart Duplicate Detection**: Not just exact matches—finds similar images and files using vector embeddings.
-**Safe & Secure**: "Plan First, Apply Later" philosophy. No files are deleted without your explicit approval.
-**Plugin Architecture**: Hard isolation ensures a crashing plugin never takes down the main app.
-**Modern Stack**: Built with Python 3.9+, Type Hinting, TOML configuration, and SQLite.
-**Hash Algorithm Autotuning**: Automatically selects the optimal hash algorithm based on system characteristics and performance benchmarks.
-**File Integrity Verification**: Comprehensive verification system to ensure file and database consistency.

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/NoDupeLabs.git
cd NoDupeLabs

# Install dependencies
pip install -r requirements.txt
```

## 🛠️ Usage

### 1. Initialize

Set up your configuration and database.

```bash
python -m nodupe.core.main init
```

### 2. Scan

Scan a directory to build the file index.

```bash
python -m nodupe.core.main scan /path/to/your/files
```

### 3. Plan

Analyze the index to find duplicates and generate a plan.

```bash
python -m nodupe.core.main plan
```

### 4. Verify

Verify file integrity and database consistency with detailed output.

```bash
python -m nodupe.core.main verify --mode all --output verification_report.json
```

### 5. Similarity Support

Find near-duplicates (images/text).

```bash
python -m nodupe.core.main similarity --backend bruteforce
```

### 6. Apply

Execute the generated plan (move/delete duplicates).

```bash
python -m nodupe.core.main apply plan_timestamp.json
```

### 7. Version

Show version information.

```bash
python -m nodupe.core.main version
```

## 📚 Documentation

- [Project Summary](PROJECT_SUMMARY.md): Current status and overview
- [Changelog](CHANGELOG.md): Detailed history of changes and releases
- [Architecture](Project_Plans/Architecture/ARCHITECTURE.md): Deep dive into the system design
- [Roadmap](Project_Plans/Implementation/ROADMAP.md): Future plans and remaining tasks
- [TODO List](Project_Plans/TODOS.md): Comprehensive task list with priorities
- [Quality Plan](Project_Plans/Quality/IMPROVEMENT_PLAN.md): Quality improvement roadmap

## 🤝 Contributing

Contributions are welcome! Please see [Project_Plans/TODOS.md](Project_Plans/TODOS.md) for a list of prioritized tasks.

## 🔄 CI/CD Pipeline

The project includes a comprehensive automated CI/CD pipeline:

-**Automated Testing**: Runs on Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, and 3.14
-**Code Quality**: Pylint, mypy type checking, black formatting, isort import sorting
-**Coverage Reporting**: pytest with XML, HTML, and terminal coverage reports
-**Security Scanning**: Automated security checks with bandit and safety
-**Dependency Management**: Automated dependency updates via Dependabot
-**Codecov Integration**: Coverage reports uploaded to Codecov for tracking

The pipeline runs automatically on every push and pull request to ensure code quality and test coverage standards are maintained.
