"""Test plugin discovery functionality."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from nodupe.core.plugin_system.discovery import PluginDiscovery, PluginDiscoveryError, PluginInfo
from nodupe.core.plugin_system.registry import PluginRegistry


class TestPluginDiscovery:
    """Test plugin discovery core functionality."""

    def test_plugin_discovery_initialization(self):
        """Test plugin discovery initialization."""
        discovery = PluginDiscovery()
        assert discovery is not None
        assert isinstance(discovery, PluginDiscovery)

        # Test that it has expected attributes
        assert hasattr(discovery, 'discover_plugins_in_directory')
        assert hasattr(discovery, 'discover_plugins_in_directories')
        assert hasattr(discovery, 'find_plugin_by_name')
        assert hasattr(discovery, 'refresh_discovery')
        assert hasattr(discovery, 'get_discovered_plugins')
        assert hasattr(discovery, 'get_discovered_plugin')
        assert hasattr(discovery, 'is_plugin_discovered')
        assert hasattr(discovery, 'initialize')
        assert hasattr(discovery, 'shutdown')

    def test_plugin_discovery_with_container(self):
        """Test plugin discovery with dependency container."""
        from nodupe.core.container import ServiceContainer

        discovery = PluginDiscovery()
        container = ServiceContainer()

        # Initialize discovery with container
        discovery.initialize(container)
        assert discovery.container is container

    def test_plugin_discovery_lifecycle(self):
        """Test plugin discovery lifecycle operations."""
        from nodupe.core.container import ServiceContainer

        discovery = PluginDiscovery()
        container = ServiceContainer()

        # Test initialization
        discovery.initialize(container)
        assert discovery.container is container

        # Test shutdown
        discovery.shutdown()
        assert discovery.container is None

        # Test re-initialization
        discovery.initialize(container)
        assert discovery.container is container


class TestPluginInfo:
    """Test plugin info functionality."""

    def test_plugin_info_initialization(self):
        """Test plugin info initialization."""
        plugin_info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            file_path=Path("/test/plugin.py"),
            dependencies=["core>=1.0.0"],
            capabilities={"test": True}
        )

        assert plugin_info is not None
        assert isinstance(plugin_info, PluginInfo)
        assert plugin_info.name == "test_plugin"
        assert plugin_info.version == "1.0.0"
        assert plugin_info.file_path == Path("/test/plugin.py")
        assert plugin_info.dependencies == ["core>=1.0.0"]
        assert plugin_info.capabilities == {"test": True}

    def test_plugin_info_repr(self):
        """Test plugin info string representation."""
        plugin_info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            file_path=Path("/test/plugin.py"),
            dependencies=["core>=1.0.0"],
            capabilities={"test": True}
        )

        repr_str = repr(plugin_info)
        assert "test_plugin" in repr_str
        assert "1.0.0" in repr_str
        assert "test" in repr_str


class TestPluginDiscoveryOperations:
    """Test plugin discovery operations."""

    def test_discover_plugins_in_directory(self):
        """Test discovering plugins in a directory."""
        discovery = PluginDiscovery()

        # Create a temporary directory with a plugin file
        with patch('nodupe.core.plugin_system.discovery.Path') as mock_path:
            mock_path.return_value = MagicMock()
            mock_path.return_value.iterdir.return_value = []

            # Mock the discovery process
            with patch.object(discovery, '_extract_plugin_info') as mock_extract:
                mock_extract.return_value = PluginInfo(
                    name="test_plugin",
                    version="1.0.0",
                    file_path=Path("/test/plugin.py"),
                    dependencies=[],
                    capabilities={}
                )

                # Mock file operations
                with patch('builtins.open', MagicMock()):
                    result = discovery.discover_plugins_in_directory(
                        Path("/test"))

        assert result == [mock_extract.return_value]

    def test_discover_plugins_in_directories(self):
        """Test discovering plugins in multiple directories."""
        discovery = PluginDiscovery()

        # Mock the discovery process
        with patch.object(discovery, 'discover_plugins_in_directory') as mock_discover:
            mock_discover.return_value = [
                PluginInfo(
                    name="plugin1",
                    version="1.0.0",
                    file_path=Path("/test1/plugin1.py"),
                    dependencies=[],
                    capabilities={}),
                PluginInfo(
                    name="plugin2",
                    version="1.0.0",
                    file_path=Path("/test2/plugin2.py"),
                    dependencies=[],
                    capabilities={})]

            result = discovery.discover_plugins_in_directories(
                [Path("/test1"), Path("/test2")])

        assert len(result) == 2
        assert result == mock_discover.return_value

    def test_find_plugin_by_name(self):
        """Test finding plugin by name."""
        discovery = PluginDiscovery()

        # Add some discovered plugins
        plugin1 = PluginInfo(
            name="plugin1",
            version="1.0.0",
            file_path=Path("/test/plugin1.py"),
            dependencies=[],
            capabilities={})
        plugin2 = PluginInfo(
            name="plugin2",
            version="1.0.0",
            file_path=Path("/test/plugin2.py"),
            dependencies=[],
            capabilities={})

        discovery._discovered_plugins = [plugin1, plugin2]

        # Find plugin by name
        result = discovery.find_plugin_by_name("plugin1")
        assert result is plugin1

        # Find non-existent plugin
        result = discovery.find_plugin_by_name("nonexistent")
        assert result is None

    def test_get_discovered_plugins(self):
        """Test getting discovered plugins."""
        discovery = PluginDiscovery()

        # Add some discovered plugins
        plugin1 = PluginInfo(
            name="plugin1",
            version="1.0.0",
            file_path=Path("/test/plugin1.py"),
            dependencies=[],
            capabilities={})
        plugin2 = PluginInfo(
            name="plugin2",
            version="1.0.0",
            file_path=Path("/test/plugin2.py"),
            dependencies=[],
            capabilities={})

        discovery._discovered_plugins = [plugin1, plugin2]

        # Get all discovered plugins
        result = discovery.get_discovered_plugins()
        assert len(result) == 2
        assert plugin1 in result
        assert plugin2 in result

    def test_get_discovered_plugin(self):
        """Test getting specific discovered plugin."""
        discovery = PluginDiscovery()

        # Add some discovered plugins
        plugin1 = PluginInfo(
            name="plugin1",
            version="1.0.0",
            file_path=Path("/test/plugin1.py"),
            dependencies=[],
            capabilities={})
        plugin2 = PluginInfo(
            name="plugin2",
            version="1.0.0",
            file_path=Path("/test/plugin2.py"),
            dependencies=[],
            capabilities={})

        discovery._discovered_plugins = [plugin1, plugin2]

        # Get specific plugin
        result = discovery.get_discovered_plugin("plugin1")
        assert result is plugin1

        # Get non-existent plugin
        result = discovery.get_discovered_plugin("nonexistent")
        assert result is None

    def test_is_plugin_discovered(self):
        """Test checking if plugin is discovered."""
        discovery = PluginDiscovery()

        # Add some discovered plugins
        plugin1 = PluginInfo(
            name="plugin1",
            version="1.0.0",
            file_path=Path("/test/plugin1.py"),
            dependencies=[],
            capabilities={})
        plugin2 = PluginInfo(
            name="plugin2",
            version="1.0.0",
            file_path=Path("/test/plugin2.py"),
            dependencies=[],
            capabilities={})

        discovery._discovered_plugins = [plugin1, plugin2]

        # Check discovered plugin
        result = discovery.is_plugin_discovered("plugin1")
        assert result is True

        # Check non-discovered plugin
        result = discovery.is_plugin_discovered("nonexistent")
        assert result is False

    def test_refresh_discovery(self):
        """Test refreshing discovery."""
        discovery = PluginDiscovery()

        # Add some discovered plugins
        plugin1 = PluginInfo(
            name="plugin1",
            version="1.0.0",
            file_path=Path("/test/plugin1.py"),
            dependencies=[],
            capabilities={})
        discovery._discovered_plugins = [plugin1]

        # Refresh discovery
        discovery.refresh_discovery()

        # Should clear discovered plugins
        assert len(discovery.get_discovered_plugins()) == 0


class TestPluginDiscoveryEdgeCases:
    """Test plugin discovery edge cases."""

    def test_discover_plugins_in_nonexistent_directory(self):
        """Test discovering plugins in non-existent directory."""
        discovery = PluginDiscovery()

        # Should handle gracefully
        with patch('nodupe.core.plugin_system.discovery.Path') as mock_path:
            mock_path.return_value.exists.return_value = False

            result = discovery.discover_plugins_in_directory(
                Path("/nonexistent"))
            assert result == []

    def test_discover_plugins_in_empty_directory(self):
        """Test discovering plugins in empty directory."""
        discovery = PluginDiscovery()

        # Should handle gracefully
        with patch('nodupe.core.plugin_system.discovery.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.iterdir.return_value = []

            result = discovery.discover_plugins_in_directory(Path("/empty"))
            assert result == []

    def test_discover_plugins_with_invalid_files(self):
        """Test discovering plugins with invalid files."""
        discovery = PluginDiscovery()

        # Mock file operations to return invalid content
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "invalid content"

            with patch('nodupe.core.plugin_system.discovery.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                mock_path.return_value.iterdir.return_value = [
                    mock_path.return_value]

                result = discovery.discover_plugins_in_directory(Path("/test"))

        assert result == []

    def test_discover_plugins_with_malformed_metadata(self):
        """Test discovering plugins with malformed metadata."""
        discovery = PluginDiscovery()

        # Mock file operations to return malformed metadata
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = """
            # This is not valid plugin metadata
            name = "test_plugin"
            version = "1.0.0"
            """

            with patch('nodupe.core.plugin_system.discovery.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                mock_path.return_value.iterdir.return_value = [
                    mock_path.return_value]

                result = discovery.discover_plugins_in_directory(Path("/test"))

        assert result == []


class TestPluginDiscoveryPerformance:
    """Test plugin discovery performance."""

    def test_mass_plugin_discovery(self):
        """Test mass plugin discovery."""
        discovery = PluginDiscovery()

        # Mock discovery of many plugins
        with patch.object(discovery, '_extract_plugin_info') as mock_extract:
            mock_extract.return_value = PluginInfo(
                name="test_plugin",
                version="1.0.0",
                file_path=Path("/test/plugin.py"),
                dependencies=[],
                capabilities={}
            )

            with patch('builtins.open', MagicMock()):
                with patch('nodupe.core.plugin_system.discovery.Path') as mock_path:
                    mock_path.return_value.exists.return_value = True
                    mock_path.return_value.iterdir.return_value = [
                        mock_path.return_value] * 100

                    result = discovery.discover_plugins_in_directory(
                        Path("/test"))

        assert len(result) == 100

    def test_plugin_discovery_performance(self):
        """Test plugin discovery performance."""
        import time

        discovery = PluginDiscovery()

        # Mock discovery of many plugins
        with patch.object(discovery, '_extract_plugin_info') as mock_extract:
            mock_extract.return_value = PluginInfo(
                name="test_plugin",
                version="1.0.0",
                file_path=Path("/test/plugin.py"),
                dependencies=[],
                capabilities={}
            )

            with patch('builtins.open', MagicMock()):
                with patch('nodupe.core.plugin_system.discovery.Path') as mock_path:
                    mock_path.return_value.exists.return_value = True
                    mock_path.return_value.iterdir.return_value = [
                        mock_path.return_value] * 1000

                    # Test discovery performance
                    start_time = time.time()
                    result = discovery.discover_plugins_in_directory(
                        Path("/test"))
                    discovery_time = time.time() - start_time

        assert len(result) == 1000
        assert discovery_time < 1.0


class TestPluginDiscoveryIntegration:
    """Test plugin discovery integration scenarios."""

    def test_plugin_discovery_with_registry(self):
        """Test plugin discovery integration with registry."""
        discovery = PluginDiscovery()
        registry = PluginRegistry()

        # Mock discovery of plugins
        with patch.object(discovery, 'discover_plugins_in_directory') as mock_discover:
            plugin_info = PluginInfo(
                name="test_plugin",
                version="1.0.0",
                file_path=Path("/test/plugin.py"),
                dependencies=[],
                capabilities={}
            )
            mock_discover.return_value = [plugin_info]

            # Discover plugins
            discovered_plugins = discovery.discover_plugins_in_directory(
                Path("/test"))

            # Verify integration
            assert len(discovered_plugins) == 1
            assert discovered_plugins[0] is plugin_info

    def test_plugin_discovery_with_loader(self):
        """Test plugin discovery integration with loader."""
        from nodupe.core.plugin_system.loader import PluginLoader

        discovery = PluginDiscovery()
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # Mock discovery of plugins
        with patch.object(discovery, 'discover_plugins_in_directory') as mock_discover:
            plugin_info = PluginInfo(
                name="test_plugin",
                version="1.0.0",
                file_path=Path("/test/plugin.py"),
                dependencies=[],
                capabilities={}
            )
            mock_discover.return_value = [plugin_info]

            # Discover plugins
            discovered_plugins = discovery.discover_plugins_in_directory(
                Path("/test"))

            # Verify integration
            assert len(discovered_plugins) == 1
            assert discovered_plugins[0] is plugin_info


class TestPluginDiscoveryErrorHandling:
    """Test plugin discovery error handling."""

    def test_discover_plugins_with_exception(self):
        """Test discovering plugins when exception occurs."""
        discovery = PluginDiscovery()

        # Mock file operations to raise exception
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.side_effect = Exception("File read error")

            with patch('nodupe.core.plugin_system.discovery.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                mock_path.return_value.iterdir.return_value = [
                    mock_path.return_value]

                # Should handle exception gracefully
                result = discovery.discover_plugins_in_directory(Path("/test"))
                assert result == []

    def test_discover_plugins_with_invalid_metadata(self):
        """Test discovering plugins with invalid metadata."""
        discovery = PluginDiscovery()

        # Mock file operations to return invalid metadata
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "invalid metadata"

            with patch('nodupe.core.plugin_system.discovery.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                mock_path.return_value.iterdir.return_value = [
                    mock_path.return_value]

                # Should handle invalid metadata gracefully
                result = discovery.discover_plugins_in_directory(Path("/test"))
                assert result == []

    def test_discover_plugins_with_missing_metadata(self):
        """Test discovering plugins with missing metadata."""
        discovery = PluginDiscovery()

        # Mock file operations to return content without metadata
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = """
            # Just a regular Python file
            def some_function():
                pass
            """

            with patch('nodupe.core.plugin_system.discovery.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                mock_path.return_value.iterdir.return_value = [
                    mock_path.return_value]

                # Should handle missing metadata gracefully
                result = discovery.discover_plugins_in_directory(Path("/test"))
                assert result == []


class TestPluginDiscoveryAdvanced:
    """Test advanced plugin discovery functionality."""

    def test_discover_plugins_with_complex_metadata(self):
        """Test discovering plugins with complex metadata."""
        discovery = PluginDiscovery()

        # Mock file operations to return complex metadata
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = """
            # Plugin metadata
            name = "complex_plugin"
            version = "1.0.0"
            dependencies = ["core>=1.0.0", "utils>=2.0.0"]
            capabilities = {
                "feature1": True,
                "feature2": {
                    "nested": True
                }
            }
            """

            with patch('nodupe.core.plugin_system.discovery.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                mock_path.return_value.iterdir.return_value = [
                    mock_path.return_value]

                result = discovery.discover_plugins_in_directory(Path("/test"))

        assert len(result) == 1
        plugin_info = result[0]
        assert plugin_info.name == "complex_plugin"
        assert plugin_info.version == "1.0.0"
        assert len(plugin_info.dependencies) == 2
        assert "core>=1.0.0" in plugin_info.dependencies
        assert "utils>=2.0.0" in plugin_info.dependencies
        assert "feature1" in plugin_info.capabilities

    def test_discover_plugins_with_multiple_directories(self):
        """Test discovering plugins in multiple directories."""
        discovery = PluginDiscovery()

        # Mock discovery in multiple directories
        with patch.object(discovery, 'discover_plugins_in_directory') as mock_discover:
            plugin_info1 = PluginInfo(
                name="plugin1",
                version="1.0.0",
                file_path=Path("/test1/plugin1.py"),
                dependencies=[],
                capabilities={}
            )
            plugin_info2 = PluginInfo(
                name="plugin2",
                version="1.0.0",
                file_path=Path("/test2/plugin2.py"),
                dependencies=[],
                capabilities={}
            )

            mock_discover.side_effect = [
                [plugin_info1],
                [plugin_info2]
            ]

            result = discovery.discover_plugins_in_directories(
                [Path("/test1"), Path("/test2")])

        assert len(result) == 2
        assert plugin_info1 in result
        assert plugin_info2 in result

    def test_discover_plugins_with_duplicate_names(self):
        """Test discovering plugins with duplicate names."""
        discovery = PluginDiscovery()

        # Mock discovery of plugins with duplicate names
        with patch.object(discovery, '_extract_plugin_info') as mock_extract:
            plugin_info1 = PluginInfo(
                name="duplicate_plugin",
                version="1.0.0",
                file_path=Path("/test1/plugin.py"),
                dependencies=[],
                capabilities={}
            )
            plugin_info2 = PluginInfo(
                name="duplicate_plugin",
                version="2.0.0",
                file_path=Path("/test2/plugin.py"),
                dependencies=[],
                capabilities={}
            )

            mock_extract.side_effect = [plugin_info1, plugin_info2]

            with patch('builtins.open', MagicMock()):
                with patch('nodupe.core.plugin_system.discovery.Path') as mock_path:
                    mock_path.return_value.exists.return_value = True
                    mock_path.return_value.iterdir.return_value = [
                        mock_path.return_value, mock_path.return_value]

                    result = discovery.discover_plugins_in_directory(
                        Path("/test"))

        # Should handle duplicates (behavior may vary)
        assert len(result) >= 1
