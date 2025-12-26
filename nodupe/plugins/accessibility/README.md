# Accessibility Plugin

The Accessibility plugin provides comprehensive accessibility features for the NoDupeLabs system, ensuring the application is usable by people with various disabilities and accessibility needs. This plugin includes dyslexia support, visual accessibility options, screen reader support, keyboard navigation enhancements, and cognitive accessibility tools.

## Features

### 🧠 **Dyslexia Support**
- **Dyslexia-friendly fonts**: OpenDyslexic font support
- **Text formatting**: Increased line spacing and letter spacing
- **Simplified language**: Automatic replacement of complex words
- **Visual organization**: Bullet points and clear paragraph separation

### 👀 **Visual Accessibility**
- **High contrast modes**: Multiple contrast levels (Normal, High, Maximum)
- **Font size control**: Small, Medium, Large, Extra Large options
- **Color customization**: Custom color schemes for different needs
- **Motion reduction**: Option to reduce animations and motion

### 🗣️ **Screen Reader Support**
- **ARIA labels**: Automatic generation of ARIA labels
- **Focus indicators**: Clear visual focus indicators
- **Skip navigation**: Keyboard shortcuts to skip navigation
- **Context descriptions**: Enhanced context for screen readers

### ⌨️ **Keyboard Navigation**
- **Enhanced shortcuts**: Comprehensive keyboard shortcut system
- **Tab order control**: Configurable tab navigation order
- **Focus management**: Improved focus handling
- **Keyboard-only mode**: Complete keyboard navigation support

### 🧩 **Cognitive Accessibility**
- **Simplified UI**: Reduced complexity interface mode
- **Clear instructions**: Step-by-step guidance
- **Progress indicators**: Clear progress feedback
- **Error messages**: Clear, helpful error messages

### 🔊 **Text-to-Speech**
- **Voice output**: Convert text to speech
- **Rate control**: Adjustable speech rate
- **Volume control**: Adjustable volume levels
- **Voice selection**: Multiple voice options

### 🎛️ **Customizable Profiles**
- **Pre-built profiles**: Default profiles for common needs
- **Custom profiles**: Create and save personalized settings
- **Profile switching**: Quick switching between profiles
- **Settings persistence**: Automatic saving and loading of preferences

## Installation

The Accessibility plugin is included with NoDupeLabs and requires no additional dependencies.

## Quick Start

### Basic Usage

```python
from nodupe.plugins.accessibility import AccessibilityPlugin

# Create plugin instance
plugin = AccessibilityPlugin()

# Initialize the plugin
plugin.initialize(container=None)

# Enable accessibility features
plugin.update_settings({'enabled': True})

# Set dyslexia-friendly mode
plugin.update_settings({
    'mode': 'dyslexia_friendly',
    'dyslexia_font': True,
    'line_spacing': 1.8,
    'font_size': 'large'
})
```

### Using Pre-built Profiles

```python
# Load high contrast profile
plugin.load_profile('high_contrast')

# Load dyslexia-friendly profile
plugin.load_profile('dyslexia_friendly')

# Load screen reader profile
plugin.load_profile('screen_reader')

# Load keyboard navigation profile
plugin.load_profile('keyboard_only')

# Load simplified UI profile
plugin.load_profile('simplified')
```

## Detailed Usage

### Accessibility Modes

The plugin supports several accessibility modes:

```python
from nodupe.plugins.accessibility import AccessibilityMode

# Set different modes
plugin.update_settings({'mode': 'normal'})           # Standard mode
plugin.update_settings({'mode': 'high_contrast'})    # High contrast mode
plugin.update_settings({'mode': 'dyslexia_friendly'}) # Dyslexia support
plugin.update_settings({'mode': 'screen_reader'})    # Screen reader mode
plugin.update_settings({'mode': 'keyboard_only'})    # Keyboard navigation
plugin.update_settings({'mode': 'simplified'})       # Simplified UI
```

### Visual Settings

```python
# Font size control (enum-based)
plugin.update_settings({'font_size': 'small'})    # 12px
plugin.update_settings({'font_size': 'medium'})   # 14px (default)
plugin.update_settings({'font_size': 'large'})    # 18px
plugin.update_settings({'font_size': 'extra_large'}) # 24px

# Custom font size (pixel-based)
plugin.set_custom_font_size(20)  # 20px
plugin.set_custom_font_size(28)  # 28px
plugin.set_custom_font_size(36)  # 36px

# Contrast levels
plugin.update_settings({'contrast': 'normal'})    # Standard colors
plugin.update_settings({'contrast': 'high'})      # High contrast
plugin.update_settings({'contrast': 'maximum'})   # Maximum contrast

# Custom colors
plugin.update_settings({
    'custom_colors': {
        'background': '#000000',
        'text': '#FFFFFF',
        'accent': '#FFFF00',
        'link': '#00FFFF'
    }
})

# Reduce motion
plugin.update_settings({'reduce_motion': True})
```

### Custom Font Spacing

```python
# Line spacing control
plugin.update_settings({'line_spacing': 1.5})  # 1.5x line height (default)
plugin.update_settings({'line_spacing': 2.0})  # 2.0x line height

# Custom line spacing
plugin.set_custom_line_spacing(1.8)  # 1.8x line height
plugin.set_custom_line_spacing(2.2)  # 2.2x line height

# Letter spacing control
plugin.update_settings({'letter_spacing': 0.12})  # 0.12em (default)
plugin.update_settings({'letter_spacing': 0.20})  # 0.20em

# Custom letter spacing
plugin.set_custom_letter_spacing(0.15)  # 0.15em
plugin.set_custom_letter_spacing(0.25)  # 0.25em

# Clear custom settings and revert to defaults
plugin.clear_custom_font_settings()
```

### Font Settings Management

```python
# Get current font settings
font_settings = plugin.get_font_settings()
print(font_settings)
# Output: {
#     'size': 18,
#     'family': 'OpenDyslexic',
#     'line_spacing': 1.8,
#     'letter_spacing': 0.15,
#     'alignment': 'left',
#     'custom_font_size': None,
#     'custom_line_spacing': None,
#     'custom_letter_spacing': None
# }

# Check if using custom font size
if font_settings['custom_font_size'] is not None:
    print(f"Using custom font size: {font_settings['custom_font_size']}px")
else:
    print(f"Using enum font size: {font_settings['size']}px")

# Combine custom settings
plugin.set_custom_font_size(22)
plugin.set_custom_line_spacing(2.0)
plugin.set_custom_letter_spacing(0.20)

# Get updated settings
font_settings = plugin.get_font_settings()
print(f"Custom font size: {font_settings['custom_font_size']}px")
print(f"Custom line spacing: {font_settings['custom_line_spacing']}x")
print(f"Custom letter spacing: {font_settings['custom_letter_spacing']}em")
```

### Dyslexia Support

```python
# Enable dyslexia-friendly features
plugin.update_settings({
    'dyslexia_font': True,
    'dyslexia_font_size': 18,
    'line_spacing': 1.8,
    'letter_spacing': 0.15,
    'text_alignment': 'left'
})

# Format text for dyslexia
text = "This is a complex sentence with difficult words."
formatted = plugin.format_text_for_dyslexia(text)
print(formatted)
# Output: "This is a simple sentence with hard words."

# Simplify text for cognitive accessibility
simplified = plugin.simplify_text(text, level=2)
print(simplified)
# Output: "This is a simple sentence with hard words."
```

### Screen Reader Support

```python
# Enable screen reader features
plugin.update_settings({
    'screen_reader_enabled': True,
    'aria_labels': True,
    'skip_navigation': True,
    'focus_indicators': True
})

# Generate screen reader text
content = "Click here to continue"
sr_text = plugin.generate_screen_reader_text(content, "Navigation link")
print(sr_text)
# Output: "To skip navigation, press Alt+Shift+N. Navigation link. Click here to continue"

# Add ARIA labels
labeled_text = plugin.add_aria_labels("Important information", "Alert message")
print(labeled_text)
# Output: "<span aria-label='Alert message' role='text'>Important information</span>"
```

### Keyboard Navigation

```python
# Enable keyboard navigation
plugin.update_settings({
    'keyboard_navigation': True,
    'shortcuts_enabled': True
})

# Get available shortcuts
shortcuts = plugin.get_keyboard_shortcuts()
print(shortcuts)
# Output: {
#     'focus_search': 'Ctrl+F',
#     'skip_navigation': 'Alt+Shift+N',
#     'increase_font': 'Ctrl+Plus',
#     'decrease_font': 'Ctrl+Minus',
#     'reset_font': 'Ctrl+0',
#     'high_contrast': 'Ctrl+Shift+C',
#     'dyslexia_mode': 'Ctrl+Shift+D',
#     'screen_reader_mode': 'Ctrl+Shift+S'
# }

# Handle keyboard shortcuts
handled = plugin.handle_keyboard_shortcut('Ctrl+Shift+C')
print(f"Handled: {handled}")  # True

# Get focus order
focus_order = plugin.get_focus_order()
print(focus_order)
# Output: ['main_navigation', 'search_bar', 'content_area', 'sidebar', 'footer']
```

### Text-to-Speech

```python
# Enable text-to-speech
plugin.update_settings({
    'tts_enabled': True,
    'tts_rate': 1.2,
    'tts_volume': 0.8,
    'tts_voice': 'default'
})

# Convert text to speech
text = "Hello, this is text-to-speech output."
success = plugin.text_to_speech(text)
print(f"TTS successful: {success}")

# Use custom settings
success = plugin.text_to_speech(
    text,
    rate=1.5,
    volume=1.0,
    voice='en-US-JennyNeural'
)
```

### Profile Management

```python
# Create a custom profile
custom_settings = AccessibilitySettings(
    mode=AccessibilityMode.HIGH_CONTRAST,
    font_size=FontSize.LARGE,
    dyslexia_font=True,
    line_spacing=2.0,
    contrast=ContrastLevel.MAXIMUM
)

plugin.create_profile('my_custom_profile', custom_settings)

# List all profiles
profiles = plugin.list_profiles()
print(profiles)
# Output: ['default', 'high_contrast', 'dyslexia_friendly', 'screen_reader', 'keyboard_only', 'simplified', 'my_custom_profile']

# Load a profile
plugin.load_profile('my_custom_profile')

# Get profile settings
profile_settings = plugin.get_profile('high_contrast')
print(profile_settings.to_dict())

# Delete a profile
plugin.delete_profile('my_custom_profile')
```

### Event Handling

```python
# Add settings change listener
def on_settings_change(settings):
    print(f"Settings changed: {settings.to_dict()}")

plugin.add_listener(on_settings_change)

# Update settings (will trigger listener)
plugin.update_settings({'font_size': 'large'})

# Remove listener
plugin.remove_listener(on_settings_change)
```

### Content Analysis

```python
# Analyze content accessibility
content = """
<h1>Main Title</h1>
<p>This is a paragraph with a <a href="#">click here</a> link.</p>
<img src="image.jpg">
"""

score = plugin.get_accessibility_score(content)
print(f"Accessibility score: {score['score']}")
print(f"Issues: {score['issues']}")
print(f"Recommendations: {score['recommendations']}")

# Output:
# Accessibility score: 80
# Issues: ['Missing alt text for images', 'Non-descriptive link text']
# Recommendations: ['Add descriptive alt text to all images', 'Use descriptive link text that explains the destination']
```

### Settings Validation

```python
# Validate settings
settings = AccessibilitySettings(
    dyslexia_font_size=40,  # Invalid: too large
    line_spacing=0.5,       # Invalid: too small
    text_alignment='center'
)

errors = plugin.validate_settings(settings)
print(f"Validation errors: {errors}")
# Output: ['Dyslexia font size must be between 10 and 36', 'Line spacing must be between 1.0 and 3.0']
```

## Advanced Features

### Custom Text Processing

```python
# Create custom dyslexia word replacements
def custom_dyslexia_format(text):
    custom_replacements = {
        "specific": "exact",
        "analysis": "study",
        "methodology": "method"
    }
    
    for difficult, simple in custom_replacements.items():
        text = text.replace(difficult, simple)
    
    return text

# Apply custom formatting
text = "This specific analysis uses a complex methodology."
formatted = custom_dyslexia_format(text)
print(formatted)
# Output: "This exact study uses a complex method."
```

### Dynamic Color Schemes

```python
# Get color scheme for contrast level
colors = plugin.get_contrast_colors(ContrastLevel.HIGH)
print(colors)
# Output: {
#     'background': '#000000',
#     'text': '#FFFFFF',
#     'accent': '#FFFF00',
#     'link': '#00FFFF'
# }

# Apply custom color scheme
plugin.update_settings({
    'custom_colors': {
        'background': '#1a1a1a',
        'text': '#e6e6e6',
        'accent': '#4da6ff',
        'link': '#66ffcc'
    }
})
```

### Font Settings

```python
# Get current font settings
font_settings = plugin.get_font_settings()
print(font_settings)
# Output: {
#     'size': 18,
#     'family': 'OpenDyslexic',
#     'line_spacing': 1.8,
#     'letter_spacing': 0.15,
#     'alignment': 'left'
# }
```

### Integration with UI Systems

```python
# Example integration with a hypothetical UI system
class AccessibilityUI:
    def __init__(self, accessibility_plugin):
        self.plugin = accessibility_plugin
        self.plugin.add_listener(self.on_settings_change)
    
    def on_settings_change(self, settings):
        """Apply settings to UI components."""
        # Update font settings
        font_settings = self.plugin.get_font_settings()
        self.apply_font_settings(font_settings)
        
        # Update colors
        colors = self.plugin.get_contrast_colors(settings.contrast)
        self.apply_colors(colors)
        
        # Update other settings
        self.apply_ui_settings(settings)
    
    def apply_font_settings(self, font_settings):
        """Apply font settings to UI."""
        # Implementation would update UI fonts
        pass
    
    def apply_colors(self, colors):
        """Apply color settings to UI."""
        # Implementation would update UI colors
        pass
    
    def apply_ui_settings(self, settings):
        """Apply other UI settings."""
        # Implementation would update other UI aspects
        pass
```

## Best Practices

### 1. Progressive Enhancement
```python
# Start with basic accessibility
plugin.update_settings({'enabled': True})

# Add specific features as needed
plugin.update_settings({'dyslexia_font': True})
plugin.update_settings({'high_contrast': True})
```

### 2. User Preferences
```python
# Respect user preferences
def load_user_preferences():
    # Load from user settings or browser preferences
    return {
        'font_size': 'large',
        'contrast': 'high',
        'dyslexia_font': True
    }

user_prefs = load_user_preferences()
plugin.update_settings(user_prefs)
```

### 3. Testing
```python
# Test accessibility features
def test_accessibility():
    # Test dyslexia formatting
    text = "This is a difficult sentence with complex words."
    formatted = plugin.format_text_for_dyslexia(text)
    assert "hard" in formatted
    assert "simple" in formatted
    
    # Test keyboard shortcuts
    handled = plugin.handle_keyboard_shortcut('Ctrl+Shift+C')
    assert handled == True
    
    # Test TTS
    success = plugin.text_to_speech("Test message")
    assert success == True

test_accessibility()
```

### 4. Performance
```python
# Use profiles for quick switching
plugin.create_profile('performance_mode', AccessibilitySettings(
    enabled=True,
    mode=AccessibilityMode.NORMAL,
    font_size=FontSize.MEDIUM,
    dyslexia_font=False
))

# Switch quickly between modes
plugin.load_profile('performance_mode')
```

## Accessibility Guidelines

### WCAG Compliance
This plugin helps achieve WCAG 2.1 compliance:

- **Perceivable**: Text alternatives, adaptable content, distinguishable text
- **Operable**: Keyboard accessible, enough time, no seizures, navigable
- **Understandable**: Readable, predictable, input assistance
- **Robust**: Compatible with assistive technologies

### Screen Reader Testing
```python
# Test with screen readers
def test_screen_reader():
    content = "Important notification message"
    sr_text = plugin.generate_screen_reader_text(content, "Alert")
    
    # Should include context
    assert "Alert" in sr_text
    assert content in sr_text
    
    # Should include navigation hints
    if plugin.settings.skip_navigation:
        assert "Alt+Shift+N" in sr_text
```

### Keyboard Navigation Testing
```python
# Test keyboard navigation
def test_keyboard_navigation():
    # Test shortcuts
    shortcuts = plugin.get_keyboard_shortcuts()
    assert 'Ctrl+F' in shortcuts.values()
    assert 'Alt+Shift+N' in shortcuts.values()
    
    # Test shortcut handling
    handled = plugin.handle_keyboard_shortcut('Ctrl+Shift+C')
    assert handled == True
    
    # Test focus order
    focus_order = plugin.get_focus_order()
    assert len(focus_order) > 0
    assert 'main_navigation' in focus_order
```

## Troubleshooting

### Common Issues

1. **TTS not working**:
   ```python
   # Check if TTS is enabled
   if not plugin.settings.tts_enabled:
       plugin.update_settings({'tts_enabled': True})
   ```

2. **Keyboard shortcuts not working**:
   ```python
   # Check if shortcuts are enabled
   if not plugin.settings.shortcuts_enabled:
       plugin.update_settings({'shortcuts_enabled': True})
   ```

3. **Dyslexia font not applying**:
   ```python
   # Check if dyslexia font is enabled
   if not plugin.settings.dyslexia_font:
       plugin.update_settings({'dyslexia_font': True})
   ```

4. **High contrast not working**:
   ```python
   # Check mode and contrast settings
   plugin.update_settings({
       'mode': 'high_contrast',
       'contrast': 'maximum'
   })
   ```

### Debugging

```python
# Get current settings
settings = plugin.get_settings()
print(f"Current settings: {settings.to_dict()}")

# Get cache stats (if applicable)
stats = plugin.get_cache_stats()
print(f"Cache stats: {stats}")

# Validate settings
errors = plugin.validate_settings(settings)
if errors:
    print(f"Validation errors: {errors}")
```

## Integration Examples

### Web Application Integration
```python
from flask import Flask, request, jsonify

app = Flask(__name__)
accessibility = AccessibilityPlugin()

@app.route('/api/accessibility/settings', methods=['GET'])
def get_settings():
    return jsonify(accessibility.get_settings().to_dict())

@app.route('/api/accessibility/settings', methods=['POST'])
def update_settings():
    updates = request.json
    accessibility.update_settings(updates)
    return jsonify({"success": True})

@app.route('/api/accessibility/text/format', methods=['POST'])
def format_text():
    data = request.json
    text = data['text']
    mode = data.get('mode', 'normal')
    
    if mode == 'dyslexia':
        formatted = accessibility.format_text_for_dyslexia(text)
    elif mode == 'simplify':
        formatted = accessibility.simplify_text(text, level=2)
    else:
        formatted = text
    
    return jsonify({"formatted": formatted})
```

### Desktop Application Integration
```python
import tkinter as tk
from nodupe.plugins.accessibility import AccessibilityPlugin

class AccessibilityApp:
    def __init__(self, root):
        self.root = root
        self.accessibility = AccessibilityPlugin()
        self.accessibility.initialize(None)
        
        # Create UI
        self.create_ui()
        
        # Listen for changes
        self.accessibility.add_listener(self.on_settings_change)
    
    def create_ui(self):
        # Create accessibility controls
        self.font_size_var = tk.StringVar(value="medium")
        self.contrast_var = tk.StringVar(value="normal")
        
        # Font size controls
        tk.Label(self.root, text="Font Size:").pack()
        for size in ["small", "medium", "large", "extra_large"]:
            tk.Radiobutton(
                self.root,
                text=size.title(),
                variable=self.font_size_var,
                value=size,
                command=self.update_font_size
            ).pack()
        
        # Contrast controls
        tk.Label(self.root, text="Contrast:").pack()
        for contrast in ["normal", "high", "maximum"]:
            tk.Radiobutton(
                self.root,
                text=contrast.title(),
                variable=self.contrast_var,
                value=contrast,
                command=self.update_contrast
            ).pack()
    
    def update_font_size(self):
        self.accessibility.update_settings({
            'font_size': self.font_size_var.get()
        })
    
    def update_contrast(self):
        self.accessibility.update_settings({
            'contrast': self.contrast_var.get()
        })
    
    def on_settings_change(self, settings):
        # Apply settings to UI
        font_settings = self.accessibility.get_font_settings()
        self.root.option_add('*Font', f"{font_settings['family']} {font_settings['size']}")
```

## Contributing

When contributing to the Accessibility plugin:

1. **Maintain backward compatibility**: Ensure existing code continues to work
2. **Add comprehensive tests**: Include tests for new accessibility features
3. **Follow accessibility standards**: Adhere to WCAG 2.1 guidelines
4. **Document new features**: Update documentation and examples
5. **Test with assistive technologies**: Verify compatibility with screen readers, etc.
6. **Consider diverse needs**: Support a wide range of accessibility requirements

## License

MIT License - see project LICENSE file.
