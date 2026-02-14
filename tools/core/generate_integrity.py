#!/usr/bin/env python3
"""Generate SHA512 integrity checksums for all files.

This script creates SHA512 checksums for all files in the project
and stores them in .integrity/ folder for GitHub integrity verification.

Usage:
    python tools/core/generate_integrity.py
    python tools/core/verify_integrity.py
"""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path


# Directories to exclude from integrity checks
EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    "htmlcov",
    ".coverage",
    "dist",
    "build",
    ".egg-info",
    ".integrity",
    "output",
    "logs",
    "merge_backup",
}

# Files to exclude
EXCLUDE_FILES = {
    ".DS_Store",
    "thumbs.db",
    "package-lock.json",
}


def get_file_hash(filepath: Path) -> str:
    """Generate SHA512 hash of a file."""
    hasher = hashlib.sha512()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_integrity(scan_path: str = ".") -> dict:
    """Generate integrity manifest for all files."""
    manifest = {
        "version": "1.0",
        "generated": datetime.now().isoformat(),
        "algorithm": "SHA-512",
        "files": {},
    }

    root = Path(scan_path)

    for filepath in sorted(root.rglob("*")):
        # Skip directories
        if filepath.is_dir():
            continue

        # Check exclusions
        if any(excluded in filepath.parts for excluded in EXCLUDE_DIRS):
            continue

        if filepath.name in EXCLUDE_FILES:
            continue

        try:
            # Get relative path for the manifest
            rel_path = filepath.relative_to(root)
            file_hash = get_file_hash(filepath)

            manifest["files"][str(rel_path)] = {
                "hash": file_hash,
                "size": filepath.stat().st_size,
            }

        except (OSError, PermissionError) as e:
            print(f"Warning: Could not hash {filepath}: {e}")

    return manifest


def save_manifest(manifest: dict, output_path: str = ".integrity/manifest.json") -> None:
    """Save manifest to file."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w") as f:
        json.dump(manifest, f, indent=2)

    # Also save as SHA512SUMS.txt for standard verification
    sums_path = output.parent / "SHA512SUMS.txt"
    with open(sums_path, "w") as f:
        for filepath, info in sorted(manifest["files"].items()):
            f.write(f"{info['hash']}  {filepath}\n")

    print(f"Generated manifest with {len(manifest['files'])} files")
    print(f"Manifest: {output}")
    print(f"Checksums: {sums_path}")


def verify_integrity(scan_path: str = ".", manifest_path: str = ".integrity/manifest.json") -> bool:
    """Verify file integrity against stored manifest."""
    manifest_file = Path(manifest_path)

    if not manifest_file.exists():
        print("Error: No manifest found. Run generate_integrity.py first.")
        return False

    with open(manifest_file) as f:
        manifest = json.load(f)

    # Generate current state
    current = generate_integrity(scan_path)

    errors = []
    root = Path(scan_path)

    # Check all files in manifest
    for filepath, info in manifest["files"].items():
        full_path = root / filepath

        if not full_path.exists():
            errors.append(f"Missing: {filepath}")
            continue

        # Check hash
        current_hash = get_file_hash(full_path)
        if current_hash != info["hash"]:
            errors.append(f"Modified: {filepath}")

    # Check for new files
    for filepath in current["files"]:
        if filepath not in manifest["files"]:
            errors.append(f"New file: {filepath}")

    if errors:
        print("Integrity verification FAILED:")
        for error in errors:
            print(f"  - {error}")
        return False

    print(f"Integrity verification PASSED: {len(manifest['files'])} files verified")
    return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="File integrity management")
    parser.add_argument("--generate", action="store_true", help="Generate integrity manifest")
    parser.add_argument("--verify", action="store_true", help="Verify integrity")
    parser.add_argument("--path", default=".", help="Path to scan")
    args = parser.parse_args()

    if args.generate:
        manifest = generate_integrity(args.path)
        save_manifest(manifest)
    elif args.verify:
        verify_integrity(args.path)
    else:
        # Default: generate
        manifest = generate_integrity(args.path)
        save_manifest(manifest)


if __name__ == "__main__":
    sys.exit(main())
