#!/usr/bin/env python3
"""Collision detection for hash-based deduplication."""
import hashlib
import sys
from pathlib import Path
from typing import Optional


def hash_file(filepath: Path, algorithm: str = 'sha256') -> Optional[str]:
    """Compute hash of a file."""
    try:
        hasher = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None


def find_hashes(directory: Path, algorithm: str = 'sha256') -> dict[str, list[Path]]:
    """Find all file hashes in a directory."""
    hashes: dict[str, list[Path]] = {}
    
    for filepath in directory.rglob('*'):
        if filepath.is_file():
            file_hash = hash_file(filepath, algorithm)
            if file_hash:
                if file_hash not in hashes:
                    hashes[file_hash] = []
                hashes[file_hash].append(filepath)
    
    return hashes


def check_for_collisions(hashes: dict[str, list[Path]]) -> list[tuple[str, list[Path]]]:
    """Check for hash collisions (same hash, different files)."""
    collisions = []
    
    for file_hash, paths in hashes.items():
        # If we have more than one path with same hash
        if len(paths) > 1:
            # Check if files are actually different
            contents = set()
            for path in paths:
                try:
                    contents.add(path.read_bytes())
                except Exception:
                    pass
            
            # If same hash but different content = collision!
            if len(contents) > 1:
                collisions.append((file_hash, paths))
    
    return collisions


def find_duplicates(hashes: dict[str, list[Path]]) -> list[tuple[str, list[Path]]]:
    """Find actual duplicates (same hash AND same content)."""
    duplicates = []
    
    for file_hash, paths in hashes.items():
        if len(paths) > 1:
            # Verify they're actually duplicates
            first_content = None
            is_duplicate = True
            
            for path in paths:
                try:
                    content = path.read_bytes()
                    if first_content is None:
                        first_content = content
                    elif content != first_content:
                        is_duplicate = False
                        break
                except Exception:
                    is_duplicate = False
                    break
            
            if is_duplicate:
                duplicates.append((file_hash, paths))
    
    return duplicates


def main() -> int:
    """Run collision check."""
    # Default to current directory or accept argument
    directory = Path('.')
    
    print(f"=== Collision Detection ===")
    print(f"Scanning: {directory}")
    
    hashes = find_hashes(directory)
    print(f"Files scanned: {len(hashes)} unique hashes")
    
    # Check for collisions
    collisions = check_for_collisions(hashes)
    if collisions:
        print(f"\n⚠️  FOUND {len(collisions)} HASH COLLISIONS:")
        for file_hash, paths in collisions:
            print(f"\nHash: {file_hash}")
            for path in paths:
                print(f"  - {path}")
        print("\nWARNING: Hash algorithm has collisions!")
    else:
        print("\n✓ No hash collisions detected")
    
    # Report duplicates
    duplicates = find_duplicates(hashes)
    if duplicates:
        print(f"\n✓ Found {len(duplicates)} duplicate file groups")
    else:
        print("\n✓ No duplicate files found")
    
    return 1 if collisions else 0


if __name__ == '__main__':
    sys.exit(main())
