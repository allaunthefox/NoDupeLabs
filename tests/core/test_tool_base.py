"""Test base tool functionality."""

import pytest
from unittest.mock import Mock
from nodupe.core.tool_system.base import Tool, ToolMetadata, AccessibleTool


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
            tags=["test", "tool"]
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
            tags=[]
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
            name="CustomTool",
            version="2.0.0",
            dependencies=["custom_dep"]
        )
        
        assert tool.name == "CustomTool"
        assert tool.version == "2.0.0"
        assert tool.dependencies == ["custom_dep"]


class TestAccessibleToolBase:
    """Test AccessibleTool base class functionality."""

    def test_accessible_tool_inheritance(self):
        """Test that AccessibleTool inherits from Tool."""
        # AccessibleTool is now an interface in base.py, so we'll test its methods
        from nodupe.core.tool_system.accessible_base import AccessibleTool as RealAccessibleTool
        
        tool = RealAccessibleTool()
        
        # Test that it has the expected methods
        assert hasattr(tool, 'announce_to_assistive_tech')
        assert hasattr(tool, 'format_for_accessibility')
        assert hasattr(tool, 'get_ipc_socket_documentation')
        assert hasattr(tool, 'get_accessible_status')
        assert hasattr(tool, 'log_accessible_message')