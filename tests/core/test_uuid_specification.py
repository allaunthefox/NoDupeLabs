"""Test UUID Specification Implementation.

Tests for UUID-based plugin naming convention, validation, and utilities.
Ensures all plugins/modules follow the UUID specification from the project.
"""

import pytest
from pathlib import Path
from uuid import UUID
import tempfile
import os

from nodupe.core.plugin_system.base import Plugin
from nodupe.core.plugin_system.discovery import PluginDiscovery
from nodupe.core.plugin_system.uuid_utils import UUIDUtils, UUIDValidationError


class TestUUIDUtils:
    """Test UUID utilities and validation."""

    def test_generate_uuid_v4(self):
        """Test UUID v4 generation."""
        uuid1 = UUIDUtils.generate_uuid_v4()
        uuid2 = UUIDUtils.generate_uuid_v4()
        
        assert isinstance(uuid1, UUID)
        assert uuid1.version == 4
        assert isinstance(uuid2, UUID)
        assert uuid2.version == 4
        assert uuid1 != uuid2  # Should be unique

    def test_validate_uuid(self):
        """Test UUID validation with various formats."""
        # Valid UUIDs
        assert UUIDUtils.validate_uuid('550e8400-e29b-41d4-a716-446655440000') is True
        assert UUIDUtils.validate_uuid('550e8400-e29b-41d4-a716-446655440000'.upper()) is True
        
        # Invalid UUIDs
        assert UUIDUtils.validate_uuid('invalid-uuid') is False
        assert UUIDUtils.validate_uuid('550e8400-e29b-41d4-a716-44665544000') is False  # Missing one character
        assert UUIDUtils.validate_uuid('550e8400-e29b-41d4-a716-4466554400000') is False  # Extra character
        assert UUIDUtils.validate_uuid('') is False
        assert UUIDUtils.validate_uuid(None) is False

    def test_validate_plugin_name(self):
        """Test plugin name validation."""
        # Valid names
        assert UUIDUtils.validate_plugin_name("scan_enhanced") is True
        assert UUIDUtils.validate_plugin_name("ml_classifier") is True
        assert UUIDUtils.validate_plugin_name("security_checker") is True
        
        # Invalid names
        assert UUIDUtils.validate_plugin_name("a") is False  # Too short
        assert UUIDUtils.validate_plugin_name("scan-enhanced") is False  # Hyphen not allowed
        assert UUIDUtils.validate_plugin_name("Scan_enhanced") is False  # Uppercase not allowed
        assert UUIDUtils.validate_plugin_name("123scan") is False  # Must start with letter
        assert UUIDUtils.validate_plugin_name("") is False
        assert UUIDUtils.validate_plugin_name(None) is False

    def test_validate_version(self):
        """Test version validation."""
        # Valid versions
        assert UUIDUtils.validate_version("v1.0.0") is True
        assert UUIDUtils.validate_version("v2.1.3") is True
        assert UUIDUtils.validate_version("v0.5.1") is True
        
        # Invalid versions
        assert UUIDUtils.validate_version("1.0.0") is False  # Missing 'v'
        assert UUIDUtils.validate_version("v1.0") is False  # Missing patch
        assert UUIDUtils.validate_version("v1.0.0.1") is False  # Too many parts
        assert UUIDUtils.validate_version("version1.0.0") is False  # Wrong format
        assert UUIDUtils.validate_version("") is False
        assert UUIDUtils.validate_version(None) is False

    def test_generate_plugin_filename(self):
        """Test plugin filename generation."""
        filename = UUIDUtils.generate_plugin_filename("scan_enhanced", "v1.2.3")
        
        assert filename.startswith("scan_enhanced_")
        assert filename.endswith(".v1.2.3.py")
        
        # Parse the generated filename
        parsed = UUIDUtils.parse_plugin_filename(filename)
        assert parsed is not None
        assert parsed['name'] == "scan_enhanced"
        assert parsed['version'] == "1.2.3"
        assert UUIDUtils.validate_uuid(parsed['uuid'])

    def test_generate_plugin_filename_invalid_name(self):
        """Test plugin filename generation with invalid name."""
        with pytest.raises(UUIDValidationError, match="Invalid plugin name format"):
            UUIDUtils.generate_plugin_filename("Invalid-Name", "v1.0.0")

    def test_generate_plugin_filename_invalid_version(self):
        """Test plugin filename generation with invalid version."""
        with pytest.raises(UUIDValidationError, match="Invalid version format"):
            UUIDUtils.generate_plugin_filename("scan_enhanced", "1.0.0")  # Missing 'v'

    def test_parse_plugin_filename(self):
        """Test plugin filename parsing."""
        filename = "scan_enhanced_550e8400-e29b-41d4-a716-446655440000.v1.2.3.py"
        parsed = UUIDUtils.parse_plugin_filename(filename)
        
        assert parsed is not None
        assert parsed['name'] == "scan_enhanced"
        assert parsed['uuid'] == "550e8400-e29b-41d4-a716-446655440000"
        assert parsed['version'] == "1.2.3"

    def test_parse_plugin_filename_invalid(self):
        """Test plugin filename parsing with invalid filename."""
        invalid_filenames = [
            "scan_enhanced.py",  # Missing UUID and version
            "scan_enhanced_v1.0.0.py",  # Missing UUID
            "scan_enhanced_uuid.v1.0.0.py",  # Invalid UUID format
            "scan-enhanced_550e8400.v1.0.0.py",  # Invalid name format
        ]
        
        for filename in invalid_filenames:
            assert UUIDUtils.parse_plugin_filename(filename) is None

    def test_validate_plugin_filename(self):
        """Test plugin filename validation."""
        valid_filename = "scan_enhanced_550e8400-e29b-41d4-a716-446655440000.v1.2.3.py"
        assert UUIDUtils.validate_plugin_filename(valid_filename) is True
        
        invalid_filename = "scan_enhanced.py"
        assert UUIDUtils.validate_plugin_filename(invalid_filename) is False

    def test_generate_marketplace_id(self):
        """Test marketplace ID generation."""
        marketplace_id = UUIDUtils.generate_marketplace_id(
            "scan_enhanced", 
            "550e8400-e29b-41d4-a716-446655440000"
        )
        
        assert marketplace_id == "scan_enhanced_550e8400-e29b-41d4-a716-446655440000"

    def test_generate_marketplace_id_invalid_name(self):
        """Test marketplace ID generation with invalid name."""
        with pytest.raises(UUIDValidationError, match="Invalid plugin name format"):
            UUIDUtils.generate_marketplace_id("Invalid-Name", "550e8400-e29b-41d4-a716-446655440000")

    def test_generate_marketplace_id_invalid_uuid(self):
        """Test marketplace ID generation with invalid UUID."""
        with pytest.raises(UUIDValidationError, match="Invalid UUID format"):
            UUIDUtils.generate_marketplace_id("scan_enhanced", "invalid-uuid")

    def test_get_plugin_categories(self):
        """Test plugin categories retrieval."""
        categories = UUIDUtils.get_plugin_categories()
        
        assert isinstance(categories, dict)
        assert 'scanning' in categories
        assert 'ml' in categories
        assert 'security' in categories
        assert 'performance' in categories
        assert 'ui' in categories
        assert 'integration' in categories
        assert 'utility' in categories

    def test_validate_category(self):
        """Test category validation."""
        # Standard categories
        assert UUIDUtils.validate_category('scanning') is True
        assert UUIDUtils.validate_category('ml') is True
        assert UUIDUtils.validate_category('security') is True
        
        # Custom categories
        assert UUIDUtils.validate_category('custom_category') is True
        assert UUIDUtils.validate_category('ai_ml') is True
        
        # Invalid categories
        assert UUIDUtils.validate_category('Invalid-Category') is False  # Uppercase
        assert UUIDUtils.validate_category('cat') is False  # Too short
        assert UUIDUtils.validate_category('very_long_category_name_that_exceeds_limit') is False  # Too long
        assert UUIDUtils.validate_category('') is False
        assert UUIDUtils.validate_category(None) is False


class TestPluginBaseWithUUID:
    """Test Plugin base class with UUID support."""

    def test_plugin_initialization_with_valid_metadata(self):
        """Test plugin initialization with valid UUID metadata."""
        metadata = {
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "name": "scan_enhanced",
            "display_name": "Enhanced File Scanner",
            "version": "v1.2.3",
            "description": "Advanced file scanning with ML integration",
            "author": "NoDupeLabs Team",
            "category": "scanning",
            "dependencies": ["numpy>=1.20.0", "scikit-learn>=1.0.0"],
            "compatibility": {
                "python": ">=3.9",
                "nodupe_core": ">=1.0.0"
            },
            "tags": ["scanning", "ml", "performance"],
            "marketplace_id": "scan_enhanced_550e8400-e29b-41d4-a716-446655440000"
        }

        # Create a concrete plugin class for testing
        class TestPlugin(Plugin):
            def initialize(self, container):
                pass
            
            def shutdown(self):
                pass
            
            def get_capabilities(self):
                return {}

        plugin = TestPlugin(metadata)
        
        assert plugin.uuid == UUID("550e8400-e29b-41d4-a716-446655440000")
        assert plugin.name == "scan_enhanced"
        assert plugin.display_name == "Enhanced File Scanner"
        assert plugin.version == "v1.2.3"
        assert plugin.description == "Advanced file scanning with ML integration"
        assert plugin.author == "NoDupeLabs Team"
        assert plugin.category == "scanning"
        assert plugin.dependencies == ["numpy>=1.20.0", "scikit-learn>=1.0.0"]
        assert plugin.tags == ["scanning", "ml", "performance"]
        assert plugin.marketplace_id == "scan_enhanced_550e8400-e29b-41d4-a716-446655440000"
        assert plugin.uuid_str == "550e8400-e29b-41d4-a716-446655440000"
        assert plugin.is_initialized is False

    def test_plugin_initialization_missing_required_fields(self):
        """Test plugin initialization with missing required fields."""
        metadata = {
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            # Missing required fields
        }

        class TestPlugin(Plugin):
            def initialize(self, container):
                pass
            
            def shutdown(self):
                pass
            
            def get_capabilities(self):
                return {}

        with pytest.raises(ValueError, match="Missing required metadata field"):
            TestPlugin(metadata)

    def test_plugin_initialization_invalid_uuid(self):
        """Test plugin initialization with invalid UUID."""
        metadata = {
            "uuid": "invalid-uuid",
            "name": "scan_enhanced",
            "display_name": "Enhanced File Scanner",
            "version": "v1.2.3",
            "description": "Advanced file scanning with ML integration",
            "author": "NoDupeLabs Team",
            "category": "scanning",
            "compatibility": {
                "python": ">=3.9",
                "nodupe_core": ">=1.0.0"
            },
            "marketplace_id": "scan_enhanced_550e8400-e29b-41d4-a716-446655440000"
        }

        class TestPlugin(Plugin):
            def initialize(self, container):
                pass
            
            def shutdown(self):
                pass
            
            def get_capabilities(self):
                return {}

        with pytest.raises(ValueError, match="Invalid UUID format"):
            TestPlugin(metadata)

    def test_plugin_initialization_invalid_uuid_version(self):
        """Test plugin initialization with UUID that's not version 4."""
        metadata = {
            "uuid": "00000000-0000-0000-0000-000000000000",  # Nil UUID
            "name": "scan_enhanced",
            "display_name": "Enhanced File Scanner",
            "version": "v1.2.3",
            "description": "Advanced file scanning with ML integration",
            "author": "NoDupeLabs Team",
            "category": "scanning",
            "compatibility": {
                "python": ">=3.9",
                "nodupe_core": ">=1.0.0"
            },
            "marketplace_id": "scan_enhanced_550e8400-e29b-41d4-a716-446655440000"
        }

        class TestPlugin(Plugin):
            def initialize(self, container):
                pass
            
            def shutdown(self):
                pass
            
            def get_capabilities(self):
                return {}

        with pytest.raises(ValueError, match="Plugin UUID must be version 4"):
            TestPlugin(metadata)

    def test_plugin_initialization_invalid_name(self):
        """Test plugin initialization with invalid name."""
        metadata = {
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Invalid-Name",  # Invalid format
            "display_name": "Enhanced File Scanner",
            "version": "v1.2.3",
            "description": "Advanced file scanning with ML integration",
            "author": "NoDupeLabs Team",
            "category": "scanning",
            "compatibility": {
                "python": ">=3.9",
                "nodupe_core": ">=1.0.0"
            },
            "marketplace_id": "scan_enhanced_550e8400-e29b-41d4-a716-446655440000"
        }

        class TestPlugin(Plugin):
            def initialize(self, container):
                pass
            
            def shutdown(self):
                pass
            
            def get_capabilities(self):
                return {}

        with pytest.raises(ValueError, match="Plugin name must be 2-50 characters"):
            TestPlugin(metadata)

    def test_plugin_initialization_invalid_version(self):
        """Test plugin initialization with invalid version."""
        metadata = {
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "name": "scan_enhanced",
            "display_name": "Enhanced File Scanner",
            "version": "1.2.3",  # Missing 'v' prefix
            "description": "Advanced file scanning with ML integration",
            "author": "NoDupeLabs Team",
            "category": "scanning",
            "compatibility": {
                "python": ">=3.9",
                "nodupe_core": ">=1.0.0"
            },
            "marketplace_id": "scan_enhanced_550e8400-e29b-41d4-a716-446655440000"
        }

        class TestPlugin(Plugin):
            def initialize(self, container):
                pass
            
            def shutdown(self):
                pass
            
            def get_capabilities(self):
                return {}

        with pytest.raises(ValueError, match="Version must follow semantic versioning format"):
            TestPlugin(metadata)

    def test_plugin_generate_uuid(self):
        """Test plugin UUID generation."""
        uuid1 = Plugin.generate_uuid()
        uuid2 = Plugin.generate_uuid()
        
        assert isinstance(uuid1, UUID)
        assert uuid1.version == 4
        assert isinstance(uuid2, UUID)
        assert uuid2.version == 4
        assert uuid1 != uuid2  # Should be unique

    def test_plugin_generate_filename(self):
        """Test plugin filename generation."""
        filename = Plugin.generate_filename("scan_enhanced", "v1.2.3")
        
        assert filename.startswith("scan_enhanced_")
        assert filename.endswith(".v1.2.3.py")
        
        # Parse the generated filename
        parsed = UUIDUtils.parse_plugin_filename(filename)
        assert parsed is not None
        assert parsed['name'] == "scan_enhanced"
        assert parsed['version'] == "1.2.3"
        assert UUIDUtils.validate_uuid(parsed['uuid'])


class TestPluginDiscoveryWithUUID:
    """Test plugin discovery with UUID support."""

    def test_discover_uuid_plugins_in_directory(self, tmp_path):
        """Test UUID plugin discovery in directory."""
        # Create test plugin files with UUID naming
        plugin1_content = '''
from uuid import UUID
from nodupe.core.plugin_system.base import Plugin

PLUGIN_METADATA = {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "name": "scan_enhanced",
    "display_name": "Enhanced File Scanner",
    "version": "v1.2.3",
    "description": "Advanced file scanning with ML integration",
    "author": "NoDupeLabs Team",
    "category": "scanning",
    "dependencies": ["numpy>=1.20.0"],
    "compatibility": {"python": ">=3.9"},
    "tags": ["scanning", "ml"],
    "marketplace_id": "scan_enhanced_550e8400-e29b-41d4-a716-446655440000"
}

class ScanEnhancedPlugin(Plugin):
    def __init__(self):
        super().__init__(PLUGIN_METADATA)
    
    def initialize(self, container):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {"scanning": True}
'''
        
        plugin2_content = '''
from uuid import UUID
from nodupe.core.plugin_system.base import Plugin

PLUGIN_METADATA = {
    "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "name": "security_checker",
    "display_name": "Security Analysis Plugin",
    "version": "v0.5.1",
    "description": "Security analysis and validation",
    "author": "NoDupeLabs Team",
    "category": "security",
    "dependencies": [],
    "compatibility": {"python": ">=3.9"},
    "tags": ["security"],
    "marketplace_id": "security_checker_a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}

class SecurityCheckerPlugin(Plugin):
    def __init__(self):
        super().__init__(PLUGIN_METADATA)
    
    def initialize(self, container):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {"security": True}
'''

        # Create plugin files with UUID naming convention
        plugin1_file = tmp_path / "scan_enhanced_550e8400-e29b-41d4-a716-446655440000.v1.2.3.py"
        plugin2_file = tmp_path / "security_checker_a1b2c3d4-e5f6-7890-abcd-ef1234567890.v0.5.1.py"
        
        plugin1_file.write_text(plugin1_content)
        plugin2_file.write_text(plugin2_content)
        
        # Create a non-UUID plugin file
        regular_plugin = tmp_path / "regular_plugin.py"
        regular_plugin.write_text("# Regular plugin without UUID")
        
        # Test discovery
        discovery = PluginDiscovery()
        plugins = discovery.discover_uuid_plugins_in_directory(tmp_path)
        
        assert len(plugins) == 2
        
        plugin_names = [p.name for p in plugins]
        assert "scan_enhanced" in plugin_names
        assert "security_checker" in plugin_names

    def test_find_uuid_plugin_by_uuid(self, tmp_path):
        """Test finding UUID plugin by UUID."""
        # Create test plugin file
        plugin_content = '''
from uuid import UUID
from nodupe.core.plugin_system.base import Plugin

PLUGIN_METADATA = {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "name": "scan_enhanced",
    "display_name": "Enhanced File Scanner",
    "version": "v1.2.3",
    "description": "Advanced file scanning with ML integration",
    "author": "NoDupeLabs Team",
    "category": "scanning",
    "dependencies": ["numpy>=1.20.0"],
    "compatibility": {"python": ">=3.9"},
    "tags": ["scanning", "ml"],
    "marketplace_id": "scan_enhanced_550e8400-e29b-41d4-a716-446655440000"
}

class ScanEnhancedPlugin(Plugin):
    def __init__(self):
        super().__init__(PLUGIN_METADATA)
    
    def initialize(self, container):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {"scanning": True}
'''
        
        plugin_file = tmp_path / "scan_enhanced_550e8400-e29b-41d4-a716-446655440000.v1.2.3.py"
        plugin_file.write_text(plugin_content)
        
        # Test finding by UUID
        discovery = PluginDiscovery()
        plugin = discovery.find_uuid_plugin_by_uuid(
            "550e8400-e29b-41d4-a716-446655440000",
            [tmp_path]
        )
        
        assert plugin is not None
        assert plugin.name == "scan_enhanced"
        assert plugin.version == "v1.2.3"

    def test_find_uuid_plugin_by_name_and_version(self, tmp_path):
        """Test finding UUID plugin by name and version."""
        # Create test plugin file
        plugin_content = '''
from uuid import UUID
from nodupe.core.plugin_system.base import Plugin

PLUGIN_METADATA = {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "name": "scan_enhanced",
    "display_name": "Enhanced File Scanner",
    "version": "v1.2.3",
    "description": "Advanced file scanning with ML integration",
    "author": "NoDupeLabs Team",
    "category": "scanning",
    "dependencies": ["numpy>=1.20.0"],
    "compatibility": {"python": ">=3.9"},
    "tags": ["scanning", "ml"],
    "marketplace_id": "scan_enhanced_550e8400-e29b-41d4-a716-446655440000"
}

class ScanEnhancedPlugin(Plugin):
    def __init__(self):
        super().__init__(PLUGIN_METADATA)
    
    def initialize(self, container):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {"scanning": True}
'''
        
        plugin_file = tmp_path / "scan_enhanced_550e8400-e29b-41d4-a716-446655440000.v1.2.3.py"
        plugin_file.write_text(plugin_content)
        
        # Test finding by name and version
        discovery = PluginDiscovery()
        plugin = discovery.find_uuid_plugin_by_name_and_version(
            "scan_enhanced",
            "v1.2.3",
            [tmp_path]
        )
        
        assert plugin is not None
        assert plugin.name == "scan_enhanced"
        assert plugin.version == "v1.2.3"


class TestUUIDIntegration:
    """Test UUID specification integration."""

    def test_complete_uuid_plugin_workflow(self, tmp_path):
        """Test complete UUID plugin workflow from generation to discovery."""
        # 1. Generate UUID and filename
        plugin_name = "test_plugin"
        version = "v1.0.0"
        
        filename = UUIDUtils.generate_plugin_filename(plugin_name, version)
        assert filename.startswith(f"{plugin_name}_")
        assert filename.endswith(f".{version}.py")
        
        # 2. Parse filename
        parsed = UUIDUtils.parse_plugin_filename(filename)
        assert parsed['name'] == plugin_name
        assert parsed['version'] == "1.0.0"
        assert UUIDUtils.validate_uuid(parsed['uuid'])
        
        # 3. Generate marketplace ID
        marketplace_id = UUIDUtils.generate_marketplace_id(
            parsed['name'], 
            parsed['uuid']
        )
        assert marketplace_id == f"{plugin_name}_{parsed['uuid']}"
        
        # 4. Create plugin file content
        plugin_content = f'''
from uuid import UUID
from nodupe.core.plugin_system.base import Plugin

PLUGIN_METADATA = {{
    "uuid": "{parsed['uuid']}",
    "name": "{plugin_name}",
    "display_name": "Test Plugin",
    "version": "{version}",
    "description": "Test plugin for UUID specification",
    "author": "NoDupeLabs Team",
    "category": "utility",
    "dependencies": [],
    "compatibility": {{"python": ">=3.9"}},
    "tags": ["test"],
    "marketplace_id": "{marketplace_id}"
}}

class TestPlugin(Plugin):
    def __init__(self):
        super().__init__(PLUGIN_METADATA)
    
    def initialize(self, container):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {{"test": True}}
'''
        
        # 5. Write plugin file
        plugin_file = tmp_path / filename
        plugin_file.write_text(plugin_content)
        
        # 6. Validate plugin file
        assert UUIDUtils.is_uuid_plugin_file(plugin_file)
        
        # 7. Extract plugin info
        plugin_info = UUIDUtils.extract_plugin_info_from_file(plugin_file)
        assert plugin_info is not None
        assert plugin_info['name'] == plugin_name
        assert plugin_info['uuid'] == parsed['uuid']
        assert plugin_info['version'] == version
        assert plugin_info['marketplace_id'] == marketplace_id
        
        # 8. Discover plugin
        discovery = PluginDiscovery()
        plugins = discovery.discover_uuid_plugins_in_directory(tmp_path)
        assert len(plugins) == 1
        
        discovered_plugin = plugins[0]
        assert discovered_plugin.name == plugin_name
        assert discovered_plugin.version == version

    def test_uuid_specification_compliance(self):
        """Test that UUID specification requirements are met."""
        # Test all specification requirements
        assert UUIDUtils.validate_plugin_name("scan_enhanced") is True
        assert UUIDUtils.validate_plugin_name("ml_classifier") is True
        assert UUIDUtils.validate_plugin_name("security_checker") is True
        
        assert UUIDUtils.validate_version("v1.0.0") is True
        assert UUIDUtils.validate_version("v2.1.3") is True
        assert UUIDUtils.validate_version("v0.5.1") is True
        
        # Test UUID generation is cryptographically secure
        uuids = [UUIDUtils.generate_uuid_v4() for _ in range(100)]
        assert len(set(uuids)) == 100  # All should be unique
        
        # Test UUID validation
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert UUIDUtils.validate_uuid(valid_uuid) is True
        
        # Test marketplace ID generation
        marketplace_id = UUIDUtils.generate_marketplace_id("scan_enhanced", valid_uuid)
        assert marketplace_id == "scan_enhanced_550e8400-e29b-41d4-a716-446655440000"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
