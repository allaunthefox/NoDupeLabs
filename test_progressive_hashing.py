#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Test script for progressive hashing implementation.

This script tests the progressive hashing functionality that was added
to improve performance through size-based filtering and quick hash comparison.
"""

import tempfile
import os
from pathlib import Path
from nodupe.core.hash_progressive import ProgressiveHasher, get_progressive_hasher, progressive_find_duplicates


def test_progressive_hasher():
    """Test progressive hashing functionality."""
    print("Testing progressive hashing...")
    
    hasher = get_progressive_hasher()
    
    # Create temporary files for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files with different characteristics
        file1 = temp_path / "file1.txt"
        file1.write_text("Hello World!")
        
        file2 = temp_path / "file2.txt"
        file2.write_text("Hello World!")  # Same content as file1
        
        file3 = temp_path / "file3.txt"
        file3.write_text("Different content")
        
        file4 = temp_path / "file4.txt"
        file4.write_text("Hello World!")  # Same content as file1 and file2
        
        file5 = temp_path / "file5.txt"
        file5.write_text("Hello World! Extra content")  # Different size
        
        files = [file1, file2, file3, file4, file5]
        
        # Test quick hash
        hash1 = hasher.quick_hash(file1)
        hash2 = hasher.quick_hash(file2)
        hash3 = hasher.quick_hash(file3)
        hash4 = hasher.quick_hash(file4)
        hash5 = hasher.quick_hash(file5)
        
        print(f"Quick hash of file1: {hash1}")
        print(f"Quick hash of file2: {hash2}")
        print(f"Quick hash of file3: {hash3}")
        print(f"Quick hash of file4: {hash4}")
        print(f"Quick hash of file5: {hash5}")
        
        # Files 1, 2, 4 should have same quick hash (same content)
        assert hash1 == hash2 == hash4, "Same content files should have same quick hash"
        assert hash1 != hash3, "Different content files should have different quick hash"
        assert hash1 != hash5, "Different sized files should have different quick hash"
        
        # Test should_full_hash
        should_hash_12 = hasher.should_full_hash(file1, file2)  # Same content
        should_hash_13 = hasher.should_full_hash(file1, file3)  # Different content
        should_hash_15 = hasher.should_full_hash(file1, file5)  # Different size
        
        print(f"Should full hash file1 vs file2 (same): {should_hash_12}")
        print(f"Should full hash file1 vs file3 (diff): {should_hash_13}")
        print(f"Should full hash file1 vs file5 (size): {should_hash_15}")
        
        # Same content files should need full hash comparison
        assert should_hash_12, "Same content files should need full hash"
        # Different content files should not need full hash (filtered by quick hash)
        assert not should_hash_13, "Different content files should not need full hash"
        # Different size files should not need full hash (filtered by size)
        assert not should_hash_15, "Different size files should not need full hash"
        
        # Test full hash
        full_hash1 = hasher.full_hash(file1)
        full_hash2 = hasher.full_hash(file2)
        full_hash3 = hasher.full_hash(file3)
        full_hash4 = hasher.full_hash(file4)
        
        assert full_hash1 == full_hash2 == full_hash4, "Same content files should have same full hash"
        assert full_hash1 != full_hash3, "Different content files should have different full hash"
        
        # Test progressive find duplicates
        duplicates = hasher.progressive_find_duplicates(files)
        
        print(f"Found {len(duplicates)} duplicate groups")
        for i, group in enumerate(duplicates):
            print(f"  Group {i+1}: {[str(f) for f in group]}")
        
        # Should find one group with file1, file2, file4 (all same content)
        assert len(duplicates) == 1, "Should find one duplicate group"
        assert len(duplicates[0]) == 3, "Duplicate group should have 3 files"
        assert file1 in duplicates[0] and file2 in duplicates[0] and file4 in duplicates[0]
        
        # Test get duplicate candidates
        candidates = hasher.get_duplicate_candidates(files)
        print(f"Found {len(candidates)} potential duplicate pairs")
        for pair in candidates:
            print(f"  Pair: {pair[0]} <-> {pair[1]}")
        
        # Should have pairs between same-sized files
        assert len(candidates) >= 2, "Should find some potential duplicate pairs"
    
    print("✓ Progressive hashing tests passed!")


def test_global_functions():
    """Test global convenience functions."""
    print("Testing global functions...")
    
    # Test get_progressive_hasher
    hasher1 = get_progressive_hasher()
    hasher2 = get_progressive_hasher()
    assert hasher1 is hasher2, "Global hasher should be singleton"
    
    # Test convenience functions
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        file1 = temp_path / "test1.txt"
        file1.write_text("Hello World!")
        
        file2 = temp_path / "test2.txt"
        file2.write_text("Hello World!")
        
        # Test should_full_hash convenience function
        from nodupe.core.hash_progressive import should_full_hash
        result = should_full_hash(file1, file2)
        assert result, "Same files should need full hash"
        
        # Test progressive_find_duplicates convenience function
        from nodupe.core.hash_progressive import progressive_find_duplicates
        duplicates = progressive_find_duplicates([file1, file2])
        assert len(duplicates) == 1, "Should find duplicate group"
        assert len(duplicates[0]) == 2, "Should have 2 files in group"
    
    print("✓ Global functions tests passed!")


def main():
    """Run all progressive hashing tests."""
    print("Running progressive hashing tests...\n")
    
    try:
        test_progressive_hasher()
        print()
        
        test_global_functions()
        print()
        
        print("🎉 All progressive hashing tests passed!")
        print("\nProgressive hashing features implemented:")
        print("- ✓ Size-based filtering (instant elimination)")
        print("- ✓ Quick hash comparison (first 8KB)")
        print("- ✓ Full hash only for remaining candidates")
        print("- ✓ Performance optimization through progressive filtering")
        print("- ✓ Global convenience functions")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
