# Tools Development Guide

This guide covers tool development standards, patterns, and best practices for the NoDupeLabs tool system, with explicit alignment to ISO/IEC/IEEE 42010 architecture description standards.

## Overview

The NoDupeLabs tool system provides a flexible architecture for extending functionality in compliance with ISO/IEC/IEEE 42010 standards. Tools can be discovered, loaded, and managed dynamically with support for hot reloading and dependency management.

## ISO/IEC/IEEE 42010 Compliance

This tool system architecture follows the ISO/IEC/IEEE 42010 standard for architecture descriptions, which establishes a framework for creating, evaluating, and comparing architecture descriptions.

### Key ISO/IEC/IEEE 42010 Concepts Applied

1. **Architecture vs. Architecture Description**: This document is an "architecture description" of the tool system "architecture"
2. **Stakeholders**: Various roles with interests in the tool system (developers, operators, end-users)
3. **Concerns**: Specific interests stakeholders have (performance, security, maintainability)
4. **Views and Viewpoints**: Different representations of the architecture from specific perspectives
5. **Architecture Rationale**: Justification for architectural decisions

## Table of Contents

- [Tool Architecture](#tool-architecture)
- [ISO Viewpoints and Views](#iso-viewpoints-and-views)
- [Tool Interface](#tool-interface)
- [Tool Discovery](#tool-discovery)
- [Tool Loading](#tool-loading)
- [Tool Lifecycle](#tool-lifecycle)
- [Tool Dependencies](#tool-dependencies)
- [Tool Compatibility](#tool-compatibility)
- [Tool Hot Reloading](#tool-hot-reloading)
- [Tool Security](#tool-security)
- [Tool Registry](#tool-registry)
- [Tool Development Patterns](#tool-development-patterns)
- [Tool Testing](#tool-testing)
- [Tool Documentation](#tool-documentation)
- [Tool Standards and Best Practices](#tool-standards-and-best-practices)

## Tool Architecture

### Core Components

1. **Tool Interface**: Abstract base class for all tools
2. **Tool Discovery**: Automatic discovery of tools in directories
3. **Tool Loading**: Dynamic loading and initialization of tools
4. **Tool Registry**: Central registry for managing tools
5. **Tool Lifecycle**: Lifecycle management for tools
6. **Tool Dependencies**: Dependency resolution and management
7. **Tool Compatibility**: Compatibility checking and version management
8. **Tool Hot Reloading**: Hot reloading of tools during development
9. **Tool Security**: Security measures for tool execution

### Tool Types

- **Core Tools**: Essential tools required for system operation
- **Optional Tools**: Optional functionality that can be loaded as needed
- **Third-party Tools**: External tools from third-party developers

## ISO Viewpoints and Views

### Stakeholder Identification

The following stakeholders have interests in the tool system:

- **Developers**: Need clear interfaces and development guidelines
- **Operators**: Need reliable operation and monitoring capabilities
- **End Users**: Need stable and performant functionality
- **Security Officers**: Need assurance of secure execution
- **Architects**: Need clear separation of concerns and extensibility

### Viewpoints and Views

#### 1. Functional Viewpoint
**Stakeholders**: Developers, End Users
**Concerns**: What functionality does each tool provide?

**View**: Functional decomposition showing tools and their capabilities
```
Core System
├── Tool Registry
├── Tool Loader
├── Tool Discovery
└── Tool Lifecycle Manager
└── Tools
    ├── Hashing Tool
    ├── Database Tool
    ├── Scanner Tool
    └── Compression Tool
```

#### 2. Development Viewpoint
**Stakeholders**: Developers
**Concerns**: How are tools implemented and integrated?

**View**: Component diagram showing interfaces and dependencies
```
[Tool Interface] <- [Concrete Tool]
       ↑
[Tool Registry] ↔ [Tool Loader]
       ↓
[Tool Discovery] ↔ [Tool Lifecycle]
```

#### 3. Deployment Viewpoint
**Stakeholders**: Operators
**Concerns**: How are tools deployed and managed in runtime?

**View**: Deployment diagram showing runtime relationships
```
Host Environment
├── Core Loader
├── Service Container
└── Tool Instances
    ├── Hashing Tool Instance
    ├── Database Tool Instance
    └── Scanner Tool Instance
```

#### 4. Security Viewpoint
**Stakeholders**: Security Officers
**Concerns**: How are tools validated and secured?

**View**: Security architecture showing validation and isolation
```
Tool File → [Security Validator] → [Sandbox Execution] → [Approved Tool]
```

## Tool Interface

### Abstract Tool Class

All tools must inherit from the `Tool` abstract base class:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class Tool(ABC):
    """Abstract base class for all NoDupeLabs tools following ISO/IEC/IEEE 42010 principles"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name"""

    @property
    @abstractmethod
    def version(self) -> str:
        """Tool version"""

    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        """List of tool dependencies"""

    @abstractmethod
    def initialize(self, container: Any) -> None:
        """Initialize the tool"""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the tool"""

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get tool capabilities"""

    @abstractmethod
    def get_architecture_rationale(self) -> Dict[str, str]:
        """Get architectural rationale for this tool following ISO/IEC/IEEE 42010"""
```

### Tool Metadata

Tools should provide metadata about their capabilities:

```python
def get_capabilities(self) -> Dict[str, Any]:
    return {
        "name": self.name,
        "version": self.version,
        "description": "Tool description",
        "author": "Tool author",
        "license": "Tool license",
        "tags": ["tag1", "tag2"],
        "capabilities": ["capability1", "capability2"],
        "iso_stakeholders": ["developer", "operator", "end_user"],
        "iso_concerns": ["performance", "security", "maintainability"]
    }

def get_architecture_rationale(self) -> Dict[str, str]:
    return {
        "design_decision": "Why this tool exists",
        "alternatives_considered": "Other approaches evaluated",
        "tradeoffs": "Pros and cons of this approach",
        "stakeholder_impact": "How this affects different stakeholders"
    }
```

## Tool Discovery

### Automatic Discovery

Tools are automatically discovered in the following locations:

1. **Core Tools**: `nodupe/tools/` directory
2. **User Tools**: User-defined directories
3. **Third-party Tools**: External tool directories

### Tool Discovery Patterns

1. **Directory Scanning**: Recursively scan directories for tool files
2. **File Pattern Matching**: Match files with specific patterns
3. **Import Path Resolution**: Resolve import paths for discovered tools
4. **Tool Validation**: Validate discovered tools for correctness

### Tool Discovery Configuration

```python
# Configure tool discovery
discovery = ToolDiscovery()
discovery.add_directory("/path/to/tools")
discovery.add_pattern("*.py")
discovery.scan()
```

## Tool Loading

### Dynamic Loading

Tools are dynamically loaded using Python's import system:

```python
loader = ToolLoader()
tool = loader.load_tool("tool_name")
```

### Tool Initialization

Tools are initialized with a container for dependency injection:

```python
def initialize(self, container: Any) -> None:
    """Initialize the tool with a container"""
    self.container = container
    # Initialize tool components
```

### Tool Shutdown

Tools should properly clean up resources:

```python
def shutdown(self) -> None:
    """Shutdown the tool and clean up resources"""
    # Clean up tool resources
```

## Tool Lifecycle

### Lifecycle States

1. **Discovered**: Tool found but not yet loaded
2. **Loaded**: Tool loaded but not initialized
3. **Initialized**: Tool initialized and ready to use
4. **Running**: Tool actively providing functionality
5. **Shutdown**: Tool shutdown and resources cleaned up

### Lifecycle Management

```python
# Tool lifecycle management
lifecycle = ToolLifecycleManager()
lifecycle.initialize_tool(tool)
lifecycle.shutdown_tool(tool)
```

## Tool Dependencies

### Dependency Declaration

Tools declare their dependencies:

```python
@property
def dependencies(self) -> List[str]:
    return ["dependency1", "dependency2"]
```

### Dependency Resolution

Dependencies are automatically resolved and loaded:

```python
resolver = DependencyResolver()
resolved = resolver.resolve_dependencies(tools)
```

### Dependency Injection

Dependencies are injected into tools:

```python
def initialize(self, container: Any) -> None:
    # Inject dependencies
    self.dependency1 = container.get("dependency1")
    self.dependency2 = container.get("dependency2")
```

## Tool Compatibility

### Version Compatibility

Tools specify compatibility requirements:

```python
def get_capabilities(self) -> Dict[str, Any]:
    return {
        "compatible_versions": [">=1.0.0", "<2.0.0"]
    }
```

### Compatibility Checking

Compatibility is automatically checked:

```python
compatibility = ToolCompatibility()
is_compatible = compatibility.check_tool(tool)
```

## Tool Hot Reloading

### Development Support

Tools support hot reloading during development:

```python
# Enable hot reloading
hot_reload = ToolHotReload()
hot_reload.enable()
```

### File Monitoring

Monitor tool files for changes:

```python
# Monitor files for changes
hot_reload.monitor_file("tool.py")
```

### Automatic Reloading

Tools are automatically reloaded when changes are detected:

```python
# Automatic reloading
hot_reload.reload_tool(tool)
```

## Tool Security

### Security Measures

1. **Code Signing**: Verify tool code integrity
2. **Sandboxing**: Run tools in isolated environments
3. **Permission Control**: Control tool permissions
4. **Security Auditing**: Audit tool security

### Security Implementation

```python
# Tool security
security = ToolSecurity()
security.verify_tool(tool)
security.run_in_sandbox(tool)
```

## Tool Registry

### Central Registry

The tool registry manages all tools:

```python
registry = ToolRegistry()
registry.register_tool(tool)
registry.get_tool("tool_name")
```

### Tool Lookup

Tools can be looked up by name or capability:

```python
# Lookup by name
tool = registry.get_tool("tool_name")

# Lookup by capability
tools = registry.get_tools_by_capability("capability")
```

### Tool Management

Registry provides tool management capabilities:

```python
# Tool management
registry.enable_tool("tool_name")
registry.disable_tool("tool_name")
registry.remove_tool("tool_name")
```

## Tool Development Patterns

### 1. Tool Initialization Pattern

```python
class MyTool(Tool):
    def __init__(self):
        self.initialized = False
        self.dependencies = {}

    def initialize(self, container: Any) -> None:
        if self.initialized:
            return

        # Initialize dependencies
        self.dependencies = {
            'db': container.get('database'),
            'config': container.get('config')
        }

        # Initialize tool
        self._setup_tool()
        self.initialized = True

    def _setup_tool(self) -> None:
        # Tool-specific setup
        pass

    def get_architecture_rationale(self) -> Dict[str, str]:
        return {
            "design_decision": "This tool provides specific functionality",
            "alternatives_considered": "Considered integrating directly into core",
            "tradeoffs": "Added complexity but improved modularity",
            "stakeholder_impact": "Developers can extend functionality independently"
        }
```

### 2. Tool Configuration Pattern

```python
class ConfigurableTool(Tool):
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.default_config = {
            'setting1': 'default_value',
            'setting2': 42
        }

    def get_config(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, self.default_config.get(key, default))
```

### 3. Tool Error Handling Pattern

```python
class RobustTool(Tool):
    def __init__(self):
        self.error_count = 0
        self.max_errors = 10

    def handle_operation(self) -> bool:
        try:
            # Tool operation
            result = self._do_operation()
            self.error_count = 0  # Reset on success
            return result
        except Exception as e:
            self.error_count += 1
            logger.error(f"Operation failed: {e}")

            # Graceful degradation or shutdown
            if self.error_count >= self.max_errors:
                logger.critical("CRITICAL: Tool has failed repeatedly. Disabling tool to prevent system degradation.")
                self.disable()
                return False

            return False
```

### 4. Tool State Management Pattern

```python
class StatefulTool(Tool):
    def __init__(self):
        self.state = {}
        self.state_file = "tool_state.json"

    def save_state(self) -> None:
        """Save tool state to file"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f)

    def load_state(self) -> None:
        """Load tool state from file"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)

    def update_state(self, key: str, value: Any) -> None:
        """Update tool state"""
        self.state[key] = value
        self.save_state()
```

### 5. Tool Event Handling Pattern

```python
class EventDrivenTool(Tool):
    def __init__(self):
        self.event_handlers = {}

    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def handle_event(self, event_type: str, data: Any) -> None:
        """Handle an event"""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Event handler failed: {e}")
```

## Tool Testing

### Unit Testing

Test individual tool components:

```python
import unittest
from nodupe.core.tool_system import Tool

class TestMyTool(unittest.TestCase):
    def setUp(self):
        self.tool = MyTool()

    def test_tool_initialization(self):
        self.assertFalse(self.tool.initialized)
        self.tool.initialize(container)
        self.assertTrue(self.tool.initialized)

    def test_tool_capabilities(self):
        capabilities = self.tool.get_capabilities()
        self.assertIn('name', capabilities)
        self.assertIn('version', capabilities)

    def test_iso_compliance(self):
        # Test ISO/IEC/IEEE 42010 compliance
        rationale = self.tool.get_architecture_rationale()
        self.assertIn('design_decision', rationale)
        self.assertIn('stakeholder_impact', rationale)
```

### Integration Testing

Test tool integration with the system:

```python
class TestToolIntegration(unittest.TestCase):
    def test_tool_discovery(self):
        discovery = ToolDiscovery()
        discovery.add_directory("test_tools")
        tools = discovery.scan()
        self.assertGreater(len(tools), 0)

    def test_tool_loading(self):
        loader = ToolLoader()
        tool = loader.load_tool("test_tool")
        self.assertIsInstance(tool, Tool)
```

### Mock Testing

Use mocks for testing tool behavior:

```python
from unittest.mock import Mock, patch

class TestToolBehavior(unittest.TestCase):
    def test_tool_with_mock_dependencies(self):
        mock_container = Mock()
        mock_container.get.return_value = Mock()

        tool = MyTool()
        tool.initialize(mock_container)

        # Test tool behavior with mocked dependencies
        self.assertTrue(tool.initialized)
```

## Tool Documentation

### Tool README

Each tool should include a README file:

```markdown
# Tool Name

Brief description of the tool.

## ISO/IEC/IEEE 42010 Compliance

- **Stakeholders**: Who benefits from this tool
- **Concerns**: What problems this tool addresses
- **Architecture Rationale**: Why this approach was chosen

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

Installation instructions.

## Configuration

Configuration options and examples.

## Usage

Usage examples and documentation.

## Dependencies

List of tool dependencies.

## Compatibility

Compatibility information.

## License

License information.
```

### Tool Documentation Standards

1. **Clear Description**: Clear description of tool functionality
2. **ISO Compliance Section**: Explicit section on ISO/IEC/IEEE 42010 compliance
3. **Stakeholder Analysis**: Who benefits from this tool and how
4. **Installation Guide**: Step-by-step installation instructions
5. **Configuration Guide**: Configuration options and examples
6. **Usage Examples**: Practical usage examples
7. **API Documentation**: API reference and documentation
8. **Troubleshooting Guide**: Common issues and solutions

## Tool Standards and Best Practices

### 1. ISO/IEC/IEEE 42010 Alignment

**Standard**: All tools must document their alignment with ISO/IEC/IEEE 42010 principles

### 2. Accessibility and Visual Impairment Support

**Standard**: All tools must support users with visual impairments and be compatible with assistive technologies including screen readers, braille displays, and voice navigation systems.

#### Accessibility Requirements

1. **Text-Based Interfaces**: All tool interfaces must be navigable via keyboard and screen readers
2. **Descriptive Output**: All tool output must be descriptive and meaningful when read aloud
3. **Structured Data**: Use structured data formats that are parseable by assistive technologies
4. **Alternative Representations**: Provide alternative representations for any visual-only information
5. **IPC Socket Documentation**: Tools must document their IPC socket interfaces for integration with assistive technologies

#### Accessibility Implementation

```python
class AccessibleTool(Tool):
    def __init__(self):
        self.accessibility_features = {
            "keyboard_navigable": True,
            "screen_reader_compatible": True,
            "braille_display_supported": True,
            "voice_navigation_ready": True
        }

    def get_accessible_output(self, data: Any) -> str:
        """
        Generate accessible output that can be interpreted by assistive technologies.

        Args:
            data: Raw data to convert to accessible format

        Returns:
            Human-readable string suitable for screen readers and braille displays
        """
        if isinstance(data, dict):
            output = []
            for key, value in data.items():
                output.append(f"{key}: {self._describe_value(value)}")
            return "\n".join(output)
        elif isinstance(data, list):
            output = []
            for i, item in enumerate(data):
                output.append(f"Item {i + 1}: {self._describe_value(item)}")
            return "\n".join(output)
        else:
            return str(data)

    def _describe_value(self, value: Any) -> str:
        """Describe a value in an accessible way."""
        if value is None:
            return "Not set"
        elif isinstance(value, bool):
            return "Enabled" if value else "Disabled"
        elif isinstance(value, (int, float)):
            return f"{value}"
        elif isinstance(value, str):
            return f"'{value}'" if value else "Empty"
        else:
            return f"{type(value).__name__} object"

    def get_ipc_socket_documentation(self) -> Dict[str, Any]:
        """
        Document IPC socket interfaces for assistive technology integration.

        Returns:
            Dictionary describing available IPC endpoints and their accessibility features
        """
        return {
            "socket_endpoints": {
                "status": {
                    "path": "/api/v1/status",
                    "method": "GET",
                    "description": "Current tool status and health information",
                    "accessible_output": True,
                    "returns": {
                        "status": "Current operational status",
                        "progress": "Current progress percentage",
                        "errors": "Any current errors or warnings",
                        "estimated_completion": "Estimated time to completion"
                    }
                },
                "operations": {
                    "path": "/api/v1/operations",
                    "method": "POST",
                    "description": "Initiate operations with accessible progress reporting",
                    "accessible_output": True,
                    "parameters": {
                        "operation": "Type of operation to perform",
                        "options": "Operation-specific options"
                    }
                }
            },
            "accessibility_features": {
                "text_only_mode": True,
                "structured_output": True,
                "progress_reporting": True,
                "error_explanation": True
            }
        }
```

#### IPC Socket Accessibility Standards

All tools must expose IPC sockets with the following accessibility features:

1. **Text-Only Mode**: All endpoints must support text-only responses without visual elements
2. **Structured Output**: Use consistent, parseable data structures (JSON, CSV, etc.)
3. **Progress Reporting**: Provide detailed progress information for long-running operations
4. **Error Explanation**: Provide clear, descriptive error messages for screen readers
5. **Keyboard Navigation**: All interactive features accessible via keyboard commands

#### Accessibility Testing

All tools must include accessibility tests:

```python
class TestAccessibleTool(unittest.TestCase):
    def test_screen_reader_compatibility(self):
        """Test that tool output is compatible with screen readers."""
        tool = AccessibleTool()
        sample_data = {"status": "running", "progress": 50, "items_processed": 100}
        accessible_output = tool.get_accessible_output(sample_data)

        # Verify output is readable and descriptive
        self.assertIn("status:", accessible_output)
        self.assertIn("running", accessible_output)
        self.assertIn("progress:", accessible_output)
        self.assertIn("items_processed:", accessible_output)

    def test_braille_display_compatibility(self):
        """Test that output is suitable for braille displays."""
        tool = AccessibleTool()
        sample_data = {"status": "completed", "results": 42}
        accessible_output = tool.get_accessible_output(sample_data)

        # Braille displays have limited space, so output should be concise but complete
        lines = accessible_output.split('\n')
        for line in lines:
            # Each line should be meaningful when read individually
            self.assertGreater(len(line.strip()), 0)

    def test_ipc_documentation_exists(self):
        """Test that IPC socket documentation is available."""
        tool = AccessibleTool()
        ipc_doc = tool.get_ipc_socket_documentation()

        # Verify documentation structure
        self.assertIn("socket_endpoints", ipc_doc)
        self.assertIn("accessibility_features", ipc_doc)

        # Verify accessibility features are documented
        features = ipc_doc["accessibility_features"]
        self.assertTrue(features["text_only_mode"])
        self.assertTrue(features["structured_output"])
```

#### Accessibility Documentation Standards

Each tool must include accessibility documentation:

```markdown
## Accessibility Features

This tool supports users with visual impairments through:

- **Screen Reader Compatibility**: All output is structured for screen reader interpretation
- **Braille Display Support**: Text output is optimized for braille displays
- **Keyboard Navigation**: All features accessible via keyboard commands
- **Voice Navigation Ready**: Commands can be issued via voice recognition software
- **High Contrast Mode**: Terminal output uses high contrast colors when applicable

## IPC Socket Integration

The tool exposes the following endpoints for assistive technology integration:

- `/api/v1/status` - Current status and progress information
- `/api/v1/operations` - Operation initiation with progress tracking
- `/api/v1/logs` - Accessible log information

See [IPC Documentation](ipc.md) for full details.
```

#### Compliance Checklist for Accessibility

All tools must comply with the following accessibility checklist:

- [ ] All interfaces navigable via keyboard
- [ ] Output suitable for screen readers
- [ ] Text alternatives for any visual-only information
- [ ] Structured data formats for assistive technology parsing
- [ ] Descriptive error messages
- [ ] Progress reporting for long-running operations
- [ ] IPC socket documentation for assistive technology integration
- [ ] Accessibility tests included
- [ ] Accessibility documentation provided
- [ ] High contrast terminal output (where applicable)
- [ ] Voice navigation compatibility
- [ ] Braille display compatibility

```python
class ISOFocusedTool(Tool):
    def get_architecture_rationale(self) -> Dict[str, str]:
        return {
            "design_decision": "Created as a separate tool to maintain loose coupling with core",
            "alternatives_considered": "Considered integrating directly into core vs. plugin vs. tool",
            "tradeoffs": "Added complexity of tool management vs. gained modularity and maintainability",
            "stakeholder_impact": "Developers can extend functionality independently, operators can manage tools separately"
        }

    def get_iso_stakeholders_and_concerns(self) -> Dict[str, List[str]]:
        return {
            "developers": ["ease_of_extension", "clear_interfaces"],
            "operators": ["reliability", "manageability"],
            "end_users": ["performance", "functionality"]
        }
```

### 2. Error Handling and Graceful Degradation

**Standard**: All tools must implement graceful error handling and degradation

```python
class ToolWithGracefulDegradation(Tool):
    def __init__(self):
        self.error_count = 0
        self.max_errors = 10
        self.is_degraded = False
        self.is_disabled = False

    def handle_critical_failure(self, error: Exception) -> None:
        """
        Handle critical failures with graceful shutdown.

        Standard Behavior:
        1. Log critical error with full context
        2. Attempt graceful degradation first
        3. If degradation fails, self-disable to prevent system spam
        4. Return appropriate fallback behavior

        Args:
            error: The critical error that occurred
        """
        logger.critical(f"CRITICAL: Tool {self.name} has encountered a critical failure: {error}")
        logger.critical(f"Tool state: errors={self.error_count}, degraded={self.is_degraded}")

        # First, try graceful degradation
        if not self.is_degraded:
            self._degrade_gracefully()
            logger.warning(f"Tool {self.name} has degraded to fallback mode")
            return

        # If already degraded and still failing, self-disable
        logger.critical(f"CRITICAL: Tool {self.name} is shutting down to prevent system degradation")
        self.disable()

    def _degrade_gracefully(self) -> None:
        """Degrade tool functionality gracefully"""
        self.is_degraded = True
        # Switch to fallback behavior
        # Reduce functionality but maintain core operations
        # Log degradation with clear indication

    def disable(self) -> None:
        """
        Disable tool to prevent system degradation.

        Standard Behavior:
        1. Stop all background operations
        2. Clean up resources
        3. Set disabled state
        4. Log shutdown with clear message
        """
        self.is_disabled = True
        self.shutdown()
        logger.critical(f"Tool {self.name} has been disabled. System will use fallback behavior.")

    def get_fallback_result(self, operation: str, *args, **kwargs) -> Any:
        """
        Provide fallback result when tool is degraded or disabled.

        Args:
            operation: The operation that failed
            *args, **kwargs: Operation arguments

        Returns:
            Fallback result appropriate for the operation
        """
        if operation == "timestamp":
            return time.monotonic()  # Fallback to monotonic time
        elif operation == "data":
            return {}  # Fallback to empty data
        # Implement appropriate fallbacks for each operation type
```

### 3. Accessible Tool Implementation

**CRITICAL REQUIREMENT**: Accessibility is a core requirement, not an optional feature. All tools that process user data or provide user-facing functionality MUST implement accessibility support. Even if external accessibility libraries are not available, the tool MUST provide basic accessibility through console output.

#### Accessibility Action Codes

The system implements specific action codes for accessibility tracking and compliance:

- **ACC_SCREEN_READER_INIT**: Screen reader initialization
- **ACC_SCREEN_READER_AVAIL**: Screen reader availability confirmed
- **ACC_SCREEN_READER_UNAVAIL**: Screen reader unavailable, using fallback
- **ACC_BRAILLE_INIT**: Braille display initialization
- **ACC_BRAILLE_AVAIL**: Braille display availability confirmed
- **ACC_BRAILLE_UNAVAIL**: Braille display unavailable, using fallback
- **ACC_OUTPUT_SENT**: Accessibility output successfully sent
- **ACC_OUTPUT_FAILED**: Accessibility output failed
- **ACC_FEATURE_ENABLED**: Accessibility feature enabled
- **ACC_FEATURE_DISABLED**: Accessibility feature disabled
- **ACC_LIB_LOAD_SUCCESS**: Accessibility library loaded successfully
- **ACC_LIB_LOAD_FAIL**: Accessibility library failed to load
- **ACC_CONSOLE_FALLBACK**: Using console fallback for accessibility
- **ACC_ISO_COMPLIANT**: ISO accessibility compliance indicator

For tools that need to support users with visual impairments, extend the `AccessibleTool` base class from `nodupe.core.tool_system.accessible_base`:

```python
from nodupe.core.tool_system.accessible_base import AccessibleTool

class MyAccessibleTool(AccessibleTool):
    def __init__(self):
        super().__init__()  # Initialize accessibility features
        self._name = "MyAccessibleTool"
        self._version = "1.0.0"
        self._dependencies = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def dependencies(self) -> List[str]:
        return self._dependencies

    def initialize(self, container: Any) -> None:
        self.announce_to_assistive_tech(f"Initializing {self.name} v{self.version}")
        # Initialization code
        self.announce_to_assistive_tech(f"{self.name} initialized successfully")

    def shutdown(self) -> None:
        self.announce_to_assistive_tech(f"Shutting down {self.name}")
        # Shutdown code
        self.announce_to_assistive_tech(f"{self.name} shutdown complete")

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": "An accessible tool example",
            "capabilities": ["accessible_operations"]
        }

    def get_ipc_socket_documentation(self) -> Dict[str, Any]:
        return {
            "socket_endpoints": {
                "status": {
                    "path": "/api/v1/status",
                    "method": "GET",
                    "description": "Current tool status and health information",
                    "accessible_output": True,
                    "returns": {
                        "status": "Current operational status",
                        "progress": "Current progress percentage",
                        "errors": "Any current errors or warnings",
                        "estimated_completion": "Estimated time to completion"
                    }
                }
            },
            "accessibility_features": {
                "text_only_mode": True,
                "structured_output": True,
                "progress_reporting": True,
                "error_explanation": True,
                "screen_reader_integration": True,
                "braille_api_support": True
            }
        }

    @property
    def api_methods(self) -> Dict[str, Callable[..., Any]]:
        return {
            'get_status': self.get_accessible_status,
            'process_data': self.process_accessible_data
        }

    def run_standalone(self, args: List[str]) -> int:
        # Implement standalone execution
        self.announce_to_assistive_tech("Running in standalone mode")
        return 0

    def describe_usage(self) -> str:
        return "This tool provides accessible functionality for users with visual impairments."

    def process_accessible_data(self, data: Any) -> str:
        """Process data with accessibility considerations."""
        formatted_data = self.format_for_accessibility(data)
        self.announce_to_assistive_tech(f"Processing: {formatted_data}")
        # Process the data
        result = f"Processed {len(str(data))} characters"
        self.announce_to_assistive_tech(f"Processing complete: {result}")
        return result
```

### 4. Tool Naming Conventions

**Standard**: Use clear, descriptive tool names

```python
# Good tool names
class FileScannerTool(Tool):
    name = "FileScanner"

class DatabaseConnectorTool(Tool):
    name = "DatabaseConnector"

class NetworkMonitorTool(Tool):
    name = "NetworkMonitor"

# Avoid generic names
class Tool(Tool):  # Bad
    name = "Tool"
```

### 4. Tool Versioning

**Standard**: Use semantic versioning for tools

```python
class MyTool(Tool):
    version = "1.2.3"  # Major.Minor.Patch

    # Version components
    major = 1
    minor = 2
    patch = 3
```

### 5. Tool Dependencies

**Standard**: Declare all dependencies explicitly

```python
class MyTool(Tool):
    dependencies = [
        "database>=1.0.0",
        "network>=2.0.0",
        "utils>=1.5.0"
    ]
```

### 6. Tool Configuration

**Standard**: Use consistent configuration patterns

```python
class ConfigurableTool(Tool):
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.default_config = {
            'timeout': 30,
            'retries': 3,
            'enabled': True
        }

    def get_config(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
```

### 7. Tool Logging

**Standard**: Use consistent logging patterns

```python
import logging

class LoggedTool(Tool):
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def initialize(self, container: Any) -> None:
        self.logger.info(f"Initializing {self.name} v{self.version}")
        # Initialization code
        self.logger.info(f"{self.name} initialized successfully")

    def shutdown(self) -> None:
        self.logger.info(f"Shutting down {self.name}")
        # Shutdown code
        self.logger.info(f"{self.name} shutdown complete")
```

### 8. Tool Testing

**Standard**: All tools must include comprehensive tests

```python
# Test file structure
tests/
  tools/
    test_my_tool.py
    test_my_tool_integration.py
    test_my_tool_performance.py
```

### 9. Tool Performance

**Standard**: Tools must not block the main thread

```python
import threading
import asyncio

class PerformantTool(Tool):
    def __init__(self):
        self.thread = None
        self.loop = None

    def initialize(self, container: Any) -> None:
        # Start background thread for long-running operations
        self.thread = threading.Thread(target=self._background_task)
        self.thread.daemon = True
        self.thread.start()

    def _background_task(self) -> None:
        """Run long-running tasks in background"""
        while not self.shutdown_event.is_set():
            # Background processing
            time.sleep(1)
```

### 10. Tool Security

**Standard**: Tools must follow security best practices

```python
class SecureTool(Tool):
    def __init__(self):
        self.permissions = []
        self.sandboxed = False

    def initialize(self, container: Any) -> None:
        # Verify permissions
        self._check_permissions()

        # Enable sandboxing if required
        if self.requires_sandboxing():
            self._enable_sandboxing()

    def _check_permissions(self) -> None:
        """Check required permissions"""
        required_permissions = self.get_required_permissions()
        for permission in required_permissions:
            if not self.has_permission(permission):
                raise PermissionError(f"Missing required permission: {permission}")
```

### 11. Tool Compatibility

**Standard**: Tools must specify compatibility requirements

```python
class CompatibleTool(Tool):
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "compatible_versions": [">=1.0.0", "<2.0.0"],
            "python_version": ">=3.8",
            "platforms": ["linux", "darwin", "windows"]
        }
```

### 12. Tool Lifecycle Management

**Standard**: Properly manage tool lifecycle

```python
class LifecycleManagedTool(Tool):
    def __init__(self):
        self.initialized = False
        self.running = False
        self.shutdown_event = threading.Event()

    def initialize(self, container: Any) -> None:
        if self.initialized:
            return

        # Initialize resources
        self.container = container
        self._setup_resources()

        self.initialized = True

    def shutdown(self) -> None:
        if not self.initialized:
            return

        # Signal shutdown
        self.shutdown_event.set()

        # Clean up resources
        self._cleanup_resources()

        self.initialized = False
        self.running = False
```

### 13. Tool Error Recovery

**Standard**: Implement error recovery mechanisms

```python
class ErrorRecoveryTool(Tool):
    def __init__(self):
        self.error_count = 0
        self.max_errors = 5
        self.recovery_attempts = 0

    def handle_error(self, error: Exception) -> bool:
        """Handle errors with recovery attempts"""
        self.error_count += 1

        if self.error_count >= self.max_errors:
            self._trigger_recovery()
            return True

        return False

    def _trigger_recovery(self) -> None:
        """Trigger recovery mechanism"""
        self.recovery_attempts += 1
        logger.warning(f"Triggering recovery attempt {self.recovery_attempts}")

        # Implement recovery logic
        # Reset error count on successful recovery
        self.error_count = 0
```

### 14. Tool Monitoring

**Standard**: Include monitoring and health checks

```python
class MonitoredTool(Tool):
    def __init__(self):
        self.health_status = "unknown"
        self.metrics = {}

    def check_health(self) -> Dict[str, Any]:
        """Check tool health"""
        health = {
            "status": self.health_status,
            "metrics": self.metrics,
            "uptime": self.get_uptime(),
            "error_count": self.error_count
        }
        return health

    def get_uptime(self) -> float:
        """Get tool uptime in seconds"""
        return time.time() - self.start_time
```

### 15. Tool Communication

**Standard**: Use standard communication patterns

```python
class CommunicatingTool(Tool):
    def __init__(self):
        self.message_queue = []
        self.event_handlers = {}

    def send_message(self, message: Dict[str, Any]) -> None:
        """Send a message to other tools"""
        # Message sending logic
        pass

    def receive_message(self, message: Dict[str, Any]) -> None:
        """Receive a message from other tools"""
        # Message processing logic
        pass

    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
```

## Tool Development Checklist

### Before Development

- [ ] Define tool requirements and scope
- [ ] Identify stakeholders and their concerns (ISO/IEC/IEEE 42010)
- [ ] Check for existing similar tools
- [ ] Define tool interface and capabilities
- [ ] Plan tool dependencies
- [ ] Design tool architecture with ISO viewpoints in mind

### During Development

- [ ] Implement tool interface with ISO compliance methods
- [ ] Add proper error handling
- [ ] Include comprehensive logging
- [ ] Write unit tests with ISO compliance checks
- [ ] Write integration tests
- [ ] Add configuration support
- [ ] Implement security measures
- [ ] Add monitoring and health checks

### Before Release

- [ ] Run all tests including ISO compliance tests
- [ ] Check compatibility
- [ ] Update documentation with ISO sections
- [ ] Verify security
- [ ] Test performance
- [ ] Validate configuration
- [ ] Check dependencies

### After Release

- [ ] Monitor tool performance
- [ ] Collect user feedback
- [ ] Address issues and bugs
- [ ] Plan improvements
- [ ] Update documentation

## Tool Examples

### Basic Tool Example

```python
from nodupe.core.tool_system import Tool
import logging

class BasicTool(Tool):
    def __init__(self):
        self._name = "BasicTool"
        self._version = "1.0.0"
        self._dependencies = []
        self.logger = logging.getLogger(__name__)

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def dependencies(self) -> List[str]:
        return self._dependencies

    def initialize(self, container: Any) -> None:
        self.logger.info(f"Initializing {self.name} v{self.version}")
        # Initialization logic

    def shutdown(self) -> None:
        self.logger.info(f"Shutting down {self.name}")
        # Cleanup logic

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": "A basic tool example",
            "capabilities": ["basic_operation"],
            "iso_stakeholders": ["developer", "end_user"],
            "iso_concerns": ["functionality", "usability"]
        }

    def get_architecture_rationale(self) -> Dict[str, str]:
        return {
            "design_decision": "Created as a separate tool to maintain modularity",
            "alternatives_considered": "Considered integrating into core vs. keeping as tool",
            "tradeoffs": "Added complexity of tool management vs. gained flexibility",
            "stakeholder_impact": "Developers can maintain independently, users get focused functionality"
        }
```

### Advanced Tool Example

```python
from nodupe.core.tool_system import Tool
import logging
import threading
import time
from typing import Dict, Any, Callable

class AdvancedTool(Tool):
    def __init__(self, config: Dict[str, Any] = None):
        self._name = "AdvancedTool"
        self._version = "1.0.0"
        self._dependencies = ["database", "network"]
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Tool state
        self.initialized = False
        self.running = False
        self.shutdown_event = threading.Event()
        self.thread = None

        # Error handling
        self.error_count = 0
        self.max_errors = 10
        self.is_degraded = False
        self.is_disabled = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def dependencies(self) -> List[str]:
        return self._dependencies

    def initialize(self, container: Any) -> None:
        if self.initialized:
            return

        self.logger.info(f"Initializing {self.name} v{self.version}")

        try:
            # Initialize dependencies
            self.container = container
            self.database = container.get("database")
            self.network = container.get("network")

            # Initialize configuration
            self._init_config()

            # Start background thread
            self._start_background_thread()

            self.initialized = True
            self.running = True

            self.logger.info(f"{self.name} initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize {self.name}: {e}")
            raise

    def shutdown(self) -> None:
        if not self.initialized:
            return

        self.logger.info(f"Shutting down {self.name}")

        # Signal shutdown
        self.shutdown_event.set()

        # Stop background thread
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

        # Cleanup resources
        self._cleanup_resources()

        self.initialized = False
        self.running = False

        self.logger.info(f"{self.name} shutdown complete")

    def _init_config(self) -> None:
        """Initialize tool configuration"""
        default_config = {
            'timeout': 30,
            'retries': 3,
            'enabled': True,
            'background_interval': 60
        }

        for key, default_value in default_config.items():
            setattr(self, key, self.config.get(key, default_value))

    def _start_background_thread(self) -> None:
        """Start background processing thread"""
        self.thread = threading.Thread(target=self._background_task)
        self.thread.daemon = True
        self.thread.start()

    def _background_task(self) -> None:
        """Background processing task"""
        while not self.shutdown_event.is_set():
            try:
                # Background processing logic
                self._do_background_work()
                time.sleep(self.background_interval)
            except Exception as e:
                self.logger.error(f"Background task error: {e}")
                self.error_count += 1

                if self.error_count >= self.max_errors:
                    self.handle_critical_failure(e)
                    break

    def _do_background_work(self) -> None:
        """Perform background work"""
        # Background processing logic
        pass

    def _cleanup_resources(self) -> None:
        """Clean up tool resources"""
        # Cleanup logic
        pass

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": "An advanced tool example",
            "author": "Tool Author",
            "license": "MIT",
            "tags": ["advanced", "example"],
            "capabilities": [
                "background_processing",
                "error_handling",
                "configuration"
            ],
            "config": self.config,
            "health": {
                "initialized": self.initialized,
                "running": self.running,
                "error_count": self.error_count,
                "degraded": self.is_degraded,
                "disabled": self.is_disabled
            },
            "iso_stakeholders": ["developer", "operator", "end_user"],
            "iso_concerns": ["performance", "reliability", "maintainability"]
        }

    def get_architecture_rationale(self) -> Dict[str, str]:
        return {
            "design_decision": "Created as a background processing tool to handle long-running tasks",
            "alternatives_considered": "Considered synchronous vs. asynchronous processing",
            "tradeoffs": "Added complexity of thread management vs. gained non-blocking operation",
            "stakeholder_impact": "Users get responsive interface, operators get background processing"
        }

    def handle_critical_failure(self, error: Exception) -> None:
        """
        Handle critical failures with graceful shutdown.

        Standard Behavior:
        1. Log critical error with full context
        2. Attempt graceful degradation first
        3. If degradation fails, self-disable to prevent system spam
        4. Return appropriate fallback behavior

        Args:
            error: The critical error that occurred
        """
        self.logger.critical(f"CRITICAL: Tool {self.name} has encountered a critical failure: {error}")
        self.logger.critical(f"Tool state: errors={self.error_count}, degraded={self.is_degraded}")

        # First, try graceful degradation
        if not self.is_degraded:
            self._degrade_gracefully()
            self.logger.warning(f"Tool {self.name} has degraded to fallback mode")
            return

        # If already degraded and still failing, self-disable
        self.logger.critical(f"CRITICAL: Tool {self.name} is shutting down to prevent system degradation")
        self.disable()

    def _degrade_gracefully(self) -> None:
        """Degrade tool functionality gracefully"""
        self.is_degraded = True
        # Switch to fallback behavior
        # Reduce functionality but maintain core operations
        # Log degradation with clear indication
        self.logger.warning(f"Tool {self.name} degrading to fallback mode")

    def disable(self) -> None:
        """
        Disable tool to prevent system degradation.

        Standard Behavior:
        1. Stop all background operations
        2. Clean up resources
        3. Set disabled state
        4. Log shutdown with clear message
        """
        self.is_disabled = True
        self.shutdown()
        self.logger.critical(f"Tool {self.name} has been disabled. System will use fallback behavior.")

    def get_fallback_result(self, operation: str, *args, **kwargs) -> Any:
        """
        Provide fallback result when tool is degraded or disabled.

        Args:
            operation: The operation that failed
            *args, **kwargs: Operation arguments

        Returns:
            Fallback result appropriate for the operation
        """
        if operation == "timestamp":
            return time.monotonic()  # Fallback to monotonic time
        elif operation == "data":
            return {}  # Fallback to empty data
        # Implement appropriate fallbacks for each operation type

        return None
```

## Tool Development Tools

### Tool Development Environment

Set up a development environment for tool development:

```bash
# Create virtual environment
python -m venv tool_dev_env
source tool_dev_env/bin/activate  # On Windows: tool_dev_env\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install tool development tools
pip install pytest pytest-cov flake8 mypy black
```

### Tool Development Scripts

```bash
# Development scripts
scripts/
  tool_dev/
    setup_dev_env.sh
    run_tests.sh
    check_style.sh
    generate_docs.sh
    package_tool.sh
```

### Tool Development Workflow

1. **Setup**: Set up development environment
2. **Develop**: Implement tool functionality with ISO compliance
3. **Test**: Run tests and check style including ISO compliance tests
4. **Document**: Ensure ISO/IEC/IEEE 42010 compliance documentation
5. **Package**: Package tool for distribution
6. **Deploy**: Deploy tool to production

## Tool Development Resources

### Documentation

- [Tool System Architecture](ARCHITECTURE.md)
- [Tool API Reference](API.md)
- [Tool Examples](examples/)
- [Tool Best Practices](BEST_PRACTICES.md)
- [ISO/IEC/IEEE 42010 Compliance Guide](ISO_COMPLIANCE.md)
- [Accessibility Guidelines for Visual Impairment Support](ACCESSIBILITY_GUIDELINES.md)
- [Python Accessibility Standards and Libraries](PYTHON_ACCESSIBILITY_STANDARDS.md)

### Tools

- [Tool Development Kit](tools/pdk/)
- [Tool Testing Framework](tools/testing/)
- [Tool Documentation Generator](tools/docs/)

### Community

- [Tool Development Forum](https://forum.nodupelabs.com/tools)
- [Tool Development Chat](https://chat.nodupelabs.com/tools)
- [Tool Development Wiki](https://wiki.nodupelabs.com/tools)

## Conclusion

This tool development guide provides comprehensive coverage of tool development for the NoDupeLabs system with explicit alignment to ISO/IEC/IEEE 42010 architecture description standards and accessibility requirements for users with visual impairments. Follow these guidelines and best practices to create high-quality, maintainable, and accessible tools that integrate seamlessly with the system and comply with international standards.

The architecture is designed with inclusivity in mind, ensuring that no user is denied access to the software due to visual impairments or other disabilities. All tools must support assistive technologies such as screen readers, braille displays, and voice navigation systems.

For additional support and resources, refer to the documentation, tools, and community resources listed above.
