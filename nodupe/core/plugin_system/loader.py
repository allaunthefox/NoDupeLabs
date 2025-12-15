"""Plugin Loader Module.

Dynamic plugin loading and management using standard library only.

Key Features:
    - Safe plugin loading with validation
    - Plugin dependency resolution
    - Plugin lifecycle management
    - Graceful error handling
    - Standard library only (no external dependencies)

Dependencies:
    - importlib (standard library)
    - pathlib (standard library)
    - typing (standard library)
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
from .base import Plugin
from .registry import PluginRegistry


class PluginLoaderError(Exception):
    """Plugin loader error"""


class PluginLoader:
    """Handle plugin loading and management.

    Provides safe plugin loading with validation, dependency resolution,
    and lifecycle management.
    """

    def __init__(self, registry: PluginRegistry):
        """Initialize plugin loader.

        Args:
            registry: Plugin registry instance
        """
        self.registry = registry
        self._loaded_plugins: Dict[str, Plugin] = {}
        self._plugin_modules: Dict[str, Any] = {}

    def load_plugin_from_file(
        self,
        plugin_path: Path
    ) -> Optional[Type[Plugin]]:
        """Load a plugin from a Python file.

        Args:
            plugin_path: Path to plugin file

        Returns:
            Plugin class or None if loading failed

        Raises:
            PluginLoaderError: If plugin loading fails
        """
        try:
            # Validate file path
            if not plugin_path.exists():
                raise PluginLoaderError(f"Plugin file does not exist: {plugin_path}")

            if not plugin_path.suffix == '.py':
                raise PluginLoaderError(f"Plugin file must be Python: {plugin_path}")

            # Create module spec and load module
            module_name = f"plugin_{plugin_path.stem}_{id(plugin_path)}"
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            if spec is None or spec.loader is None:
                raise PluginLoaderError(f"Could not create module spec: {plugin_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find plugin class in module
            plugin_class = self._find_plugin_class(module)
            if plugin_class is None:
                raise PluginLoaderError(f"No Plugin subclass found in: {plugin_path}")

            # Validate plugin class
            if not self._validate_plugin_class(plugin_class):
                raise PluginLoaderError(f"Invalid plugin class: {plugin_class}")

            # Store module reference
            self._plugin_modules[plugin_class.__name__] = module

            return plugin_class

        except Exception as e:
            if isinstance(e, PluginLoaderError):
                raise
            raise PluginLoaderError(f"Failed to load plugin {plugin_path}: {e}") from e

    def load_plugin_from_directory(
        self,
        plugin_dir: Path,
        recursive: bool = False
    ) -> List[Type[Plugin]]:
        """Load all plugins from a directory.

        Args:
            plugin_dir: Directory containing plugin files
            recursive: If True, search subdirectories

        Returns:
            List of loaded plugin classes

        Raises:
            PluginLoaderError: If plugin loading fails
        """
        try:
            if not plugin_dir.exists():
                raise PluginLoaderError(f"Plugin directory does not exist: {plugin_dir}")

            if not plugin_dir.is_dir():
                raise PluginLoaderError(f"Path is not a directory: {plugin_dir}")

            # Find Python files, excluding __init__.py files
            pattern = "**/*.py" if recursive else "*.py"
            python_files = list(plugin_dir.glob(pattern))
            
            # Filter out __init__.py files as they're not plugins
            python_files = [f for f in python_files if f.name != '__init__.py']

            loaded_plugins: List[Type[Plugin]] = []
            for file_path in python_files:
                try:
                    plugin_class = self.load_plugin_from_file(file_path)
                    if plugin_class:
                        loaded_plugins.append(plugin_class)
                except PluginLoaderError:
                    # Continue loading other plugins even if one fails
                    continue

            return loaded_plugins

        except Exception as e:
            if isinstance(e, PluginLoaderError):
                raise
            raise PluginLoaderError(f"Failed to load plugins from {plugin_dir}: {e}") from e

    def load_plugin_by_name(
        self,
        plugin_name: str,
        plugin_dirs: List[Path]
    ) -> Optional[Type[Plugin]]:
        """Load a plugin by name from specified directories.

        Args:
            plugin_name: Name of plugin to load
            plugin_dirs: List of directories to search

        Returns:
            Plugin class or None if not found

        Raises:
            PluginLoaderError: If plugin loading fails
        """
        for plugin_dir in plugin_dirs:
            plugin_path = plugin_dir / f"{plugin_name}.py"
            if plugin_path.exists():
                return self.load_plugin_from_file(plugin_path)

            # Also try subdirectory with __init__.py
            plugin_subdir = plugin_dir / plugin_name
            if plugin_subdir.exists() and (plugin_subdir / "__init__.py").exists():
                return self.load_plugin_from_file(plugin_subdir / "__init__.py")

        return None

    def instantiate_plugin(
        self,
        plugin_class: Type[Plugin],
        *args: Any,
        **kwargs: Any
    ) -> Plugin:
        """Instantiate a plugin class.

        Args:
            plugin_class: Plugin class to instantiate
            *args: Arguments to pass to plugin constructor
            **kwargs: Keyword arguments to pass to plugin constructor

        Returns:
            Plugin instance

        Raises:
            PluginLoaderError: If instantiation fails
        """
        try:
            instance = plugin_class(*args, **kwargs)
            return instance
        except Exception as e:
            raise PluginLoaderError(f"Failed to instantiate plugin {plugin_class}: {e}") from e

    def register_loaded_plugin(
        self,
        plugin_instance: Plugin,
        plugin_path: Optional[Path] = None
    ) -> None:
        """Register a loaded plugin with the registry.

        Args:
            plugin_instance: Plugin instance to register
            plugin_path: Optional path where plugin was loaded from

        Raises:
            PluginLoaderError: If registration fails
        """
        try:
            self.registry.register(plugin_instance)

        except Exception as e:
            raise PluginLoaderError(f"Failed to register plugin {plugin_instance.name}: {e}") from e

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin.

        Args:
            plugin_name: Name of plugin to unload

        Returns:
            True if plugin was unloaded, False if not found
        """
        if plugin_name in self._loaded_plugins:
            plugin_instance = self._loaded_plugins[plugin_name]
            
            # Remove from registry
            try:
                self.registry.unregister(plugin_name)
            except KeyError:
                pass  # Plugin might not be registered in registry
            
            # Remove from loaded plugins
            del self._loaded_plugins[plugin_name]
            
            # Remove module from sys.modules if it exists
            module_name = getattr(plugin_instance, '__module__', None)
            if module_name and module_name in sys.modules:
                del sys.modules[module_name]

            return True

        return False

    def get_loaded_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get a loaded plugin instance.

        Args:
            plugin_name: Name of plugin to get

        Returns:
            Plugin instance or None if not loaded
        """
        return self._loaded_plugins.get(plugin_name)

    def get_all_loaded_plugins(self) -> Dict[str, Plugin]:
        """Get all loaded plugin instances.

        Returns:
            Dictionary of plugin name to instance
        """
        return self._loaded_plugins.copy()

    def _find_plugin_class(self, module: Any) -> Optional[Type[Plugin]]:
        """Find Plugin subclass in module.

        Args:
            module: Module to search

        Returns:
            Plugin class or None if not found
        """
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, Plugin) and 
                attr != Plugin):
                return attr
        return None

    def _validate_plugin_class(self, plugin_class: Type[Plugin]) -> bool:
        """Validate plugin class.

        Args:
            plugin_class: Plugin class to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required attributes exist
            required_attrs = ['name']
            for attr in required_attrs:
                if not hasattr(plugin_class, attr):
                    return False

            # Check name is valid
            # For properties, we need to check if it's a property descriptor
            name_attr = getattr(plugin_class, 'name')
            
            # Check if it's a property descriptor
            if isinstance(name_attr, property):
                # For property, try to instantiate the class and get the value
                try:
                    temp_instance = plugin_class()
                    name = temp_instance.name
                except Exception:
                    return False
            else:
                # It's a class attribute
                name = name_attr

            if not name or not isinstance(name, str) or not name.strip():
                return False

            return True

        except Exception:
            return False


def create_plugin_loader(registry: PluginRegistry) -> PluginLoader:
    """Create a plugin loader instance.

    Args:
        registry: Plugin registry instance

    Returns:
        PluginLoader instance
    """
    return PluginLoader(registry)
