# NoDupeLabs Beginner's Guide

This guide provides clear, step-by-step instructions for beginners to set up and use NoDupeLabs effectively.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Your First Scan](#your-first-scan)
- [Finding Duplicates](#finding-duplicates)
- [Removing Duplicates](#removing-duplicates)
- [Undo Operations](#undo-operations)
- [Advanced Tips](#advanced-tips)
- [Getting Help](#getting-help)

## Prerequisites

Before you start, ensure you have:

- **Computer**: Linux, macOS, or Windows
- **Terminal**: Command prompt or terminal application
- **Python**: Version 3.9 or newer

### Check Python Installation

```bash
# Check Python version
python3 --version

# If that doesn't work, try:
python --version

# Expected output: Python 3.10.12 (or similar)
# If you get an error, install Python from https://www.python.org/
```

## Installation

Follow these clear, reproducible steps to install NoDupeLabs:

### 1. Download the Code

```bash
# Clone repository using git
git clone https://github.com/allaunthefox/NoDupeLabs.git
cd NoDupeLabs

# Alternatively, download ZIP from GitHub and extract
```

### 2. Install NoDupeLabs

```bash
# Install in editable mode
pip install -e .

# Note: Use pip3 instead of pip on some systems
```

### 3. Verify Installation

```bash
# Check installation
nodupe --help

# Expected: Help output with available commands
```

## Your First Scan

Catalog your files by creating fingerprints (hashes) for duplicate detection.

### Example: Scan Photos Folder

```bash
# Scan your photos folder
nodupe scan --root /path/to/MyPhotos

# Replace /path/to/MyPhotos with your actual folder location
```

### What Happens During Scan

- **Progress bar** shows scanning progress
- **meta.json** files created in each folder (catalog information)
- **Database** saved to `output/index.db` (master record)

## Finding Duplicates

Generate a plan to identify and handle duplicate files.

### Create Deduplication Plan

```bash
# Generate CSV plan
nodupe plan --out my_cleanup_plan.csv

# This creates a file listing all duplicates
```

### Review the Plan

```bash
# Open the plan file
# Use Excel, LibreOffice, or a text editor

# Plan format:
# - DELETE: Files to be moved
# - KEEP: Files to be preserved
# - You can delete the CSV file to cancel without changes
```

## Removing Duplicates

Execute the deduplication plan safely.

### Apply the Plan

```bash
# Execute the plan
nodupe apply --plan my_cleanup_plan.csv

# Safety: Files are moved to .nodupe_duplicates folder (not deleted)
```

### What Happens During Application

- **Files moved** to `.nodupe_duplicates` subdirectories
- **Checkpoint created** in `output/checkpoints/` for undo capability
- **Original files** preserved in hidden location

## Undo Operations

Recover files if you make a mistake.

### Find Checkpoint File

```bash
# List checkpoint files
ls output/checkpoints/

# Example filename: checkpoint_20251202_120000.json
```

### Rollback Changes

```bash
# Undo the operation
nodupe rollback --checkpoint output/checkpoints/checkpoint_20251202_120000.json

# Replace filename with your actual checkpoint file
```

### Rollback Result

- **All files** moved back to original locations
- **No data loss** - complete recovery
- **Safe operation** - can be repeated if needed

## Advanced Tips

### Network Drive Scanning

```bash
# Scan network drives safely
nodupe scan --root /network/drive

# Automatically handles disconnections and errors
```

### Custom Configuration

```bash
# Edit configuration file
nano nodupe.yml

# Common settings to customize:
# - ignore_patterns: Add folders/files to ignore
# - parallelism: Adjust worker threads
# - hash_algo: Change hashing algorithm
```

### Configuration Example

```yaml
# nodupe.yml example
hash_algo: sha512
parallelism: 4
ignore_patterns:
  - ".git"
  - "node_modules"
  - "*.tmp"
```

## Getting Help

### Command Help

```bash
# List all available commands
nodupe --help

# Get help for specific command
nodupe scan --help
```

### Common Issues

**Issue**: `nodupe: command not found`

```bash
# Solution: Ensure virtual environment is activated
source .venv/bin/activate
```

**Issue**: Permission denied errors

```bash
# Solution: Check and fix permissions
chmod -R u+rw /your/data/folder
```

### Additional Resources

- [Advanced Usage Guide](ADVANCED_USAGE.md) for complex scenarios
- [Integration Guides](INTEGRATION_GUIDES.md) for platform-specific examples
- [Documentation Guide](DOCUMENTATION_GUIDE.md) for contribution standards

## Conclusion

This beginner's guide provides **clear, reproducible instructions** for getting started with NoDupeLabs. Follow the examples step-by-step to safely scan, identify, and remove duplicate files.

**Next Steps**:
- Try the [Advanced Usage Guide](ADVANCED_USAGE.md) for more complex scenarios
- Explore [Integration Guides](INTEGRATION_GUIDES.md) for platform-specific examples
- Review [Documentation Standards](DOCUMENTATION_GUIDE.md) if you want to contribute
