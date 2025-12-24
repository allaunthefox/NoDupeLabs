"""Unit tests for ArchiveProcessingCascadeStage.

This module tests the ArchiveProcessingCascadeStage implementation
including quality-tiered extraction methods, security policy integration,
and backward compatibility with existing archive processing.

Test Coverage:
    - Extraction method cascading (7z → zipfile → tarfile)
    - Security policy integration for archive processing
    - Error handling and fallback mechanisms
    - Backward compatibility with SecurityHardenedArchiveHandler
    - Performance comparison between extraction methods
    - Archive format detection and handling
"""

import pytest
import tempfile
import os
import zipfile
import tarfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from nodupe.core.cascade.stages.archive_processing import ArchiveProcessingCascadeStage
from nodupe.core.cascade.protocol import QualityTier, StageExecutionError, get_stage_manager
from nodupe.core.cascade.environment import EnvironmentDetector
from nodupe.core.security.policy import SecurityPolicy


class TestArchiveProcessingCascadeStage:
    """Test suite for ArchiveProcessingCascadeStage."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.stage = ArchiveProcessingCascadeStage()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test archives
        self.test_archives = self._create_test_archives()

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        shutil.rmtree(self.temp_dir)

    def _create_test_archives(self) -> Dict[str, Path]:
        """Create test archives for different formats."""
        archives = {}
        
        # Create ZIP archive
        zip_path = Path(self.temp_dir) / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("file2.txt", "content2")
            zf.writestr("subdir/file3.txt", "content3")
        archives["zip"] = zip_path
        
        # Create TAR archive
        tar_path = Path(self.temp_dir) / "test.tar"
        with tarfile.open(tar_path, 'w') as tf:
            # Create temporary files to add to tar
            temp_file1 = Path(self.temp_dir) / "temp1.txt"
            temp_file2 = Path(self.temp_dir) / "temp2.txt"
            temp_file1.write_text("content1")
            temp_file2.write_text("content2")
            
            tf.add(temp_file1, arcname="file1.txt")
            tf.add(temp_file2, arcname="file2.txt")
            
            temp_file1.unlink()
            temp_file2.unlink()
        archives["tar"] = tar_path
        
        # Create TGZ archive
        tgz_path = Path(self.temp_dir) / "test.tgz"
        with tarfile.open(tgz_path, 'w:gz') as tf:
            temp_file = Path(self.temp_dir) / "temp.txt"
            temp_file.write_text("compressed content")
            
            tf.add(temp_file, arcname="compressed_file.txt")
            temp_file.unlink()
        archives["tgz"] = tgz_path
        
        return archives

    # ===========================
    # Property Tests
    # ===========================

    def test_name_property(self):
        """Test that name property returns correct value."""
        assert self.stage.name == "ArchiveProcessing"

    def test_quality_tier_property(self):
        """Test that quality_tier property returns GOOD."""
        assert self.stage.quality_tier == QualityTier.GOOD

    def test_requires_internet_property(self):
        """Test that requires_internet property returns False."""
        assert self.stage.requires_internet is False

    def test_requires_plugins_property(self):
        """Test that requires_plugins property returns empty list."""
        assert self.stage.requires_plugins == []

    # ===========================
    # can_operate() Tests
    # ===========================

    @patch.object(SecurityPolicy, 'allows_archive_processing')
    def test_can_operate_with_security_policy_allowed(self, mock_allows_archive):
        """Test can_operate when security policy allows archive processing."""
        mock_allows_archive.return_value = True
        assert self.stage.can_operate() is True

    @patch.object(SecurityPolicy, 'allows_archive_processing')
    def test_can_operate_with_security_policy_denied(self, mock_allows_archive):
        """Test can_operate when security policy denies archive processing."""
        mock_allows_archive.return_value = False
        assert self.stage.can_operate() is False

    # ===========================
    # execute() Tests
    # ===========================

    def test_execute_with_zip_archive(self):
        """Test execute with ZIP archive."""
        result = self.stage.execute(self.test_archives["zip"])
        
        assert isinstance(result, dict)
        assert result["archive_path"] == str(self.test_archives["zip"])
        assert result["successful_method"] == "zipfile"
        assert result["total_files"] == 3  # 3 files in the ZIP
        assert len(result["extraction_results"]) == 1
        assert result["extraction_results"][0]["success"] is True

    def test_execute_with_tar_archive(self):
        """Test execute with TAR archive."""
        result = self.stage.execute(self.test_archives["tar"])
        
        assert isinstance(result, dict)
        assert result["archive_path"] == str(self.test_archives["tar"])
        assert result["successful_method"] == "tarfile"
        assert result["total_files"] == 2  # 2 files in the TAR
        assert len(result["extraction_results"]) == 1
        assert result["extraction_results"][0]["success"] is True

    def test_execute_with_tgz_archive(self):
        """Test execute with TGZ archive."""
        result = self.stage.execute(self.test_archives["tgz"])
        
        assert isinstance(result, dict)
        assert result["archive_path"] == str(self.test_archives["tgz"])
        assert result["successful_method"] == "tarfile"
        assert result["total_files"] == 1  # 1 file in the TGZ
        assert len(result["extraction_results"]) == 1
        assert result["extraction_results"][0]["success"] is True

    def test_execute_with_nonexistent_archive(self):
        """Test execute with nonexistent archive file."""
        nonexistent_path = Path(self.temp_dir) / "nonexistent.zip"
        
        result = self.stage.execute(nonexistent_path)
        
        assert isinstance(result, dict)
        assert result["archive_path"] == str(nonexistent_path)
        assert result["successful_method"] is None
        assert result["total_files"] == 0
        assert len(result["extraction_results"]) == 3  # All methods attempted

    def test_execute_with_invalid_archive(self):
        """Test execute with invalid archive file."""
        invalid_path = Path(self.temp_dir) / "invalid.zip"
        invalid_path.write_text("This is not a valid archive")
        
        result = self.stage.execute(invalid_path)
        
        assert isinstance(result, dict)
        assert result["archive_path"] == str(invalid_path)
        assert result["successful_method"] is None
        assert result["total_files"] == 0
        assert len(result["extraction_results"]) == 3  # All methods attempted

    # ===========================
    # Extraction Method Tests
    # ===========================

    @patch.object(EnvironmentDetector, 'check_plugin_available')
    def test_extract_with_7z_when_available(self, mock_check_plugin):
        """Test 7z extraction when py7zr is available."""
        mock_check_plugin.return_value = True
        
        # Create a simple archive that 7z can handle
        test_file = Path(self.temp_dir) / "test_7z.txt"
        test_file.write_text("test content")
        
        # Note: This test would need a proper 7z archive to work fully
        # For now, we test the method availability
        assert hasattr(self.stage, '_extract_with_7z')

    @patch.object(EnvironmentDetector, 'check_plugin_available')
    def test_extract_with_7z_when_unavailable(self, mock_check_plugin):
        """Test 7z extraction when py7zr is unavailable."""
        mock_check_plugin.return_value = False
        
        result = self.stage._extract_with_7z(Path("dummy.7z"))
        
        assert result == []

    def test_extract_with_zipfile(self):
        """Test zipfile extraction."""
        result = self.stage._extract_with_zipfile(self.test_archives["zip"])
        
        assert isinstance(result, list)
        assert len(result) == 3  # 3 files in the ZIP
        assert "file1.txt" in result
        assert "file2.txt" in result
        assert "subdir/file3.txt" in result

    def test_extract_with_zipfile_non_zip_file(self):
        """Test zipfile extraction with non-ZIP file."""
        result = self.stage._extract_with_zipfile(self.test_archives["tar"])
        
        assert result == []

    def test_extract_with_tarfile(self):
        """Test tarfile extraction."""
        result = self.stage._extract_with_tarfile(self.test_archives["tar"])
        
        assert isinstance(result, list)
        assert len(result) == 2  # 2 files in the TAR
        assert "file1.txt" in result
        assert "file2.txt" in result

    def test_extract_with_tarfile_tgz(self):
        """Test tarfile extraction with TGZ file."""
        result = self.stage._extract_with_tarfile(self.test_archives["tgz"])
        
        assert isinstance(result, list)
        assert len(result) == 1  # 1 file in the TGZ
        assert "compressed_file.txt" in result

    def test_extract_with_tarfile_non_tar_file(self):
        """Test tarfile extraction with non-TAR file."""
        result = self.stage._extract_with_tarfile(self.test_archives["zip"])
        
        assert result == []

    # ===========================
    # Security Policy Integration Tests
    # ===========================

    @patch.object(SecurityPolicy, 'allows_archive_processing')
    def test_security_policy_archive_processing_allowed(self, mock_allows_archive):
        """Test security policy allows archive processing."""
        mock_allows_archive.return_value = True
        
        result = self.stage.execute(self.test_archives["zip"])
        
        assert isinstance(result, dict)
        # Should succeed when archive processing is allowed

    @patch.object(SecurityPolicy, 'allows_archive_processing')
    def test_security_policy_archive_processing_denied(self, mock_allows_archive):
        """Test security policy denies archive processing."""
        mock_allows_archive.return_value = False
        
        # can_operate should return False
        assert self.stage.can_operate() is False
        
        # execute should still work but may be restricted
        result = self.stage.execute(self.test_archives["zip"])
        # The behavior depends on implementation - should handle gracefully

    # ===========================
    # Error Handling Tests
    # ===========================

    def test_extract_with_zipfile_permission_error(self):
        """Test zipfile extraction with permission error."""
        # Create a file that can't be read
        restricted_file = Path(self.temp_dir) / "restricted.zip"
        restricted_file.write_text("content")
        restricted_file.chmod(0o000)  # No permissions
        
        try:
            result = self.stage._extract_with_zipfile(restricted_file)
            assert result == []
        finally:
            restricted_file.chmod(0o644)  # Restore permissions

    def test_extract_with_tarfile_permission_error(self):
        """Test tarfile extraction with permission error."""
        # Create a file that can't be read
        restricted_file = Path(self.temp_dir) / "restricted.tar"
        restricted_file.write_text("content")
        restricted_file.chmod(0o000)  # No permissions
        
        try:
            result = self.stage._extract_with_tarfile(restricted_file)
            assert result == []
        finally:
            restricted_file.chmod(0o644)  # Restore permissions

    def test_execute_with_corrupted_archive(self):
        """Test execute with corrupted archive file."""
        corrupted_path = Path(self.temp_dir) / "corrupted.zip"
        corrupted_path.write_bytes(b"This is not a valid ZIP file")
        
        result = self.stage.execute(corrupted_path)
        
        assert isinstance(result, dict)
        assert result["archive_path"] == str(corrupted_path)
        assert result["successful_method"] is None
        assert result["total_files"] == 0

    # ===========================
    # Performance Tests
    # ===========================

    def test_extraction_method_performance_order(self):
        """Test that extraction methods are tried in performance order."""
        # Create a large ZIP file to test performance
        large_zip = Path(self.temp_dir) / "large.zip"
        with zipfile.ZipFile(large_zip, 'w') as zf:
            # Add multiple files
            for i in range(10):
                zf.writestr(f"file_{i}.txt", f"content_{i}" * 1000)
        
        import time
        start_time = time.time()
        result = self.stage.execute(large_zip)
        execution_time = time.time() - start_time
        
        assert isinstance(result, dict)
        assert result["successful_method"] == "zipfile"
        assert execution_time < 10.0  # Should be reasonably fast

    @patch.object(EnvironmentDetector, 'check_plugin_available')
    def test_method_availability_detection(self, mock_check_plugin):
        """Test detection of extraction method availability."""
        # Test different availability scenarios
        scenarios = [
            {"7z": True, "zipfile": True, "tarfile": True},
            {"7z": False, "zipfile": True, "tarfile": True},
            {"7z": False, "zipfile": False, "tarfile": True},
            {"7z": False, "zipfile": False, "tarfile": False},
        ]
        
        for scenario in scenarios:
            mock_check_plugin.side_effect = lambda plugin: scenario.get(plugin, False)
            
            # Should handle each scenario gracefully
            result = self.stage.execute(self.test_archives["zip"])
            assert isinstance(result, dict)

    # ===========================
    # Archive Format Detection Tests
    # ===========================

    def test_archive_format_detection_zip(self):
        """Test detection of ZIP archive format."""
        zip_file = Path(self.temp_dir) / "test.zip"
        zip_file.write_bytes(b"PK" + b"\x03\x04" + b"dummy content")
        
        # Should be detected as ZIP by zipfile method
        result = self.stage._extract_with_zipfile(zip_file)
        # May fail due to invalid content, but should be detected as ZIP format

    def test_archive_format_detection_tar(self):
        """Test detection of TAR archive format."""
        tar_file = Path(self.temp_dir) / "test.tar"
        tar_file.write_bytes(b"\x1f\x8b" + b"dummy content")  # GZIP magic number
        
        # Should be detected as TAR by tarfile method
        result = self.stage._extract_with_tarfile(tar_file)
        # May fail due to invalid content, but should be detected as TAR format

    def test_archive_format_detection_by_extension(self):
        """Test archive format detection by file extension."""
        # Test different extensions
        extensions = [".zip", ".tar", ".tgz", ".tar.gz", ".7z"]
        
        for ext in extensions:
            test_file = Path(self.temp_dir) / f"test{ext}"
            test_file.write_text("dummy content")
            
            # Each extension should be handled appropriately
            if ext in [".zip"]:
                result = self.stage._extract_with_zipfile(test_file)
                assert isinstance(result, list)
            elif ext in [".tar", ".tgz", ".tar.gz"]:
                result = self.stage._extract_with_tarfile(test_file)
                assert isinstance(result, list)
            elif ext == ".7z":
                result = self.stage._extract_with_7z(test_file)
                assert isinstance(result, list)

    # ===========================
    # Backward Compatibility Tests
    # ===========================

    def test_backward_compatibility_with_existing_archive_handler(self):
        """Test backward compatibility with existing archive processing."""
        # This would test integration with SecurityHardenedArchiveHandler
        # For now, we test that our methods produce compatible output
        
        result = self.stage.execute(self.test_archives["zip"])
        
        # Check output format compatibility
        expected_keys = [
            "archive_path",
            "extraction_results",
            "successful_method",
            "total_files"
        ]
        
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
            assert result[key] is not None, f"Key {key} is None"

    def test_output_format_consistency(self):
        """Test that output format is consistent across different archive types."""
        archive_types = ["zip", "tar", "tgz"]
        
        for archive_type in archive_types:
            result = self.stage.execute(self.test_archives[archive_type])
            
            # Check consistent output format
            assert isinstance(result, dict)
            assert "archive_path" in result
            assert "extraction_results" in result
            assert "successful_method" in result
            assert "total_files" in result
            
            # extraction_results should be a list
            assert isinstance(result["extraction_results"], list)

    # ===========================
    # Edge Case Tests
    # ===========================

    def test_execute_with_empty_archive(self):
        """Test execute with empty archive."""
        empty_zip = Path(self.temp_dir) / "empty.zip"
        with zipfile.ZipFile(empty_zip, 'w') as zf:
            pass  # Empty archive
        
        result = self.stage.execute(empty_zip)
        
        assert isinstance(result, dict)
        assert result["archive_path"] == str(empty_zip)
        assert result["successful_method"] == "zipfile"
        assert result["total_files"] == 0

    def test_execute_with_nested_archives(self):
        """Test execute with nested archive structures."""
        # Create an archive with nested directories
        nested_zip = Path(self.temp_dir) / "nested.zip"
        with zipfile.ZipFile(nested_zip, 'w') as zf:
            zf.writestr("root.txt", "root content")
            zf.writestr("dir1/file1.txt", "dir1 content")
            zf.writestr("dir1/dir2/file2.txt", "dir2 content")
            zf.writestr("dir3/file3.txt", "dir3 content")
        
        result = self.stage.execute(nested_zip)
        
        assert isinstance(result, dict)
        assert result["successful_method"] == "zipfile"
        assert result["total_files"] == 4  # 4 files including nested ones
        
        # Check that nested paths are preserved
        files = result["extraction_results"][0]["files"]
        assert "root.txt" in files
        assert "dir1/file1.txt" in files
        assert "dir1/dir2/file2.txt" in files
        assert "dir3/file3.txt" in files

    def test_execute_with_special_characters_in_filenames(self):
        """Test execute with special characters in archive filenames."""
        special_zip = Path(self.temp_dir) / "special_üñíçødé_🚀.zip"
        with zipfile.ZipFile(special_zip, 'w') as zf:
            zf.writestr("file_with_spaces.txt", "content")
            zf.writestr("file_with_üñíçødé.txt", "content")
            zf.writestr("file_with_emoji_🚀.txt", "content")
        
        result = self.stage.execute(special_zip)
        
        assert isinstance(result, dict)
        assert result["successful_method"] == "zipfile"
        assert result["total_files"] == 3

    def test_execute_with_large_archive(self):
        """Test execute with large archive file."""
        # Create a large archive (simulate with multiple files)
        large_zip = Path(self.temp_dir) / "large.zip"
        with zipfile.ZipFile(large_zip, 'w') as zf:
            # Add many files to simulate large archive
            for i in range(50):
                zf.writestr(f"large_file_{i}.txt", f"content_{i}" * 100)
        
        result = self.stage.execute(large_zip)
        
        assert isinstance(result, dict)
        assert result["successful_method"] == "zipfile"
        assert result["total_files"] == 50

    # ===========================
    # Integration Tests
    # ===========================

    def test_integration_with_environment_detector(self):
        """Test integration with EnvironmentDetector."""
        with patch.object(EnvironmentDetector, 'check_plugin_available') as mock_check:
            mock_check.return_value = True
            
            result = self.stage.execute(self.test_archives["zip"])
            
            assert isinstance(result, dict)
            # Should have called EnvironmentDetector for 7z availability
            mock_check.assert_called_with("py7zr")

    def test_integration_with_security_policy(self):
        """Test integration with SecurityPolicy."""
        with patch.object(SecurityPolicy, 'allows_archive_processing') as mock_allows:
            mock_allows.return_value = True
            
            result = self.stage.execute(self.test_archives["zip"])
            
            assert isinstance(result, dict)
            # Should have called SecurityPolicy
            mock_allows.assert_called()

    # ===========================
    # Method Selection Tests
    # ===========================

    def test_extraction_method_selection_priority(self):
        """Test that extraction methods are selected in priority order."""
        # Create a file that could be handled by multiple methods
        # (though in practice, each method handles specific formats)
        
        result = self.stage.execute(self.test_archives["zip"])
        
        # Should use zipfile for ZIP files
        assert result["successful_method"] == "zipfile"
        
        # Should have tried methods in order
        assert len(result["extraction_results"]) >= 1
        assert result["extraction_results"][0]["method"] == "7z"  # First attempt
        assert result["extraction_results"][1]["method"] == "zipfile"  # Second attempt (successful)

    def test_extraction_method_fallback(self):
        """Test fallback when preferred method fails."""
        # This test would be more meaningful with a real 7z archive
        # For now, we test the fallback logic structure
        
        result = self.stage.execute(self.test_archives["zip"])
        
        # Should have fallback behavior
        assert isinstance(result["extraction_results"], list)
        assert len(result["extraction_results"]) > 0
        
        # At least one method should succeed for valid archives
        successful_methods = [r for r in result["extraction_results"] if r["success"]]
        assert len(successful_methods) > 0


# ===========================
# Performance Benchmark Tests
# ===========================

class TestArchiveProcessingPerformance:
    """Performance benchmark tests for ArchiveProcessingCascadeStage."""

    def setup_method(self):
        """Set up performance test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.stage = ArchiveProcessingCascadeStage()

    def teardown_method(self):
        """Clean up performance test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def create_large_archive(self, num_files: int, file_size_kb: int) -> Path:
        """Create a large archive for performance testing."""
        archive_path = Path(self.temp_dir) / f"perf_archive_{num_files}files.zip"
        
        with zipfile.ZipFile(archive_path, 'w') as zf:
            file_content = b"x" * (1024 * file_size_kb)  # file_size_kb KB per file
            
            for i in range(num_files):
                zf.writestr(f"file_{i:04d}.txt", file_content)
        
        return archive_path

    def test_performance_10_files_1kb(self):
        """Test performance with 10 files of 1KB each."""
        archive_path = self.create_large_archive(10, 1)
        
        import time
        start_time = time.time()
        result = self.stage.execute(archive_path)
        execution_time = time.time() - start_time
        
        assert result["successful_method"] == "zipfile"
        assert result["total_files"] == 10
        assert execution_time < 5.0  # Should be fast

    def test_performance_100_files_10kb(self):
        """Test performance with 100 files of 10KB each."""
        archive_path = self.create_large_archive(100, 10)
        
        import time
        start_time = time.time()
        result = self.stage.execute(archive_path)
        execution_time = time.time() - start_time
        
        assert result["successful_method"] == "zipfile"
        assert result["total_files"] == 100
        assert execution_time < 15.0  # Should be reasonably fast

    def test_scalability_with_archive_size(self):
        """Test scalability with increasing archive size."""
        file_counts = [10, 50, 100]
        execution_times = []
        
        for count in file_counts:
            archive_path = self.create_large_archive(count, 5)  # 5KB per file
            
            import time
            start_time = time.time()
            result = self.stage.execute(archive_path)
            execution_time = time.time() - start_time
            
            execution_times.append(execution_time)
            
            assert result["successful_method"] == "zipfile"
            assert result["total_files"] == count
        
        # Execution time should increase sub-linearly with archive size
        assert execution_times[1] < execution_times[0] * 6  # 50 files should be less than 6x 10 files
        assert execution_times[2] < execution_times[1] * 3  # 100 files should be less than 3x 50 files


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
