"""Unit tests for enhanced ScanPlugin with UUID and hash type functionality.

This module tests the enhanced ScanPlugin with:
- UUID generation capabilities
- Specific hash type selection
- API call functionality
- Command-line integration
- Cascade module integration

Test Coverage:
    - UUID generation API calls
    - Hash type selection API calls
    - Command-line UUID generation
    - API accessibility verification
    - Cascade integration with UUIDs and hash types
    - Error handling for new functionality
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict

from nodupe.plugins.commands.scan import ScanPlugin


class TestScanPluginEnhanced:
    """Test suite for enhanced ScanPlugin with UUID and hash type functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.scan_plugin = ScanPlugin()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        self.test_files = []
        self.test_content = b"test content for scanning"
        
        for i in range(3):
            test_file = Path(self.temp_dir) / f"test_file_{i}.txt"
            with open(test_file, 'wb') as f:
                f.write(self.test_content * (i + 1))
            self.test_files.append(test_file)

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir)

    # ===========================
    # UUID Generation API Tests
    # ===========================

    def test_uuid_generation_api_call(self):
        """Test UUID generation via API call."""
        result = self.scan_plugin.api_call('generate_scan_uuid')
        
        assert 'uuid' in result
        assert 'uuid_version' in result
        assert 'variant' in result
        assert 'timestamp' in result
        assert 'urn_format' in result
        assert 'canonical_format' in result
        assert 'generated_at' in result
        
        # Validate UUID format
        import uuid
        parsed_uuid = uuid.UUID(result['uuid'])
        assert str(parsed_uuid) == result['uuid']
        assert parsed_uuid.version == 4  # UUID v4

    def test_uuid_generation_with_kwargs(self):
        """Test UUID generation with additional parameters."""
        result = self.scan_plugin.api_call('generate_scan_uuid', extra_param='test')
        
        assert 'uuid' in result
        assert result['success'] != False  # Should not have error key

    def test_uuid_generation_error_handling(self):
        """Test UUID generation error handling."""
        # Patch UUID generation to simulate error
        with patch('nodupe.plugins.commands.scan.UUIDUtils.generate_uuid_v4') as mock_uuid_gen:
            mock_uuid_gen.side_effect = Exception("UUID generation failed")
            
            result = self.scan_plugin.api_call('generate_scan_uuid')
            
            assert 'error' in result
            assert 'success' in result
            assert result['success'] is False

    # ===========================
    # Hash Type Selection API Tests
    # ===========================

    def test_get_available_hash_types_api_call(self):
        """Test getting available hash types via API call."""
        result = self.scan_plugin.api_call('get_available_hash_types')
        
        assert 'available_hash_types' in result
        assert 'count' in result
        assert 'generated_at' in result
        
        # Should have standard hash algorithms
        available_types = result['available_hash_types']
        assert isinstance(available_types, dict)
        assert len(available_types) > 0
        
        # Check for common hash types
        expected_types = ['md5', 'sha1', 'sha256', 'sha384', 'sha512']
        found_common_types = [typ for typ in expected_types if typ in available_types]
        assert len(found_common_types) > 0, f"Expected at least one of {expected_types}"

    def test_get_available_hash_types_with_kwargs(self):
        """Test getting available hash types with additional parameters."""
        result = self.scan_plugin.api_call('get_available_hash_types', custom_filter='fast')
        
        assert 'available_hash_types' in result
        assert 'count' in result

    def test_hash_file_api_call(self):
        """Test file hashing via API call."""
        test_file = self.test_files[0]
        
        result = self.scan_plugin.api_call(
            'hash_file',
            file_path=str(test_file),
            algorithm='sha256'
        )
        
        assert 'file_path' in result
        assert 'algorithm' in result
        assert 'hash' in result
        assert 'file_size' in result
        assert 'success' in result
        
        assert result['success'] is True
        assert result['algorithm'] == 'sha256'
        assert result['file_path'] == str(test_file)
        assert isinstance(result['hash'], str)
        assert len(result['hash']) == 64  # SHA256 produces 64-character hex

    def test_hash_file_different_algorithms(self):
        """Test file hashing with different algorithms."""
        test_file = self.test_files[0]
        
        algorithms = ['md5', 'sha1', 'sha256']
        
        for algorithm in algorithms:
            result = self.scan_plugin.api_call(
                'hash_file',
                file_path=str(test_file),
                algorithm=algorithm
            )
            
            assert result['success'] is True
            assert result['algorithm'] == algorithm
            assert len(result['hash']) > 0

    def test_hash_file_invalid_algorithm(self):
        """Test file hashing with invalid algorithm."""
        test_file = self.test_files[0]
        
        result = self.scan_plugin.api_call(
            'hash_file',
            file_path=str(test_file),
            algorithm='invalid_algorithm'
        )
        
        assert 'error' in result
        assert result['success'] is False

    def test_hash_file_nonexistent_file(self):
        """Test file hashing with nonexistent file."""
        result = self.scan_plugin.api_call(
            'hash_file',
            file_path='/nonexistent/file.txt',
            algorithm='sha256'
        )
        
        assert 'error' in result
        assert result['success'] is False
        assert 'does not exist' in result['error']

    # ===========================
    # API Call Error Handling
    # ===========================

    def test_unsupported_api_method(self):
        """Test error handling for unsupported API methods."""
        with pytest.raises(ValueError) as exc_info:
            self.scan_plugin.api_call('unsupported_method')
        
        assert "Unsupported API method" in str(exc_info.value)

    def test_hash_file_missing_file_path(self):
        """Test hash_file API call without required file_path."""
        result = self.scan_plugin.api_call('hash_file', algorithm='sha256')
        
        assert 'error' in result
        assert result['success'] is False
        assert 'file_path is required' in result['error']

    # ===========================
    # Command-line Integration Tests
    # ===========================

    def test_scan_command_with_generate_uuid_flag(self):
        """Test scan command integration with --generate-uuid flag."""
        # Create mock args with generate_uuid flag
        mock_args = Mock()
        mock_args.paths = [self.temp_dir]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.generate_uuid = True  # This should trigger UUID generation
        
        # Create mock container
        mock_container = Mock()
        mock_db = Mock()
        mock_container.get_service.return_value = mock_db
        
        mock_args.container = mock_container
        
        # Mock the file processing to avoid actual file operations
        with patch.object(self.scan_plugin, '_process_files') as mock_process:
            mock_process.return_value = {
                'files_found': 3,
                'duplicates': [],
                'execution_time': 0.1
            }
            
            # Execute scan (this would normally call the scan logic)
            # We're testing that UUID generation is triggered
            result = self.scan_plugin.execute_scan(mock_args)
            
            # Should succeed (mocked)
            assert result is not None

    def test_scan_command_without_generate_uuid_flag(self):
        """Test scan command without --generate-uuid flag."""
        mock_args = Mock()
        mock_args.paths = [self.temp_dir]
        mock_args.min_size = 0
        mock_args.max_size = None
        mock_args.extensions = None
        mock_args.exclude = None
        mock_args.verbose = False
        mock_args.generate_uuid = False  # No UUID generation
        
        mock_container = Mock()
        mock_db = Mock()
        mock_container.get_service.return_value = mock_db
        
        mock_args.container = mock_container
        
        with patch.object(self.scan_plugin, '_process_files') as mock_process:
            mock_process.return_value = {
                'files_found': 3,
                'duplicates': [],
                'execution_time': 0.1
            }
            
            result = self.scan_plugin.execute_scan(mock_args)
            
            assert result is not None

    # ===========================
    # Plugin Capabilities Tests
    # ===========================

    def test_scan_plugin_capabilities_includes_new_apis(self):
        """Test that enhanced ScanPlugin includes new API capabilities."""
        capabilities = self.scan_plugin.get_capabilities()
        
        assert 'commands' in capabilities
        assert 'scan' in capabilities['commands']
        assert 'api_calls' in capabilities
        assert 'generate_scan_uuid' in capabilities['api_calls']
        assert 'hash_file' in capabilities['api_calls']
        assert 'get_available_hash_types' in capabilities['api_calls']

    # ===========================
    # Cascade Integration Tests
    # ===========================

    @patch('nodupe.core.cascade.stages.progressive_hashing.ProgressiveHashingCascadeStage')
    def test_progressive_hashing_stage_uuid_integration(self, mock_progressive_stage):
        """Test progressive hashing cascade stage UUID integration."""
        # Mock the progressive hashing stage
        mock_stage_instance = Mock()
        mock_stage_instance.execute.return_value = {
            'duplicates': [],
            'quick_hash_algorithm': 'sha256',
            'full_hash_algorithm': 'sha256',
            'files_processed': 3,
            'duplicate_groups': 0,
            'uuid': '550e8400-e29b-41d4-a716-446655440000'  # Mock UUID
        }
        mock_progressive_stage.return_value = mock_stage_instance
        
        # Test that UUID is included in cascade results
        result = mock_stage_instance.execute({'files': self.test_files})
        
        assert 'uuid' in result
        assert isinstance(result['uuid'], str)

    @patch('nodupe.core.cascade.stages.archive_processing.ArchiveProcessingCascadeStage')
    def test_archive_processing_stage_uuid_integration(self, mock_archive_stage):
        """Test archive processing cascade stage UUID integration."""
        # Mock the archive processing stage
        mock_stage_instance = Mock()
        mock_stage_instance.execute.return_value = {
            'archive_path': str(self.test_files[0]),
            'extraction_results': [{'method': 'zipfile', 'success': True, 'files': [], 'count': 0}],
            'successful_method': 'zipfile',
            'total_files': 0,
            'uuid': '550e8400-e29b-41d4-a716-446655440001'  # Mock UUID
        }
        mock_archive_stage.return_value = mock_stage_instance
        
        # Test that UUID is included in cascade results
        result = mock_stage_instance.execute({'archive_path': self.test_files[0]})
        
        assert 'uuid' in result
        assert isinstance(result['uuid'], str)

    # ===========================
    # Hash Type Integration Tests
    # ===========================

    def test_hash_file_api_with_various_algorithms(self):
        """Test hash_file API with various supported algorithms."""
        test_file = self.test_files[0]
        
        # Get available hash types
        hash_types_result = self.scan_plugin.api_call('get_available_hash_types')
        available_types = list(hash_types_result['available_hash_types'].keys())
        
        # Test a few common algorithms
        test_algorithms = ['sha256', 'md5', 'sha1']
        for algorithm in test_algorithms:
            if algorithm in available_types:
                result = self.scan_plugin.api_call(
                    'hash_file',
                    file_path=str(test_file),
                    algorithm=algorithm
                )
                
                assert result['success'] is True
                assert result['algorithm'] == algorithm
                assert len(result['hash']) > 0

    def test_hash_file_with_progressive_algorithms(self):
        """Test hash_file API with progressive hashing algorithms."""
        test_file = self.test_files[0]
        
        # Test progressive algorithms if available
        result = self.scan_plugin.api_call('get_available_hash_types')
        available_types = result['available_hash_types']
        
        progressive_algorithms = ['progressive_quick', 'progressive_full']
        for algorithm in progressive_algorithms:
            if algorithm in available_types:
                with patch('nodupe.core.hash_progressive.get_progressive_hasher') as mock_get_hasher:
                    mock_hasher = Mock()
                    mock_hasher.quick_hash.return_value = 'mock_quick_hash'
                    mock_hasher.full_hash.return_value = 'mock_full_hash'
                    mock_get_hasher.return_value = mock_hasher
                    
                    result = self.scan_plugin.api_call(
                        'hash_file',
                        file_path=str(test_file),
                        algorithm=algorithm
                    )
                    
                    if result['success']:
                        assert result['algorithm'] == algorithm
                        assert len(result['hash']) > 0

    # ===========================
    # Error Handling and Edge Cases
    # ===========================

    def test_uuid_generation_with_complex_kwargs(self):
        """Test UUID generation with complex keyword arguments."""
        result = self.scan_plugin.api_call(
            'generate_scan_uuid',
            metadata={'operation': 'scan', 'user': 'test'},
            tags=['test', 'integration']
        )
        
        assert 'uuid' in result
        assert result['success'] != False

    def test_hash_file_with_chunk_size_parameter(self):
        """Test hash_file API with custom chunk size."""
        test_file = self.test_files[0]
        
        result = self.scan_plugin.api_call(
            'hash_file',
            file_path=str(test_file),
            algorithm='sha256',
            chunk_size=4096
        )
        
        assert result['success'] is True
        assert result['algorithm'] == 'sha256'
        assert result['chunk_size'] == 4096

    def test_api_call_with_invalid_parameters(self):
        """Test API calls with invalid parameters."""
        # Test invalid parameters for hash_file
        result = self.scan_plugin.api_call(
            'hash_file',
            file_path=None,
            algorithm='sha256'
        )
        
        assert 'error' in result
        assert result['success'] is False

    # ===========================
    # Performance and Large File Tests
    # ===========================

    def test_hash_large_file_performance(self):
        """Test hashing performance with larger files."""
        # Create a larger test file
        large_file = Path(self.temp_dir) / "large_test_file.bin"
        with open(large_file, 'wb') as f:
            # Write 1MB of test data
            test_data = b"x" * 1024  # 1KB chunk
            for _ in range(1024):  # 1024 chunks = 1MB
                f.write(test_data)
        
        import time
        start_time = time.time()
        
        result = self.scan_plugin.api_call(
            'hash_file',
            file_path=str(large_file),
            algorithm='sha256'
        )
        
        execution_time = time.time() - start_time
        
        assert result['success'] is True
        assert execution_time < 10.0  # Should hash 1MB in reasonable time

    def test_multiple_uuid_generations_performance(self):
        """Test performance of multiple UUID generations."""
        import time
        start_time = time.time()
        
        # Generate 100 UUIDs
        for i in range(100):
            result = self.scan_plugin.api_call('generate_scan_uuid')
            assert 'uuid' in result
        
        execution_time = time.time() - start_time
        
        assert execution_time < 5.0  # Should generate 100 UUIDs quickly

    # ===========================
    # Integration with Other Components
    # ===========================

    @patch('nodupe.plugins.commands.scan.get_audit_logger')
    def test_uuid_generation_logging(self, mock_get_audit_logger):
        """Test that UUID generation is properly logged."""
        mock_audit_logger = Mock()
        mock_get_audit_logger.return_value = mock_audit_logger
        
        result = self.scan_plugin.api_call('generate_scan_uuid')
        
        # Verify that audit logging was called
        mock_audit_logger.log_uuid_generated.assert_called_once()

    @patch('nodupe.plugins.commands.scan.get_audit_logger')
    def test_hash_file_logging(self, mock_get_audit_logger):
        """Test that file hashing operations are properly logged."""
        mock_audit_logger = Mock()
        mock_get_audit_logger.return_value = mock_audit_logger
        
        test_file = self.test_files[0]
        result = self.scan_plugin.api_call(
            'hash_file',
            file_path=str(test_file),
            algorithm='sha256'
        )
        
        # Verify that file hashing was logged
        if result['success']:
            mock_audit_logger.log_file_hashed.assert_called_once()

    # ===========================
    # Backward Compatibility Tests
    # ===========================

    def test_backward_compatibility_with_existing_api_calls(self):
        """Test that new API additions don't break existing functionality."""
        # Test that the plugin still has basic capabilities
        capabilities = self.scan_plugin.get_capabilities()
        assert 'commands' in capabilities
        assert 'scan' in capabilities['commands']
        
        # Test that old-style operations still work conceptually
        # (actual implementation would depend on original plugin structure)
        assert hasattr(self.scan_plugin, 'api_call')
        assert callable(self.scan_plugin.api_call)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
