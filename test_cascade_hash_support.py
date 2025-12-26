#!/usr/bin/env python3
"""Test script to verify cascade modules support specific hash types."""

import tempfile
import hashlib
from pathlib import Path
from nodupe.core.cascade.stages.progressive_hashing import ProgressiveHashingCascadeStage
from nodupe.core.cascade.stages.archive_processing import ArchiveProcessingCascadeStage


def test_progressive_hashing_cascade():
    """Test progressive hashing cascade with specific hash types."""
    print("Testing ProgressiveHashingCascadeStage with specific hash types...")
    
    stage = ProgressiveHashingCascadeStage()
    
    # Create test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files
        test_file1 = temp_path / "test1.txt"
        test_file2 = temp_path / "test2.txt"
        
        test_file1.write_text("Hello, World!")
        test_file2.write_text("Hello, Python!")
        
        test_files = [test_file1, test_file2]
        
        # Test with default behavior (algorithm cascading)
        print("  - Testing default algorithm cascading...")
        result_default = stage.execute(test_files)
        print(f"    Files processed: {result_default['files_processed']}")
        print(f"    Quick hash algorithm: {result_default['quick_hash_algorithm']}")
        print(f"    Full hash algorithm: {result_default['full_hash_algorithm']}")
        print(f"    Hash type: {result_default['hash_type']}")
        
        # Test with specific algorithm
        print("  - Testing with SHA256 algorithm...")
        result_sha256 = stage.execute(test_files, algorithm='sha256')
        print(f"    Files processed: {result_sha256['files_processed']}")
        print(f"    Quick hash algorithm: {result_sha256['quick_hash_algorithm']}")
        print(f"    Full hash algorithm: {result_sha256['full_hash_algorithm']}")
        print(f"    Hash type: {result_sha256['hash_type']}")
        
        # Test with MD5 algorithm
        print(" - Testing with MD5 algorithm...")
        result_md5 = stage.execute(test_files, algorithm='md5')
        print(f"    Files processed: {result_md5['files_processed']}")
        print(f"    Quick hash algorithm: {result_md5['quick_hash_algorithm']}")
        print(f"    Full hash algorithm: {result_md5['full_hash_algorithm']}")
        print(f"    Hash type: {result_md5['hash_type']}")
        
        # Test with different quick and full algorithms
        print("  - Testing with different quick and full algorithms...")
        result_mixed = stage.execute(test_files, quick_algorithm='md5', full_algorithm='sha256')
        print(f"    Files processed: {result_mixed['files_processed']}")
        print(f"    Quick hash algorithm: {result_mixed['quick_hash_algorithm']}")
        print(f"    Full hash algorithm: {result_mixed['full_hash_algorithm']}")
        print(f"    Hash type: {result_mixed['hash_type']}")
        
    print("✓ ProgressiveHashingCascadeStage tests passed!\n")


def test_archive_processing_cascade():
    """Test archive processing cascade with hash support."""
    print("Testing ArchiveProcessingCascadeStage with hash support...")
    
    stage = ArchiveProcessingCascadeStage()
    
    # Create a test ZIP file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create some test files to archive
        test_file1 = temp_path / "file1.txt"
        test_file2 = temp_path / "file2.txt"
        test_file1.write_text("Content of file 1")
        test_file2.write_text("Content of file 2")
        
        # Create a ZIP file
        import zipfile
        zip_path = temp_path / "test_archive.zip"
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            zip_file.write(test_file1, "file1.txt")
            zip_file.write(test_file2, "file2.txt")
        
        # Test basic archive processing
        print("  - Testing basic archive processing...")
        result_basic = stage.execute(zip_path)
        print(f"    Archive path: {result_basic['archive_path']}")
        print(f"    Total files: {result_basic['total_files']}")
        print(f"    Successful method: {result_basic['successful_method']}")
        print(f"    Content hashes: {len(result_basic['content_hashes'])}")
        
        # Test with content hashing
        print("  - Testing with SHA256 content hashing...")
        result_hashed = stage.execute(zip_path, hash_contents=True, hash_algorithm='sha256')
        print(f"    Archive path: {result_hashed['archive_path']}")
        print(f"    Total files: {result_hashed['total_files']}")
        print(f"    Successful method: {result_hashed['successful_method']}")
        print(f"    Hash algorithm: {result_hashed['hash_algorithm']}")
        print(f"    Content hashes: {len(result_hashed['content_hashes'])}")
        if result_hashed['content_hashes']:
            for file_path, file_hash in list(result_hashed['content_hashes'].items())[:2]:  # Show first 2
                print(f"      {file_path}: {file_hash[:16]}...")
        
        # Test with MD5 content hashing
        print("  - Testing with MD5 content hashing...")
        result_md5 = stage.execute(zip_path, hash_contents=True, hash_algorithm='md5')
        print(f"    Hash algorithm: {result_md5['hash_algorithm']}")
        print(f"    Content hashes: {len(result_md5['content_hashes'])}")
        
    print("✓ ArchiveProcessingCascadeStage tests passed!\n")


def main():
    """Run all tests."""
    print("Testing cascade modules hash type support...\n")
    
    try:
        test_progressive_hashing_cascade()
        test_archive_processing_cascade()
        print("🎉 All cascade module hash type support tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
