"""Test tool discovery functionality."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, mock_open

import pytest

from nodupe.core.tool_system.discovery import (
    ToolDiscovery,
    ToolDiscoveryError,
    ToolInfo,
)


class TestToolInfo:
    """Test ToolInfo functionality."""

    def test_tool_info_creation(self):
        """Test ToolInfo instance creation."""
        tool_info = ToolInfo(
            name="TestTool",
            file_path=Path("/path/to/tool.py"),
            version="1.0.0",
            dependencies=["dep1", "dep2"],
            capabilities={"feature1": "value1"},
        )

        assert tool_info.name == "TestTool"
        assert tool_info.path == Path("/path/to/tool.py")
        assert tool_info.version == "1.0.0"
        assert tool_info.dependencies == ["dep1", "dep2"]
        assert tool_info.capabilities == {"feature1": "value1"}

    def test_tool_info_default_values(self):
        """Test ToolInfo with default values."""
        tool_info = ToolInfo(
            name="TestTool", file_path=Path("/path/to/tool.py")
        )

        assert tool_info.name == "TestTool"
        assert tool_info.path == Path("/path/to/tool.py")
        assert tool_info.version == "1.0.0"  # Default
        assert tool_info.dependencies == []  # Default
        assert tool_info.capabilities == {}  # Default

    def test_tool_info_repr(self):
        """Test ToolInfo string representation."""
        tool_info = ToolInfo(
            name="TestTool", file_path=Path("/path/to/tool.py")
        )

        repr_str = repr(tool_info)
        assert "ToolInfo" in repr_str
        assert "name='TestTool'" in repr_str
        assert "version='1.0.0'" in repr_str
        assert "/path/to/tool.py" in repr_str


class TestToolDiscoveryInitialization:
    """Test ToolDiscovery initialization functionality."""

    def test_tool_discovery_creation(self):
        """Test ToolDiscovery instance creation."""
        discovery = ToolDiscovery()

        assert discovery is not None
        assert discovery._discovered_tools == []
        assert discovery.container is None

    def test_tool_discovery_initialize(self):
        """Test ToolDiscovery initialization with container."""
        discovery = ToolDiscovery()
        container = Mock()

        discovery.initialize(container)

        assert discovery.container is container

    def test_tool_discovery_shutdown(self):
        """Test ToolDiscovery shutdown."""
        discovery = ToolDiscovery()
        container = Mock()
        discovery.initialize(container)

        discovery.shutdown()

        assert discovery.container is None


class TestToolDiscoveryFileValidation:
    """Test tool discovery file validation functionality."""

    def test_validate_tool_file_valid(self):
        """Test validating a valid tool file."""
        discovery = ToolDiscovery()

        # Create a temporary file with valid Python content
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
            patch(
                "builtins.open",
                mock_open(read_data="class TestTool:\n    pass"),
            ),
        ):

            mock_stat.return_value.st_size = 100  # Non-zero size

            result = discovery.validate_tool_file(Path("/fake/tool.py"))
            assert result is True

    def test_validate_tool_file_wrong_extension(self):
        """Test validating a file with wrong extension."""
        discovery = ToolDiscovery()

        result = discovery.validate_tool_file(Path("/fake/tool.txt"))
        assert result is False

    def test_validate_tool_file_nonexistent(self):
        """Test validating a nonexistent file."""
        discovery = ToolDiscovery()

        with patch("pathlib.Path.exists", return_value=False):
            result = discovery.validate_tool_file(Path("/fake/tool.py"))
            assert result is False

    def test_validate_tool_file_not_file(self):
        """Test validating a path that is not a file."""
        discovery = ToolDiscovery()

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=False),
        ):

            result = discovery.validate_tool_file(Path("/fake/tool.py"))
            assert result is False

    def test_validate_tool_file_zero_size(self):
        """Test validating a file with zero size."""
        discovery = ToolDiscovery()

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
        ):

            mock_stat.return_value.st_size = 0  # Zero size

            result = discovery.validate_tool_file(Path("/fake/tool.py"))
            assert result is False

    def test_validate_tool_file_syntax_error(self):
        """Test validating a file with syntax errors."""
        discovery = ToolDiscovery()

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
            patch(
                "builtins.open", mock_open(read_data="invalid python syntax")
            ),
        ):

            mock_stat.return_value.st_size = 100  # Non-zero size

            result = discovery.validate_tool_file(Path("/fake/tool.py"))
            assert result is False


class TestToolDiscoveryContentParsing:
    """Test tool discovery content parsing functionality."""

    def test_parse_metadata_simple(self):
        """Test parsing simple metadata."""
        discovery = ToolDiscovery()

        content = """
__version__ = "2.0.0"
__author__ = "Test Author"
__description__ = "A test tool"
"""

        metadata = discovery._parse_metadata(content)

        assert metadata.get("version") == "2.0.0"
        assert metadata.get("author") == "Test Author"
        assert metadata.get("description") == "A test tool"

    def test_parse_metadata_with_quotes(self):
        """Test parsing metadata with different quote styles."""
        discovery = ToolDiscovery()

        content = """
version = "1.5.0"
author = 'Another Author'
description = "Another description"
"""

        metadata = discovery._parse_metadata(content)

        assert metadata.get("version") == "1.5.0"
        assert metadata.get("author") == "Another Author"
        assert metadata.get("description") == "Another description"

    def test_parse_metadata_dependencies(self):
        """Test parsing dependencies metadata."""
        discovery = ToolDiscovery()

        content = """
dependencies = ["dep1", "dep2", "dep3"]
"""

        metadata = discovery._parse_metadata(content)

        assert metadata.get("dependencies") == ["dep1", "dep2", "dep3"]

    def test_parse_metadata_capabilities(self):
        """Test parsing capabilities metadata."""
        discovery = ToolDiscovery()

        content = """
capabilities = {"feature1": "value1", "feature2": "value2"}
"""

        metadata = discovery._parse_metadata(content)

        assert metadata.get("capabilities") == {
            "feature1": "value1",
            "feature2": "value2",
        }

    def test_parse_metadata_complex(self):
        """Test parsing complex metadata."""
        discovery = ToolDiscovery()

        content = """
name = "ComplexTool"
version = "3.0.0"
dependencies = ["req1", "req2"]
capabilities = {"feature": "value"}
"""

        metadata = discovery._parse_metadata(content)

        assert metadata.get("name") == "ComplexTool"
        assert metadata.get("version") == "3.0.0"
        assert metadata.get("dependencies") == ["req1", "req2"]
        assert metadata.get("capabilities") == {"feature": "value"}


class TestToolDiscoveryContentAnalysis:
    """Test tool discovery content analysis functionality."""

    def test_looks_like_tool_with_imports_classes_functions(self):
        """Test detecting tool-like content with imports, classes, and functions."""
        discovery = ToolDiscovery()

        content = """
import os
import sys

class TestTool:
    def __init__(self):
        pass

    def method(self):
        return True

def helper_function():
    pass
"""

        result = discovery._looks_like_tool(content)
        assert result is True

    def test_looks_like_tool_minimal(self):
        """Test detecting minimal tool-like content."""
        discovery = ToolDiscovery()

        content = """
class MinimalTool:
    pass
"""

        result = discovery._looks_like_tool(content)
        assert result is True

    def test_extract_tool_info_success(self):
        """Test successful tool info extraction."""
        discovery = ToolDiscovery()

        with (
            patch(
                "builtins.open",
                mock_open(
                    read_data="""
name = "ExtractedTool"
version = "1.0.0"
dependencies = ["req1"]
"""
                ),
            ),
            patch("pathlib.Path.exists", return_value=True),
        ):

            tool_path = Path("/fake/tool.py")
            result = discovery._extract_tool_info(tool_path)

            assert result is not None
            assert result.name == "ExtractedTool"
            assert result.version == "1.0.0"
            assert result.dependencies == ["req1"]

    def test_extract_tool_info_not_tool_like(self):
        """Test tool info extraction for non-tool content."""
        discovery = ToolDiscovery()

        with (
            patch(
                "builtins.open",
                mock_open(
                    read_data="""
# This is just a comment file
# No actual tool code here
"""
                ),
            ),
            patch("pathlib.Path.exists", return_value=True),
        ):

            tool_path = Path("/fake/tool.py")
            result = discovery._extract_tool_info(tool_path)

            assert result is None

    def test_extract_tool_info_detects_accessibility_feature(self):
        """_extract_tool_info should detect accessibility-related keywords
        in the file content and include the tool in discovered results."""
        discovery = ToolDiscovery()

        content = 'name = "AccessibleTool"\n# mentions AccessibleTool and screen_reader in docs\n'

        with (
            patch("builtins.open", mock_open(read_data=content)),
            patch("pathlib.Path.exists", return_value=True),
        ):
            tool_path = Path("/fake/accessible_tool.py")
            info = discovery._extract_tool_info(tool_path)

            assert info is not None
            assert info.name == "AccessibleTool"


class TestToolDiscoveryDirectoryScanning:
    """Test tool discovery directory scanning functionality."""

    def test_discover_tools_in_directory_empty(self):
        """Test discovering tools in an empty directory."""
        discovery = ToolDiscovery()

        with (
            patch("pathlib.Path.iterdir", return_value=[]),
            patch("pathlib.Path.is_file", return_value=False),
            patch("pathlib.Path.is_dir", return_value=False),
        ):

            result = discovery.discover_tools_in_directory(Path("/empty/dir"))
            assert result == []

    def test_discover_tools_in_directory_with_files(self):
        """Test discovering tools in a directory with files."""
        discovery = ToolDiscovery()

        # Create mock files
        mock_py_file = Mock()
        mock_py_file.name = "tool1.py"
        mock_py_file.suffix = ".py"
        mock_py_file.is_file.return_value = True
        mock_py_file.is_dir.return_value = False

        mock_init_file = Mock()
        mock_init_file.name = "__init__.py"
        mock_init_file.suffix = ".py"
        mock_init_file.is_file.return_value = True
        mock_init_file.is_dir.return_value = False

        mock_txt_file = Mock()
        mock_txt_file.name = "readme.txt"
        mock_txt_file.suffix = ".txt"
        mock_txt_file.is_file.return_value = True
        mock_txt_file.is_dir.return_value = False

        with (
            patch(
                "pathlib.Path.iterdir",
                return_value=[mock_py_file, mock_init_file, mock_txt_file],
            ),
            patch(
                "builtins.open",
                mock_open(
                    read_data='name = "TestTool"\nclass TestTool:\n    pass'
                ),
            ),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
        ):

            mock_stat.return_value.st_size = 100

            result = discovery.discover_tools_in_directory(Path("/test/dir"))

            # Should find 1 tool (tool1.py), ignoring __init__.py and .txt files
            assert len(result) == 1

    def test_discover_tools_in_directory_real_files(self, tmp_path):
        """Integration-style test: discovery should find real .py files in a dir.

        This exercise uses actual files on disk (not mocks) to cover the file
        I/O branches of discovery._extract_tool_info and _parse_metadata.
        """
        discovery = ToolDiscovery()

        # Create a temporary directory with a simple tool-like Python file
        d = tmp_path / "toolsdir"
        d.mkdir()

        tool_file = d / "real_tool.py"
        tool_file.write_text(
            'name = "RealTool"\nversion = "1.2.3"\n\nimport os\nclass X:\n    pass\n'
        )

        tools = discovery.discover_tools_in_directory(d)
        assert len(tools) == 1
        assert tools[0].name == "RealTool"
        assert tools[0].version == "1.2.3"

    def test_discover_tools_in_directory_recursive(self):
        """Test discovering tools in a directory recursively."""
        discovery = ToolDiscovery()

        # Create mock directory structure
        mock_py_file = Mock()
        mock_py_file.name = "tool1.py"
        mock_py_file.suffix = ".py"
        mock_py_file.is_file.return_value = True
        mock_py_file.is_dir.return_value = False

        mock_subdir = Mock()
        mock_subdir.name = "subdir"
        mock_subdir.is_dir.return_value = True
        mock_subdir.is_file.return_value = False

        # Mock the subdir's contents
        mock_sub_py_file = Mock()
        mock_sub_py_file.name = "tool2.py"
        mock_sub_py_file.suffix = ".py"
        mock_sub_py_file.is_file.return_value = True
        mock_sub_py_file.is_dir.return_value = False

        with patch("pathlib.Path.iterdir") as mock_iterdir:
            # First call (main dir) returns file and subdir
            mock_iterdir.return_value = [mock_py_file, mock_subdir]

            # When iterating subdir, return the sub-py-file
            def side_effect_iterdir(path):
                if str(path) == str(mock_subdir):
                    return [mock_sub_py_file]
                return [mock_py_file, mock_subdir]

            # Patch the subdirectory's iterdir separately
            with patch.object(
                mock_subdir, "iterdir", return_value=[mock_sub_py_file]
            ):
                with (
                    patch(
                        "builtins.open",
                        mock_open(
                            read_data='name = "TestTool"\nclass TestTool:\n    pass'
                        ),
                    ),
                    patch("pathlib.Path.exists", return_value=True),
                    patch("pathlib.Path.stat") as mock_stat,
                ):

                    mock_stat.return_value.st_size = 100

                    result = discovery.discover_tools_in_directory(
                        Path("/test/dir"), recursive=True
                    )

                    # Should find 2 tools (one from main dir, one from subdir)
                    assert len(result) == 2

    def test_discover_tools_in_directory_nonexistent(self):
        """Test discovering tools in a nonexistent directory."""
        discovery = ToolDiscovery()

        with patch("pathlib.Path.iterdir", side_effect=FileNotFoundError()):
            result = discovery.discover_tools_in_directory(
                Path("/nonexistent/dir")
            )
            assert result == []


class TestToolDiscoveryMainMethods:
    """Test main tool discovery methods."""

    def test_discover_tools_multiple_directories(self):
        """Test discovering tools in multiple directories."""
        discovery = ToolDiscovery()

        # Mock the discovery in each directory
        with patch.object(
            discovery, "discover_tools_in_directory"
        ) as mock_discover_dir:
            # Return different tools for each directory
            t1 = Mock(); t1.name = "Tool1"
            t2 = Mock(); t2.name = "Tool2"
            t3 = Mock(); t3.name = "Tool1"
            mock_discover_dir.side_effect = [
                [t1],  # First directory
                [t2],  # Second directory
                [t3],  # Third directory (duplicate name)
            ]

            directories = [Path("/dir1"), Path("/dir2"), Path("/dir3")]
            result = discovery.discover_tools_in_directories(directories)

            # Should return 2 unique tools (Tool1 from first and Tool2 from second)
            # Tool1 from third directory should be skipped due to duplicate name
            assert len(result) == 2

    def test_discover_tools_with_directories_param(self):
        """Test discovering tools with directories parameter."""
        discovery = ToolDiscovery()

        with patch.object(
            discovery, "discover_tools_in_directories"
        ) as mock_discover_dirs:
            mock_discover_dirs.return_value = [Mock(name="TestTool")]

            directories = [Path("/dir1"), Path("/dir2")]
            result = discovery.discover_tools(directories)

            mock_discover_dirs.assert_called_once_with(
                directories, True, "*.py"
            )
            assert len(result) == 1

    def test_discover_tools_without_directories_param(self):
        """Test discovering tools without directories parameter."""
        discovery = ToolDiscovery()

        # Add some tools to the discovered list
        mock_tool = Mock()
        mock_tool.name = "ExistingTool"
        discovery._discovered_tools = [mock_tool]

        result = discovery.discover_tools()

        # Should return the already discovered tools
        assert result == [mock_tool]

    def test_find_tool_by_name_found(self):
        """Test finding a tool by name when it exists."""
        discovery = ToolDiscovery()

        mock_tool = Mock()
        mock_tool.name = "TargetTool"

        discovery._discovered_tools = [mock_tool]

        result = discovery.find_tool_by_name("TargetTool")
        assert result is mock_tool

    def test_find_tool_by_name_not_found(self):
        """Test finding a tool by name when it doesn't exist."""
        discovery = ToolDiscovery()

        mock_tool = Mock()
        mock_tool.name = "OtherTool"

        discovery._discovered_tools = [mock_tool]

        result = discovery.find_tool_by_name("TargetTool")
        assert result is None

    def test_find_tool_by_name_in_directories(self):
        """Test finding a tool by name in specific directories."""
        discovery = ToolDiscovery()

        # Mock the directory discovery
        mock_found_tool = Mock()
        mock_found_tool.name = "TargetTool"

        with patch.object(
            discovery, "discover_tools_in_directory"
        ) as mock_discover:
            mock_discover.return_value = [mock_found_tool]

            result = discovery.find_tool_by_name(
                "TargetTool", [Path("/search/dir")]
            )

            assert result is mock_found_tool

    def test_refresh_discovery(self):
        """Test refreshing the discovery."""
        discovery = ToolDiscovery()

        mock_tool = Mock()
        mock_tool.name = "OldTool"
        discovery._discovered_tools = [mock_tool]

        assert len(discovery._discovered_tools) == 1

        discovery.refresh_discovery()

        assert len(discovery._discovered_tools) == 0

    def test_get_discovered_tools(self):
        """Test getting all discovered tools."""
        discovery = ToolDiscovery()

        mock_tool1 = Mock()
        mock_tool1.name = "Tool1"
        mock_tool2 = Mock()
        mock_tool2.name = "Tool2"

        discovery._discovered_tools = [mock_tool1, mock_tool2]

        result = discovery.get_discovered_tools()

        assert result == [mock_tool1, mock_tool2]
        # Should return a copy, not the original list
        assert result is not discovery._discovered_tools

    def test_get_discovered_tool(self):
        """Test getting a specific discovered tool."""
        discovery = ToolDiscovery()

        mock_tool1 = Mock()
        mock_tool1.name = "Tool1"
        mock_tool2 = Mock()
        mock_tool2.name = "Tool2"

        discovery._discovered_tools = [mock_tool1, mock_tool2]

        result = discovery.get_discovered_tool("Tool1")
        assert result is mock_tool1

    def test_is_tool_discovered(self):
        """Test checking if a tool is discovered."""
        discovery = ToolDiscovery()

        mock_tool = Mock()
        mock_tool.name = "Tool1"

        discovery._discovered_tools = [mock_tool]

        assert discovery.is_tool_discovered("Tool1") is True
        assert discovery.is_tool_discovered("Tool2") is False
