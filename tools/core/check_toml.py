#!/usr/bin/env python3
"""Validate TOML configuration files."""
import tomllib
import sys
from pathlib import Path


def check_file(filepath: Path) -> bool:
    """Validate a single TOML file."""
    try:
        with open(filepath, 'rb') as f:
            tomllib.load(f)
        return True
    except Exception as e:
        print(f"Error in {filepath}: {e}")
        return False


def main() -> int:
    """Check all TOML files in the project."""
    root = Path('.')
    error_count = 0
    checked_count = 0
    
    # Directories to skip
    skip_dirs = {'.git', '.venv', 'venv', 'node_modules', '__pycache__'}
    
    for path in root.rglob('*.toml'):
        # Skip certain directories
        if any(skip in path.parts for skip in skip_dirs):
            continue
        
        checked_count += 1
        if not check_file(path):
            error_count += 1
    
    print(f"Checked {checked_count} TOML files.")
    if error_count > 0:
        print(f"Found {error_count} TOML errors.")
        return 1
    else:
        print("All TOML files valid.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
