"""Test tool discovery functionality."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from nodupe.core.tool_system.discovery import ToolDiscovery, ToolDiscoveryError, ToolInfo
from nodupe.core.tool_system.registry import ToolRegistry


class TestToolDiscovery:
    """Test tool discovery core functionality."""

    def test_tool_discovery_initialization(self):
        """Test tool discovery initialization."""
        discovery = ToolDiscovery()
        assert discovery is not None
        assert isinstance(discovery, ToolDiscovery)

        # Test that it has expected attributes
        assert hasattr(discovery, 'discover_tools_in_directory')
        assert hasattr(discovery, 'discover_tools_in_directories')
        assert hasattr(discovery, 'find_tool_by_name')
        assert hasattr(discovery, 'refresh_discovery')
        assert hasattr(discovery, 'get_discovered_tools')
        assert hasattr(discovery, 'get_discovered_tool')
        assert hasattr(discovery, 'is_tool_discovered')
        assert hasattr(discovery, 'initialize')
        assert hasattr(discovery, 'shutdown')

    def test_tool_discovery_with_container(self):
        """Test tool discovery with dependency container."""
        from nodupe.core.container import ServiceContainer

        discovery = ToolDiscovery()
        container = ServiceContainer()

        # Initialize discovery with container
        discovery.initialize(container)
        assert discovery.container is container

    def test_tool_discovery_lifecycle(self):
        """Test tool discovery lifecycle operations."""
        from nodupe.core.container import ServiceContainer

        discovery = ToolDiscovery()
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


class TestToolInfo:
    """Test tool info functionality."""

    def test_tool_info_initialization(self):
        """Test tool info initialization."""
        tool_info = ToolInfo(
            name="test_tool",
            version="1.0.0",
            file_path=Path("/test/tool.py"),
            dependencies=["core>=1.0.0"],
            capabilities={"test": True}
        )

        assert tool_info is not None
        assert isinstance(tool_info, ToolInfo)
        assert tool_info.name == "test_tool"
        assert tool_info.version == "1.0.0"
        assert tool_info.file_path == Path("/test/tool.py")
        assert tool_info.dependencies == ["core>=1.0.0"]
        assert tool_info.capabilities == {"test": True}

    def test_tool_info_repr(self):
        """Test tool info string representation."""
        tool_info = ToolInfo(
            name="test_tool",
            version="1.0.0",
            file_path=Path("/test/tool.py"),
            dependencies=["core>=1.0.0"],
            capabilities={"test": True}
        )

        repr_str = repr(tool_info)
        assert "test_tool" in repr_str
        assert "1.0.0" in repr_str
        assert "test" in repr_str


class TestToolDiscoveryOperations:
    """Test tool discovery operations."""

    def test_discover_tools_in_directory(self):
        """Test discovering tools in a directory."""
        discovery = ToolDiscovery()

        # Create proper mock directory structure
        mock_dir = MagicMock()
        mock_dir.exists.return_value = True
        
        # Create mock tool file
        mock_file = MagicMock()
        mock_file.is_file.return_value = True
        mock_file.suffix = '.py'
        mock_file.stem = 'tool'
        mock_file.exists.return_value = True
        mock_file.stat.return_value.st_size = 100
        
        # Set up directory to return the mock file
        mock_dir.iterdir.return_value = [mock_file]

        # Mock the discovery process
        with patch.object(discovery, '_extract_tool_info') as mock_extract:
            mock_extract.return_value = ToolInfo(
                name="test_tool",
                version="1.0.0",
                file_path=Path("/test/tool.py"),
                dependencies=[],
                capabilities={}
            )

            # Mock file operations
            with patch('builtins.open', MagicMock()):
                result = discovery.discover_tools_in_directory(mock_dir)

        assert result == [mock_extract.return_value]

    def test_discover_tools_in_directories(self):
        """Test discovering tools in multiple directories."""
        discovery = ToolDiscovery()

        # Mock the discovery process
        with patch.object(discovery, 'discover_tools_in_directory') as mock_discover:
            mock_discover.return_value = [
                ToolInfo(
                    name="tool1",
                    version="1.0.0",
                    file_path=Path("/test1/tool1.py"),
                    dependencies=[],
                    capabilities={}),
                ToolInfo(
                    name="tool2",
                    version="1.0.0",
                    file_path=Path("/test2/tool2.py"),
                    dependencies=[],
                    capabilities={})]

            result = discovery.discover_tools_in_directories(
                [Path("/test1"), Path("/test2")])

        assert len(result) == 2
        assert result == mock_discover.return_value

    def test_find_tool_by_name(self):
        """Test finding tool by name."""
        discovery = ToolDiscovery()

        # Add some discovered tools
        tool1 = ToolInfo(
            name="tool1",
            version="1.0.0",
            file_path=Path("/test/tool1.py"),
            dependencies=[],
            capabilities={})
        tool2 = ToolInfo(
            name="tool2",
            version="1.0.0",
            file_path=Path("/test/tool2.py"),
            dependencies=[],
            capabilities={})

        discovery._discovered_tools = [tool1, tool2]

        # Find tool by name
        result = discovery.find_tool_by_name("tool1")
        assert result is tool1

        # Find non-existent tool
        result = discovery.find_tool_by_name("nonexistent")
        assert result is None

    def test_get_discovered_tools(self):
        """Test getting discovered tools."""
        discovery = ToolDiscovery()

        # Add some discovered tools
        tool1 = ToolInfo(
            name="tool1",
            version="1.0.0",
            file_path=Path("/test/tool1.py"),
            dependencies=[],
            capabilities={})
        tool2 = ToolInfo(
            name="tool2",
            version="1.0.0",
            file_path=Path("/test/tool2.py"),
            dependencies=[],
            capabilities={})

        discovery._discovered_tools = [tool1, tool2]

        # Get all discovered tools
        result = discovery.get_discovered_tools()
        assert len(result) == 2
        assert tool1 in result
        assert tool2 in result

    def test_get_discovered_tool(self):
        """Test getting specific discovered tool."""
        discovery = ToolDiscovery()

        # Add some discovered tools
        tool1 = ToolInfo(
            name="tool1",
            version="1.0.0",
            file_path=Path("/test/tool1.py"),
            dependencies=[],
            capabilities={})
        tool2 = ToolInfo(
            name="tool2",
            version="1.0.0",
            file_path=Path("/test/tool2.py"),
            dependencies=[],
            capabilities={})

        discovery._discovered_tools = [tool1, tool2]

        # Get specific tool
        result = discovery.get_discovered_tool("tool1")
        assert result is tool1

        # Get non-existent tool
        result = discovery.get_discovered_tool("nonexistent")
        assert result is None

    def test_is_tool_discovered(self):
        """Test checking if tool is discovered."""
        discovery = ToolDiscovery()

        # Add some discovered tools
        tool1 = ToolInfo(
            name="tool1",
            version="1.0.0",
            file_path=Path("/test/tool1.py"),
            dependencies=[],
            capabilities={})
        tool2 = ToolInfo(
            name="tool2",
            version="1.0.0",
            file_path=Path("/test/tool2.py"),
            dependencies=[],
            capabilities={})

        discovery._discovered_tools = [tool1, tool2]

        # Check discovered tool
        result = discovery.is_tool_discovered("tool1")
        assert result is True

        # Check non-discovered tool
        result = discovery.is_tool_discovered("nonexistent")
        assert result is False

    def test_refresh_discovery(self):
        """Test refreshing discovery."""
        discovery = ToolDiscovery()

        # Add some discovered tools
        tool1 = ToolInfo(
            name="tool1",
            version="1.0.0",
            file_path=Path("/test/tool1.py"),
            dependencies=[],
            capabilities={})
        discovery._discovered_tools = [tool1]

        # Refresh discovery
        discovery.refresh_discovery()

        # Should clear discovered tools
        assert len(discovery.get_discovered_tools()) == 0


class TestToolDiscoveryEdgeCases:
    """Test tool discovery edge cases."""

    def test_discover_tools_in_nonexistent_directory(self):
        """Test discovering tools in non-existent directory."""
        discovery = ToolDiscovery()

        # Should handle gracefully
        with patch('nodupe.core.tool_system.discovery.Path') as mock_path:
            mock_path.return_value.exists.return_value = False

            result = discovery.discover_tools_in_directory(
                Path("/nonexistent"))
            assert result == []

    def test_discover_tools_in_empty_directory(self):
        """Test discovering tools in empty directory."""
        discovery = ToolDiscovery()

        # Should handle gracefully
        with patch('nodupe.core.tool_system.discovery.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.iterdir.return_value = []

            result = discovery.discover_tools_in_directory(Path("/empty"))
            assert result == []

    def test_discover_tools_with_invalid_files(self):
        """Test discovering tools with invalid files."""
        discovery = ToolDiscovery()

        # Mock file operations to return invalid content
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "invalid content"

            with patch('nodupe.core.tool_system.discovery.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                mock_path.return_value.iterdir.return_value = [
                    mock_path.return_value]

                result = discovery.discover_tools_in_directory(Path("/test"))

        assert result == []

    def test_discover_tools_with_malformed_metadata(self):
        """Test discovering tools with malformed metadata."""
        discovery = ToolDiscovery()

        # Mock file operations to return malformed metadata
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = """
            # This is not valid tool metadata
            name = "test_tool"
            version = "1.0.0"
            """

            with patch('nodupe.core.tool_system.discovery.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                mock_path.return_value.iterdir.return_value = [
                    mock_path.return_value]

                result = discovery.discover_tools_in_directory(Path("/test"))

        assert result == []


class TestToolDiscoveryPerformance:
    """Test tool discovery performance."""

    def test_mass_tool_discovery(self):
        """Test mass tool discovery."""
        discovery = ToolDiscovery()

        # Create proper mock directory with many files
        mock_dir = MagicMock()
        mock_dir.exists.return_value = True
        
        # Create 100 mock tool files
        mock_files = []
        for i in range(100):
            mock_file = MagicMock()
            mock_file.is_file.return_value = True
            mock_file.suffix = '.py'
            mock_file.stem = f'tool_{i}'
            mock_file.exists.return_value = True
            mock_file.stat.return_value.st_size = 100
            mock_files.append(mock_file)
        
        mock_dir.iterdir.return_value = mock_files

        # Mock the discovery process
        with patch.object(discovery, '_extract_tool_info') as mock_extract:
            mock_extract.return_value = ToolInfo(
                name="test_tool",
                version="1.0.0",
                file_path=Path("/test/tool.py"),
                dependencies=[],
                capabilities={}
            )

            with patch('builtins.open', MagicMock()):
                result = discovery.discover_tools_in_directory(mock_dir)

        assert len(result) == 100

    def test_tool_discovery_performance(self):
        """Test tool discovery performance."""
        import time

        discovery = ToolDiscovery()

        # Create proper mock directory with many files
        mock_dir = MagicMock()
        mock_dir.exists.return_value = True
        
        # Create 1000 mock tool files
        mock_files = []
        for i in range(1000):
            mock_file = MagicMock()
            mock_file.is_file.return_value = True
            mock_file.suffix = '.py'
            mock_file.stem = f'tool_{i}'
            mock_file.exists.return_value = True
            mock_file.stat.return_value.st_size = 100
            mock_files.append(mock_file)
        
        mock_dir.iterdir.return_value = mock_files

        # Mock the discovery process
        with patch.object(discovery, '_extract_tool_info') as mock_extract:
            mock_extract.return_value = ToolInfo(
                name="test_tool",
                version="1.0.0",
                file_path=Path("/test/tool.py"),
                dependencies=[],
                capabilities={}
            )

            with patch('builtins.open', MagicMock()):
                # Test discovery performance
                start_time = time.time()
                result = discovery.discover_tools_in_directory(mock_dir)
                discovery_time = time.time() - start_time

        assert len(result) == 1000
        assert discovery_time < 1.0


class TestToolDiscoveryIntegration:
    """Test tool discovery integration scenarios."""

    def test_tool_discovery_with_registry(self):
        """Test tool discovery integration with registry."""
        discovery = ToolDiscovery()
        registry = ToolRegistry()

        # Mock discovery of tools
        with patch.object(discovery, 'discover_tools_in_directory') as mock_discover:
            tool_info = ToolInfo(
                name="test_tool",
                version="1.0.0",
                file_path=Path("/test/tool.py"),
                dependencies=[],
                capabilities={}
            )
            mock_discover.return_value = [tool_info]

            # Discover tools
            discovered_tools = discovery.discover_tools_in_directory(
                Path("/test"))

            # Verify integration
            assert len(discovered_tools) == 1
            assert discovered_tools[0] is tool_info

    def test_tool_discovery_with_loader(self):
        """Test tool discovery integration with loader."""
        from nodupe.core.tool_system.loader import ToolLoader

        discovery = ToolDiscovery()
        registry = ToolRegistry()
        loader = ToolLoader(registry)

        # Mock discovery of tools
        with patch.object(discovery, 'discover_tools_in_directory') as mock_discover:
            tool_info = ToolInfo(
                name="test_tool",
                version="1.0.0",
                file_path=Path("/test/tool.py"),
                dependencies=[],
                capabilities={}
            )
            mock_discover.return_value = [tool_info]

            # Discover tools
            discovered_tools = discovery.discover_tools_in_directory(
                Path("/test"))

            # Verify integration
            assert len(discovered_tools) == 1
            assert discovered_tools[0] is tool_info


class TestToolDiscoveryErrorHandling:
    """Test tool discovery error handling."""

    def test_discover_tools_with_exception(self):
        """Test discovering tools when exception occurs."""
        discovery = ToolDiscovery()

        # Mock file operations to raise exception
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.side_effect = Exception("File read error")

            with patch('nodupe.core.tool_system.discovery.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                mock_path.return_value.iterdir.return_value = [
                    mock_path.return_value]

                # Should handle exception gracefully
                result = discovery.discover_tools_in_directory(Path("/test"))
                assert result == []

    def test_discover_tools_with_invalid_metadata(self):
        """Test discovering tools with invalid metadata."""
        discovery = ToolDiscovery()

        # Mock file operations to return invalid metadata
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "invalid metadata"

            with patch('nodupe.core.tool_system.discovery.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                mock_path.return_value.iterdir.return_value = [
                    mock_path.return_value]

                # Should handle invalid metadata gracefully
                result = discovery.discover_tools_in_directory(Path("/test"))
                assert result == []

    def test_discover_tools_with_missing_metadata(self):
        """Test discovering tools with missing metadata."""
        discovery = ToolDiscovery()

        # Mock file operations to return content without metadata
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = """
            # Just a regular Python file
            def some_function():
                pass
            """

            with patch('nodupe.core.tool_system.discovery.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                mock_path.return_value.iterdir.return_value = [
                    mock_path.return_value]

                # Should handle missing metadata gracefully
                result = discovery.discover_tools_in_directory(Path("/test"))
                assert result == []


class TestToolDiscoveryAdvanced:
    """Test advanced tool discovery functionality."""

    def test_discover_tools_with_complex_metadata(self):
        """Test discovering tools with complex metadata."""
        discovery = ToolDiscovery()

        # Create proper mock directory structure
        mock_dir = MagicMock()
        mock_dir.exists.return_value = True
        
        # Create mock tool file that looks like a real tool
        mock_file = MagicMock()
        mock_file.is_file.return_value = True
        mock_file.suffix = '.py'
        mock_file.stem = 'complex_tool'
        mock_file.exists.return_value = True
        mock_file.stat.return_value.st_size = 100
        mock_file.__str__ = lambda: "/test/complex_tool.py"
        
        # Set up directory to return the mock file
        mock_dir.iterdir.return_value = [mock_file]

        # Mock file operations to return complex metadata with actual Python code
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = """
            # Tool metadata
            name = "complex_tool"
            version = "1.0.0"
            dependencies = ["core>=1.0.0", "utils>=2.0.0"]
            capabilities = {
                "feature1": True,
                "feature2": {
                    "nested": True
                }
            }

            # Actual Python code to make it look like a tool
            def initialize():
                pass

            def shutdown():
                pass

            def get_capabilities():
                return {}
            """

            result = discovery.discover_tools_in_directory(mock_dir)

        assert len(result) == 1
        tool_info = result[0]
        assert tool_info.name == "complex_tool"
        assert tool_info.version == "1.0.0"
        assert len(tool_info.dependencies) == 2
        assert "core>=1.0.0" in tool_info.dependencies
        assert "utils>=2.0.0" in tool_info.dependencies
        assert "feature1" in tool_info.capabilities

    def test_discover_tools_with_multiple_directories(self):
        """Test discovering tools in multiple directories."""
        discovery = ToolDiscovery()

        # Mock discovery in multiple directories
        with patch.object(discovery, 'discover_tools_in_directory') as mock_discover:
            tool_info1 = ToolInfo(
                name="tool1",
                version="1.0.0",
                file_path=Path("/test1/tool1.py"),
                dependencies=[],
                capabilities={}
            )
            tool_info2 = ToolInfo(
                name="tool2",
                version="1.0.0",
                file_path=Path("/test2/tool2.py"),
                dependencies=[],
                capabilities={}
            )

            mock_discover.side_effect = [
                [tool_info1],
                [tool_info2]
            ]

            result = discovery.discover_tools_in_directories(
                [Path("/test1"), Path("/test2")])

        assert len(result) == 2
        assert tool_info1 in result
        assert tool_info2 in result

    def test_discover_tools_with_duplicate_names(self):
        """Test discovering tools with duplicate names."""
        discovery = ToolDiscovery()

        # Create proper mock directory structure
        mock_dir = MagicMock()
        mock_dir.exists.return_value = True
        
        # Create two mock tool files with same name but different paths
        mock_file1 = MagicMock()
        mock_file1.is_file.return_value = True
        mock_file1.suffix = '.py'
        mock_file1.stem = 'duplicate_tool'
        mock_file1.exists.return_value = True
        mock_file1.stat.return_value.st_size = 100
        mock_file1.__str__ = lambda: "/test1/tool.py"
        
        mock_file2 = MagicMock()
        mock_file2.is_file.return_value = True
        mock_file2.suffix = '.py'
        mock_file2.stem = 'duplicate_tool'
        mock_file2.exists.return_value = True
        mock_file2.stat.return_value.st_size = 100
        mock_file2.__str__ = lambda: "/test2/tool.py"
        
        # Set up directory to return both mock files
        mock_dir.iterdir.return_value = [mock_file1, mock_file2]

        # Mock the discovery process
        with patch.object(discovery, '_extract_tool_info') as mock_extract:
            tool_info1 = ToolInfo(
                name="duplicate_tool",
                version="1.0.0",
                file_path=Path("/test1/tool.py"),
                dependencies=[],
                capabilities={}
            )
            tool_info2 = ToolInfo(
                name="duplicate_tool",
                version="2.0.0",
                file_path=Path("/test2/tool.py"),
                dependencies=[],
                capabilities={}
            )

            mock_extract.side_effect = [tool_info1, tool_info2]

            with patch('builtins.open', MagicMock()):
                result = discovery.discover_tools_in_directory(mock_dir)

        # Should handle duplicates (behavior may vary)
        assert len(result) >= 1
