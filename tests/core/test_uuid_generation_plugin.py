"""Test UUID Generation Plugin.

Tests for the UUID generation plugin functionality including
UUID generation, validation, plugin template generation, and
marketplace ID creation.
"""

import pytest
import tempfile
import json
from pathlib import Path
from uuid import UUID

from nodupe.core.plugin_system.base import Plugin
from nodupe.plugins.commands.generate_uuid import GenerateUUIDPlugin


class TestUUIDGenerationPlugin:
    """Test UUID generation plugin functionality."""

    def test_plugin_initialization(self):
        """Test UUID generation plugin initialization."""
        plugin = GenerateUUIDPlugin()
        
        assert plugin.name == "generate_uuid"
        assert plugin.display_name == "UUID Generation Plugin"
        assert plugin.version == "v1.0.0"
        assert plugin.category == "utility"
        assert plugin.uuid_str == "f1a2b3c4-d5e6-7890-abcd-ef1234567892"
        assert plugin.is_initialized is False

    def test_plugin_capabilities(self):
        """Test plugin capabilities."""
        plugin = GenerateUUIDPlugin()
        capabilities = plugin.get_capabilities()
        
        assert 'commands' in capabilities
        assert 'generate-uuid' in capabilities['commands']
        assert 'uuid-validate' in capabilities['commands']
        assert 'uuid-plugin-template' in capabilities['commands']
        
        assert 'features' in capabilities
        assert 'uuid_generation' in capabilities['features']
        assert 'plugin_metadata_generation' in capabilities['features']
        assert 'validation' in capabilities['features']

    def test_execute_generate_uuid_single(self):
        """Test single UUID generation."""
        plugin = GenerateUUIDPlugin()
        
        # Create mock args
        class MockArgs:
            count = 1
            format = 'canonical'
            output = None
        
        args = MockArgs()
        
        # Execute generation
        result = plugin.execute_generate_uuid(args)
        
        assert result == 0

    def test_execute_generate_uuid_multiple(self):
        """Test multiple UUID generation."""
        plugin = GenerateUUIDPlugin()
        
        # Create mock args
        class MockArgs:
            count = 5
            format = 'canonical'
            output = None
        
        args = MockArgs()
        
        # Execute generation
        result = plugin.execute_generate_uuid(args)
        
        assert result == 0

    def test_execute_generate_uuid_with_output(self, tmp_path):
        """Test UUID generation with output file."""
        plugin = GenerateUUIDPlugin()
        
        # Create mock args
        output_file = tmp_path / "uuids.json"
        class MockArgs:
            count = 3
            format = 'canonical'
            output = str(output_file)
        
        args = MockArgs()
        
        # Execute generation
        result = plugin.execute_generate_uuid(args)
        
        assert result == 0
        assert output_file.exists()
        
        # Verify output file content
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert 'generated_uuids' in data
        assert len(data['generated_uuids']) == 3
        assert data['count'] == 3
        assert data['format'] == 'canonical'
        
        # Verify UUID format
        for uuid_str in data['generated_uuids']:
            assert len(uuid_str) == 36  # Canonical format
            assert uuid_str.count('-') == 4  # Standard UUID format

    def test_execute_validate_uuid_valid(self):
        """Test UUID validation with valid UUID."""
        plugin = GenerateUUIDPlugin()
        
        # Create mock args
        class MockArgs:
            uuid = "550e8400-e29b-41d4-a716-446655440000"
        
        args = MockArgs()
        
        # Execute validation
        result = plugin.execute_validate_uuid(args)
        
        assert result == 0

    def test_execute_validate_uuid_invalid(self):
        """Test UUID validation with invalid UUID."""
        plugin = GenerateUUIDPlugin()
        
        # Create mock args
        class MockArgs:
            uuid = "invalid-uuid"
        
        args = MockArgs()
        
        # Execute validation
        result = plugin.execute_validate_uuid(args)
        
        assert result == 1

    def test_execute_validate_uuid_short(self):
        """Test UUID validation with too short UUID."""
        plugin = GenerateUUIDPlugin()
        
        # Create mock args
        class MockArgs:
            uuid = "550e8400-e29b-41d4-a716-44665544000"
        
        args = MockArgs()
        
        # Execute validation
        result = plugin.execute_validate_uuid(args)
        
        assert result == 1

    def test_execute_plugin_template_generation(self, tmp_path):
        """Test plugin template generation."""
        plugin = GenerateUUIDPlugin()
        
        # Create mock args
        output_file = tmp_path / "test_plugin.py"
        class MockArgs:
            name = "test_plugin"
            version = "v1.0.0"
            description = "Test plugin for UUID generation"
            category = "utility"
            output = str(output_file)
        
        args = MockArgs()
        
        # Execute template generation
        result = plugin.execute_plugin_template(args)
        
        assert result == 0
        assert output_file.exists()
        
        # Verify template content
        content = output_file.read_text()
        
        assert "test_plugin" in content
        assert "TestPlugin" in content
        assert "PLUGIN_METADATA" in content
        assert "NoDupeLabs Team" in content
        assert "utility" in content

    def test_execute_filename_generation(self):
        """Test UUID-based filename generation."""
        plugin = GenerateUUIDPlugin()
        
        # Create mock args
        class MockArgs:
            name = "test_plugin"
            version = "v1.0.0"
        
        args = MockArgs()
        
        # Execute filename generation
        result = plugin.execute_filename_generation(args)
        
        assert result == 0

    def test_execute_marketplace_id_generation(self):
        """Test marketplace ID generation with provided UUID."""
        plugin = GenerateUUIDPlugin()
        
        # Create mock args
        class MockArgs:
            name = "test_plugin"
            uuid = "550e8400-e29b-41d4-a716-446655440000"
        
        args = MockArgs()
        
        # Execute marketplace ID generation
        result = plugin.execute_marketplace_id(args)
        
        assert result == 0

    def test_execute_marketplace_id_generation_auto_uuid(self):
        """Test marketplace ID generation with auto-generated UUID."""
        plugin = GenerateUUIDPlugin()
        
        # Create mock args
        class MockArgs:
            name = "test_plugin"
            uuid = None  # Should auto-generate
        
        args = MockArgs()
        
        # Execute marketplace ID generation
        result = plugin.execute_marketplace_id(args)
        
        assert result == 0

    def test_execute_marketplace_id_generation_invalid_uuid(self):
        """Test marketplace ID generation with invalid UUID."""
        plugin = GenerateUUIDPlugin()
        
        # Create mock args
        class MockArgs:
            name = "test_plugin"
            uuid = "invalid-uuid"
        
        args = MockArgs()
        
        # Execute marketplace ID generation
        result = plugin.execute_marketplace_id(args)
        
        assert result == 1

    def test_plugin_initialization_with_valid_metadata(self):
        """Test plugin initialization with valid UUID metadata."""
        plugin = GenerateUUIDPlugin()
        
        # Verify UUID validation
        uuid_obj = UUID(plugin.uuid_str)
        assert uuid_obj.version == 4
        assert uuid_obj.variant == 'RFC 4122'
        assert len(str(uuid_obj)) == 36  # Canonical format

    def test_plugin_lifecycle(self):
        """Test plugin lifecycle management."""
        plugin = GenerateUUIDPlugin()
        
        # Test initialization
        assert plugin.is_initialized is False
        plugin.initialize(None)
        assert plugin.is_initialized is True
        
        # Test shutdown
        plugin.shutdown()
        assert plugin.is_initialized is False

    def test_plugin_commands_registration(self):
        """Test that plugin commands are properly registered."""
        plugin = GenerateUUIDPlugin()
        
        # Create mock subparsers
        class MockSubparsers:
            def add_parser(self, name, **kwargs):
                return MockParser(name)
        
        class MockParser:
            def __init__(self, name):
                self.name = name
                self.subparsers = MockSubparsers()
            
            def add_subparsers(self, **kwargs):
                return self.subparsers
        
        subparsers = MockSubparsers()
        
        # Register commands (should not raise exceptions)
        plugin.register_commands(subparsers)

    def test_uuid_format_variations(self):
        """Test different UUID output formats."""
        plugin = GenerateUUIDPlugin()
        
        # Test canonical format
        class MockArgsCanonical:
            count = 1
            format = 'canonical'
            output = None
        
        # Test simple format
        class MockArgsSimple:
            count = 1
            format = 'simple'
            output = None
        
        # Test URN format
        class MockArgsURN:
            count = 1
            format = 'urn'
            output = None
        
        # Execute generation for each format
        result_canonical = plugin.execute_generate_uuid(MockArgsCanonical())
        result_simple = plugin.execute_generate_uuid(MockArgsSimple())
        result_urn = plugin.execute_generate_uuid(MockArgsURN())
        
        assert result_canonical == 0
        assert result_simple == 0
        assert result_urn == 0

    def test_batch_uuid_generation(self):
        """Test batch UUID generation with large count."""
        plugin = GenerateUUIDPlugin()
        
        # Create mock args for batch generation
        class MockArgs:
            count = 100
            format = 'canonical'
            output = None
        
        args = MockArgs()
        
        # Execute batch generation
        result = plugin.execute_generate_uuid(args)
        
        assert result == 0

    def test_plugin_metadata_structure(self):
        """Test that plugin metadata follows specification."""
        from nodupe.plugins.commands.generate_uuid import PLUGIN_METADATA
        
        required_fields = [
            "uuid", "name", "display_name", "version", 
            "description", "author", "category", "compatibility",
            "tags", "marketplace_id"
        ]
        
        for field in required_fields:
            assert field in PLUGIN_METADATA
        
        # Verify UUID format
        uuid_obj = UUID(PLUGIN_METADATA["uuid"])
        assert uuid_obj.version == 4
        assert uuid_obj.variant == 'RFC 4122'
        
        # Verify marketplace ID format
        expected_marketplace_id = f"{PLUGIN_METADATA['name']}_{PLUGIN_METADATA['uuid']}"
        assert PLUGIN_METADATA["marketplace_id"] == expected_marketplace_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
