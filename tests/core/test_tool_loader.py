"""Test tool loader functionality."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch, PropertyMock

import pytest

from nodupe.core.tool_system.base import Tool
from nodupe.core.tool_system.loader import ToolLoader, ToolLoaderError


class TestToolLoaderInitialization:
    """Test ToolLoader initialization functionality."""

    def test_tool_loader_creation(self):
        """Test ToolLoader instance creation."""
        loader = ToolLoader()
        assert loader is not None
        assert loader._loaded_tools == {}
        assert loader._tool_modules == {}
        assert loader.container is None

    def test_tool_loader_with_registry(self):
        """Test ToolLoader with registry."""
        mock_registry = Mock()
        loader = ToolLoader(mock_registry)
        assert loader.registry is mock_registry

    def test_tool_loader_initialize(self):
        """Test ToolLoader initialization with container."""
        loader = ToolLoader()
        container = Mock()

        loader.initialize(container)
        assert loader.container is container


class TestToolLoadingFromFile:
    """Test loading tools from files."""

    def test_load_tool_from_nonexistent_file(self):
        """Test loading tool from nonexistent file."""
        loader = ToolLoader()
        nonexistent_path = Path("/nonexistent/file.py")

        with pytest.raises(ToolLoaderError) as exc_info:
            loader.load_tool_from_file(nonexistent_path)

        assert "does not exist" in str(exc_info.value)

    def test_load_tool_from_invalid_extension(self):
        """Test loading tool from file with invalid extension."""
        loader = ToolLoader()
        invalid_path = Path("/some/file.txt")

        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(ToolLoaderError) as exc_info:
                loader.load_tool_from_file(invalid_path)

            assert "must be Python" in str(exc_info.value)

    def test_load_tool_from_file_success(self):
        """Test successful tool loading from file."""

        # Create a temporary tool class for testing
        class TestTool(Tool):
            def __init__(self):
                self._name = "TestTool"
                self._version = "1.0.0"
                self._dependencies = []
                self._initialized = False

            @property
            def name(self):
                return self._name

            @property
            def version(self):
                return self._version

            @property
            def dependencies(self):
                return self._dependencies

            def initialize(self, container):
                self._initialized = True

            def shutdown(self):
                self._initialized = False

            def get_capabilities(self):
                return {"test": "capability"}

            @property
            def api_methods(self):
                return {}

            def run_standalone(self, args):
                return 0

            def describe_usage(self):
                return "Test tool usage"

        # Mock the file loading process
        loader = ToolLoader()
        mock_path = Path("/fake/tool.py")

        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "suffix", new_callable=PropertyMock, return_value=".py"),
            patch(
                "importlib.util.spec_from_file_location"
            ) as mock_spec_from_file,
            patch("importlib.util.module_from_spec") as mock_module_from_spec,
        ):

            # Create a mock module with our test tool
            mock_module = Mock()
            mock_module.TestTool = TestTool
            mock_module.SomeOtherClass = str  # Not a Tool subclass

            # Mock the spec and module creation
            mock_spec = Mock()
            mock_spec_from_file.return_value = mock_spec
            mock_module_from_spec.return_value = mock_module

            # Mock exec_module to set up the module
            def exec_module_func(module):
                # Add our test tool to the module
                module.TestTool = TestTool
                module.SomeOtherClass = str

            mock_spec.loader.exec_module.side_effect = exec_module_func

            # Try to load the tool
            result = loader.load_tool_from_file(mock_path)

            # Should return our TestTool class
            assert result is TestTool

    def test_load_tool_from_file_no_tool_subclass(self):
        """Test loading tool from file with no Tool subclass."""
        loader = ToolLoader()
        mock_path = Path("/fake/tool.py")

        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "suffix", new_callable=PropertyMock, return_value=".py"),
            patch(
                "importlib.util.spec_from_file_location"
            ) as mock_spec_from_file,
            patch("importlib.util.module_from_spec") as mock_module_from_spec,
        ):

            # Create a mock module with no Tool subclasses
            mock_module = Mock()
            mock_module.SomeClass = str  # Not a Tool subclass
            mock_module.SomeOtherClass = int  # Not a Tool subclass

            # Mock the spec and module creation
            mock_spec = Mock()
            mock_spec_from_file.return_value = mock_spec
            mock_module_from_spec.return_value = mock_module

            # Mock exec_module
            def exec_module_func(module):
                module.SomeClass = str
                module.SomeOtherClass = int

            mock_spec.loader.exec_module.side_effect = exec_module_func

            # Try to load the tool - should raise error
            with pytest.raises(ToolLoaderError) as exc_info:
                loader.load_tool_from_file(mock_path)

            assert "No Tool subclass found" in str(exc_info.value)

    def test_load_tool_from_file_with_relative_imports(self, tmp_path, monkeypatch):
        """ToolLoader should correctly load modules that use relative imports.

        This verifies the package-aware loading we added so that modules which
        perform relative imports (e.g. `from .helper import ...`) work when
        loaded dynamically from a file path.
        """
        # Create a small package layout under tmp_path: nodupe.tools.pkg
        pkg_dir = tmp_path / "nodupe" / "tools" / "pkg"
        pkg_dir.mkdir(parents=True)
        # Create __init__.py files to make it a package
        (tmp_path / "nodupe" / "__init__.py").write_text("")
        (tmp_path / "nodupe" / "tools" / "__init__.py").write_text("")
        (pkg_dir / "__init__.py").write_text("")

        # Helper module that will be imported relatively
        (pkg_dir / "helper.py").write_text("def hello():\n    return 'ok'\n")

        # Tool module that uses a relative import and defines a Tool subclass
        tool_code = '''
from .helper import hello
from nodupe.core.tool_system.base import Tool

class DummyTool(Tool):
    name = "dummy_tool"
    version = "1.0.0"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "usage"
'''
        tool_path = pkg_dir / "tool_mod.py"
        tool_path.write_text(tool_code)

        # Ensure our temporary package root is importable
        monkeypatch.syspath_prepend(str(tmp_path))

        loader = ToolLoader()
        tool_class = loader.load_tool_from_file(tool_path)

        assert tool_class.__name__ == "DummyTool"
        # Confirm the helper relative import worked by executing it
        assert hasattr(tool_class, "__module__")
        assert "pkg" in tool_class.__module__

    def test_load_tool_from_file_validation_error(self):
        """Test loading tool from file with validation error."""

        class InvalidTool(Tool):
            # Missing required abstract methods
            pass

        loader = ToolLoader()
        mock_path = Path("/fake/tool.py")

        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "suffix", new_callable=PropertyMock, return_value=".py"),
            patch(
                "importlib.util.spec_from_file_location"
            ) as mock_spec_from_file,
            patch("importlib.util.module_from_spec") as mock_module_from_spec,
        ):

            # Create a mock module with invalid tool
            mock_module = Mock()
            mock_module.InvalidTool = InvalidTool

            # Mock the spec and module creation
            mock_spec = Mock()
            mock_spec_from_file.return_value = mock_spec
            mock_module_from_spec.return_value = mock_module

            # Mock exec_module
            def exec_module_func(module):
                module.InvalidTool = InvalidTool

            mock_spec.loader.exec_module.side_effect = exec_module_func

            # Try to load the tool - should raise validation error
            with pytest.raises(ToolLoaderError) as exc_info:
                loader.load_tool_from_file(mock_path)

            assert "Invalid tool class" in str(exc_info.value)


class TestToolLoadingFromDirectory:
    """Test loading tools from directories."""

    def test_load_tool_from_directory_nonexistent(self):
        """Test loading tools from nonexistent directory."""
        loader = ToolLoader()
        nonexistent_dir = Path("/nonexistent/dir")

        with pytest.raises(ToolLoaderError) as exc_info:
            loader.load_tool_from_directory(nonexistent_dir)

        assert "does not exist" in str(exc_info.value)

    def test_load_tool_from_directory_not_dir(self):
        """Test loading tools from path that is not a directory."""
        loader = ToolLoader()
        file_path = Path("/some/file.py")

        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_dir", return_value=False),
        ):

            with pytest.raises(ToolLoaderError) as exc_info:
                loader.load_tool_from_directory(file_path)

            assert "not a directory" in str(exc_info.value)

    def test_load_tool_from_directory_empty(self):
        """Test loading tools from empty directory."""
        loader = ToolLoader()
        mock_dir = Path("/empty/dir")

        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "is_dir", return_value=True),
            patch.object(Path, "glob", return_value=[]),
        ):

            result = loader.load_tool_from_directory(mock_dir)
            assert result == []


class TestToolInstantiation:
    """Test tool instantiation functionality."""

    def test_instantiate_tool_success(self):
        """Test successful tool instantiation."""

        class TestTool(Tool):
            def __init__(self, param="default"):
                self.param = param
                self._name = "TestTool"
                self._version = "1.0.0"
                self._dependencies = []

            @property
            def name(self):
                return self._name

            @property
            def version(self):
                return self._version

            @property
            def dependencies(self):
                return self._dependencies

            def initialize(self, container):
                pass

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {}

            @property
            def api_methods(self):
                return {}

            def run_standalone(self, args):
                return 0

            def describe_usage(self):
                return "Test tool usage"

        loader = ToolLoader()

        # Test instantiation with no args
        instance = loader.instantiate_tool(TestTool)
        assert isinstance(instance, TestTool)
        assert instance.param == "default"

        # Test instantiation with args
        instance = loader.instantiate_tool(TestTool, "custom_param")
        assert isinstance(instance, TestTool)
        assert instance.param == "custom_param"

    def test_instantiate_tool_failure(self):
        """Test tool instantiation failure."""

        class FailingTool(Tool):
            def __init__(self):
                raise Exception("Instantiation failed")

            @property
            def name(self):
                return "FailingTool"

            @property
            def version(self):
                return "1.0.0"

            @property
            def dependencies(self):
                return []

            def initialize(self, container):
                pass

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {}

            @property
            def api_methods(self):
                return {}

            def run_standalone(self, args):
                return 0

            def describe_usage(self):
                return "Failing tool usage"

        loader = ToolLoader()

        with pytest.raises(ToolLoaderError) as exc_info:
            loader.instantiate_tool(FailingTool)

        assert "Failed to instantiate tool" in str(exc_info.value)


class TestToolRegistration:
    """Test tool registration functionality."""

    def test_register_loaded_tool(self):
        """Test registering a loaded tool."""
        loader = ToolLoader()
        mock_registry = Mock()
        loader.registry = mock_registry

        mock_tool = Mock()
        mock_tool.name = "TestTool"

        # Register the tool
        loader.register_loaded_tool(mock_tool)

        # Verify registry was called
        mock_registry.register.assert_called_once_with(mock_tool)

    def test_register_loaded_tool_failure(self):
        """Test registering a loaded tool with failure."""
        loader = ToolLoader()
        mock_registry = Mock()
        loader.registry = mock_registry

        # Make registry raise an exception
        mock_registry.register.side_effect = Exception("Registration failed")

        mock_tool = Mock()
        mock_tool.name = "TestTool"

        with pytest.raises(ToolLoaderError) as exc_info:
            loader.register_loaded_tool(mock_tool)

        assert "Failed to register tool" in str(exc_info.value)


class TestToolManagement:
    """Test tool management functionality."""

    def test_unload_tool(self):
        """Test unloading a tool."""
        loader = ToolLoader()

        # Add a tool to the loaded tools
        mock_tool = Mock()
        mock_tool.name = "TestTool"
        mock_tool.shutdown = Mock()
        loader._loaded_tools["TestTool"] = mock_tool

        # Mock registry
        loader.registry = Mock()

        # Unload the tool
        result = loader.unload_tool("TestTool")

        assert result is True
        mock_tool.shutdown.assert_called_once()
        assert "TestTool" not in loader._loaded_tools
        loader.registry.unregister.assert_called_once_with("TestTool")

    def test_unload_nonexistent_tool(self):
        """Test unloading a nonexistent tool."""
        loader = ToolLoader()

        result = loader.unload_tool("NonExistentTool")
        assert result is False

    def test_get_loaded_tool(self):
        """Test getting a loaded tool."""
        loader = ToolLoader()

        mock_tool = Mock()
        loader._loaded_tools["TestTool"] = mock_tool

        result = loader.get_loaded_tool("TestTool")
        assert result is mock_tool

    def test_get_nonexistent_loaded_tool(self):
        """Test getting a nonexistent loaded tool."""
        loader = ToolLoader()

        result = loader.get_loaded_tool("NonExistentTool")
        assert result is None

    def test_get_all_loaded_tools(self):
        """Test getting all loaded tools."""
        loader = ToolLoader()

        mock_tool1 = Mock()
        mock_tool1.name = "Tool1"
        mock_tool2 = Mock()
        mock_tool2.name = "Tool2"

        loader._loaded_tools = {"Tool1": mock_tool1, "Tool2": mock_tool2}

        result = loader.get_all_loaded_tools()
        assert result == {"Tool1": mock_tool1, "Tool2": mock_tool2}

        # Verify it returns a copy, not the original dict
        assert result is not loader._loaded_tools


# Additional tests to increase coverage for Loader
def test_load_tool_from_file_synthetic_module_name(tmp_path, monkeypatch):
    """When the tool file is outside a 'nodupe' package, loader should use
    a synthetic module name and still load the Tool subclass."""
    pkg_dir = tmp_path / "external_pkg"
    pkg_dir.mkdir()

    tool_code = '''
from nodupe.core.tool_system.base import Tool

class ExternalTool(Tool):
    name = "external_tool"
    version = "0.1"
    dependencies = []

    def initialize(self, container):
        pass

    def shutdown(self):
        pass

    def get_capabilities(self):
        return {}

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "usage"
'''
    tool_path = pkg_dir / "external_tool.py"
    tool_path.write_text(tool_code)

    # Ensure our temporary package root is importable
    monkeypatch.syspath_prepend(str(tmp_path))

    loader = ToolLoader()
    tool_class = loader.load_tool_from_file(tool_path)

    assert tool_class.__name__ == "ExternalTool"


def test_load_tool_from_directory_recursive_real_files(tmp_path):
    """load_tool_from_directory should find tools recursively on disk."""
    root = tmp_path / "toolsroot"
    sub = root / "subpkg"
    sub.mkdir(parents=True)

    # File in root
    root_tool = root / "root_tool.py"
    root_tool.write_text('from nodupe.core.tool_system.base import Tool\nclass RootTool(Tool):\n    name = "root_tool"\n    version="1"\n    dependencies=[]\n    def initialize(self, container): pass\n    def shutdown(self): pass\n    def get_capabilities(self): return {}\n    @property\n    def api_methods(self): return {}\n    def run_standalone(self, args): return 0\n    def describe_usage(self): return "u"')

    # File in subdir
    sub_tool = sub / "sub_tool.py"
    sub_tool.write_text('from nodupe.core.tool_system.base import Tool\nclass SubTool(Tool):\n    name = "sub_tool"\n    version="1"\n    dependencies=[]\n    def initialize(self, container): pass\n    def shutdown(self): pass\n    def get_capabilities(self): return {}\n    @property\n    def api_methods(self): return {}\n    def run_standalone(self, args): return 0\n    def describe_usage(self): return "u"')

    loader = ToolLoader()
    found = loader.load_tool_from_directory(root, recursive=True)

    names = {c.__name__ for c in found}
    assert "RootTool" in names
    assert "SubTool" in names


def test_load_tool_by_name_with_package_init(tmp_path, monkeypatch):
    """load_tool_by_name should load a tool from a package __init__.py"""
    pkg_dir = tmp_path / "mypkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text('from nodupe.core.tool_system.base import Tool\nclass PkgTool(Tool):\n    name = "pkg_tool"\n    version = "1"\n    dependencies=[]\n    def initialize(self, container): pass\n    def shutdown(self): pass\n    def get_capabilities(self): return {}\n    @property\n    def api_methods(self): return {}\n    def run_standalone(self, args): return 0\n    def describe_usage(self): return "u"')

    monkeypatch.syspath_prepend(str(tmp_path))

    loader = ToolLoader()
    cls = loader.load_tool_by_name("mypkg", [tmp_path])
    assert cls.__name__ == "PkgTool"


def test_unload_tool_removes_module_from_sys_modules(monkeypatch):
    """unload_tool should remove the module from sys.modules when present."""
    loader = ToolLoader()

    # Create a fake tool class with a module name and ensure the module is
    # present in sys.modules so unload_tool removes it.
    class FakeTool:
        name = "fake"

    # Simulate that the tool instance reports __module__ pointing to 'fake_mod'
    fake_instance = Mock()
    fake_instance.name = "fake"
    fake_instance.__module__ = "fake_mod"
    loader._loaded_tools["fake"] = fake_instance

    # Insert a dummy module into sys.modules
    import types
    import sys as _sys

    mod = types.ModuleType("fake_mod")
    _sys.modules["fake_mod"] = mod

    # Mock shutdown and registry
    fake_instance.shutdown = Mock()
    loader.registry = Mock()

    result = loader.unload_tool("fake")

    assert result is True
    fake_instance.shutdown.assert_called_once()
    assert "fake" not in loader._loaded_tools
    assert "fake_mod" not in _sys.modules
