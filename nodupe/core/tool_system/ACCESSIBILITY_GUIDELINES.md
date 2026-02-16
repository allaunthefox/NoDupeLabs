# Accessibility Guidelines for NoDupeLabs Tools

## Overview

This document outlines the accessibility requirements and guidelines for NoDupeLabs tools to ensure equal access for users with visual impairments. All tools must comply with these guidelines to support users who rely on assistive technologies such as screen readers, braille displays, and voice navigation systems.

This document incorporates international standards including:
- **ISO/IEC 40500:2025** (identical to WCAG 2.2) - Web Content Accessibility Guidelines
- **Section 508** - US federal accessibility standards
- **ISO 25010** - Systems and software quality requirements and evaluation (with accessibility considerations)

## Legal and Ethical Framework

The NoDupeLabs project is committed to inclusive design principles and follows accessibility standards to ensure that no user is denied access to the software due to visual impairments or other disabilities. This commitment aligns with international accessibility standards and promotes digital inclusion.

## Core Accessibility Requirements

### 0. Accessibility as Core Requirement

**CRITICAL REQUIREMENT**: Accessibility is a fundamental, non-negotiable requirement for all tools that process user data or provide user-facing functionality. Accessibility features MUST NOT be treated as optional or removable components. Even if external accessibility libraries are not available, tools MUST provide basic accessibility through console output.

### 1. Text-Based Interface Design

All tools must provide full functionality through text-based interfaces that are navigable via keyboard commands. Visual elements should have text alternatives.

**Implementation Requirements:**
- All features accessible via keyboard shortcuts
- Menu systems navigable without mouse input
- Clear text labels for all controls and options
- Status messages in text format

### 2. Screen Reader Compatibility

All tool output must be structured in a way that is interpretable by screen readers.

**Implementation Requirements:**
- Semantic markup in any displayed text
- Logical reading order for information
- Descriptive labels for all interactive elements
- Clear announcements of state changes

### 3. Braille Display Support

Text output must be suitable for braille displays, which have limited character display capacity.

**Implementation Requirements:**
- Concise but complete information
- Structured data that can be parsed efficiently
- Meaningful abbreviated forms where appropriate
- Line-by-line readability

### 4. Voice Navigation Compatibility

Tools should support voice command interfaces for users who navigate primarily through speech.

**Implementation Requirements:**
- Command-based operation mode
- Clear, predictable command structure
- Audio feedback for operations
- Speech synthesis compatibility

## Python-Specific Accessibility Standards

### WCAG 2.2 Guidelines Applied to Console Applications

The following WCAG 2.2 principles apply to Python console applications:

1. **Perceivable**: Information must be presentable in ways that users can perceive
   - Provide text alternatives for non-text content
   - Ensure content can be presented in different ways (e.g., simpler layout)
   - Make it easier for users to see and hear content

2. **Operable**: Interface components must be operable by all users
   - Make all functionality available from a keyboard
   - Give users enough time to read and use content
   - Do not design content in a way that is known to cause seizures
   - Provide ways to help users navigate, find content, and determine where they are

3. **Understandable**: Information and UI operation must be understandable
   - Make text readable and understandable
   - Make web pages appear and operate in predictable ways
   - Help users avoid and correct mistakes

4. **Robust**: Content must be robust enough to work with various assistive technologies
   - Maximize compatibility with current and future user tools

### Section 508 Compliance for Python Applications

Python applications must meet the following Section 508 standards:

- **1194.21 Software applications and operating systems**: Applications shall not disrupt or disable activated features of other products that are identified as accessibility features.
- **1194.22 Web-based intranet and internet information and applications**: When software applications use web technologies, they must comply with web accessibility standards.
- **1194.31 Functional performance criterion**: Products must operate in ways that do not require user vision, user hearing, or user manual dexterity.

## Python Libraries for Accessibility

### Recommended Libraries

The following Python libraries support accessibility features:

#### 1. accessible-output2
- **Purpose**: Provides a unified interface for speaking and brailling through multiple screen readers
- **Installation**: `pip install accessible-output2`
- **Usage**: Enables output to multiple screen readers and accessibility systems

```python
from accessible_output2.outputs.auto import Auto
outputter = Auto()
outputter.output("Hello, world!")
```

#### 2. BrlAPI Python Bindings
- **Purpose**: Provides access to braille displays
- **Installation**: `apt-get install python3-brlapi` (Ubuntu/Debian) or equivalent
- **Usage**: Allows applications to write text to braille displays

```python
import brlapi
client = brlapi.Connection()
client.writeText("Hello, braille user!")
```

#### 3. pybraille
- **Purpose**: Converts text to 6-dot pattern braille (Grade 1)
- **Installation**: `pip install pybraille`
- **Usage**: Simple text-to-braille conversion

```python
import pybraille
braille_text = pybraille.translate('Hello world')
print(braille_text)
```

#### 4. SRAL (Screen Reader Abstraction Library)
- **Purpose**: Cross-platform library for unified interface to speech and braille output
- **GitHub**: m1maker/SRAL
- **Usage**: Provides abstraction layer for multiple screen readers

## IPC Socket Accessibility Standards

All tools must expose IPC (Inter-Process Communication) sockets with specific accessibility features to enable integration with assistive technologies.

### Required IPC Endpoints

#### Status Endpoint
```
GET /api/v1/status
```
Returns current tool status in accessible format:
- Plain text status description
- Progress percentage as numeric value
- Error messages in clear, descriptive text
- Estimated completion time in human-readable format

#### Operations Endpoint
```
POST /api/v1/operations
```
Accepts operations with accessible progress reporting:
- Text-based operation parameters
- Detailed progress reporting
- Clear error responses

#### Logs Endpoint
```
GET /api/v1/logs
```
Provides accessible log information:
- Structured log entries
- Clear timestamps
- Descriptive log messages

### Accessibility Features for IPC

1. **Text-Only Mode**: All endpoints support text-only responses without visual elements
2. **Structured Output**: Use consistent, parseable data structures (JSON, CSV, etc.)
3. **Progress Reporting**: Provide detailed progress information for long-running operations
4. **Error Explanation**: Provide clear, descriptive error messages for screen readers
5. **Keyboard Navigation**: All interactive features accessible via keyboard commands

## Implementation Patterns

### Accessible Output Generation

Tools should implement methods to generate accessible output:

```python
def generate_accessible_output(self, data: Any) -> str:
    """
    Generate output that is suitable for assistive technologies.
    
    Args:
        data: Raw data to convert to accessible format
        
    Returns:
        Human-readable string suitable for screen readers and braille displays
    """
    if isinstance(data, dict):
        output = []
        for key, value in data.items():
            output.append(f"{key}: {self.describe_value(value)}")
        return "\n".join(output)
    elif isinstance(data, list):
        output = []
        for i, item in enumerate(data):
            output.append(f"Item {i + 1}: {self.describe_value(item)}")
        return "\n".join(output)
    else:
        return str(data)

def describe_value(self, value: Any) -> str:
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
```

### Accessibility Integration with Python Libraries

Tools should integrate with accessibility libraries when available:

```python
try:
    from accessible_output2.outputs.auto import Auto
    screen_reader_available = True
    outputter = Auto()
except ImportError:
    screen_reader_available = False
    outputter = None

class AccessibleTool(Tool):
    def __init__(self):
        self.screen_reader_available = screen_reader_available
        self.outputter = outputter
        self.accessibility_features = {
            "keyboard_navigable": True,
            "screen_reader_compatible": True,
            "braille_display_supported": True,
            "voice_navigation_ready": True
        }

    def announce_to_assistive_tech(self, message: str):
        """Announce a message to assistive technologies when available."""
        if self.screen_reader_available and self.outputter:
            try:
                self.outputter.output(message)
            except:
                # Fallback to standard output if screen reader fails
                print(message)
        else:
            print(message)
```

### IPC Documentation Template

Each tool must provide comprehensive IPC documentation:

```python
def get_ipc_documentation(self) -> Dict[str, Any]:
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
            "error_explanation": True,
            "screen_reader_integration": True,
            "braille_api_support": True
        }
    }
```

## Testing Accessibility

### Automated Tests

All tools must include automated accessibility tests:

```python
def test_screen_reader_compatibility(self):
    """Test that tool output is compatible with screen readers."""
    tool = MyAccessibleTool()
    sample_data = {"status": "running", "progress": 50, "items_processed": 100}
    accessible_output = tool.generate_accessible_output(sample_data)
    
    # Verify output is readable and descriptive
    self.assertIn("status:", accessible_output)
    self.assertIn("running", accessible_output)
    self.assertIn("progress:", accessible_output)
    self.assertIn("items_processed:", accessible_output)

def test_braille_display_compatibility(self):
    """Test that output is suitable for braille displays."""
    tool = MyAccessibleTool()
    sample_data = {"status": "completed", "results": 42}
    accessible_output = tool.generate_accessible_output(sample_data)
    
    # Braille displays have limited space, so output should be concise but complete
    lines = accessible_output.split('\n')
    for line in lines:
        # Each line should be meaningful when read individually
        self.assertGreater(len(line.strip()), 0)

def test_ipc_documentation_exists(self):
    """Test that IPC socket documentation is available."""
    tool = MyAccessibleTool()
    ipc_doc = tool.get_ipc_documentation()
    
    # Verify documentation structure
    self.assertIn("socket_endpoints", ipc_doc)
    self.assertIn("accessibility_features", ipc_doc)
    
    # Verify accessibility features are documented
    features = ipc_doc["accessibility_features"]
    self.assertTrue(features["text_only_mode"])
    self.assertTrue(features["structured_output"])

def test_library_integration(self):
    """Test that accessibility libraries are properly integrated."""
    tool = MyAccessibleTool()
    
    # Test that screen reader announcement works
    try:
        tool.announce_to_assistive_tech("Test message")
        # If we reach here, the integration works
        self.assertTrue(True)
    except Exception as e:
        # If there's an exception, check if it's expected (library not available)
        self.assertIn("accessible_output2", str(e))  # Expected if library not installed
```

## Documentation Requirements

### Accessibility Statement

Each tool must include an accessibility statement in its documentation:

```markdown
## Accessibility Statement

This tool is designed to be accessible to users with visual impairments and compatible with assistive technologies including:

- Screen readers (JAWS, NVDA, VoiceOver, etc.) via accessible-output2 library
- Braille displays via BrlAPI integration
- Voice navigation systems
- Keyboard-only navigation

### Features for Accessibility

- All functionality available through keyboard commands
- Descriptive text output suitable for screen readers
- Structured data formats for assistive technology parsing
- Progress reporting for long-running operations
- Clear, descriptive error messages
- High contrast terminal output (where applicable)
- Integration with accessibility libraries (accessible-output2, BrlAPI)

### IPC Integration

The tool exposes the following endpoints for assistive technology integration:

- `/api/v1/status` - Current status and progress information
- `/api/v1/operations` - Operation initiation with progress tracking
- `/api/v1/logs` - Accessible log information

See [IPC Documentation](ipc.md) for full details.

### Compliance Standards

This tool complies with:
- WCAG 2.2 (ISO/IEC 40500:2025) guidelines
- Section 508 accessibility standards
- ISO 25010 quality model (accessibility considerations)
```

## Compliance Checklist

All tools must satisfy the following accessibility requirements:

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
- [ ] Clear accessibility statement in documentation
- [ ] Integration with accessibility libraries (accessible-output2, BrlAPI, etc.)
- [ ] WCAG 2.2 compliance verification
- [ ] Section 508 compliance verification

## Training and Awareness

Developers working on NoDupeLabs tools should familiarize themselves with accessibility principles and the needs of users with visual impairments. Understanding how assistive technologies work will help create more accessible tools.

Resources for learning:
- WCAG 2.2 guidelines (https://www.w3.org/TR/WCAG22/)
- Section 508 standards (https://www.section508.gov/)
- Python accessibility libraries documentation
- Assistive technology user experiences

## Continuous Improvement

Accessibility is an ongoing commitment. Regular reviews and updates to accessibility features ensure continued support for users with visual impairments as technology and standards evolve.

## Accessibility Action Codes

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

## Additional Resources

For detailed information on Python-specific accessibility implementation, see:
- [Python Accessibility Standards and Libraries](PYTHON_ACCESSIBILITY_STANDARDS.md)

## Contact Information

For questions or suggestions regarding accessibility, please contact the NoDupeLabs accessibility team.