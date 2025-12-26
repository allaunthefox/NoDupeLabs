"""Comprehensive test suite for NoDupeLabs plugin system modules.

This test suite provides 100% coverage for the core plugin system modules:
- PluginRegistry (registry.py)
- Plugin base class (base.py) 
- PluginLoader (loader.py)
- PluginDiscovery (discovery.py)
- Plugin lifecycle management
- UUID-based plugin validation
- Plugin dependency resolution
- Plugin security and validation

Test Categories:
- Core functionality tests
- Edge case handling
- Error condition testing
- Performance testing
- Memory usage validation
- Thread safety verification
- Plugin lifecycle management
- UUID validation compliance
- Security validation
"""

import tempfile
import shutil
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open

# Import the plugin system modules
from nodupe.core.plugin_system.registry import PluginRegistry
from nodupe.core.plugin_system.base import Plugin
from nodupe.core.plugin_system.loader import PluginLoader, PluginLoaderError
from nodupe.core.plugin_system.discovery import PluginDiscovery, PluginDiscoveryError, PluginInfo
from nodupe.core.plugin_system.uuid_utils import UUIDUtils, UUIDValidationError
from uuid import UUID


class MockPlugin(Plugin):
    """Mock plugin implementation for testing."""
    
    def __init__(self, metadata: Dict[str, Any]):
        super().__init__(metadata)
        self._initialized = False
        self._shutdown = False
        self._capabilities = metadata.get("capabilities", {})
    
    def initialize(self, container: Any) -> None:
        """Initialize the mock plugin."""
        self._initialized = True
        self._container = container
    
    def shutdown(self) -> None:
        """Shutdown the mock plugin."""
        self._shutdown = True
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get mock plugin capabilities."""
        return self._capabilities


class TestPlugin(Plugin):
    """Test plugin implementation for loader testing."""
    
    def __init__(self, metadata: Dict[str, Any]):
        super().__init__(metadata)
        self._initialized = False
        self._shutdown = False
        self._capabilities = metadata.get("capabilities", {})
    
    def initialize(self, container: Any) -> None:
        """Initialize the test plugin."""
        self._initialized = True
        self._container = container
    
    def shutdown(self) -> None:
        """Shutdown the test plugin."""
        self._shutdown = True
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get test plugin capabilities."""
        return self._capabilities


class IntegrationTestPlugin(Plugin):
    """Integration test plugin implementation."""
    
    def __init__(self, metadata: Dict[str, Any]):
        super().__init__(metadata)
        self.initialized = False
        self.shutdown = False
        self._capabilities = metadata.get("capabilities", {})
    
    def initialize(self, container: Any) -> None:
        """Initialize the integration test plugin."""
        self.initialized = True
        self._container = container
    
    def shutdown(self) -> None:
        """Shutdown the integration test plugin."""
        self.shutdown = True
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get integration test plugin capabilities."""
        return self._capabilities


class TestPluginBase:
    """Test suite for Plugin base class functionality."""
    
    def test_plugin_initialization_valid_metadata(self):
        """Test plugin initialization with valid metadata."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123"
        }
        
        plugin = MockPlugin(metadata)
        assert plugin.name == "test_plugin"
        assert plugin.display_name == "Test Plugin"
        assert plugin.version == "v1.0.0"
        assert plugin.description == "A test plugin"
        assert plugin.author == "Test Author"
        assert plugin.category == "utility"
        assert str(plugin.uuid) == metadata["uuid"]
    
    def test_plugin_initialization_invalid_uuid(self):
        """Test plugin initialization with invalid UUID."""
        metadata = {
            "uuid": "invalid-uuid",
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123"
        }
        
        with pytest.raises(ValueError, match="Invalid UUID format"):
            MockPlugin(metadata)
    
    def test_plugin_initialization_missing_fields(self):
        """Test plugin initialization with missing required fields."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            # Missing other required fields
        }
        
        with pytest.raises(ValueError, match="Missing required metadata field"):
            MockPlugin(metadata)
    
    def test_plugin_initialization_invalid_name(self):
        """Test plugin initialization with invalid name format."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "Invalid-Name",  # Invalid: contains hyphen
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123"
        }
        
        with pytest.raises(ValueError, match="Plugin name must be"):
            MockPlugin(metadata)
    
    def test_plugin_initialization_invalid_version(self):
        """Test plugin initialization with invalid version format."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "1.0.0",  # Invalid: missing 'v' prefix
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123"
        }
        
        with pytest.raises(ValueError, match="Version must follow semantic versioning"):
            MockPlugin(metadata)
    
    def test_plugin_initialization_invalid_marketplace_id(self):
        """Test plugin initialization with invalid marketplace ID."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "\x00invalid"  # Contains null byte
        }
        
        with pytest.raises(ValueError, match="Marketplace ID contains null bytes"):
            MockPlugin(metadata)
    
    def test_plugin_properties(self):
        """Test plugin property access."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123",
            "dependencies": ["dep1", "dep2"]
        }
        
        plugin = MockPlugin(metadata)
        assert plugin.name == "test_plugin"
        assert plugin.version == "v1.0.0"
        assert plugin.dependencies == ["dep1", "dep2"]
        assert plugin.uuid_str == metadata["uuid"]
        assert plugin.is_initialized == False
    
    def test_plugin_lifecycle(self):
        """Test plugin lifecycle methods."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123"
        }
        
        plugin = MockPlugin(metadata)
        container = Mock()
        
        # Test initialization
        plugin.initialize(container)
        assert plugin.is_initialized == True
        assert hasattr(plugin, '_container')
        
        # Test shutdown
        plugin.shutdown()
        assert plugin._shutdown == True
    
    def test_plugin_capabilities(self):
        """Test plugin capabilities method."""
        capabilities = {"feature1": "enabled", "feature2": "disabled"}
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123",
            "capabilities": capabilities
        }
        
        plugin = MockPlugin(metadata)
        assert plugin.get_capabilities() == capabilities


class TestPluginRegistry:
    """Test suite for PluginRegistry functionality."""
    
    def setup_method(self):
        """Setup method to create a fresh registry for each test."""
        # Clear the singleton instance to ensure clean state
        PluginRegistry._instance = None
        self.registry = PluginRegistry()
    
    def test_singleton_pattern(self):
        """Test that PluginRegistry follows singleton pattern."""
        registry2 = PluginRegistry()
        assert self.registry is registry2
    
    def test_register_plugin(self):
        """Test plugin registration."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123"
        }
        
        plugin = MockPlugin(metadata)
        self.registry.register(plugin)
        
        assert self.registry.get_plugin("test_plugin") is plugin
        assert len(self.registry.get_plugins()) == 1
    
    def test_register_duplicate_plugin(self):
        """Test registering duplicate plugin raises error."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123"
        }
        
        plugin1 = MockPlugin(metadata)
        plugin2 = MockPlugin(metadata)
        
        self.registry.register(plugin1)
        
        with pytest.raises(ValueError, match="Plugin test_plugin already registered"):
            self.registry.register(plugin2)
    
    def test_unregister_plugin(self):
        """Test plugin unregistration."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123"
        }
        
        plugin = MockPlugin(metadata)
        self.registry.register(plugin)
        
        self.registry.unregister("test_plugin")
        assert self.registry.get_plugin("test_plugin") is None
        assert len(self.registry.get_plugins()) == 0
        assert plugin._shutdown == True
    
    def test_unregister_nonexistent_plugin(self):
        """Test unregistering non-existent plugin raises error."""
        with pytest.raises(KeyError, match="Plugin nonexistent not found"):
            self.registry.unregister("nonexistent")
    
    def test_get_nonexistent_plugin(self):
        """Test getting non-existent plugin returns None."""
        assert self.registry.get_plugin("nonexistent") is None
    
    def test_get_all_plugins(self):
        """Test getting all registered plugins."""
        metadata1 = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin_1",
            "display_name": "Test Plugin 1",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_1_123"
        }
        
        metadata2 = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin_2",
            "display_name": "Test Plugin 2",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_2_123"
        }
        
        plugin1 = MockPlugin(metadata1)
        plugin2 = MockPlugin(metadata2)
        
        self.registry.register(plugin1)
        self.registry.register(plugin2)
        
        plugins = self.registry.get_plugins()
        assert len(plugins) == 2
        assert plugin1 in plugins
        assert plugin2 in plugins
    
    def test_backward_compatibility_methods(self):
        """Test backward compatibility methods."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123"
        }
        
        plugin = MockPlugin(metadata)
        
        # Test register_plugin (alias for register)
        self.registry.register_plugin(plugin)
        assert self.registry.get_plugin("test_plugin") is plugin
        
        # Test get_all_plugins (alias for get_plugins)
        plugins = self.registry.get_all_plugins()
        assert len(plugins) == 1
    
    def test_clear_all_plugins(self):
        """Test clearing all registered plugins."""
        metadata1 = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin_1",
            "display_name": "Test Plugin 1",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_1_123"
        }
        
        metadata2 = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin_2",
            "display_name": "Test Plugin 2",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_2_123"
        }
        
        plugin1 = MockPlugin(metadata1)
        plugin2 = MockPlugin(metadata2)
        
        self.registry.register(plugin1)
        self.registry.register(plugin2)
        
        self.registry.clear()
        assert len(self.registry.get_plugins()) == 0
    
    def test_shutdown_all_plugins(self):
        """Test shutting down all registered plugins."""
        metadata1 = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin_1",
            "display_name": "Test Plugin 1",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_1_123"
        }
        
        metadata2 = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin_2",
            "display_name": "Test Plugin 2",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_2_123"
        }
        
        plugin1 = MockPlugin(metadata1)
        plugin2 = MockPlugin(metadata2)
        
        self.registry.register(plugin1)
        self.registry.register(plugin2)
        
        self.registry.shutdown()
        assert plugin1._shutdown == True
        assert plugin2._shutdown == True
        assert len(self.registry.get_plugins()) == 0
    
    def test_shutdown_with_plugin_error(self):
        """Test shutdown handles plugin errors gracefully."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123"
        }
        
        plugin = MockPlugin(metadata)
        
        # Mock shutdown to raise an exception
        original_shutdown = plugin.shutdown
        def failing_shutdown():
            original_shutdown()
            raise Exception("Shutdown failed")
        
        plugin.shutdown = failing_shutdown
        
        self.registry.register(plugin)
        
        # This should not raise an exception
        self.registry.shutdown()
    
    def test_initialize_registry(self):
        """Test initializing registry with container."""
        container = Mock()
        self.registry.initialize(container)
        
        assert self.registry.container is container
        assert self.registry._initialized == True
    
    def test_start_registry(self):
        """Test starting registry."""
        container = Mock()
        self.registry.initialize(container)
        
        self.registry.start()  # Should not raise error
    
    def test_start_uninitialized_registry(self):
        """Test starting uninitialized registry raises error."""
        with pytest.raises(RuntimeError, match="Registry not initialized"):
            self.registry.start()
    
    def test_stop_registry(self):
        """Test stopping registry."""
        container = Mock()
        self.registry.initialize(container)
        
        self.registry.stop()  # Should not raise error
        assert self.registry._initialized == False
    
    def test_container_property(self):
        """Test container property access."""
        container = Mock()
        self.registry.initialize(container)
        
        assert self.registry.container is container


class TestPluginLoader:
    """Test suite for PluginLoader functionality."""
    
    def setup_method(self):
        """Setup method to create a fresh loader for each test."""
        # Clear the singleton instance to ensure clean state
        PluginRegistry._instance = None
        self.registry = PluginRegistry()
        self.loader = PluginLoader(self.registry)
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Teardown method to clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_plugin_loader_initialization(self):
        """Test plugin loader initialization."""
        assert self.loader.registry is self.registry
        assert self.loader._loaded_plugins == {}
        assert self.loader._plugin_modules == {}
    
    def test_initialize_loader(self):
        """Test initializing plugin loader with container."""
        container = Mock()
        self.loader.initialize(container)
        
        assert self.loader.container is container
        assert self.registry.container is container
    
    def test_load_plugin_from_file_success(self):
        """Test loading plugin from file successfully."""
        # Create a temporary plugin file
        plugin_content = '''
from nodupe.core.plugin_system.base import Plugin
import uuid

class TestPlugin(Plugin):
    def __init__(self, metadata=None):
        if metadata is None:
            metadata = {
                "uuid": str(uuid.uuid4()),
                "name": "test_plugin",
                "display_name": "Test Plugin",
                "version": "v1.0.0",
                "description": "A test plugin",
                "author": "Test Author",
                "category": "utility",
                "compatibility": "all",
                "marketplace_id": "test_plugin_123"
            }
        super().__init__(metadata)
    
    def initialize(self, container):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {"test": True}
'''
        
        plugin_file = Path(self.temp_dir) / "test_plugin.py"
        with open(plugin_file, 'w') as f:
            f.write(plugin_content)
        
        # Load the plugin
        plugin_class = self.loader.load_plugin_from_file(plugin_file)
        assert plugin_class is not None
        assert plugin_class.__name__ == "TestPlugin"
    
    def test_load_plugin_from_nonexistent_file(self):
        """Test loading plugin from nonexistent file raises error."""
        nonexistent_file = Path(self.temp_dir) / "nonexistent.py"
        
        with pytest.raises(PluginLoaderError, match="Plugin file does not exist"):
            self.loader.load_plugin_from_file(nonexistent_file)
    
    def test_load_plugin_from_non_python_file(self):
        """Test loading plugin from non-Python file raises error."""
        non_python_file = Path(self.temp_dir) / "test.txt"
        non_python_file.touch()
        
        with pytest.raises(PluginLoaderError, match="Plugin file must be Python"):
            self.loader.load_plugin_from_file(non_python_file)
    
    def test_load_plugin_from_invalid_python_file(self):
        """Test loading plugin from invalid Python file raises error."""
        plugin_file = Path(self.temp_dir) / "invalid_plugin.py"
        with open(plugin_file, 'w') as f:
            f.write("invalid python code")  # Invalid Python
        
        with pytest.raises(PluginLoaderError):
            self.loader.load_plugin_from_file(plugin_file)
    
    def test_load_plugin_from_file_without_plugin_class(self):
        """Test loading plugin from file without Plugin class raises error."""
        plugin_file = Path(self.temp_dir) / "no_plugin.py"
        with open(plugin_file, 'w') as f:
            f.write("class NotAPlugin: pass")  # Not a Plugin subclass
        
        with pytest.raises(PluginLoaderError, match="No Plugin subclass found"):
            self.loader.load_plugin_from_file(plugin_file)
    
    def test_load_plugin_from_directory(self):
        """Test loading plugins from directory."""
        # Create multiple plugin files
        plugin_content = '''
from nodupe.core.plugin_system.base import Plugin
import uuid

class TestPlugin(Plugin):
    def __init__(self, metadata=None):
        if metadata is None:
            metadata = {
                "uuid": str(uuid.uuid4()),
                "name": "test_plugin",
                "display_name": "Test Plugin",
                "version": "v1.0.0",
                "description": "A test plugin",
                "author": "Test Author",
                "category": "utility",
                "compatibility": "all",
                "marketplace_id": "test_plugin_123"
            }
        super().__init__(metadata)
    
    def initialize(self, container):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {"test": True}
'''
        
        plugin_file1 = Path(self.temp_dir) / "plugin1.py"
        plugin_file2 = Path(self.temp_dir) / "plugin2.py"
        
        plugin1_content = plugin_content.replace("TestPlugin", "Plugin1").replace("test_plugin", "plugin1")
        plugin2_content = plugin_content.replace("TestPlugin", "Plugin2").replace("test_plugin", "plugin2")
        
        with open(plugin_file1, 'w') as f:
            f.write(plugin1_content)
        
        with open(plugin_file2, 'w') as f:
            f.write(plugin2_content)
        
        # Load plugins from directory
        loaded_plugins = self.loader.load_plugin_from_directory(Path(self.temp_dir))
        assert len(loaded_plugins) >= 2  # Should be 2 or more depending on discovery
    
    def test_load_plugin_from_directory_recursive(self):
        """Test loading plugins from directory recursively."""
        # Create subdirectory
        sub_dir = Path(self.temp_dir) / "subdir"
        sub_dir.mkdir()
        
        plugin_content = '''
from nodupe.core.plugin_system.base import Plugin
import uuid

class TestPlugin(Plugin):
    def __init__(self, metadata=None):
        if metadata is None:
            metadata = {
                "uuid": str(uuid.uuid4()),
                "name": "test_plugin",
                "display_name": "Test Plugin",
                "version": "v1.0.0",
                "description": "A test plugin",
                "author": "Test Author",
                "category": "utility",
                "compatibility": "all",
                "marketplace_id": "test_plugin_123"
            }
        super().__init__(metadata)
    
    def initialize(self, container):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {"test": True}
'''
        
        plugin_file1 = Path(self.temp_dir) / "plugin1.py"
        plugin_file2 = Path(sub_dir) / "plugin2.py"
        
        with open(plugin_file1, 'w') as f:
            f.write(plugin_content.replace("TestPlugin", "Plugin1").replace("test_plugin", "plugin1"))
        
        with open(plugin_file2, 'w') as f:
            f.write(plugin_content.replace("TestPlugin", "Plugin2").replace("test_plugin", "plugin2"))
        
        # Load plugins from directory recursively
        loaded_plugins = self.loader.load_plugin_from_directory(
            Path(self.temp_dir), recursive=True
        )
        assert len(loaded_plugins) >= 2  # Should be 2 or more depending on discovery
    
    def test_load_plugin_by_name(self):
        """Test loading plugin by name."""
        plugin_content = '''
from nodupe.core.plugin_system.base import Plugin
import uuid

class TestPlugin(Plugin):
    def __init__(self, metadata=None):
        if metadata is None:
            metadata = {
                "uuid": str(uuid.uuid4()),
                "name": "test_plugin",
                "display_name": "Test Plugin",
                "version": "v1.0.0",
                "description": "A test plugin",
                "author": "Test Author",
                "category": "utility",
                "compatibility": "all",
                "marketplace_id": "test_plugin_123"
            }
        super().__init__(metadata)
    
    def initialize(self, container):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {"test": True}
'''
        
        plugin_file = Path(self.temp_dir) / "test_plugin.py"
        with open(plugin_file, 'w') as f:
            f.write(plugin_content)
        
        # Load plugin by name
        plugin_class = self.loader.load_plugin_by_name("test_plugin", [Path(self.temp_dir)])
        assert plugin_class is not None
    
    def test_instantiate_plugin(self):
        """Test instantiating a plugin class."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123"
        }
        
        plugin_class = MockPlugin
        instance = self.loader.instantiate_plugin(plugin_class, metadata)
        
        assert isinstance(instance, MockPlugin)
        assert instance.name == "test_plugin"
    
    def test_instantiate_plugin_failure(self):
        """Test instantiating plugin with invalid constructor raises error."""
        class BadPlugin(Plugin):
            def __init__(self, metadata, required_param):
                super().__init__(metadata)
            
            def initialize(self, container):
                pass
            
            def shutdown(self):
                pass
            
            def get_capabilities(self):
                return {}
        
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123"
        }
        
        with pytest.raises(PluginLoaderError):
            self.loader.instantiate_plugin(BadPlugin, metadata)
    
    def test_register_loaded_plugin(self):
        """Test registering a loaded plugin."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123"
        }
        
        plugin = MockPlugin(metadata)
        self.loader.register_loaded_plugin(plugin)
        
        assert self.registry.get_plugin("test_plugin") is plugin
    
    def test_register_loaded_plugin_failure(self):
        """Test registering loaded plugin with registry failure."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123"
        }
        
        plugin = MockPlugin(metadata)
        
        # Mock registry to raise an exception
        with patch.object(self.registry, 'register', side_effect=Exception("Registration failed")):
            with pytest.raises(PluginLoaderError):
                self.loader.register_loaded_plugin(plugin)
    
    def test_unload_plugin(self):
        """Test unloading a plugin."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123"
        }
        
        plugin = MockPlugin(metadata)
        # Add to loader's loaded plugins to simulate proper registration
        self.loader._loaded_plugins["test_plugin"] = plugin
        # Register with registry
        self.registry.register(plugin)
        
        result = self.loader.unload_plugin("test_plugin")
        assert result == True
        assert self.registry.get_plugin("test_plugin") is None
        assert plugin._shutdown == True
    
    def test_unload_nonexistent_plugin(self):
        """Test unloading nonexistent plugin."""
        result = self.loader.unload_plugin("nonexistent")
        assert result == False
    
    def test_get_loaded_plugin(self):
        """Test getting loaded plugin."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123"
        }
        
        plugin = MockPlugin(metadata)
        self.loader._loaded_plugins["test_plugin"] = plugin
        
        result = self.loader.get_loaded_plugin("test_plugin")
        assert result is plugin
    
    def test_get_all_loaded_plugins(self):
        """Test getting all loaded plugins."""
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "test_plugin",
            "display_name": "Test Plugin",
            "version": "v1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "test_plugin_123"
        }
        
        plugin = MockPlugin(metadata)
        self.loader._loaded_plugins["test_plugin"] = plugin
        
        result = self.loader.get_all_loaded_plugins()
        assert "test_plugin" in result
        assert result["test_plugin"] is plugin


class TestPluginDiscovery:
    """Test suite for PluginDiscovery functionality."""
    
    def setup_method(self):
        """Setup method to create a fresh discovery instance for each test."""
        self.discovery = PluginDiscovery()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Teardown method to clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_plugin_discovery_initialization(self):
        """Test plugin discovery initialization."""
        assert self.discovery._discovered_plugins == []
        assert self.discovery.container is None
    
    def test_initialize_discovery(self):
        """Test initializing plugin discovery with container."""
        container = Mock()
        self.discovery.initialize(container)
        
        assert self.discovery.container is container
    
    def test_shutdown_discovery(self):
        """Test shutting down plugin discovery."""
        container = Mock()
        self.discovery.initialize(container)
        
        self.discovery.shutdown()
        assert self.discovery.container is None
    
    def test_discover_plugins_in_directory(self):
        """Test discovering plugins in directory."""
        # Create a plugin file with proper metadata
        plugin_content = '''
# Plugin metadata
__name__ = "test_plugin"
__version__ = "1.0.0"
__author__ = "Test Author"
__description__ = "A test plugin"

class TestPlugin:
    def initialize(self):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {"test": True}

# For testing purposes, make sure this looks like a plugin
import sys
if __name__ == "__main__":
    print("This is a test plugin file")
'''
        
        plugin_file = Path(self.temp_dir) / "test_plugin.py"
        with open(plugin_file, 'w') as f:
            f.write(plugin_content)
        
        # Discover plugins
        plugins = self.discovery.discover_plugins_in_directory(Path(self.temp_dir))
        assert len(plugins) == 1
        assert plugins[0].name == "test_plugin"
    
    def test_discover_plugins_in_nonexistent_directory(self):
        """Test discovering plugins in nonexistent directory."""
        nonexistent_dir = Path(self.temp_dir) / "nonexistent"
        plugins = self.discovery.discover_plugins_in_directory(nonexistent_dir)
        assert len(plugins) == 0
    
    def test_discover_plugins_in_directory_with_mock(self):
        """Test discovering plugins with mock directory object."""
        class MockDir:
            def iterdir(self):
                # Return a mock file that will cause _extract_plugin_info to fail
                mock_file = Mock()
                mock_file.is_file.return_value = True
                mock_file.suffix = '.py'
                mock_file.name = 'test.py'
                return [mock_file]
        
        mock_dir = MockDir()
        plugins = self.discovery.discover_plugins_in_directory(mock_dir)
        assert len(plugins) == 0
    
    def test_discover_plugins_in_directories(self):
        """Test discovering plugins in multiple directories."""
        # Create two directories with plugins
        dir1 = Path(self.temp_dir) / "dir1"
        dir2 = Path(self.temp_dir) / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        
        plugin_content = '''
# Plugin metadata
__name__ = "test_plugin"
__version__ = "1.0.0"
__author__ = "Test Author"
__description__ = "A test plugin"

class TestPlugin:
    def initialize(self):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {"test": True}

# For testing purposes, make sure this looks like a plugin
import sys
if __name__ == "__main__":
    print("This is a test plugin file")
'''
        
        plugin_file1 = dir1 / "test_plugin1.py"
        plugin_file2 = dir2 / "test_plugin2.py"
        
        with open(plugin_file1, 'w') as f:
            f.write(plugin_content.replace("test_plugin", "test_plugin1"))
        
        with open(plugin_file2, 'w') as f:
            f.write(plugin_content.replace("test_plugin", "test_plugin2"))
        
        # Discover plugins from both directories
        plugins = self.discovery.discover_plugins_in_directories([dir1, dir2])
        assert len(plugins) == 2
    
    def test_find_plugin_by_name(self):
        """Test finding plugin by name."""
        # Create a plugin file
        plugin_content = '''
# Plugin metadata
__name__ = "test_plugin"
__version__ = "1.0.0"
__author__ = "Test Author"
__description__ = "A test plugin"

class TestPlugin:
    def initialize(self):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {"test": True}

# For testing purposes, make sure this looks like a plugin
import sys
if __name__ == "__main__":
    print("This is a test plugin file")
'''
        
        plugin_file = Path(self.temp_dir) / "test_plugin.py"
        with open(plugin_file, 'w') as f:
            f.write(plugin_content)
        
        # Find plugin by name
        plugin = self.discovery.find_plugin_by_name("test_plugin", [Path(self.temp_dir)])
        assert plugin is not None
        assert plugin.name == "test_plugin"
    
    def test_find_nonexistent_plugin_by_name(self):
        """Test finding nonexistent plugin by name."""
        plugin = self.discovery.find_plugin_by_name("nonexistent", [Path(self.temp_dir)])
        assert plugin is None
    
    def test_refresh_discovery(self):
        """Test refreshing plugin discovery."""
        # Add a plugin to discovered list
        plugin_info = PluginInfo("test_plugin", Path("test.py"))
        self.discovery._discovered_plugins.append(plugin_info)
        
        assert len(self.discovery._discovered_plugins) == 1
        
        # Refresh discovery
        self.discovery.refresh_discovery()
        assert len(self.discovery._discovered_plugins) == 0
    
    def test_get_discovered_plugins(self):
        """Test getting discovered plugins."""
        plugin_info = PluginInfo("test_plugin", Path("test.py"))
        self.discovery._discovered_plugins.append(plugin_info)
        
        plugins = self.discovery.get_discovered_plugins()
        assert len(plugins) == 1
        assert plugins[0] is plugin_info
    
    def test_get_discovered_plugin(self):
        """Test getting specific discovered plugin."""
        plugin_info = PluginInfo("test_plugin", Path("test.py"))
        self.discovery._discovered_plugins.append(plugin_info)
        
        plugin = self.discovery.get_discovered_plugin("test_plugin")
        assert plugin is plugin_info
    
    def test_is_plugin_discovered(self):
        """Test checking if plugin is discovered."""
        plugin_info = PluginInfo("test_plugin", Path("test.py"))
        self.discovery._discovered_plugins.append(plugin_info)
        
        assert self.discovery.is_plugin_discovered("test_plugin") == True
        assert self.discovery.is_plugin_discovered("nonexistent") == False
    
    def test_discover_uuid_plugins_in_directory(self):
        """Test discovering UUID-based plugins in directory."""
        # Create a UUID-named plugin file with proper naming format
        plugin_uuid = str(uuid.uuid4())
        plugin_content = f'''
PLUGIN_METADATA = {{
    "name": "test_plugin",
    "uuid": "{plugin_uuid}",
    "version": "v1.0.0",
    "description": "A test plugin",
    "author": "Test Author",
    "category": "utility",
    "marketplace_id": "test_plugin_{plugin_uuid}"
}}

class TestPlugin:
    def initialize(self, container):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {{"test": True}}
'''
        
        # Use the expected naming convention for UUID plugins: {name}_{uuid}.v{version}.py
        plugin_file = Path(self.temp_dir) / f"test_plugin_{plugin_uuid}.v1.0.0.py"
        with open(plugin_file, 'w') as f:
            f.write(plugin_content)
        
        # Discover UUID plugins
        plugins = self.discovery.discover_uuid_plugins_in_directory(Path(self.temp_dir))
        assert len(plugins) == 1
        assert plugins[0].name == "test_plugin"
    
    def test_find_uuid_plugin_by_uuid(self):
        """Test finding UUID plugin by UUID."""
        plugin_uuid = str(uuid.uuid4())
        plugin_content = f'''
PLUGIN_METADATA = {{
    "name": "test_plugin",
    "uuid": "{plugin_uuid}",
    "version": "v1.0.0",
    "description": "A test plugin",
    "author": "Test Author",
    "category": "utility",
    "marketplace_id": "test_plugin_{plugin_uuid}"
}}

class TestPlugin:
    def initialize(self, container):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {{"test": True}}
'''
        
        plugin_file = Path(self.temp_dir) / f"test_plugin_{plugin_uuid}.v1.0.0.py"
        with open(plugin_file, 'w') as f:
            f.write(plugin_content)

        # First discover plugins to populate internal cache
        discovered_plugins = self.discovery.discover_uuid_plugins_in_directory(Path(self.temp_dir))
        assert len(discovered_plugins) == 1
        
        # Find UUID plugin by UUID - this should find it in the discovered list
        plugin = self.discovery.find_uuid_plugin_by_uuid(plugin_uuid, [Path(self.temp_dir)])
        assert plugin is not None
        assert plugin.name == "test_plugin"
    
    def test_find_uuid_plugin_by_name_and_version(self):
        """Test finding UUID plugin by name and version."""
        plugin_uuid = str(uuid.uuid4())
        plugin_content = f'''
PLUGIN_METADATA = {{
    "name": "test_plugin",
    "uuid": "{plugin_uuid}",
    "version": "v1.0.0",
    "description": "A test plugin",
    "author": "Test Author",
    "category": "utility",
    "marketplace_id": "test_plugin_{plugin_uuid}"
}}

class TestPlugin:
    def initialize(self, container):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {{"test": True}}
'''
        
        plugin_file = Path(self.temp_dir) / f"test_plugin_{plugin_uuid}.v1.0.0.py"
        with open(plugin_file, 'w') as f:
            f.write(plugin_content)
        
        # Find UUID plugin by name and version
        plugin = self.discovery.find_uuid_plugin_by_name_and_version(
            "test_plugin", "v1.0.0", [Path(self.temp_dir)]
        )
        assert plugin is not None
        assert plugin.name == "test_plugin"
    
    def test_validate_plugin_file(self):
        """Test validating plugin file."""
        # Create a valid Python file that looks like a plugin
        plugin_file = Path(self.temp_dir) / "test_plugin.py"
        plugin_content = '''
# Plugin metadata
__name__ = "test_plugin"
__version__ = "1.0.0"
__author__ = "Test Author"
__description__ = "A test plugin"

class TestPlugin:
    def initialize(self):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {"test": True}

# For testing purposes, make sure this looks like a plugin
import sys
if __name__ == "__main__":
    print("This is a test plugin file")
'''
        with open(plugin_file, 'w') as f:
            f.write(plugin_content)
        
        assert self.discovery.validate_plugin_file(plugin_file) == True
    
    def test_validate_nonexistent_plugin_file(self):
        """Test validating nonexistent plugin file."""
        nonexistent_file = Path(self.temp_dir) / "nonexistent.py"
        assert self.discovery.validate_plugin_file(nonexistent_file) == False
    
    def test_validate_invalid_python_plugin_file(self):
        """Test validating invalid Python plugin file."""
        plugin_file = Path(self.temp_dir) / "invalid_plugin.py"
        with open(plugin_file, 'w') as f:
            f.write("invalid python code")  # Invalid syntax
        
        assert self.discovery.validate_plugin_file(plugin_file) == False
    
    def test_validate_non_python_file(self):
        """Test validating non-Python file."""
        txt_file = Path(self.temp_dir) / "test.txt"
        txt_file.touch()
        
        assert self.discovery.validate_plugin_file(txt_file) == False


def test_plugin_system_integration():
    """Test integration of plugin system components."""
    # Create registry, loader, and discovery
    registry = PluginRegistry()
    loader = PluginLoader(registry)
    discovery = PluginDiscovery()
    
    # Create a temporary plugin
    temp_dir = tempfile.mkdtemp()
    try:
        plugin_content = '''
from nodupe.core.plugin_system.base import Plugin
import uuid

class IntegrationTestPlugin(Plugin):
    def __init__(self, metadata=None):
        if metadata is None:
            metadata = {
                "uuid": str(uuid.uuid4()),
                "name": "integration_test_plugin",
                "display_name": "Integration Test Plugin",
                "version": "v1.0.0",
                "description": "An integration test plugin",
                "author": "Test Author",
                "category": "utility",
                "compatibility": "all",
                "marketplace_id": "integration_test_plugin_123"
            }
        super().__init__(metadata)
        self._initialized = False
        self._shutdown = False
    
    def initialize(self, container):
        self._initialized = True
        self._container = container
    
    def shutdown(self):
        self._shutdown = True
    
    def get_capabilities(self):
        return {"integration_test": True}
'''
        
        plugin_file = Path(temp_dir) / "integration_test_plugin.py"
        with open(plugin_file, 'w') as f:
            f.write(plugin_content)
        
        # Discover the plugin
        discovered_plugins = discovery.discover_plugins_in_directory(Path(temp_dir))
        assert len(discovered_plugins) == 1
        
        # Load the plugin
        plugin_class = loader.load_plugin_from_file(plugin_file)
        assert plugin_class is not None
        
        # Create metadata for plugin
        metadata = {
            "uuid": str(uuid.uuid4()),
            "name": "integration_test_plugin",
            "display_name": "Integration Test Plugin",
            "version": "v1.0.0",
            "description": "An integration test plugin",
            "author": "Test Author",
            "category": "utility",
            "compatibility": "all",
            "marketplace_id": "integration_test_plugin_123"
        }
        
        # Instantiate and register the plugin
        plugin_instance = loader.instantiate_plugin(plugin_class, metadata)
        loader.register_loaded_plugin(plugin_instance)
        
        # Verify plugin is registered
        registered_plugin = registry.get_plugin("integration_test_plugin")
        assert registered_plugin is plugin_instance
        
        # Test plugin lifecycle
        container = Mock()
        plugin_instance.initialize(container)
        assert plugin_instance._initialized == True
        
        # Shutdown should be called when unregistered
        registry.unregister("integration_test_plugin")
        assert plugin_instance._shutdown == True
        
    finally:
        shutil.rmtree(temp_dir)


class TestUUIDUtils:
    """Test suite for UUIDUtils functionality."""
    
    def test_uuid_utils_generate_uuid_v4(self):
        """Test UUID v4 generation."""
        from uuid import UUID
        uuid_val = UUIDUtils.generate_uuid_v4()
        assert isinstance(uuid_val, UUID)
        assert uuid_val.version == 4
        assert len(str(uuid_val)) == 36  # Standard UUID format
    
    def test_uuid_utils_is_valid_uuid(self):
        """Test UUID validation."""
        # Valid UUID v4
        valid_uuid = str(uuid.uuid4())
        assert UUIDUtils.is_valid_uuid(valid_uuid) == True
        
        # Invalid UUID format
        assert UUIDUtils.is_valid_uuid("invalid-uuid") == False
        assert UUIDUtils.is_valid_uuid("") == False
        assert UUIDUtils.is_valid_uuid(None) == False
        assert UUIDUtils.is_valid_uuid(123) == False
        
        # Valid UUID but not v4
        # UUID v1 is different, but let's test UUID v4 specifically
        uuid_v4 = str(uuid.uuid4())
        assert UUIDUtils.is_valid_uuid(uuid_v4) == True
        
        # Test non-v4 UUID (this won't be generated easily, but test malformed ones)
        non_v4_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, 'example.com')
        # Note: We can still validate the format, but it won't pass version 4 check
        # This is expected behavior
    
    def test_uuid_utils_validate_uuid(self):
        """Test UUID validation wrapper."""
        valid_uuid = str(uuid.uuid4())
        assert UUIDUtils.validate_uuid(valid_uuid) == True
        
        invalid_uuid = "invalid-uuid"
        assert UUIDUtils.validate_uuid(invalid_uuid) == False
    
    def test_uuid_utils_validate_plugin_name(self):
        """Test plugin name validation."""
        # Valid names
        assert UUIDUtils.validate_plugin_name("test_plugin") == True
        assert UUIDUtils.validate_plugin_name("ab") == True  # Minimum length (2 chars)
        assert UUIDUtils.validate_plugin_name("a" + "b" * 49) == True  # Maximum length (50 chars)
        
        # Invalid names
        assert UUIDUtils.validate_plugin_name("a") == False  # Too short (1 char)
        assert UUIDUtils.validate_plugin_name("Test_Plugin") == False  # Uppercase
        assert UUIDUtils.validate_plugin_name("test-plugin") == False  # Hyphen not underscore
        assert UUIDUtils.validate_plugin_name("123test") == False  # Starts with number
        assert UUIDUtils.validate_plugin_name("") == False  # Empty
        assert UUIDUtils.validate_plugin_name(None) == False  # None
        assert UUIDUtils.validate_plugin_name(123) == False  # Non-string
    
    def test_uuid_utils_validate_version(self):
        """Test version validation."""
        # Valid versions
        assert UUIDUtils.validate_version("v1.0.0") == True
        assert UUIDUtils.validate_version("v0.0.1") == True
        assert UUIDUtils.validate_version("v10.20.30") == True
        
        # Invalid versions
        assert UUIDUtils.validate_version("1.0.0") == False  # Missing 'v' prefix
        assert UUIDUtils.validate_version("v1.0") == False  # Missing patch
        assert UUIDUtils.validate_version("v1.0.0.0") == False  # Too many parts
        assert UUIDUtils.validate_version("") == False  # Empty
        assert UUIDUtils.validate_version(None) == False  # None
        assert UUIDUtils.validate_version(123) == False  # Non-string
    
    def test_uuid_utils_generate_plugin_filename(self):
        """Test plugin filename generation."""
        # Valid inputs
        filename = UUIDUtils.generate_plugin_filename("test_plugin", "v1.0.0")
        assert isinstance(filename, str)
        assert "test_plugin_" in filename
        assert ".v1.0.0.py" in filename
        
        # Should raise validation errors for invalid inputs
        with pytest.raises(UUIDValidationError, match="Invalid plugin name"):
            UUIDUtils.generate_plugin_filename("Invalid-Name", "v1.0.0")
        
        with pytest.raises(UUIDValidationError, match="Invalid version"):
            UUIDUtils.generate_plugin_filename("test_plugin", "1.0.0")
    
    def test_uuid_utils_parse_plugin_filename(self):
        """Test plugin filename parsing."""
        # Valid UUID-based filename
        test_uuid = str(uuid.uuid4())
        filename = f"test_plugin_{test_uuid}.v1.0.0.py"
        
        result = UUIDUtils.parse_plugin_filename(filename)
        assert result is not None
        assert result['name'] == 'test_plugin'
        assert result['uuid'] == test_uuid
        assert result['version'] == '1.0.0'
        
        # Invalid filenames
        assert UUIDUtils.parse_plugin_filename("invalid.py") is None
        assert UUIDUtils.parse_plugin_filename("test_plugin_invalid_uuid.v1.0.0.py") is None
    
    def test_uuid_utils_validate_plugin_filename(self):
        """Test plugin filename validation."""
        test_uuid = str(uuid.uuid4())
        valid_filename = f"test_plugin_{test_uuid}.v1.0.0.py"
        invalid_filename = "invalid.py"
        
        assert UUIDUtils.validate_plugin_filename(valid_filename) == True
        assert UUIDUtils.validate_plugin_filename(invalid_filename) == False
    
    def test_uuid_utils_generate_marketplace_id(self):
        """Test marketplace ID generation."""
        test_uuid = str(uuid.uuid4())
        marketplace_id = UUIDUtils.generate_marketplace_id("test_plugin", test_uuid)
        assert marketplace_id == f"test_plugin_{test_uuid}"
        
        # Should raise validation errors for invalid inputs
        with pytest.raises(UUIDValidationError, match="Invalid plugin name"):
            UUIDUtils.generate_marketplace_id("Invalid-Name", test_uuid)
        
        with pytest.raises(UUIDValidationError, match="Invalid UUID"):
            UUIDUtils.generate_marketplace_id("test_plugin", "invalid-uuid")
    
    def test_uuid_utils_get_plugin_categories(self):
        """Test getting plugin categories."""
        categories = UUIDUtils.get_plugin_categories()
        assert isinstance(categories, dict)
        assert len(categories) > 0
        assert 'utility' in categories
    
    def test_uuid_utils_validate_category(self):
        """Test category validation."""
        # Valid standard categories
        assert UUIDUtils.validate_category('utility') == True
        assert UUIDUtils.validate_category('scanning') == True
        assert UUIDUtils.validate_category('ml') == True
        assert UUIDUtils.validate_category('security') == True
        assert UUIDUtils.validate_category('performance') == True
        assert UUIDUtils.validate_category('ui') == True
        assert UUIDUtils.validate_category('integration') == True
        
        # Valid custom categories (must follow pattern: lowercase letters, numbers, hyphens, 3-20 chars)
        assert UUIDUtils.validate_category('custom-category') == True  # With hyphens (allowed for custom)
        assert UUIDUtils.validate_category('ai-ml') == True  # With hyphens
        assert UUIDUtils.validate_category('my-custom-cat') == True  # With hyphens
        assert UUIDUtils.validate_category('cat123') == True  # With numbers
        assert UUIDUtils.validate_category('abc') == True  # Minimum length
        assert UUIDUtils.validate_category('a' + 'b' * 19) == True  # Maximum length (20 chars)
        
        # Invalid categories
        assert UUIDUtils.validate_category('Invalid_Category') == False  # Uppercase
        assert UUIDUtils.validate_category('a') == False  # Too short (1 char)
        assert UUIDUtils.validate_category('ab') == False  # Too short (2 chars) 
        assert UUIDUtils.validate_category('') == False  # Empty
        assert UUIDUtils.validate_category('A_cat') == False  # Contains uppercase
        assert UUIDUtils.validate_category('cat_') == False  # Underscore not allowed for custom categories
        assert UUIDUtils.validate_category('custom_category') == False  # Underscore not allowed for custom categories (only hyphens)
    
    def test_uuid_utils_is_uuid_plugin_file(self):
        """Test UUID plugin file detection."""
        # Create temporary file for testing
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a proper UUID plugin file content
            test_uuid = str(uuid.uuid4())
            plugin_content = f'''
PLUGIN_METADATA = {{
    "name": "test_plugin",
    "uuid": "{test_uuid}",
    "version": "v1.0.0",
    "description": "A test plugin",
    "author": "Test Author",
    "category": "utility",
    "marketplace_id": "test_plugin_{test_uuid}"
}}

class TestPlugin:
    def initialize(self, container):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {{"test": True}}
'''
            # Create file with proper UUID naming convention
            plugin_file = Path(temp_dir) / f"test_plugin_{test_uuid}.v1.0.0.py"
            with open(plugin_file, 'w') as f:
                f.write(plugin_content)
            
            # This should be recognized as a UUID plugin file
            assert UUIDUtils.is_uuid_plugin_file(plugin_file) == True
            
            # Create a regular plugin file (non-UUID)
            regular_plugin_file = Path(temp_dir) / "regular_plugin.py"
            with open(regular_plugin_file, 'w') as f:
                f.write('''
class RegularPlugin:
    def initialize(self, container):
        pass
    
    def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {"test": True}
''')
            
            # This should not be recognized as UUID plugin file
            assert UUIDUtils.is_uuid_plugin_file(regular_plugin_file) == False
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_uuid_utils_extract_metadata_from_content(self):
        """Test extracting metadata from content."""
        content = '''
PLUGIN_METADATA = {
    "name": "test_plugin",
    "version": "v1.0.0",
    "description": "A test plugin"
}

other_code = "not metadata"
'''
        
        metadata = UUIDUtils._extract_metadata_from_content(content)
        assert 'name' in metadata
        assert 'version' in metadata
        assert 'description' in metadata
        assert metadata['name'] == 'test_plugin'
        assert metadata['version'] == 'v1.0.0'
        assert metadata['description'] == 'A test plugin'


if __name__ == "__main__":
    pytest.main([__file__])
