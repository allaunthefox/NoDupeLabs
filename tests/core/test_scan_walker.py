"""
Test suite for nodupe.core.scan.walker module
"""
import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from nodupe.core.scan.walker import FileWalker, create_file_walker


class TestFileWalker:
    """Test cases for the FileWalker class"""
    
    def test_file_walker_initialization(self):
        """Test FileWalker initialization"""
        walker = FileWalker()
        assert walker is not None
        assert walker._file_count == 0
        assert walker._dir_count == 0
        assert walker._error_count == 0
        assert walker._start_time == 0
        assert walker._last_update == 0
        assert walker._enable_archive_support is True
    
    def test_file_walker_walk_with_empty_directory(self):
        """Test FileWalker.walk with an empty directory"""
        walker = FileWalker()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            files = walker.walk(temp_dir)
            assert isinstance(files, list)
            assert len(files) == 0
    
    def test_file_walker_walk_with_files(self):
        """Test FileWalker.walk with files in directory"""
        walker = FileWalker()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_file1 = os.path.join(temp_dir, "test1.txt")
            test_file2 = os.path.join(temp_dir, "test2.py")
            
            with open(test_file1, 'w') as f:
                f.write("test content 1")
            with open(test_file2, 'w') as f:
                f.write("test content 2")
            
            files = walker.walk(temp_dir)
            assert isinstance(files, list)
            assert len(files) == 2
            
            # Check that both files are in the results
            file_paths = [f['path'] for f in files]
            assert test_file1 in file_paths
            assert test_file2 in file_paths
    
    def test_file_walker_walk_with_file_filter(self):
        """Test FileWalker.walk with file filter"""
        walker = FileWalker()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_file1 = os.path.join(temp_dir, "test1.txt")
            test_file2 = os.path.join(temp_dir, "test2.py")
            
            with open(test_file1, 'w') as f:
                f.write("test content 1")
            with open(test_file2, 'w') as f:
                f.write("test content 2")
            
            # Filter to only include .txt files
            txt_filter = lambda file_info: file_info['extension'] == '.txt'
            files = walker.walk(temp_dir, file_filter=txt_filter)
            assert isinstance(files, list)
            assert len(files) == 1
            assert files[0]['path'] == test_file1
    
    def test_file_walker_walk_with_progress_callback(self):
        """Test FileWalker.walk with progress callback"""
        walker = FileWalker()
        progress_calls = []
        
        def progress_callback(progress_info):
            progress_calls.append(progress_info)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_file1 = os.path.join(temp_dir, "test1.txt")
            test_file2 = os.path.join(temp_dir, "test2.py")
            
            with open(test_file1, 'w') as f:
                f.write("test content 1")
            with open(test_file2, 'w') as f:
                f.write("test content 2")
            
            files = walker.walk(temp_dir, on_progress=progress_callback)
            
            # Check that progress callback was called
            assert len(progress_calls) >= 1  # Should have at least one progress update
    
    def test_file_walker_get_statistics(self):
        """Test FileWalker.get_statistics"""
        walker = FileWalker()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test content")
            
            # Walk the directory to populate statistics
            walker.walk(temp_dir)
            
            stats = walker.get_statistics()
            assert isinstance(stats, dict)
            assert 'total_files' in stats
            assert 'total_directories' in stats
            assert 'total_errors' in stats
            assert 'total_time' in stats
            assert 'average_files_per_second' in stats
            assert stats['total_files'] >= 1  # At least 1 file
            assert stats['total_directories'] >= 1  # At least 1 directory
    
    def test_file_walker_enable_archive_support(self):
        """Test FileWalker.enable_archive_support and is_archive_support_enabled"""
        walker = FileWalker()
        
        # Initially enabled
        assert walker.is_archive_support_enabled() is True
        
        # Disable
        walker.enable_archive_support(False)
        assert walker.is_archive_support_enabled() is False
        
        # Re-enable
        walker.enable_archive_support(True)
        assert walker.is_archive_support_enabled() is True
    
    def test_file_walker_reset_counters(self):
        """Test FileWalker._reset_counters"""
        walker = FileWalker()
        
        # Manually set some values to test reset
        walker._file_count = 10
        walker._dir_count = 5
        walker._error_count = 2
        walker._start_time = 1000
        walker._last_update = 2000
        
        walker._reset_counters()
        
        assert walker._file_count == 0
        assert walker._dir_count == 0
        assert walker._error_count == 0
        assert walker._start_time == 0
        assert walker._last_update == 0


class TestCreateFileWalker:
    """Test cases for the create_file_walker function"""
    
    def test_create_file_walker_function(self):
        """Test create_file_walker function"""
        walker = create_file_walker()
        assert isinstance(walker, FileWalker)
        assert walker is not None
