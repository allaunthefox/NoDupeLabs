"""
Test suite for nodupe.core.plugin_system.base module
"""
import pytest
from unittest.mock import MagicMock
from uuid import UUID, uuid4
from nodupe.core.plugin_system.base import Plugin


class TestPlugin:
    """Test cases for the Plugin abstract base class"""
    
    def test_plugin_abstract_base_class(self):
        """Test that Plugin is an abstract base class"""
        # We can't directly instantiate an abstract class, so we'll test it by creating a concrete implementation
        class ConcretePlugin(Plugin):
            def initialize(self, container):
                self._initialized = True
            
            def shutdown(self):
                self._initialized = False
            
            def get_capabilities(self):
                return {"test": True}
        
        # Create valid metadata
        metadata = {
            "uuid": str(uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "test",
            "compatibility": "all",
            "marketplace_id": "test_plugin_id"
        }
        
        plugin = ConcretePlugin(metadata)
        assert isinstance(plugin, Plugin)
        assert isinstance(plugin.uuid, UUID)
        assert plugin.name == "test_plugin"
        assert plugin.display_name == "Test Plugin"
        assert plugin.version == "v1.0.0"
        assert plugin.description == "A test plugin"
        assert plugin.author == "Test Author"
        assert plugin.category == "test"
        assert plugin.dependencies == []
        assert plugin.tags == []
        assert plugin.marketplace_id == "test_plugin_id"
        assert plugin.is_initialized is False
    
    def test_plugin_validate_metadata_success(self):
        """Test Plugin._validate_metadata with valid metadata"""
        metadata = {
            "uuid": str(uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "test",
            "compatibility": "all",
            "marketplace_id": "test_plugin_id"
        }
        
        # This should not raise any exceptions
        Plugin._validate_metadata(metadata)
    
    def test_plugin_validate_metadata_missing_field(self):
        """Test Plugin._validate_metadata with missing required field"""
        metadata = {
            "uuid": str(uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "test",
            # Missing "compatibility" field
            "marketplace_id": "test_plugin_id"
        }
        
        with pytest.raises(ValueError, match="Missing required metadata field: compatibility"):
            Plugin._validate_metadata(metadata)
    
    def test_plugin_validate_metadata_invalid_uuid(self):
        """Test Plugin._validate_metadata with invalid UUID"""
        metadata = {
            "uuid": "invalid-uuid",
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "test",
            "compatibility": "all",
            "marketplace_id": "test_plugin_id"
        }
        
        with pytest.raises(ValueError, match="Invalid UUID format"):
            Plugin._validate_metadata(metadata)
    
    def test_plugin_validate_metadata_invalid_name(self):
        """Test Plugin._validate_metadata with invalid name"""
        metadata = {
            "uuid": str(uuid4()),
            "name": "Invalid Name",  # Contains space, should be lowercase with underscores only
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "test",
            "compatibility": "all",
            "marketplace_id": "test_plugin_id"
        }
        
        with pytest.raises(ValueError, match="Plugin name must be 2-50 characters"):
            Plugin._validate_metadata(metadata)
    
    def test_plugin_validate_metadata_invalid_version(self):
        """Test Plugin._validate_metadata with invalid version"""
        metadata = {
            "uuid": str(uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "1.0.0",  # Missing 'v' prefix
            "description": "A test plugin",
            "author": "Test Author",
            "category": "test",
            "compatibility": "all",
            "marketplace_id": "test_plugin_id"
        }
        
        with pytest.raises(ValueError, match="Version must follow semantic versioning format"):
            Plugin._validate_metadata(metadata)
    
    def test_plugin_validate_metadata_long_marketplace_id(self):
        """Test Plugin._validate_metadata with long marketplace_id"""
        metadata = {
            "uuid": str(uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "test",
            "compatibility": "all",
            "marketplace_id": "a" * 256  # Too long
        }
        
        with pytest.raises(ValueError, match="Marketplace ID too long"):
            Plugin._validate_metadata(metadata)
    
    def test_plugin_generate_uuid(self):
        """Test Plugin.generate_uuid method"""
        uuid = Plugin.generate_uuid()
        assert isinstance(uuid, UUID)
        assert uuid.version == 4
    
    def test_plugin_generate_filename(self):
        """Test Plugin.generate_filename method"""
        filename = Plugin.generate_filename("test_plugin", "v1.0")
        assert "test_plugin" in filename
        assert "v1.0.0" in filename
        assert ".py" in filename
    
    def test_plugin_name_property(self):
        """Test Plugin name property and setter"""
        class ConcretePlugin(Plugin):
            def initialize(self, container):
                pass
            
            def shutdown(self):
                pass
            
            def get_capabilities(self):
                return {}
        
        metadata = {
            "uuid": str(uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "test",
            "compatibility": "all",
            "marketplace_id": "test_plugin_id"
        }
        
        plugin = ConcretePlugin(metadata)
        assert plugin.name == "test_plugin"
        
        # Test setter
        plugin.name = "new_plugin_name"
        assert plugin.name == "new_plugin_name"
    
    def test_plugin_name_setter_invalid(self):
        """Test Plugin name setter with invalid value"""
        class ConcretePlugin(Plugin):
            def initialize(self, container):
                pass
            
            def shutdown(self):
                pass
            
            def get_capabilities(self):
                return {}
        
        metadata = {
            "uuid": str(uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "test",
            "compatibility": "all",
            "marketplace_id": "test_plugin_id"
        }
        
        plugin = ConcretePlugin(metadata)
        
        with pytest.raises(ValueError, match="Plugin name must be 2-50 characters"):
            plugin.name = "Invalid Name"
    
    def test_plugin_version_property(self):
        """Test Plugin version property and setter"""
        class ConcretePlugin(Plugin):
            def initialize(self, container):
                pass
            
            def shutdown(self):
                pass
            
            def get_capabilities(self):
                return {}
        
        metadata = {
            "uuid": str(uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "test",
            "compatibility": "all",
            "marketplace_id": "test_plugin_id"
        }
        
        plugin = ConcretePlugin(metadata)
        assert plugin.version == "v1.0.0"
        
        # Test setter
        plugin.version = "v2.0.0"
        assert plugin.version == "v2.0.0"
    
    def test_plugin_version_setter_invalid(self):
        """Test Plugin version setter with invalid value"""
        class ConcretePlugin(Plugin):
            def initialize(self, container):
                pass
            
            def shutdown(self):
                pass
            
            def get_capabilities(self):
                return {}
        
        metadata = {
            "uuid": str(uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "test",
            "compatibility": "all",
            "marketplace_id": "test_plugin_id"
        }
        
        plugin = ConcretePlugin(metadata)
        
        with pytest.raises(ValueError, match="Version must follow semantic versioning format"):
            plugin.version = "2.0.0"  # Missing 'v' prefix
    
    def test_plugin_dependencies_property(self):
        """Test Plugin dependencies property and setter"""
        class ConcretePlugin(Plugin):
            def initialize(self, container):
                pass
            
            def shutdown(self):
                pass
            
            def get_capabilities(self):
                return {}
        
        metadata = {
            "uuid": str(uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "test",
            "compatibility": "all",
            "marketplace_id": "test_plugin_id",
            "dependencies": ["dep1", "dep2"]
        }
        
        plugin = ConcretePlugin(metadata)
        assert plugin.dependencies == ["dep1", "dep2"]
        
        # Test setter
        plugin.dependencies = ["dep3", "dep4"]
        assert plugin.dependencies == ["dep3", "dep4"]
    
    def test_plugin_uuid_str_property(self):
        """Test Plugin uuid_str property"""
        test_uuid = str(uuid4())
        class ConcretePlugin(Plugin):
            def initialize(self, container):
                pass
            
            def shutdown(self):
                pass
            
            def get_capabilities(self):
                return {}
        
        metadata = {
            "uuid": test_uuid,
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "test",
            "compatibility": "all",
            "marketplace_id": "test_plugin_id"
        }
        
        plugin = ConcretePlugin(metadata)
        assert plugin.uuid_str == test_uuid
    
    def test_plugin_is_initialized_property(self):
        """Test Plugin is_initialized property"""
        class ConcretePlugin(Plugin):
            def initialize(self, container):
                self._initialized = True
            
            def shutdown(self):
                self._initialized = False
            
            def get_capabilities(self):
                return {}
        
        metadata = {
            "uuid": str(uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "test",
            "compatibility": "all",
            "marketplace_id": "test_plugin_id"
        }
        
        plugin = ConcretePlugin(metadata)
        assert plugin.is_initialized is False
        
        # Initialize the plugin
        plugin.initialize(MagicMock())
        assert plugin.is_initialized is True
        
        # Shutdown the plugin
        plugin.shutdown()
        assert plugin.is_initialized is False
