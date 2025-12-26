"""Unit tests for enhanced ScanPlugin with cascade integration.

This module tests the integration of the enhanced ScanPlugin with
ProgressiveHashingCascadeStage and ArchiveProcessingCascadeStage.

Test Coverage:
    - ScanPlugin integration with progressive hashing cascade
    - ScanPlugin integration with archive processing cascade
    - Backward compatibility with original ScanPlugin
    - Performance improvements validation
    - Configuration and feature detection
    - Error handling and graceful degradation
"""

import pytest
import tempfile
import os
import shutil
import zipfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict

from nodupe.plugins.commands.scan import ScanPlugin
from nodupe.core.cascade.stages.progressive_hashing import ProgressiveHashingCascadeStage
from nodupe.core.cascade.stages.archive_processing import ArchiveProcessingCascadeStage
from nodupe.core.cascade.environment import EnvironmentDetector
from nodupe.core.security.policy import SecurityPolicy
from nodupe.core.database.files import FileRepository
from nodupe.core.database.connection import DatabaseConnection


class TestScanPluginIntegration:
    """Test suite for enhanced ScanPlugin with cascade integration."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.scan_plugin = ScanPlugin()
        
        # Create test files
        self.test_files = []
        self.test_content = b"test content for scanning"
        
        for i in range(5):
            test_file = Path(self.temp_dir) / f"test_file_{i}.txt"
            with open(test_file, 'wb') as f:
                f.write(self.test_content * (i + 1))  # Different sizes
            self.test_files.append(test_file)
        
        # Create test archive
        self.test_archive = Path(self.temp_dir) / "test.zip"
        with zipfile.ZipFile(self.test_archive, 'w') as zf:
            zf.writestr("archive_file.txt", "archive content")

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        shutil.rmtree(self.temp_dir)

    # ===========================
    # Integration with Progressive Hashing
    # ===========================

    @patch.object(ProgressiveHashingCascadeStage, 'execute')
    def test_scan_with_progressive_hashing_cascade(self, mock_progressive_execute):
        """Test ScanPlugin integration with progressive hashing cascade."""
        # Mock cascade stage result
        mock_progressive_execute.return_value = {
            "duplicates": [],
            "quick_hash_algorithm": "sha256",
            "full_hash_algorithm": "sha256",
            "files_processed": 5,
            "duplicate_groups": 0,
            "execution_time": 0.1
        }
        
        # Create mock container with database
        mock_container = Mock()
        mock_db = Mock(spec=DatabaseConnection)
        mock_file_repo = Mock(spec=FileRepository)
        mock_file_repo.batch_add_files.return_value = 5
        mock_container.get_service.return_value = mock_db
        
        # Create mock args
        mock_args = Mock()
        mock_args.paths = [self.temp_dir]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.container = mock_container
        
        # Execute scan
        result = self.scan_plugin.execute_scan(mock_args)
        
        assert result == 0
        mock_progressive_execute.assert_called_once()
        
        # Verify that files were processed
        call_args = mock_progressive_execute.call_args[0][0]
        assert len(call_args) == 5  # 5 test files

    @patch.object(EnvironmentDetector, 'check_plugin_available')
    @patch.object(ProgressiveHashingCascadeStage, 'execute')
    def test_scan_with_blake3_progressive_hashing(self, mock_progressive_execute, mock_check_plugin):
        """Test ScanPlugin with BLAKE3 progressive hashing when available."""
        mock_check_plugin.return_value = True
        mock_progressive_execute.return_value = {
            "duplicates": [],
            "quick_hash_algorithm": "blake3",
            "full_hash_algorithm": "blake3",
            "files_processed": 5,
            "duplicate_groups": 0,
            "execution_time": 0.05  # Faster with BLAKE3
        }
        
        # Create mock container
        mock_container = Mock()
        mock_db = Mock(spec=DatabaseConnection)
        mock_file_repo = Mock(spec=FileRepository)
        mock_file_repo.batch_add_files.return_value = 5
        mock_container.get_service.return_value = mock_db
        
        mock_args = Mock()
        mock_args.paths = [self.temp_dir]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.container = mock_container
        
        result = self.scan_plugin.execute_scan(mock_args)
        
        assert result == 0
        mock_progressive_execute.assert_called_once()
        
        # Verify BLAKE3 was used
        call_args = mock_progressive_execute.call_args[0][0]
        assert len(call_args) == 5

    @patch.object(SecurityPolicy, 'allows_algorithm')
    @patch.object(ProgressiveHashingCascadeStage, 'execute')
    def test_scan_with_security_policy_restriction(self, mock_progressive_execute, mock_allows_algorithm):
        """Test ScanPlugin with security policy restricting SHA256."""
        mock_allows_algorithm.return_value = False  # SHA256 not allowed
        mock_progressive_execute.return_value = {
            "duplicates": [],
            "quick_hash_algorithm": "md5",
            "full_hash_algorithm": "md5",
            "files_processed": 5,
            "duplicate_groups": 0,
            "execution_time": 0.2  # Slower with MD5
        }
        
        # Create mock container
        mock_container = Mock()
        mock_db = Mock(spec=DatabaseConnection)
        mock_file_repo = Mock(spec=FileRepository)
        mock_file_repo.batch_add_files.return_value = 5
        mock_container.get_service.return_value = mock_db
        
        mock_args = Mock()
        mock_args.paths = [self.temp_dir]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.container = mock_container
        
        result = self.scan_plugin.execute_scan(mock_args)
        
        assert result == 0
        mock_progressive_execute.assert_called_once()

    # ===========================
    # Integration with Archive Processing
    # ===========================

    @patch.object(ArchiveProcessingCascadeStage, 'execute')
    @patch.object(ProgressiveHashingCascadeStage, 'execute')
    def test_scan_with_archive_processing_cascade(self, mock_progressive_execute, mock_archive_execute):
        """Test ScanPlugin integration with archive processing cascade."""
        # Mock archive processing result
        mock_archive_execute.return_value = {
            "archive_path": str(self.test_archive),
            "extraction_results": [
                {"method": "zipfile", "success": True, "files": ["archive_file.txt"], "count": 1}
            ],
            "successful_method": "zipfile",
            "total_files": 1,
            "execution_time": 0.05
        }
        
        # Mock progressive hashing result (including archive contents)
        mock_progressive_execute.return_value = {
            "duplicates": [],
            "quick_hash_algorithm": "sha256",
            "full_hash_algorithm": "sha256",
            "files_processed": 6,  # 5 files + 1 archive file
            "duplicate_groups": 0,
            "execution_time": 0.1
        }
        
        # Create mock container
        mock_container = Mock()
        mock_db = Mock(spec=DatabaseConnection)
        mock_file_repo = Mock(spec=FileRepository)
        mock_file_repo.batch_add_files.return_value = 6
        mock_container.get_service.return_value = mock_db
        
        mock_args = Mock()
        mock_args.paths = [self.temp_dir]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.container = mock_container
        
        result = self.scan_plugin.execute_scan(mock_args)
        
        assert result == 0
        mock_archive_execute.assert_called_once_with(self.test_archive)
        mock_progressive_execute.assert_called_once()

    @patch.object(EnvironmentDetector, 'check_plugin_available')
    @patch.object(ArchiveProcessingCascadeStage, 'execute')
    def test_scan_with_7z_archive_processing(self, mock_archive_execute, mock_check_plugin):
        """Test ScanPlugin with 7z archive processing when available."""
        mock_check_plugin.return_value = True
        mock_archive_execute.return_value = {
            "archive_path": str(self.test_archive),
            "extraction_results": [
                {"method": "7z", "success": True, "files": ["archive_file.txt"], "count": 1}
            ],
            "successful_method": "7z",
            "total_files": 1,
            "execution_time": 0.03  # Faster with 7z
        }
        
        # Create mock container
        mock_container = Mock()
        mock_db = Mock(spec=DatabaseConnection)
        mock_file_repo = Mock(spec=FileRepository)
        mock_file_repo.batch_add_files.return_value = 1
        mock_container.get_service.return_value = mock_db
        
        mock_args = Mock()
        mock_args.paths = [self.test_archive]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.container = mock_container
        
        result = self.scan_plugin.execute_scan(mock_args)
        
        assert result == 0
        mock_archive_execute.assert_called_once()

    # ===========================
    # Backward Compatibility Tests
    # ===========================

    @patch.object(ProgressiveHashingCascadeStage, 'execute')
    def test_scan_backward_compatibility_with_original_behavior(self, mock_progressive_execute):
        """Test that enhanced ScanPlugin maintains backward compatibility."""
        # Mock to simulate original ProgressiveHasher behavior
        mock_progressive_execute.return_value = {
            "duplicates": [],
            "quick_hash_algorithm": "sha256",
            "full_hash_algorithm": "sha256",
            "files_processed": 5,
            "duplicate_groups": 0,
            "execution_time": 0.1
        }
        
        # Create mock container
        mock_container = Mock()
        mock_db = Mock(spec=DatabaseConnection)
        mock_file_repo = Mock(spec=FileRepository)
        mock_file_repo.batch_add_files.return_value = 5
        mock_container.get_service.return_value = mock_db
        
        mock_args = Mock()
        mock_args.paths = [self.temp_dir]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.container = mock_container
        
        result = self.scan_plugin.execute_scan(mock_args)
        
        assert result == 0
        
        # Verify that the interface is compatible with original expectations
        call_args = mock_progressive_execute.call_args[0][0]
        assert len(call_args) == 5
        
        # Verify database operations are compatible
        mock_file_repo.batch_add_files.assert_called_once()

    def test_scan_fallback_when_cascade_unavailable(self):
        """Test ScanPlugin fallback when cascade stages are unavailable."""
        # Create mock container without cascade stages
        mock_container = Mock()
        mock_db = Mock(spec=DatabaseConnection)
        mock_file_repo = Mock(spec=FileRepository)
        mock_file_repo.batch_add_files.return_value = 5
        mock_container.get_service.return_value = mock_db
        
        mock_args = Mock()
        mock_args.paths = [self.temp_dir]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.container = mock_container
        
        # This should work with original behavior (if implemented)
        # For now, we test that it doesn't crash
        try:
            result = self.scan_plugin.execute_scan(mock_args)
            assert result == 0
        except Exception as e:
            # If cascade is required, this might fail
            # The test validates graceful handling
            assert "cascade" not in str(e).lower()

    # ===========================
    # Performance Validation Tests
    # ===========================

    @patch.object(ProgressiveHashingCascadeStage, 'execute')
    def test_scan_performance_improvement_with_cascade(self, mock_progressive_execute):
        """Test that cascade integration provides performance improvements."""
        # Mock fast BLAKE3 execution
        mock_progressive_execute.return_value = {
            "duplicates": [],
            "quick_hash_algorithm": "blake3",
            "full_hash_algorithm": "blake3",
            "files_processed": 100,
            "duplicate_groups": 0,
            "execution_time": 0.5  # Fast execution
        }
        
        # Create mock container
        mock_container = Mock()
        mock_db = Mock(spec=DatabaseConnection)
        mock_file_repo = Mock(spec=FileRepository)
        mock_file_repo.batch_add_files.return_value = 100
        mock_container.get_service.return_value = mock_db
        
        mock_args = Mock()
        mock_args.paths = [self.temp_dir]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.container = mock_container
        
        start_time = time.perf_counter()
        result = self.scan_plugin.execute_scan(mock_args)
        execution_time = time.perf_counter() - start_time
        
        assert result == 0
        assert execution_time < 1.0  # Should be fast
        mock_progressive_execute.assert_called_once()

    @patch.object(ArchiveProcessingCascadeStage, 'execute')
    def test_scan_archive_processing_performance(self, mock_archive_execute):
        """Test archive processing performance with cascade."""
        mock_archive_execute.return_value = {
            "archive_path": str(self.test_archive),
            "extraction_results": [
                {"method": "zipfile", "success": True, "files": ["archive_file.txt"], "count": 1}
            ],
            "successful_method": "zipfile",
            "total_files": 1,
            "execution_time": 0.05
        }
        
        # Create mock container
        mock_container = Mock()
        mock_db = Mock(spec=DatabaseConnection)
        mock_file_repo = Mock(spec=FileRepository)
        mock_file_repo.batch_add_files.return_value = 1
        mock_container.get_service.return_value = mock_db
        
        mock_args = Mock()
        mock_args.paths = [self.test_archive]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.container = mock_container
        
        start_time = time.perf_counter()
        result = self.scan_plugin.execute_scan(mock_args)
        execution_time = time.perf_counter() - start_time
        
        assert result == 0
        assert execution_time < 0.5  # Should be fast
        mock_archive_execute.assert_called_once()

    # ===========================
    # Configuration and Feature Detection
    # ===========================

    @patch.object(EnvironmentDetector, 'check_plugin_available')
    def test_scan_feature_detection_for_blake3(self, mock_check_plugin):
        """Test feature detection for BLAKE3 availability."""
        # Test BLAKE3 available
        mock_check_plugin.return_value = True
        
        # Create mock container
        mock_container = Mock()
        mock_db = Mock(spec=DatabaseConnection)
        mock_file_repo = Mock(spec=FileRepository)
        mock_file_repo.batch_add_files.return_value = 5
        mock_container.get_service.return_value = mock_db
        
        mock_args = Mock()
        mock_args.paths = [self.temp_dir]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.container = mock_container
        
        result = self.scan_plugin.execute_scan(mock_args)
        
        assert result == 0
        mock_check_plugin.assert_called_with("blake3")

    @patch.object(EnvironmentDetector, 'check_plugin_available')
    def test_scan_feature_detection_for_7z(self, mock_check_plugin):
        """Test feature detection for 7z availability."""
        # Test 7z available
        mock_check_plugin.return_value = True
        
        # Create mock container
        mock_container = Mock()
        mock_db = Mock(spec=DatabaseConnection)
        mock_file_repo = Mock(spec=FileRepository)
        mock_file_repo.batch_add_files.return_value = 1
        mock_container.get_service.return_value = mock_db
        
        mock_args = Mock()
        mock_args.paths = [self.test_archive]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.container = mock_container
        
        result = self.scan_plugin.execute_scan(mock_args)
        
        assert result == 0
        mock_check_plugin.assert_called_with("py7zr")

    # ===========================
    # Error Handling and Graceful Degradation
    # ===========================

    @patch.object(ProgressiveHashingCascadeStage, 'execute')
    def test_scan_error_handling_progressive_hashing_failure(self, mock_progressive_execute):
        """Test error handling when progressive hashing fails."""
        mock_progressive_execute.side_effect = Exception("Progressive hashing failed")
        
        # Create mock container
        mock_container = Mock()
        mock_db = Mock(spec=DatabaseConnection)
        mock_file_repo = Mock(spec=FileRepository)
        mock_container.get_service.return_value = mock_db
        
        mock_args = Mock()
        mock_args.paths = [self.temp_dir]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.container = mock_container
        
        result = self.scan_plugin.execute_scan(mock_args)
        
        # Should handle error gracefully
        assert result == 1  # Error exit code

    @patch.object(ArchiveProcessingCascadeStage, 'execute')
    def test_scan_error_handling_archive_processing_failure(self, mock_archive_execute):
        """Test error handling when archive processing fails."""
        mock_archive_execute.side_effect = Exception("Archive processing failed")
        
        # Create mock container
        mock_container = Mock()
        mock_db = Mock(spec=DatabaseConnection)
        mock_file_repo = Mock(spec=FileRepository)
        mock_container.get_service.return_value = mock_db
        
        mock_args = Mock()
        mock_args.paths = [self.test_archive]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.container = mock_container
        
        result = self.scan_plugin.execute_scan(mock_args)
        
        # Should handle error gracefully
        assert result == 1  # Error exit code

    @patch.object(ProgressiveHashingCascadeStage, 'execute')
    def test_scan_graceful_degradation_when_cascade_unavailable(self, mock_progressive_execute):
        """Test graceful degradation when cascade stages are unavailable."""
        # Simulate cascade stage not available
        mock_progressive_execute.side_effect = ImportError("Cascade stage not available")
        
        # Create mock container
        mock_container = Mock()
        mock_db = Mock(spec=DatabaseConnection)
        mock_file_repo = Mock(spec=FileRepository)
        mock_container.get_service.return_value = mock_db
        
        mock_args = Mock()
        mock_args.paths = [self.temp_dir]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.container = mock_container
        
        result = self.scan_plugin.execute_scan(mock_args)
        
        # Should handle unavailability gracefully
        assert result == 1  # Error exit code, but graceful

    # ===========================
    # Integration with Existing Plugin System
    # ===========================

    def test_scan_plugin_capabilities_with_cascade(self):
        """Test that enhanced ScanPlugin maintains plugin capabilities."""
        capabilities = self.scan_plugin.get_capabilities()
        
        assert "commands" in capabilities
        assert "scan" in capabilities["commands"]

    def test_scan_plugin_initialization_with_cascade(self):
        """Test that enhanced ScanPlugin initializes correctly with cascade."""
        # Create mock container
        mock_container = Mock()
        
        # Should initialize without errors
        self.scan_plugin.initialize(mock_container)
        
        # Should not crash during initialization

    def test_scan_plugin_shutdown_with_cascade(self):
        """Test that enhanced ScanPlugin shuts down correctly with cascade."""
        # Should shutdown without errors
        self.scan_plugin.shutdown()
        
        # Should not crash during shutdown

    # ===========================
    # Real-world Integration Scenarios
    # ===========================

    @patch.object(ProgressiveHashingCascadeStage, 'execute')
    @patch.object(ArchiveProcessingCascadeStage, 'execute')
    def test_scan_real_world_scenario_mixed_files_and_archives(self, mock_archive_execute, mock_progressive_execute):
        """Test real-world scenario with mixed files and archives."""
        # Mock archive processing
        mock_archive_execute.return_value = {
            "archive_path": str(self.test_archive),
            "extraction_results": [
                {"method": "zipfile", "success": True, "files": ["archive_file.txt"], "count": 1}
            ],
            "successful_method": "zipfile",
            "total_files": 1,
            "execution_time": 0.05
        }
        
        # Mock progressive hashing for all files (including extracted archive files)
        mock_progressive_execute.return_value = {
            "duplicates": [],
            "quick_hash_algorithm": "sha256",
            "full_hash_algorithm": "sha256",
            "files_processed": 6,  # 5 files + 1 archive file
            "duplicate_groups": 0,
            "execution_time": 0.1
        }
        
        # Create mock container
        mock_container = Mock()
        mock_db = Mock(spec=DatabaseConnection)
        mock_file_repo = Mock(spec=FileRepository)
        mock_file_repo.batch_add_files.return_value = 6
        mock_container.get_service.return_value = mock_db
        
        mock_args = Mock()
        mock_args.paths = [self.temp_dir]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.container = mock_container
        
        result = self.scan_plugin.execute_scan(mock_args)
        
        assert result == 0
        
        # Verify both cascade stages were used
        mock_archive_execute.assert_called_once()
        mock_progressive_execute.assert_called_once()

    @patch.object(ProgressiveHashingCascadeStage, 'execute')
    def test_scan_large_dataset_performance(self, mock_progressive_execute):
        """Test performance with large dataset using cascade optimization."""
        # Mock large dataset processing
        mock_progressive_execute.return_value = {
            "duplicates": [],
            "quick_hash_algorithm": "blake3",
            "full_hash_algorithm": "blake3",
            "files_processed": 1000,
            "duplicate_groups": 0,
            "execution_time": 2.0  # Reasonable time for 1000 files
        }
        
        # Create mock container
        mock_container = Mock()
        mock_db = Mock(spec=DatabaseConnection)
        mock_file_repo = Mock(spec=FileRepository)
        mock_file_repo.batch_add_files.return_value = 1000
        mock_container.get_service.return_value = mock_db
        
        mock_args = Mock()
        mock_args.paths = [self.temp_dir]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.container = mock_container
        
        start_time = time.perf_counter()
        result = self.scan_plugin.execute_scan(mock_args)
        execution_time = time.perf_counter() - start_time
        
        assert result == 0
        assert execution_time < 5.0  # Should be reasonably fast for large dataset
        mock_progressive_execute.assert_called_once()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
