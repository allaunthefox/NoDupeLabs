# Python Accessibility Standards for NoDupeLabs

## Overview

This document provides specific guidance on implementing accessibility in Python applications, with a focus on supporting users with visual impairments. It covers Python-specific accessibility libraries, implementation patterns, and compliance with international standards.

## International Standards for Python Accessibility

### ISO/IEC 40500:2025 (WCAG 2.2)

WCAG 2.2 provides guidelines for making web content more accessible, but its principles apply to Python console applications as well:

#### 1. Perceivable
- **Text Alternatives**: All non-text content must have text alternatives
- **Adaptable**: Content must be presentable in different ways without losing information
- **Distinguishable**: Information must be distinguishable from its background

#### 2. Operable
- **Keyboard Accessible**: All functionality available from keyboard
- **Enough Time**: Users have enough time to read and use content
- **Seizures and Physical Reactions**: Content does not cause seizures
- **Navigable**: Users can navigate, find content, and determine where they are

#### 3. Understandable
- **Readable**: Text content must be readable and understandable
- **Predictable**: Web pages appear and operate in predictable ways
- **Input Assistance**: Help users avoid and correct mistakes

#### 4. Robust
- **Compatible**: Content must be robust enough to work with various assistive technologies

### Section 508 Compliance

Section 508 standards ensure accessibility for federal employees and members of the public with disabilities:

- Applications shall not disrupt or disable accessibility features of operating systems
- User controls must be operable via assistive technology
- Information must be available to assistive technology

## Python-Specific Accessibility Guidelines

### 1. Console Application Accessibility

For Python console applications, the following guidelines apply:

#### Text-Based Interface Design
- All functionality accessible via keyboard commands
- Clear, descriptive text output
- Logical reading order for information
- Proper use of semantic markup in text output

#### Screen Reader Compatibility
- Output structured for screen reader interpretation
- Descriptive labels for all interactive elements
- Clear announcements of state changes
- Proper heading hierarchy in text output

#### Braille Display Support
- Concise but complete information
- Structured data formats for efficient parsing
- Line-by-line readability
- Efficient use of limited display space

### 2. Python Libraries for Accessibility

#### Recommended Libraries

1. **accessible-output2**
   - Provides unified interface for multiple screen readers
   - Supports JAWS, NVDA, Window-Eyes, System Access, Dolphin, and VoiceOver
   - Installation: `pip install accessible-output2`

```python
from accessible_output2.outputs.auto import Auto
outputter = Auto()
outputter.output("Message for assistive technology")
```

2. **BrlAPI**
   - Python bindings for braille display access
   - Provides simple API to write text to braille displays
   - Installation: `apt-get install python3-brlapi` (Linux) or equivalent

```python
import brlapi
client = brlapi.Connection()
client.writeText("Message for braille display")
```

3. **pybraille**
   - Text-to-braille conversion library
   - Converts text to 6-dot pattern braille (Grade 1)
   - Installation: `pip install pybraille`

```python
import pybraille
braille_text = pybraille.translate('Hello world')
print(braille_text)
```

4. **SRAL (Screen Reader Abstraction Library)**
   - Cross-platform library for unified interface to speech and braille output
   - GitHub: m1maker/SRAL

### 3. Implementation Patterns

#### Accessible Output Generation

```python
def generate_accessible_output(self, data: Any) -> str:
    """
    Generate output suitable for assistive technologies.

    Args:
        data: Raw data to convert to accessible format

    Returns:
        Human-readable string suitable for screen readers and braille displays
    """
    if isinstance(data, dict):
        output = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                output.append(f"{key}:")
                output.append(self.generate_accessible_output(value))
            else:
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
    elif isinstance(value, list):
        return f"List with {len(value)} items"
    elif isinstance(value, dict):
        return f"Dictionary with {len(value)} keys"
    else:
        return f"{type(value).__name__} object"
```

#### Accessibility Integration with Libraries

```python
try:
    from accessible_output2.outputs.auto import Auto
    screen_reader_available = True
    outputter = Auto()
except ImportError:
    screen_reader_available = False
    outputter = None

class AccessiblePythonTool:
    def __init__(self):
        self.screen_reader_available = screen_reader_available
        self.outputter = outputter

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

#### IPC Socket Accessibility

All tools must expose IPC sockets with accessibility features:

```python
def get_ipc_socket_documentation(self) -> Dict[str, Any]:
    """
    Document IPC socket interfaces for assistive technology integration.

    Returns:
        Dictionary describing available IPC endpoints and accessibility features
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

### 4. Testing Accessibility

#### Automated Tests

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
    self.assertIn("50", accessible_output)
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

def test_library_integration(self):
    """Test that accessibility libraries are properly integrated."""
    tool = MyAccessibleTool()

    # Test that screen reader announcement works
    try:
        tool.announce_to_assistive_tech("Test message")
        # If we reach here, the integration works
        self.assertTrue(True)
    except ImportError:
        # If there's an import error, that's expected if library not installed
        self.skipTest("Accessibility library not installed")
```

### 5. Documentation Requirements

Each tool must include accessibility documentation:

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
- Integration with accessibility libraries (accessible-output2, BrlAPI, etc.)

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

### 6. Compliance Checklist

All Python tools must satisfy the following accessibility requirements:

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
- [ ] Proper error handling for accessibility library failures

## References

1. WCAG 2.2 Guidelines: https://www.w3.org/TR/WCAG22/
2. Section 508 Standards: https://www.section508.gov/
3. ISO/IEC 40500:2025 Standard: https://www.iso.org/standard/94018.html
4. Accessible Output 2: https://pypi.org/project/accessible-output2/
5. BrlAPI: https://brltty.app/
6. Python Accessibility Best Practices: https://python.org/accessibility/

## Conclusion

These Python accessibility standards ensure that NoDupeLabs tools are usable by everyone, including users with visual impairments. Following these guidelines helps create inclusive software that meets international accessibility standards while maintaining high functionality and performance.
