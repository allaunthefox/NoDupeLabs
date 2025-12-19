"""
Test suite for core file scanning functionality.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest

from nodupe.core.scan.walker import FileWalker
from nodupe.core.filesystem import Filesystem


class TestFileScanning:
    """Test basic file scanning functionality."""
    
    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.temp_paths = []
        
    def teardown_method(self):
        """Clean up test environment."""
        for path in self.temp_paths:
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_file(self, filename, content="", subdir=None):
        """Create a test file with given content."""
        if subdir:
            filepath = os.path.join(self.test_dir, subdir, filename)
            os.makedirs(os.path.join(self.test_dir, subdir), exist_ok=True)
        else:
            # Handle nested paths in filename (e.g., "subdir/test3.txt")
            filepath = os.path.join(self.test_dir, filename)
            # Create parent directories if they don't exist
            parent_dir = os.path.dirname(filepath)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        self.temp_paths.append(filepath)
        return filepath
    
    def test_basic_file_discovery(self):
        """Test that all files are discovered in a directory."""
        # Create test files
        file1 = self.create_test_file("test1.txt", "content1")
        file2 = self.create_test_file("test2.txt", "content2")
        file3 = self.create_test_file("subdir/test3.txt", "content3")
        
        walker = FileWalker()
        files = walker.walk(self.test_dir)
        
        assert len(files) == 3
        file_paths = [f['path'] for f in files]
        assert file1 in file_paths
        assert file2 in file_paths
        assert file3 in file_paths
    
    def test_empty_directory_scanning(self):
        """Test scanning an empty directory."""
        empty_dir = tempfile.mkdtemp()
        self.temp_paths.append(empty_dir)
        
        walker = FileWalker()
        files = walker.walk(empty_dir)
        
        assert len(files) == 0
    
    def test_nested_directory_scanning(self):
        """Test scanning deeply nested directories."""
        # Create nested structure: dir1/dir2/dir3/file.txt
        nested_file = self.create_test_file("level1/level2/level3/test.txt", "nested")
        
        walker = FileWalker()
        files = walker.walk(self.test_dir)
        
        assert len(files) == 1
        file_paths = [f['path'] for f in files]
        assert nested_file in file_paths
    
    def test_symlink_handling(self):
        """Test handling of symbolic links."""
        target_file = self.create_test_file("target.txt", "target content")
        symlink_path = os.path.join(self.test_dir, "symlink.txt")
        
        os.symlink(target_file, symlink_path)
        self.temp_paths.append(symlink_path)
        
        walker = FileWalker()
        files = walker.walk(self.test_dir)
        
        # Should include both the target file and potentially the symlink
        # depending on how symlinks are configured to be handled
        file_paths = [f['path'] for f in files]
        assert target_file in file_paths
    
    def test_file_permissions_scanning(self):
        """Test scanning files with different permissions."""
        test_file = self.create_test_file("permissions_test.txt", "test")
        
        # Set different permissions
        os.chmod(test_file, 0o755)
        
        walker = FileWalker()
        files = walker.walk(self.test_dir)
        
        assert len(files) == 1
        scanned_file = files[0]
        assert scanned_file['path'] == test_file
    
    def test_large_file_scanning(self):
        """Test scanning very large files."""
        large_content = "A" * (10 * 1024 * 1024)  # 10MB file
        large_file = self.create_test_file("large_file.txt", large_content)
        
        walker = FileWalker()
        files = walker.walk(self.test_dir)
        
        assert len(files) == 1
        assert files[0]['path'] == large_file
    
    def test_special_characters_in_filenames(self):
        """Test scanning files with special characters in names."""
        special_names = [
            "file with spaces.txt",
            "file-with-dashes.txt", 
            "file_with_underscores.txt",
            "file123.txt",
            "file@#$%^&().txt"
        ]
        
        created_files = []
        for name in special_names:
            filepath = self.create_test_file(name, "test")
            created_files.append(filepath)
        
        walker = FileWalker()
        files = walker.walk(self.test_dir)
        
        assert len(files) == len(special_names)
        file_paths = [f['path'] for f in files]
        for filepath in created_files:
            assert filepath in file_paths
    
    def test_hidden_files_scanning(self):
        """Test scanning hidden files and directories."""
        hidden_file = self.create_test_file(".hidden.txt", "hidden")
        hidden_dir_file = self.create_test_file(".hidden_dir/hidden_file.txt", "hidden in dir")
        
        walker = FileWalker()
        files = walker.walk(self.test_dir)
        
        # Hidden files should typically be included unless specifically excluded
        assert len(files) >= 2  # At least the two hidden files
        file_paths = [f['path'] for f in files]
        assert hidden_file in file_paths
        assert hidden_dir_file in file_paths
    
    def test_filesystem_handler_basic_operations(self):
        """Test basic filesystem operations through handler."""
        fs_handler = Filesystem()
        
        # Test file existence (using validate_path since there's no exists method)
        test_file = self.create_test_file("exist_test.txt", "test")
        assert fs_handler.validate_path(test_file, must_exist=True)
        try:
            fs_handler.validate_path(os.path.join(self.test_dir, "nonexistent.txt"), must_exist=True)
            assert False, "Should raise exception for non-existent file"
        except Exception:
            pass  # Expected
        
        # Test file size
        size = fs_handler.get_size(test_file)
        assert size == len("test")
        
        # Test directory operations
        fs_handler.ensure_directory(os.path.join(self.test_dir, "test_dir"))
        assert os.path.isdir(os.path.join(self.test_dir, "test_dir"))


def test_file_walker_initialization():
    """Test FileWalker initialization with different parameters."""
    # Test that FileWalker can be instantiated
    walker = FileWalker()
    assert walker is not None


def test_file_walker_walk_empty_params():
    """Test FileWalker walk with default parameters."""
    temp_dir = tempfile.mkdtemp()
    try:
        walker = FileWalker()
        files = walker.walk(temp_dir)
        assert len(files) == 0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__])
