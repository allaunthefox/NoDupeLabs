"""Test accessible base class functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from nodupe.core.tool_system.accessible_base import AccessibleTool
from nodupe.core.api.codes import ActionCode


class ConcreteAccessibleTool(AccessibleTool):
    """Concrete implementation of AccessibleTool for testing."""
    
    def __init__(self):
        super().__init__()
        self._name = "TestAccessibleTool"
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
        self.announce_to_assistive_tech(f"Initializing {self.name}")

    def shutdown(self):
        self._initialized = False
        self.announce_to_assistive_tech(f"Shutting down {self.name}")

    def get_capabilities(self):
        return {
            "name": self.name,
            "version": self.version,
            "description": "Test accessible tool",
            "capabilities": ["test"]
        }

    @property
    def api_methods(self):
        return {}

    def run_standalone(self, args):
        return 0

    def describe_usage(self):
        return "Test accessible tool for testing purposes."


class TestAccessibleToolInitialization:
    """Test AccessibleTool initialization functionality."""

    def test_accessible_tool_creation(self):
        """Test AccessibleTool instance creation."""
        tool = ConcreteAccessibleTool()
        assert tool is not None
        assert tool.name == "TestAccessibleTool"
        assert tool.version == "1.0.0"
        assert tool.dependencies == []
        assert tool.accessible_output is not None

    def test_initialize_with_container(self):
        """Test initialization with container."""
        tool = ConcreteAccessibleTool()
        container = Mock()
        
        with patch('builtins.print') as mock_print:
            tool.initialize(container)
            assert tool._initialized is True
            mock_print.assert_called()  # Should announce to assistive tech

    def test_shutdown(self):
        """Test tool shutdown."""
        tool = ConcreteAccessibleTool()
        tool._initialized = True
        
        with patch('builtins.print') as mock_print:
            tool.shutdown()
            assert tool._initialized is False
            mock_print.assert_called()  # Should announce to assistive tech


class TestAccessibleOutput:
    """Test accessible output functionality."""

    def test_announce_to_assistive_tech(self):
        """Test announcing to assistive technology."""
        tool = ConcreteAccessibleTool()
        
        with patch('builtins.print') as mock_print:
            tool.announce_to_assistive_tech("Test message")
            mock_print.assert_called_with("Test message")

    def test_format_for_accessibility_dict(self):
        """Test formatting dictionary for accessibility."""
        tool = ConcreteAccessibleTool()
        
        test_data = {
            "status": "running",
            "count": 42,
            "active": True,
            "nested": {"inner": "value"}
        }
        
        result = tool.format_for_accessibility(test_data)
        assert "status:" in result
        assert "running" in result
        assert "count:" in result
        assert "42" in result
        assert "active:" in result
        assert "Enabled" in result  # True should become "Enabled"
        assert "nested:" in result
        assert "inner:" in result
        assert "value" in result

    def test_format_for_accessibility_list(self):
        """Test formatting list for accessibility."""
        tool = ConcreteAccessibleTool()
        
        test_data = ["item1", "item2", {"key": "value"}]
        
        result = tool.format_for_accessibility(test_data)
        assert "Item 1:" in result
        assert "item1" in result
        assert "Item 2:" in result
        assert "item2" in result
        assert "key:" in result
        assert "value" in result

    def test_format_for_accessibility_primitives(self):
        """Test formatting primitive types for accessibility."""
        tool = ConcreteAccessibleTool()
        
        # Test None
        result = tool.format_for_accessibility(None)
        assert result == "Not set"
        
        # Test boolean
        result = tool.format_for_accessibility(True)
        assert result == "Enabled"
        result = tool.format_for_accessibility(False)
        assert result == "Disabled"
        
        # Test numbers
        result = tool.format_for_accessibility(42)
        assert result == "42"
        result = tool.format_for_accessibility(3.14)
        assert result == "3.14"
        
        # Test string
        result = tool.format_for_accessibility("hello")
        assert result == "'hello'"
        result = tool.format_for_accessibility("")
        assert result == "Empty"
        
        # Test list
        result = tool.format_for_accessibility([1, 2, 3])
        assert "List with 3 items" in result
        
        # Test dict
        result = tool.format_for_accessibility({"a": 1})
        assert "Dictionary with 1 keys" in result


class TestAccessibleStatus:
    """Test accessible status functionality."""

    def test_get_accessible_status(self):
        """Test getting accessible status."""
        tool = ConcreteAccessibleTool()
        
        result = tool.get_accessible_status()
        assert "TestAccessibleTool" in result
        assert "1.0.0" in result
        assert "not initialized" in result  # Initially not initialized
        
        # Initialize and test again
        container = Mock()
        tool.initialize(container)
        result = tool.get_accessible_status()
        assert "TestAccessibleTool" in result
        assert "ready" in result  # Now initialized


class TestAccessibleLogging:
    """Test accessible logging functionality."""

    def test_log_accessible_message(self):
        """Test logging accessible message."""
        tool = ConcreteAccessibleTool()
        
        with patch('builtins.print') as mock_print:
            tool.log_accessible_message("Test info message", "info")
            # Should print the message
            assert mock_print.called
            
            tool.log_accessible_message("Test error message", "error")
            # Should print the message and announce as alert
            assert mock_print.call_count >= 2


class TestDescribeValue:
    """Test describe_value functionality."""

    def test_describe_value_various_types(self):
        """Test describing various value types."""
        tool = ConcreteAccessibleTool()
        
        # Test None
        assert tool.describe_value(None) == "Not set"
        
        # Test boolean
        assert tool.describe_value(True) == "Enabled"
        assert tool.describe_value(False) == "Disabled"
        
        # Test numbers
        assert tool.describe_value(42) == "42"
        assert tool.describe_value(3.14) == "3.14"
        
        # Test string
        assert tool.describe_value("hello") == "'hello'"
        assert tool.describe_value("") == "Empty"
        
        # Test list
        assert "List with" in tool.describe_value([1, 2, 3])
        
        # Test dict
        assert "Dictionary with" in tool.describe_value({"a": 1})
        
        # Test object
        class TestObj:
            pass
        obj = TestObj()
        result = tool.describe_value(obj)
        assert "TestObj object" in result


class TestGetIPCSocketDocumentation:
    """Test IPC socket documentation functionality."""

    def test_get_ipc_socket_documentation(self):
        """Test getting IPC socket documentation."""
        tool = ConcreteAccessibleTool()
        
        result = tool.get_ipc_socket_documentation()
        assert "socket_endpoints" in result
        assert "accessibility_features" in result
        
        features = result["accessibility_features"]
        assert features["text_only_mode"] is True
        assert features["structured_output"] is True
        assert features["progress_reporting"] is True
        assert features["error_explanation"] is True
        assert features["screen_reader_integration"] is True
        assert features["braille_api_support"] is True