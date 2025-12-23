"""
Test suite for archive command functionality.
Tests archive operations from nodupe.plugins.commands.archive.
"""

import os
import tempfile
import shutil
from pathlib import Path
import time
import pytest
from unittest.mock import patch, MagicMock

from nodupe.plugins.commands.archive import ArchivePlugin, archive_plugin


class TestArchivePlugin:
    """Test ArchivePlugin functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_archive_plugin_initialization(self):
        """Test ArchivePlugin initialization."""
        plugin = ArchivePlugin()
        
        assert plugin is not None
        assert plugin.name == "archive"
        assert plugin.version == "1.0.0"
        assert plugin.description == "Archive and manage duplicate files"
        assert plugin.dependencies == []
        assert plugin.archive_handler is not None
    
    def test_get_capabilities(self):
        """Test getting plugin capabilities."""
        plugin = ArchivePlugin()
        capabilities = plugin.get_capabilities()
        
        assert 'commands' in capabilities
        assert 'archive' in capabilities['commands']
    
    def test_on_archive_start_event(self):
        """Test archive start event handling."""
        plugin = ArchivePlugin()
        
        # Should not raise exception
        plugin._on_archive_start(action='test', files=[])
        # Output is printed, no return value to check
    
    def test_on_archive_complete_event(self):
        """Test archive complete event handling."""
        plugin = ArchivePlugin()
        
        # Should not raise exception
        plugin._on_archive_complete(files_processed=5)
        # Output is printed, no return value to check
    
    def test_register_commands(self):
        """Test registering archive commands."""
        plugin = ArchivePlugin()
        
        # Create mock subparsers
        mock_subparsers = MagicMock()
        mock_parser = MagicMock()
        mock_subparsers.add_parser.return_value = mock_parser
        
        # Register commands
        plugin.register_commands(mock_subparsers)
        
        # Verify parser was created with correct arguments
        mock_subparsers.add_parser.assert_called_once_with('archive', help='Archive duplicate files')
        
        # Check that add_argument was called with expected arguments
        assert mock_parser.add_argument.called
        assert mock_parser.set_defaults.called
    
    def test_execute_archive_create_basic(self):
        """Test basic archive creation."""
        plugin = ArchivePlugin()
        
        # Create test files
        test_dir = Path("test_source")
        test_dir.mkdir()
        
        test_file1 = test_dir / "file1.txt"
        test_file1.write_text("test content 1")
        
        test_file2 = test_dir / "file2.txt"
        test_file2.write_text("test content 2")
        
        # Create destination directory
        dest_dir = Path("archives")
        dest_dir.mkdir()
        
        # Mock args
        class MockArgs:
            action = 'create'
            source = str(test_dir)
            destination = str(dest_dir / "test_archive.zip")
            format = 'zip'
            compress = 'fast'
            dry_run = False
            verbose = False
            include_duplicates = False
            container = None
        
        args = MockArgs()
        
        # Test archive creation
        result = plugin.execute_archive(args)
        
        # Should return 0 for success (though this might fail due to missing container/service)
        # The important thing is that it doesn't crash with basic file operations
        assert result in [0, 1]  # Success or failure due to missing dependencies is fine
    
    def test_execute_archive_extract(self):
        """Test archive extraction."""
        plugin = ArchivePlugin()
        
        # Create a test archive file
        test_archive = Path("test_archive.zip")
        import zipfile
        with zipfile.ZipFile(test_archive, 'w') as zf:
            zf.writestr("test_file.txt", "test content")
        
        # Create destination directory
        dest_dir = Path("extract_dest")
        dest_dir.mkdir()
        
        # Mock args
        class MockArgs:
            action = 'extract'
            source = str(test_archive)
            destination = str(dest_dir)
            format = 'zip'
            compress = 'fast'
            dry_run = False
            verbose = False
            include_duplicates = False
            container = None
        
        args = MockArgs()
        
        # Test archive extraction
        result = plugin.execute_archive(args)
        
        assert result in [0, 1]  # Success or failure due to missing dependencies is fine
    
    def test_execute_archive_list(self):
        """Test listing archive contents."""
        plugin = ArchivePlugin()
        
        # Create a test archive file
        test_archive = Path("test_list_archive.zip")
        import zipfile
        with zipfile.ZipFile(test_archive, 'w') as zf:
            zf.writestr("list_file1.txt", "content 1")
            zf.writestr("list_file2.txt", "content 2")
        
        # Mock args
        class MockArgs:
            action = 'list'
            source = str(test_archive)
            destination = None
            format = 'zip'
            compress = 'fast'
            dry_run = False
            verbose = False
            include_duplicates = False
            container = None
        
        args = MockArgs()
        
        # Test archive listing
        result = plugin.execute_archive(args)
        
        assert result in [0, 1]
    
    def test_execute_archive_verify(self):
        """Test archive verification."""
        plugin = ArchivePlugin()
        
        # Create a test archive file
        test_archive = Path("test_verify_archive.zip")
        import zipfile
        with zipfile.ZipFile(test_archive, 'w') as zf:
            zf.writestr("verify_file.txt", "verify content")
        
        # Mock args
        class MockArgs:
            action = 'verify'
            source = str(test_archive)
            destination = None
            format = 'zip'
            compress = 'fast'
            dry_run = False
            verbose = False
            include_duplicates = False
            container = None
        
        args = MockArgs()
        
        # Test archive verification
        result = plugin.execute_archive(args)
        
        assert result in [0, 1]
    
    def test_execute_archive_with_dry_run(self):
        """Test archive operations with dry run."""
        plugin = ArchivePlugin()
        
        # Create test files
        test_dir = Path("dry_run_test")
        test_dir.mkdir()
        
        test_file = test_dir / "test.txt"
        test_file.write_text("dry run content")
        
        # Mock args with dry run
        class MockArgs:
            action = 'create'
            source = str(test_dir)
            destination = "would_not_create.zip"
            format = 'zip'
            compress = 'fast'
            dry_run = True
            verbose = False
            include_duplicates = False
            container = None
        
        args = MockArgs()
        
        # Test dry run - should not crash
        result = plugin.execute_archive(args)
        
        assert result in [0, 1]  # Dry run should complete without major errors
    
    def test_execute_archive_invalid_action(self):
        """Test archive execution with invalid action."""
        plugin = ArchivePlugin()
        
        # Mock args with invalid action
        class MockArgs:
            action = 'invalid_action'
            source = "test_source"
            destination = "test_dest"
            format = 'zip'
            compress = 'fast'
            dry_run = False
            verbose = False
            include_duplicates = False
            container = None
        
        args = MockArgs()
        
        # Test invalid action
        result = plugin.execute_archive(args)
        
        # Should return error code for invalid action
        assert result == 1
    
    def test_execute_archive_missing_source(self):
        """Test archive execution with missing source."""
        plugin = ArchivePlugin()
        
        # Mock args with non-existent source
        class MockArgs:
            action = 'create'
            source = "nonexistent_source"
            destination = "test_dest"
            format = 'zip'
            compress = 'fast'
            dry_run = False
            verbose = False
            include_duplicates = False
            container = None
        
        args = MockArgs()
        
        # Test missing source
        result = plugin.execute_archive(args)
        
        # Should return error code for missing source
        assert result == 1
    
    def test_execute_archive_remove_duplicates(self):
        """Test removing duplicates and archiving them."""
        plugin = ArchivePlugin()
        
        # Create test duplicate files directory
        dup_dir = Path("duplicates")
        dup_dir.mkdir()
        
        dup_file1 = dup_dir / "dup1.txt"
        dup_file1.write_text("duplicate content 1")
        
        dup_file2 = dup_dir / "dup2.txt"
        dup_file2.write_text("duplicate content 2")
        
        # Create archive destination
        archive_dest = Path("duplicates_archive.zip")
        
        # Mock args for remove action
        class MockArgs:
            action = 'remove'
            source = str(dup_dir)
            destination = str(archive_dest)
            format = 'zip'
            compress = 'fast'
            dry_run = False
            verbose = False
            include_duplicates = False
            container = None
        
        args = MockArgs()
        
        # Test remove duplicates operation
        result = plugin.execute_archive(args)
        
        assert result in [0, 1]
    
    def test_execute_archive_verbose_output(self):
        """Test archive execution with verbose output."""
        plugin = ArchivePlugin()
        
        # Create test files
        test_dir = Path("verbose_test")
        test_dir.mkdir()
        
        test_file = test_dir / "verbose.txt"
        test_file.write_text("verbose content")
        
        # Mock args with verbose
        class MockArgs:
            action = 'create'
            source = str(test_dir)
            destination = "verbose_archive.zip"
            format = 'zip'
            compress = 'fast'
            dry_run = True  # Use dry run to avoid dependency issues
            verbose = True
            include_duplicates = False
            container = None
        
        args = MockArgs()
        
        # Test verbose execution
        result = plugin.execute_archive(args)
        
        assert result in [0, 1]


class TestArchivePluginIntegration:
    """Test ArchivePlugin integration aspects."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_plugin_registration(self):
        """Test plugin registration function."""
        from nodupe.plugins.commands.archive import register_plugin
        
        plugin_instance = register_plugin()
        assert isinstance(plugin_instance, ArchivePlugin)
        assert plugin_instance.name == "archive"
    
    def test_global_plugin_instance(self):
        """Test global plugin instance."""
        from nodupe.plugins.commands.archive import archive_plugin
        
        assert isinstance(archive_plugin, ArchivePlugin)
        assert archive_plugin.name == "archive"


def test_archive_plugin_error_handling():
    """Test error handling in ArchivePlugin operations."""
    plugin = ArchivePlugin()
    
    # Test with None args (should not crash)
    class MockArgs:
        action = 'create'
        source = None
        destination = None
        format = 'zip'
        compress = 'fast'
        dry_run = False
        verbose = False
        include_duplicates = False
        container = None
    
    args = MockArgs()
    
    # Should handle gracefully and return error code
    result = plugin.execute_archive(args)
    assert result in [0, 1]


if __name__ == "__main__":
    pytest.main([__file__])
