"""Plugin Discovery Module.

Plugin discovery and scanning using standard library only.

Key Features:
    - Plugin file discovery in directories
    - Plugin metadata extraction
    - Plugin validation and compatibility checking
    - Standard library only (no external dependencies)

Dependencies:
    - pathlib (standard library)
    - typing (standard library)
    - importlib (standard library)
"""

from pathlib import Path
from typing import List, Dict, Optional, Any


class PluginDiscoveryError(Exception):
    """Plugin discovery error"""


class PluginInfo:
    """Plugin metadata information."""

    def __init__(
        self,
        name: str,
        path: Path,
        version: str = "1.0.0",
        description: str = "",
        author: str = "",
        dependencies: Optional[List[str]] = None,
        type: str = "generic"
    ):
        self.name = name
        self.path = path
        self.version = version
        self.description = description
        self.author = author
        self.dependencies = dependencies if dependencies is not None else []
        self.type = type
        self.enabled = True

    def __repr__(self) -> str:
        return f"PluginInfo(name='{self.name}', version='{self.version}', path='{self.path}')"


class PluginDiscovery:
    """Handle plugin discovery and scanning.

    Discovers plugins in specified directories and extracts metadata.
    """

    def __init__(self):
        """Initialize plugin discovery."""
        self._discovered_plugins: Dict[str, PluginInfo] = {}

    def discover_plugins_in_directory(
        self,
        directory: Path,
        recursive: bool = True,
        file_pattern: str = "*.py"
    ) -> List[PluginInfo]:
        """Discover plugins in a directory.

        Args:
            directory: Directory to scan for plugins
            recursive: If True, scan subdirectories recursively
            file_pattern: File pattern to match (default: "*.py")

        Returns:
            List of discovered plugin information

        Raises:
            PluginDiscoveryError: If discovery fails
        """
        try:
            if not directory.exists():
                raise PluginDiscoveryError(f"Directory does not exist: {directory}")

            if not directory.is_dir():
                raise PluginDiscoveryError(f"Path is not a directory: {directory}")

            # Find Python files
            if recursive:
                pattern = f"**/{file_pattern}"
            else:
                pattern = file_pattern

            python_files = list(directory.glob(pattern))

            discovered_plugins = []
            for file_path in python_files:
                try:
                    plugin_info = self._extract_plugin_info(file_path)
                    if plugin_info:
                        discovered_plugins.append(plugin_info)
                        self._discovered_plugins[plugin_info.name] = plugin_info
                except PluginDiscoveryError:
                    # Continue discovering other plugins even if one fails
                    continue

            return discovered_plugins

        except Exception as e:
            if isinstance(e, PluginDiscoveryError):
                raise
            raise PluginDiscoveryError(f"Failed to discover plugins in {directory}: {e}") from e

    def discover_plugins_in_directories(
        self,
        directories: List[Path],
        recursive: bool = True,
        file_pattern: str = "*.py"
    ) -> List[PluginInfo]:
        """Discover plugins in multiple directories.

        Args:
            directories: List of directories to scan
            recursive: If True, scan subdirectories recursively
            file_pattern: File pattern to match (default: "*.py")

        Returns:
            List of discovered plugin information
        """
        all_plugins = []
        for directory in directories:
            try:
                plugins = self.discover_plugins_in_directory(
                    directory, recursive, file_pattern
                )
                all_plugins.extend(plugins)
            except PluginDiscoveryError:
                # Continue with other directories even if one fails
                continue

        return all_plugins

    def find_plugin_by_name(
        self,
        plugin_name: str,
        search_directories: List[Path],
        recursive: bool = True
    ) -> Optional[PluginInfo]:
        """Find a specific plugin by name in search directories.

        Args:
            plugin_name: Name of plugin to find
            search_directories: List of directories to search
            recursive: If True, search subdirectories

        Returns:
            PluginInfo if found, None otherwise
        """
        for directory in search_directories:
            try:
                plugins = self.discover_plugins_in_directory(
                    directory, recursive, f"{plugin_name}.py"
                )

                for plugin in plugins:
                    if plugin.name == plugin_name:
                        return plugin

                # Also check for plugin as directory with __init__.py
                plugin_dir = directory / plugin_name
                if plugin_dir.exists() and (plugin_dir / "__init__.py").exists():
                    plugin_path = plugin_dir / "__init__.py"
                    plugin_info = self._extract_plugin_info(plugin_path)
                    if plugin_info and plugin_info.name == plugin_name:
                        return plugin_info

            except PluginDiscoveryError:
                continue

        return None

    def refresh_discovery(self) -> None:
        """Clear cached discoveries and rediscover plugins."""
        self._discovered_plugins.clear()

    def get_discovered_plugins(self) -> List[PluginInfo]:
        """Get all currently discovered plugins.

        Returns:
            List of discovered plugin information
        """
        return list(self._discovered_plugins.values())

    def get_discovered_plugin(self, plugin_name: str) -> Optional[PluginInfo]:
        """Get a specific discovered plugin.

        Args:
            plugin_name: Name of plugin to get

        Returns:
            PluginInfo if discovered, None otherwise
        """
        return self._discovered_plugins.get(plugin_name)

    def is_plugin_discovered(self, plugin_name: str) -> bool:
        """Check if a plugin has been discovered.

        Args:
            plugin_name: Name of plugin to check

        Returns:
            True if plugin is discovered
        """
        return plugin_name in self._discovered_plugins

    def _extract_plugin_info(self, file_path: Path) -> Optional[PluginInfo]:
        """Extract plugin information from a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            PluginInfo if valid plugin found, None otherwise
        """
        try:
            # Read file and look for plugin metadata
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for common plugin metadata patterns
            metadata = self._parse_metadata(content)

            # Use filename as default name if not found in metadata
            name = metadata.get('name', file_path.stem)

            # Validate that this looks like a plugin file
            if not self._looks_like_plugin(content):
                return None

            return PluginInfo(
                name=name,
                path=file_path,
                version=metadata.get('version', '1.0.0'),
                description=metadata.get('description', ''),
                author=metadata.get('author', ''),
                dependencies=metadata.get('dependencies', []),
                type=metadata.get('type', 'generic')
            )

        except Exception:
            # If parsing fails, return None (not a valid plugin)
            return None

    def _parse_metadata(self, content: str) -> Dict[str, Any]:
        """Parse metadata from Python file content.

        Args:
            content: Python file content

        Returns:
            Dictionary of parsed metadata
        """
        metadata = {}

        # Look for common metadata patterns
        lines = content.split('\n')

        for line in lines:
            line = line.strip()

            # Look for assignment patterns
            if '=' in line and not line.startswith('#'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()

                    # Clean up value
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    # Map common metadata keys
                    if key in ['__version__', 'VERSION', 'version']:
                        metadata['version'] = value
                    elif key in ['__author__', 'AUTHOR', 'author']:
                        metadata['author'] = value
                    elif key in ['__description__', 'DESCRIPTION', 'description']:
                        metadata['description'] = value
                    elif key in ['__name__', 'NAME', 'name']:
                        metadata['name'] = value
                    elif key in ['TYPE', 'type']:
                        metadata['type'] = value

        return metadata

    def _looks_like_plugin(self, content: str) -> bool:
        """Check if content looks like a plugin file.

        Args:
            content: Python file content

        Returns:
            True if content appears to be a plugin
        """
        # Look for plugin-related keywords
        content_lower = content.lower()

        # Simple keyword checks
        has_imports = 'import' in content
        has_class = 'class' in content
        has_methods = ('def ' in content and
                       any(keyword in content_lower for keyword in ['initialize', 'shutdown', 'get_capabilities']))

        return has_imports and has_class and has_methods

    def validate_plugin_file(self, file_path: Path) -> bool:
        """Validate that a file is a valid plugin file.

        Args:
            file_path: Path to file to validate

        Returns:
            True if file is a valid plugin
        """
        try:
            # Check file extension
            if file_path.suffix != '.py':
                return False

            # Check if file exists
            if not file_path.exists():
                return False

            # Check if file is readable
            if not file_path.is_file():
                return False

            # Check file size (reasonable limit)
            if file_path.stat().st_size == 0:
                return False

            # Try to parse the file syntactically
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            # Attempt to compile to check syntax
            try:
                compile(file_content, str(file_path), 'exec')
            except SyntaxError:
                return False

            # Check if it looks like a plugin
            return self._looks_like_plugin(file_content)

        except Exception:
            return False


def create_plugin_discovery() -> PluginDiscovery:
    """Create a plugin discovery instance.

    Returns:
        PluginDiscovery instance
    """
    return PluginDiscovery()
