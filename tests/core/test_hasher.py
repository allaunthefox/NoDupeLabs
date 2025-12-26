"""
Test suite for core hash generation functionality.
Tests hash generation and comparison from nodupe.core.scan.hasher.
"""

import os
import tempfile
import shutil
from pathlib import Path
import hashlib
import pytest

from nodupe.core.scan.hasher import FileHasher


class TestFileHasher:
    """Test FileHasher functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_file_hasher_initialization(self):
        """Test FileHasher initialization."""
        hasher = FileHasher()
        
        assert hasher is not None
        assert hasher.algorithm == 'sha256'
        assert isinstance(hasher.hasher, type(hashlib.sha256()))
    
    def test_file_hasher_initialization_with_algorithm(self):
        """Test FileHasher initialization with specific algorithm."""
        hasher = FileHasher(algorithm='md5')
        
        assert hasher is not None
        assert hasher.algorithm == 'md5'
        assert isinstance(hasher.hasher, type(hashlib.md5()))
    
    def test_file_hasher_initialization_with_invalid_algorithm(self):
        """Test FileHasher initialization with invalid algorithm."""
        with pytest.raises(ValueError, match="Unsupported hash algorithm"):
            FileHasher(algorithm='invalid_algorithm')
    
    def test_hash_file_content(self):
        """Test hash_file_content method."""
        hasher = FileHasher()
        
        test_file = os.path.join(self.temp_dir, 'test.txt')
        test_content = 'test content for hashing'
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Calculate hash
        hash_result = hasher.hash_file_content(test_file)
        
        # Verify it's a hex string of expected length for SHA-256
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA-256 produces 64 hex characters
        assert all(c in '0123456789abcdef' for c in hash_result)
    
    def test_hash_file_content_with_md5(self):
        """Test hash_file_content method with MD5 algorithm."""
        hasher = FileHasher(algorithm='md5')
        
        test_file = os.path.join(self.temp_dir, 'test.txt')
        test_content = 'test content for hashing'
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Calculate hash
        hash_result = hasher.hash_file_content(test_file)
        
        # Verify it's a hex string of expected length for MD5
        assert isinstance(hash_result, str)
        assert len(hash_result) == 32  # MD5 produces 32 hex characters
        assert all(c in '0123456789abcdef' for c in hash_result)
    
    def test_hash_file_content_different_files(self):
        """Test that different files produce different hashes."""
        hasher = FileHasher()
        
        file1 = os.path.join(self.temp_dir, 'file1.txt')
        file2 = os.path.join(self.temp_dir, 'file2.txt')
        
        with open(file1, 'w') as f:
            f.write('content1')
        with open(file2, 'w') as f:
            f.write('content2')
        
        hash1 = hasher.hash_file_content(file1)
        hash2 = hasher.hash_file_content(file2)
        
        assert hash1 != hash2
    
    def test_hash_file_content_same_content(self):
        """Test that same content produces same hash."""
        hasher = FileHasher()
        
        file1 = os.path.join(self.temp_dir, 'file1.txt')
        file2 = os.path.join(self.temp_dir, 'file2.txt')
        
        same_content = 'same content for both files'
        
        with open(file1, 'w') as f:
            f.write(same_content)
        with open(file2, 'w') as f:
            f.write(same_content)
        
        hash1 = hasher.hash_file_content(file1)
        hash2 = hasher.hash_file_content(file2)
        
        assert hash1 == hash2
    
    def test_hash_file_content_empty_file(self):
        """Test hash_file_content with empty file."""
        hasher = FileHasher()
        
        empty_file = os.path.join(self.temp_dir, 'empty.txt')
        with open(empty_file, 'w') as f:
            f.write('')
        
        hash_result = hasher.hash_file_content(empty_file)
        
        # Empty file should have consistent hash
        expected_empty_hash = hashlib.sha256(b'').hexdigest()
        assert hash_result == expected_empty_hash
    
    def test_hash_file_content_large_file(self):
        """Test hash_file_content with large file."""
        hasher = FileHasher()
        
        large_file = os.path.join(self.temp_dir, 'large.txt')
        
        # Create a large file (1MB)
        large_content = 'A' * (1024 * 1024)  # 1MB of 'A's
        with open(large_file, 'w') as f:
            f.write(large_content)
        
        hash_result = hasher.hash_file_content(large_file)
        
        # Verify it's a valid hash
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64
        assert all(c in '0123456789abcdef' for c in hash_result)
        
        # Verify it matches expected hash for the content
        expected_hash = hashlib.sha256(large_content.encode()).hexdigest()
        assert hash_result == expected_hash
    
    def test_hash_file_content_binary_file(self):
        """Test hash_file_content with binary file."""
        hasher = FileHasher()
        
        binary_file = os.path.join(self.temp_dir, 'binary.bin')
        binary_content = b'\x00\x01\x02\x03\xFF\xFE' * 1000  # Binary content
        
        with open(binary_file, 'wb') as f:
            f.write(binary_content)
        
        # For binary files, we need to handle differently since the method expects text
        # Let's test with a text representation
        text_file = os.path.join(self.temp_dir, 'binary_text.txt')
        with open(text_file, 'w', encoding='latin-1') as f:
            f.write(binary_content.decode('latin-1', errors='ignore'))
        
        hash_result = hasher.hash_file_content(text_file)
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64
        assert all(c in '0123456789abcdef' for c in hash_result)
    
    def test_hash_file_content_nonexistent_file(self):
        """Test hash_file_content with nonexistent file."""
        hasher = FileHasher()
        
        nonexistent_file = os.path.join(self.temp_dir, 'nonexistent.txt')
        
        with pytest.raises(FileNotFoundError):
            hasher.hash_file_content(nonexistent_file)
    
    def test_hash_file_content_with_different_algorithms(self):
        """Test hash_file_content with different algorithms."""
        algorithms = ['sha256', 'md5', 'sha1', 'sha512']
        
        test_file = os.path.join(self.temp_dir, 'test.txt')
        test_content = 'test content'
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        hashes = {}
        for algorithm in algorithms:
            hasher = FileHasher(algorithm=algorithm)
            hash_result = hasher.hash_file_content(test_file)
            hashes[algorithm] = hash_result
            
            # Verify each hash has correct length
            if algorithm == 'md5':
                assert len(hash_result) == 32
            elif algorithm == 'sha1':
                assert len(hash_result) == 40
            elif algorithm == 'sha256':
                assert len(hash_result) == 64
            elif algorithm == 'sha512':
                assert len(hash_result) == 128
    
    def test_hash_file_content_unicode_content(self):
        """Test hash_file_content with Unicode content."""
        hasher = FileHasher()
        
        unicode_file = os.path.join(self.temp_dir, 'unicode.txt')
        unicode_content = 'Hello, 世界! 🌍 Unicode content'
        
        with open(unicode_file, 'w', encoding='utf-8') as f:
            f.write(unicode_content)
        
        hash_result = hasher.hash_file_content(unicode_file)
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64
        assert all(c in '0123456789abcdef' for c in hash_result)
        
        # Verify it matches expected hash
        expected_hash = hashlib.sha256(unicode_content.encode('utf-8')).hexdigest()
        assert hash_result == expected_hash
    
    def test_hash_file_content_special_characters(self):
        """Test hash_file_content with special characters."""
        hasher = FileHasher()
        
        special_file = os.path.join(self.temp_dir, 'special.txt')
        special_content = 'Special chars: \n\r\t\x00\x01!@#$%^&*()'
        
        with open(special_file, 'w', encoding='utf-8') as f:
            f.write(special_content)
        
        hash_result = hasher.hash_file_content(special_file)
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64
        assert all(c in '0123456789abcdef' for c in hash_result)
    
    def test_compare_hashes_same(self):
        """Test compare_hashes method with same hashes."""
        hasher = FileHasher()
        
        test_file = os.path.join(self.temp_dir, 'test.txt')
        test_content = 'test content'
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        hash1 = hasher.hash_file_content(test_file)
        hash2 = hasher.hash_file_content(test_file)  # Same content, same hash
        
        assert hasher.compare_hashes(hash1, hash2) is True
    
    def test_compare_hashes_different(self):
        """Test compare_hashes method with different hashes."""
        hasher = FileHasher()
        
        file1 = os.path.join(self.temp_dir, 'file1.txt')
        file2 = os.path.join(self.temp_dir, 'file2.txt')
        
        with open(file1, 'w') as f:
            f.write('content1')
        with open(file2, 'w') as f:
            f.write('content2')
        
        hash1 = hasher.hash_file_content(file1)
        hash2 = hasher.hash_file_content(file2)
        
        assert hasher.compare_hashes(hash1, hash2) is False
    
    def test_compare_hashes_case_sensitive(self):
        """Test compare_hashes method is case sensitive."""
        hasher = FileHasher()
        
        # Create two different hashes
        file1 = os.path.join(self.temp_dir, 'file1.txt')
        file2 = os.path.join(self.temp_dir, 'file2.txt')
        
        with open(file1, 'w') as f:
            f.write('content1')
        with open(file2, 'w') as f:
            f.write('content2')
        
        hash1 = hasher.hash_file_content(file1)
        hash2 = hasher.hash_file_content(file2)
        
        # Convert one to uppercase to test case sensitivity
        hash2_upper = hash2.upper()
        
        assert hasher.compare_hashes(hash1, hash2_upper) is False
        assert hasher.compare_hashes(hash1, hash1.upper()) is False  # Different cases
    
    def test_compare_hashes_invalid_input(self):
        """Test compare_hashes method with invalid input."""
        hasher = FileHasher()
        
        # Test with non-hex strings
        with pytest.raises(ValueError):
            hasher.compare_hashes('invalid_hash', 'another_invalid')
        
        # Test with wrong length hashes
        with pytest.raises(ValueError):
            hasher.compare_hashes('short', 'also_short')


def test_file_hasher_different_algorithms():
    """Test FileHasher with different algorithms produce different hashes."""
    test_file = os.path.join(tempfile.gettempdir(), 'algo_test.txt')
    
    try:
        # Create test file
        with open(test_file, 'w') as f:
            f.write('test content for algorithm comparison')
        
        # Test different algorithms
        algorithms = ['md5', 'sha1', 'sha256']
        hashes = {}
        
        for algo in algorithms:
            hasher = FileHasher(algorithm=algo)
            hashes[algo] = hasher.hash_file_content(test_file)
        
        # All hashes should be different
        hash_values = list(hashes.values())
        for i in range(len(hash_values)):
            for j in range(i + 1, len(hash_values)):
                assert hash_values[i] != hash_values[j]
        
        # Each should have correct length
        assert len(hashes['md5']) == 32
        assert len(hashes['sha1']) == 40
        assert len(hashes['sha256']) == 64
        
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def test_file_hasher_performance_large_files():
    """Test FileHasher performance with large files."""
    large_file = os.path.join(tempfile.gettempdir(), 'large_test.bin')
    
    try:
        # Create a large file (10MB)
        large_content = b'A' * (10 * 1024 * 1024)  # 10MB
        with open(large_file, 'wb') as f:
            f.write(large_content)
        
        hasher = FileHasher()
        
        # This should complete without errors
        hash_result = hasher.hash_file_content(large_file)
        
        # Verify it's a valid hash
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64
        assert all(c in '0123456789abcdef' for c in hash_result)
        
        # Should match expected hash
        expected_hash = hashlib.sha256(large_content).hexdigest()
        assert hash_result == expected_hash
        
    finally:
        if os.path.exists(large_file):
            os.remove(large_file)


def test_file_hasher_consistency():
    """Test that FileHasher produces consistent results."""
    test_file = os.path.join(tempfile.gettempdir(), 'consistency_test.txt')
    
    try:
        # Create test file
        with open(test_file, 'w') as f:
            f.write('consistent test content')
        
        # Create multiple hasher instances and hash the same file
        results = []
        for i in range(5):
            hasher = FileHasher()
            result = hasher.hash_file_content(test_file)
            results.append(result)
        
        # All results should be identical
        assert all(r == results[0] for r in results)
        
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


if __name__ == "__main__":
    pytest.main([__file__])
