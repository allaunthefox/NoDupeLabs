# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Progressive hashing system for NoDupeLabs.

This module provides progressive hashing functionality that improves
performance by doing size-based filtering, quick hash comparison,
then full hash only for remaining candidates.
"""

import hashlib
from pathlib import Path
from typing import List, Tuple, Dict, Any
from collections import defaultdict

# Try to import blake3 for faster hashing, fall back to hashlib if not available
try:
    import blake3
    HAS_BLAKE3 = True
except ImportError:
    HAS_BLAKE3 = False
    blake3 = None  # Will be used in conditional code


class ProgressiveHasher:
    """Progressive file hasher that improves performance through filtering."""

    def __init__(self, quick_hash_size: int = 8192):
        """Initialize progressive hasher.
        
        Args:
            quick_hash_size: Size in bytes for quick hash (default 8KB)
        """
        self.quick_hash_size = quick_hash_size

    def quick_hash(self, path: Path) -> str:
        """Hash first N bytes of file for quick comparison.
        
        Args:
            path: Path to file to hash
            
        Returns:
            Hash of first N bytes
        """
        with path.open('rb') as f:
            data = f.read(self.quick_hash_size)
            if HAS_BLAKE3:
                return blake3.blake3(data).hexdigest()
            else:
                return hashlib.sha256(data).hexdigest()

    def should_full_hash(self, path1: Path, path2: Path) -> bool:
        """Check if full hash comparison is needed.
        
        Args:
            path1: First file path
            path2: Second file path
            
        Returns:
            True if full hash is needed, False if files are definitely different
        """
        # First check: file sizes must match
        if path1.stat().st_size != path2.stat().st_size:
            return False
        
        # Second check: quick hash must match
        return self.quick_hash(path1) == self.quick_hash(path2)

    def progressive_find_duplicates(self, files: List[Path]) -> List[List[Path]]:
        """Find duplicates using progressive hashing approach.
        
        Args:
            files: List of file paths to check for duplicates
            
        Returns:
            List of lists, where each inner list contains duplicate files
        """
        # Phase 1: Group by size (instant elimination)
        by_size = defaultdict(list)
        for f in files:
            size = f.stat().st_size
            by_size[size].append(f)

        # Filter out unique sizes (no duplicates possible)
        size_groups = [group for group in by_size.values() if len(group) > 1]

        # Phase 2: Quick hash comparison for same-sized files
        by_quick_hash = defaultdict(list)
        for group in size_groups:
            for f in group:
                quick = self.quick_hash(f)
                by_quick_hash[quick].append(f)

        # Filter again (more elimination)
        quick_hash_groups = [group for group in by_quick_hash.values() if len(group) > 1]

        # Phase 3: Full hash comparison for remaining candidates
        duplicates = []
        for group in quick_hash_groups:
            by_full_hash = defaultdict(list)
            for f in group:
                full_hash = self.full_hash(f)
                by_full_hash[full_hash].append(f)

            # Add groups with actual duplicates
            actual_duplicates = [g for g in by_full_hash.values() if len(g) > 1]
            duplicates.extend(actual_duplicates)

        return duplicates

    def full_hash(self, path: Path) -> str:
        """Compute full file hash.
        
        Args:
            path: Path to file to hash
            
        Returns:
            Full file hash
        """
        if HAS_BLAKE3:
            hasher = blake3.blake3()
            with path.open('rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        else:
            hasher = hashlib.sha256()
            with path.open('rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()

    def get_duplicate_candidates(self, files: List[Path]) -> List[Tuple[Path, Path]]:
        """Get pairs of files that might be duplicates (after size and quick hash filtering).
        
        Args:
            files: List of file paths to check
            
        Returns:
            List of tuples containing potential duplicate pairs
        """
        # Group by size first
        by_size = defaultdict(list)
        for f in files:
            size = f.stat().st_size
            by_size[size].append(f)

        # Filter to only groups with potential duplicates
        size_groups = [group for group in by_size.values() if len(group) > 1]

        # Group by quick hash
        candidates = []
        for group in size_groups:
            by_quick_hash = defaultdict(list)
            for f in group:
                quick = self.quick_hash(f)
                by_quick_hash[quick].append(f)

            # Create pairs from quick hash groups
            for quick_group in by_quick_hash.values():
                if len(quick_group) > 1:
                    # Generate all pairs within this group
                    for i in range(len(quick_group)):
                        for j in range(i + 1, len(quick_group)):
                            candidates.append((quick_group[i], quick_group[j]))

        return candidates


# Global progressive hasher instance
_progressive_hasher: ProgressiveHasher = None


def get_progressive_hasher() -> ProgressiveHasher:
    """Get the global progressive hasher instance."""
    global _progressive_hasher
    if _progressive_hasher is None:
        _progressive_hasher = ProgressiveHasher()
    return _progressive_hasher


def progressive_find_duplicates(files: List[Path]) -> List[List[Path]]:
    """Convenience function to find duplicates using progressive hashing."""
    hasher = get_progressive_hasher()
    return hasher.progressive_find_duplicates(files)


def should_full_hash(path1: Path, path2: Path) -> bool:
    """Convenience function to check if full hash is needed."""
    hasher = get_progressive_hasher()
    return hasher.should_full_hash(path1, path2)


__all__ = [
    'ProgressiveHasher',
    'get_progressive_hasher',
    'progressive_find_duplicates',
    'should_full_hash'
]
