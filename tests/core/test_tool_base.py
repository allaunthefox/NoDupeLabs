"""Test base tool functionality."""

from unittest.mock import Mock

import pytest

from nodupe.core.tool_system.base import AccessibleTool, Tool, ToolMetadata


class ConcreteTool(Tool):
    """Concrete implementation of Tool for testing."""

    def __init__(self, name="TestTool", version="1.0.0", dependencies=None):
        self._name = name
        self._version = version
        self._dependencies = dependencies or []
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
        return "Test tool usage description"


class TestToolMetadata:
    """Test ToolMetadata functionality."""

    def test_tool_metadata_creation(self):
        """Test ToolMetadata instance creation."""
        metadata = ToolMetadata(
            name="TestTool",
            version="1.0.0",
            software_id="org.test.tool",
            description="A test tool",
            author="Test Author",
            license="MIT",
            dependencies=["dep1", "dep2"],
            tags=["test", "tool"],
        )

        assert metadata.name == "TestTool"
        assert metadata.version == "1.0.0"
        assert metadata.software_id == "org.test.tool"
        assert metadata.description == "A test tool"
        assert metadata.author == "Test Author"
        assert metadata.license == "MIT"
        assert metadata.dependencies == ["dep1", "dep2"]
        assert metadata.tags == ["test", "tool"]

    def test_tool_metadata_immutable(self):
        """Test that ToolMetadata is immutable."""
        metadata = ToolMetadata(
            name="TestTool",
            version="1.0.0",
            software_id="org.test.tool",
            description="A test tool",
            author="Test Author",
            license="MIT",
            dependencies=[],
            tags=[],
        )

        # Should not be able to modify
        with pytest.raises(AttributeError):
            metadata.name = "NewName"


class TestToolBase:
    """Test Tool base class functionality."""

    def test_tool_abstract_properties(self):
        """Test that Tool has required abstract properties."""
        tool = ConcreteTool()

        assert tool.name == "TestTool"
        assert tool.version == "1.0.0"
        assert tool.dependencies == []

    def test_tool_abstract_methods(self):
        """Test that Tool has required abstract methods."""
        tool = ConcreteTool()
        container = Mock()

        # Test initialization
        tool.initialize(container)
        assert tool._initialized is True

        # Test shutdown
        tool.shutdown()
        assert tool._initialized is False

        # Test capabilities
        caps = tool.get_capabilities()
        assert caps == {"test": "capability"}

        # Test API methods
        api_methods = tool.api_methods
        assert api_methods == {}

        # Test standalone execution
        result = tool.run_standalone([])
        assert result == 0

        # Test usage description
        usage = tool.describe_usage()
        assert usage == "Test tool usage description"

    def test_tool_instantiation(self):
        """Test Tool instantiation with various parameters."""
        # Test with custom parameters
        tool = ConcreteTool(
            name="CustomTool", version="2.0.0", dependencies=["custom_dep"]
        )

        assert tool.name == "CustomTool"
        assert tool.version == "2.0.0"
        assert tool.dependencies == ["custom_dep"]


class TestAccessibleToolBase:
    """Test AccessibleTool base class functionality."""

    def test_accessible_tool_inheritance(self):
        """Test that AccessibleTool inherits from Tool."""
        # AccessibleTool is now an interface in base.py, so we'll test its methods
        from nodupe.core.tool_system.accessible_base import (
            AccessibleTool as RealAccessibleTool,
        )

        tool = RealAccessibleTool()

        # Test that it has the expected methods
        assert hasattr(tool, "announce_to_assistive_tech")
        assert hasattr(tool, "format_for_accessibility")
        assert hasattr(tool, "get_ipc_socket_documentation")
        assert hasattr(tool, "get_accessible_status")
        assert hasattr(tool, "log_accessible_message")

    def test_format_for_accessibility_and_describe_value(self):
        """Exercise formatting helpers for dicts, lists and primitives."""
        from nodupe.core.tool_system.accessible_base import AccessibleTool

        t = AccessibleTool()

        # Primitive dict -> compact summary
        compact = t.format_for_accessibility({"a": 1, "b": 2})
        assert "Dictionary with" in compact

        # Nested dict -> expanded output contains keys
        nested = {"k": {"x": 1}, "v": "s"}
        formatted = t.format_for_accessibility(nested)
        assert "k:" in formatted and "v:" in formatted

        # List of primitives -> compact summary
        lst = t.format_for_accessibility([1, 2, 3])
        assert "List with 3 items" in lst

        # List with complex items -> expanded contains 'Item 0'
        complex_list = t.format_for_accessibility([{"a": 1}, 2])
        assert "Item 0" in complex_list

        # describe_value edge cases
        assert t.describe_value(None) == "Not set"
        assert t.describe_value(True) == "Enabled"
        assert t.describe_value(False) == "Disabled"
        assert t.describe_value(42) == "42"
        assert t.describe_value(3.14) == "3.14"
        assert t.describe_value("") == "Empty"
        assert "List with" in t.describe_value([1, 2])
        assert "Dictionary with" in t.describe_value({"a": 1})

    def test_get_ipc_doc_and_status_and_announce(self, capfd):
        """Verify IPC doc, accessible status formatting and announce falls back to console."""
        from nodupe.core.tool_system.accessible_base import AccessibleTool

        t = AccessibleTool()
        ipc = t.get_ipc_socket_documentation()
        assert isinstance(ipc, dict)
        assert "accessibility_features" in ipc

        # Create a small concrete tool to test get_accessible_status
        class CT(AccessibleTool):
            @property
            def name(self):
                return "cname"

            @property
            def version(self):
                return "v1"

            def get_capabilities(self):
                return {"capabilities": ["a"], "description": "d"}

        ct = CT()
        # Not initialized -> status contains 'not initialized' when formatted
        status = ct.get_accessible_status()
        assert "not initialized" in status or "Dictionary with" in status

        # announce_to_assistive_tech prints to stdout (fallback)
        ct.announce_to_assistive_tech("hello test")
        out = capfd.readouterr().out
        assert "hello test" in out

    def test_log_accessible_message_calls_logger_and_announcer(self):
        """log_accessible_message should log and call announce for warnings/errors."""
        from nodupe.core.tool_system.accessible_base import AccessibleTool

        class LT(AccessibleTool):
            @property
            def name(self):
                return "lt"

            @property
            def version(self):
                return "v"

            def get_capabilities(self):
                return {}

        lt = LT()

        # Replace announce_to_assistive_tech with a mock to assert it's called
        lt.announce_to_assistive_tech = Mock()
        lt.logger = Mock()

        lt.log_accessible_message("info-msg", level="info")
        lt.logger.info.assert_called()
        lt.announce_to_assistive_tech.assert_called_with("info-msg", interrupt=False)

        lt.announce_to_assistive_tech.reset_mock()
        lt.logger.reset_mock()

        lt.log_accessible_message("warn-msg", level="warning")
        lt.logger.warning.assert_called()
        # warning should trigger announcement with prefix
        lt.announce_to_assistive_tech.assert_called()
