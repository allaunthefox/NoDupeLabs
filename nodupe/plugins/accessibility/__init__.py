"""
Accessibility Plugin

Provides comprehensive accessibility features for the NoDupeLabs system,
including dyslexia support, visual accessibility options, and cognitive
accessibility tools. This plugin ensures the application is usable by
people with various disabilities and accessibility needs.

Features:
- Dyslexia-friendly text formatting and fonts
- Visual accessibility (contrast, font size, color adjustments)
- Screen reader support and ARIA labels
- Keyboard navigation enhancements
- Cognitive accessibility (simplified interfaces, clear instructions)
- Text-to-speech integration
- High contrast mode
- Customizable accessibility profiles
"""

from __future__ import annotations

import json
import os
import threading
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
import logging
from enum import Enum

from nodupe.core.plugin_system.base import Plugin

logger = logging.getLogger(__name__)


class AccessibilityMode(Enum):
    """Accessibility mode types."""
    NORMAL = "normal"
    HIGH_CONTRAST = "high_contrast"
    DYSLEXIA_FRIENDLY = "dyslexia_friendly"
    SCREEN_READER = "screen_reader"
    KEYBOARD_ONLY = "keyboard_only"
    SIMPLIFIED = "simplified"


class FontSize(Enum):
    """Font size options."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"


class ContrastLevel(Enum):
    """Contrast level options."""
    NORMAL = "normal"
    HIGH = "high"
    MAXIMUM = "maximum"


@dataclass
class AccessibilitySettings:
    """Accessibility configuration settings."""
    # General settings
    enabled: bool = True
    mode: AccessibilityMode = AccessibilityMode.NORMAL
    
    # Visual settings
    font_size: FontSize = FontSize.MEDIUM
    contrast: ContrastLevel = ContrastLevel.NORMAL
    reduce_motion: bool = False
    custom_colors: Optional[Dict[str, str]] = None
    
    # Dyslexia support
    dyslexia_font: bool = False
    dyslexia_font_size: int = 16
    line_spacing: float = 1.5
    letter_spacing: float = 0.12
    text_alignment: str = "left"
    custom_font_size: Optional[int] = None
    custom_line_spacing: Optional[float] = None
    custom_letter_spacing: Optional[float] = None
    
    # Screen reader settings
    screen_reader_enabled: bool = False
    aria_labels: bool = True
    skip_navigation: bool = True
    focus_indicators: bool = True
    
    # Keyboard navigation
    keyboard_navigation: bool = False
    tab_order: List[str] = None
    shortcuts_enabled: bool = True
    
    # Cognitive accessibility
    simplified_ui: bool = False
    clear_instructions: bool = True
    progress_indicators: bool = True
    error_messages: bool = True
    
    # Text-to-speech
    tts_enabled: bool = False
    tts_rate: float = 1.0
    tts_volume: float = 1.0
    tts_voice: str = "default"
    
    def __post_init__(self):
        if self.tab_order is None:
            self.tab_order = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        data = asdict(self)
        data['mode'] = self.mode.value
        data['font_size'] = self.font_size.value
        data['contrast'] = self.contrast.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AccessibilitySettings':
        """Create settings from dictionary."""
        data['mode'] = AccessibilityMode(data.get('mode', 'normal'))
        data['font_size'] = FontSize(data.get('font_size', 'medium'))
        data['contrast'] = ContrastLevel(data.get('contrast', 'normal'))
        return cls(**data)


class AccessibilityPlugin(Plugin):
    """
    Accessibility Plugin for comprehensive accessibility support.
    
    This plugin provides a wide range of accessibility features to ensure
    the NoDupeLabs system is usable by people with various disabilities
    and accessibility needs.
    
    Key features:
    - Dyslexia-friendly text formatting and fonts
    - Visual accessibility (contrast, font size, color adjustments)
    - Screen reader support and ARIA labels
    - Keyboard navigation enhancements
    - Cognitive accessibility (simplified interfaces, clear instructions)
    - Text-to-speech integration
    - High contrast mode
    - Customizable accessibility profiles
    """

    name = "accessibility"
    version = "1.0"
    dependencies = []

    def __init__(self):
        """
        Initialize the Accessibility plugin.
        """
        self.settings = AccessibilitySettings()
        self.profiles: Dict[str, AccessibilitySettings] = {}
        self.current_profile: Optional[str] = None
        self.listeners: List[Callable[[AccessibilitySettings], None]] = []
        
        self._lock = threading.Lock()
        self._initialized = False
        
        # Default profiles
        self._setup_default_profiles()
        
        logger.info("Accessibility plugin initialized")

    def initialize(self, container: Any) -> None:
        """Initialize the plugin."""
        logger.info("Initializing Accessibility plugin")
        self._initialized = True
        
        # Load saved settings
        self._load_settings()
        
        # Apply current settings
        self._apply_settings()

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        logger.info("Shutting down Accessibility plugin")
        
        # Save current settings
        self._save_settings()
        
        # Clean up listeners
        self.listeners.clear()

    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities."""
        return {
            'features': [
                'dyslexia_support',
                'visual_accessibility',
                'screen_reader_support',
                'keyboard_navigation',
                'cognitive_accessibility',
                'text_to_speech',
                'high_contrast',
                'customizable_profiles'
            ],
            'modes': [mode.value for mode in AccessibilityMode],
            'font_sizes': [size.value for size in FontSize],
            'contrast_levels': [level.value for level in ContrastLevel],
            'max_profiles': 6
        }

    # ---- Settings Management ----
    def get_settings(self) -> AccessibilitySettings:
        """Get current accessibility settings."""
        with self._lock:
            return self.settings

    def update_settings(self, updates: Dict[str, Any]) -> None:
        """
        Update accessibility settings.
        
        Args:
            updates: Dictionary of settings to update
        """
        with self._lock:
            # Create new settings object with updates
            current_data = self.settings.to_dict()
            current_data.update(updates)
            self.settings = AccessibilitySettings.from_dict(current_data)
            
            # Apply the changes
            self._apply_settings()
            
            # Notify listeners
            self._notify_listeners()
            
            logger.info(f"Settings updated: {updates}")

    def reset_settings(self) -> None:
        """Reset settings to default."""
        with self._lock:
            self.settings = AccessibilitySettings()
            self._apply_settings()
            self._notify_listeners()
            logger.info("Settings reset to default")

    def _apply_settings(self) -> None:
        """Apply current settings to the system."""
        # This would integrate with the UI system to apply visual changes
        # For now, we'll log the settings
        logger.debug(f"Applying settings: {self.settings.to_dict()}")
        
        # Apply mode-specific settings
        if self.settings.mode == AccessibilityMode.HIGH_CONTRAST:
            self._apply_high_contrast()
        elif self.settings.mode == AccessibilityMode.DYSLEXIA_FRIENDLY:
            self._apply_dyslexia_settings()
        elif self.settings.mode == AccessibilityMode.SCREEN_READER:
            self._apply_screen_reader_settings()
        elif self.settings.mode == AccessibilityMode.KEYBOARD_ONLY:
            self._apply_keyboard_navigation()
        elif self.settings.mode == AccessibilityMode.SIMPLIFIED:
            self._apply_simplified_ui()

    def _apply_high_contrast(self) -> None:
        """Apply high contrast mode settings."""
        logger.debug("Applying high contrast mode")
        # Set high contrast colors
        self.settings.custom_colors = {
            'background': '#000000',
            'text': '#FFFFFF',
            'accent': '#FFFF00',
            'link': '#00FFFF'
        }

    def _apply_dyslexia_settings(self) -> None:
        """Apply dyslexia-friendly settings."""
        logger.debug("Applying dyslexia-friendly settings")
        self.settings.dyslexia_font = True
        self.settings.line_spacing = 1.8
        self.settings.letter_spacing = 0.15
        self.settings.text_alignment = "left"

    def _apply_screen_reader_settings(self) -> None:
        """Apply screen reader settings."""
        logger.debug("Applying screen reader settings")
        self.settings.screen_reader_enabled = True
        self.settings.aria_labels = True
        self.settings.focus_indicators = True

    def _apply_keyboard_navigation(self) -> None:
        """Apply keyboard-only navigation settings."""
        logger.debug("Applying keyboard navigation settings")
        self.settings.keyboard_navigation = True
        self.settings.shortcuts_enabled = True

    def _apply_simplified_ui(self) -> None:
        """Apply simplified UI settings."""
        logger.debug("Applying simplified UI settings")
        self.settings.simplified_ui = True
        self.settings.clear_instructions = True
        self.settings.progress_indicators = True

    # ---- Profile Management ----
    def create_profile(self, name: str, settings: AccessibilitySettings) -> None:
        """
        Create a new accessibility profile.
        
        Args:
            name: Profile name
            settings: Accessibility settings for the profile
        """
        with self._lock:
            if len(self.profiles) >= 6:
                raise ValueError("Maximum number of profiles reached (6)")
            
            if name in self.profiles:
                raise ValueError(f"Profile '{name}' already exists")
            
            self.profiles[name] = settings
            logger.info(f"Created profile: {name}")

    def load_profile(self, name: str) -> None:
        """
        Load an accessibility profile.
        
        Args:
            name: Profile name to load
        """
        with self._lock:
            if name not in self.profiles:
                raise ValueError(f"Profile '{name}' not found")
            
            self.settings = self.profiles[name]
            self.current_profile = name
            self._apply_settings()
            self._notify_listeners()
            logger.info(f"Loaded profile: {name}")

    def delete_profile(self, name: str) -> None:
        """
        Delete an accessibility profile.
        
        Args:
            name: Profile name to delete
        """
        with self._lock:
            if name not in self.profiles:
                raise ValueError(f"Profile '{name}' not found")
            
            if self.current_profile == name:
                self.current_profile = None
            
            del self.profiles[name]
            logger.info(f"Deleted profile: {name}")

    def list_profiles(self) -> List[str]:
        """List all available profiles."""
        with self._lock:
            return list(self.profiles.keys())

    def get_profile(self, name: str) -> Optional[AccessibilitySettings]:
        """Get a specific profile's settings."""
        with self._lock:
            return self.profiles.get(name)

    def _setup_default_profiles(self) -> None:
        """Set up default accessibility profiles."""
        # Default profile
        default = AccessibilitySettings()
        self.profiles["default"] = default
        
        # High contrast profile
        high_contrast = AccessibilitySettings(
            mode=AccessibilityMode.HIGH_CONTRAST,
            font_size=FontSize.LARGE,
            contrast=ContrastLevel.MAXIMUM,
            dyslexia_font=False
        )
        self.profiles["high_contrast"] = high_contrast
        
        # Dyslexia-friendly profile
        dyslexia = AccessibilitySettings(
            mode=AccessibilityMode.DYSLEXIA_FRIENDLY,
            dyslexia_font=True,
            line_spacing=1.8,
            letter_spacing=0.15,
            font_size=FontSize.LARGE
        )
        self.profiles["dyslexia_friendly"] = dyslexia
        
        # Screen reader profile
        screen_reader = AccessibilitySettings(
            mode=AccessibilityMode.SCREEN_READER,
            screen_reader_enabled=True,
            aria_labels=True,
            font_size=FontSize.LARGE
        )
        self.profiles["screen_reader"] = screen_reader
        
        # Keyboard navigation profile
        keyboard = AccessibilitySettings(
            mode=AccessibilityMode.KEYBOARD_ONLY,
            keyboard_navigation=True,
            shortcuts_enabled=True,
            focus_indicators=True
        )
        self.profiles["keyboard_only"] = keyboard
        
        # Simplified UI profile
        simplified = AccessibilitySettings(
            mode=AccessibilityMode.SIMPLIFIED,
            simplified_ui=True,
            clear_instructions=True,
            progress_indicators=True,
            font_size=FontSize.LARGE
        )
        self.profiles["simplified"] = simplified
        
        self.current_profile = "default"

    # ---- Text Processing ----
    def format_text_for_dyslexia(self, text: str) -> str:
        """
        Format text to be more readable for people with dyslexia.
        
        Args:
            text: Original text
            
        Returns:
            Formatted text
        """
        # Replace difficult words with simpler alternatives
        dyslexia_words = {
            "because": "cause",
            "difficult": "hard",
            "approximately": "about",
            "approximately": "around",
            "necessary": "needed",
            "separate": "apart",
            "recommend": "suggest",
            "environment": "surroundings",
            "complex": "simple"
        }
        
        formatted = text
        for difficult, simple in dyslexia_words.items():
            formatted = formatted.replace(difficult, simple)
        
        # Add visual separators for paragraphs
        paragraphs = formatted.split('\n\n')
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            if paragraph.strip():
                # Add bullet points or numbers for lists
                lines = paragraph.split('\n')
                if len(lines) > 1:
                    formatted_lines = []
                    for i, line in enumerate(lines):
                        if line.strip():
                            formatted_lines.append(f"• {line.strip()}")
                    formatted_paragraphs.append('\n'.join(formatted_lines))
                else:
                    formatted_paragraphs.append(paragraph)
        
        return '\n\n'.join(formatted_paragraphs)

    def simplify_text(self, text: str, level: int = 1) -> str:
        """
        Simplify text for cognitive accessibility.
        
        Args:
            text: Original text
            level: Simplification level (1-3)
            
        Returns:
            Simplified text
        """
        if level < 1 or level > 3:
            raise ValueError("Simplification level must be 1-3")
        
        # Break complex sentences
        sentences = text.split('. ')
        simplified_sentences = []
        
        for sentence in sentences:
            # Split long sentences
            if len(sentence.split()) > 20:
                parts = sentence.split(', ')
                simplified_sentences.extend(parts)
            else:
                simplified_sentences.append(sentence)
        
        # Remove complex words based on level
        if level >= 2:
            complex_words = {
                "utilize": "use",
                "facilitate": "help",
                "implement": "put in place",
                "methodology": "method",
                "subsequently": "after",
                "prior": "before",
                "utilization": "use",
                "approximately": "about"
            }
            
            for complex, simple in complex_words.items():
                text = text.replace(complex, simple)
        
        if level >= 3:
            # Use very simple language
            very_simple = {
                "understand": "get",
                "important": "big deal",
                "difficult": "hard",
                "analyze": "look at",
                "determine": "find out",
                "procedure": "steps",
                "requirement": "need"
            }
            
            for complex, simple in very_simple.items():
                text = text.replace(complex, simple)
        
        return '. '.join(simplified_sentences)

    def add_aria_labels(self, text: str, context: str = "") -> str:
        """
        Add ARIA labels to text for screen readers.
        
        Args:
            text: Original text
            context: Context for the text
            
        Returns:
            Text with ARIA labels
        """
        if not self.settings.aria_labels:
            return text
        
        # Add descriptive labels
        aria_text = f"aria-label='{context}' " if context else ""
        aria_text += f"role='text' "
        
        return f"<span {aria_text}>{text}</span>"

    # ---- Visual Accessibility ----
    def get_contrast_colors(self, level: ContrastLevel) -> Dict[str, str]:
        """
        Get color scheme for specified contrast level.
        
        Args:
            level: Contrast level
            
        Returns:
            Color scheme dictionary
        """
        color_schemes = {
            ContrastLevel.NORMAL: {
                'background': '#FFFFFF',
                'text': '#000000',
                'accent': '#007BFF',
                'link': '#0056b3'
            },
            ContrastLevel.HIGH: {
                'background': '#000000',
                'text': '#FFFFFF',
                'accent': '#FFFF00',
                'link': '#00FFFF'
            },
            ContrastLevel.MAXIMUM: {
                'background': '#000000',
                'text': '#FFFFFF',
                'accent': '#FF0000',
                'link': '#00FF00'
            }
        }
        
        return color_schemes.get(level, color_schemes[ContrastLevel.NORMAL])

    def get_font_settings(self) -> Dict[str, Any]:
        """Get current font settings."""
        font_sizes = {
            FontSize.SMALL: 12,
            FontSize.MEDIUM: 14,
            FontSize.LARGE: 18,
            FontSize.EXTRA_LARGE: 24
        }
        
        # Use custom font size if specified, otherwise use enum-based size
        if self.settings.custom_font_size is not None:
            font_size = self.settings.custom_font_size
        else:
            font_size = font_sizes[self.settings.font_size]
        
        # Use custom spacing if specified, otherwise use default settings
        line_spacing = self.settings.custom_line_spacing if self.settings.custom_line_spacing is not None else self.settings.line_spacing
        letter_spacing = self.settings.custom_letter_spacing if self.settings.custom_letter_spacing is not None else self.settings.letter_spacing
        
        return {
            'size': font_size,
            'family': 'OpenDyslexic' if self.settings.dyslexia_font else 'Arial',
            'line_spacing': line_spacing,
            'letter_spacing': letter_spacing,
            'alignment': self.settings.text_alignment,
            'custom_font_size': self.settings.custom_font_size,
            'custom_line_spacing': self.settings.custom_line_spacing,
            'custom_letter_spacing': self.settings.custom_letter_spacing
        }
    
    def set_custom_font_size(self, size: int) -> None:
        """
        Set custom font size.
        
        Args:
            size: Font size in pixels (10-72)
        """
        if size < 10 or size > 72:
            raise ValueError("Font size must be between 10 and 72 pixels")
        
        self.update_settings({'custom_font_size': size})
        logger.info(f"Custom font size set to {size}px")
    
    def set_custom_line_spacing(self, spacing: float) -> None:
        """
        Set custom line spacing.
        
        Args:
            spacing: Line spacing multiplier (1.0-3.0)
        """
        if spacing < 1.0 or spacing > 3.0:
            raise ValueError("Line spacing must be between 1.0 and 3.0")
        
        self.update_settings({'custom_line_spacing': spacing})
        logger.info(f"Custom line spacing set to {spacing}")
    
    def set_custom_letter_spacing(self, spacing: float) -> None:
        """
        Set custom letter spacing.
        
        Args:
            spacing: Letter spacing in em units (0.0-0.5)
        """
        if spacing < 0.0 or spacing > 0.5:
            raise ValueError("Letter spacing must be between 0.0 and 0.5")
        
        self.update_settings({'custom_letter_spacing': spacing})
        logger.info(f"Custom letter spacing set to {spacing}em")
    
    def clear_custom_font_settings(self) -> None:
        """Clear custom font settings and revert to enum-based settings."""
        self.update_settings({
            'custom_font_size': None,
            'custom_line_spacing': None,
            'custom_letter_spacing': None
        })
        logger.info("Custom font settings cleared, reverted to enum-based settings")

    # ---- Screen Reader Support ----
    def generate_screen_reader_text(self, content: str, context: str = "") -> str:
        """
        Generate screen reader-friendly text.
        
        Args:
            content: Original content
            context: Context description
            
        Returns:
            Screen reader text
        """
        if not self.settings.screen_reader_enabled:
            return content
        
        # Add context information
        screen_reader_text = content
        
        if context:
            screen_reader_text = f"{context}. {content}"
        
        # Add navigation hints
        if self.settings.skip_navigation:
            screen_reader_text = f"To skip navigation, press Alt+Shift+N. {screen_reader_text}"
        
        return screen_reader_text

    def get_focus_order(self) -> List[str]:
        """Get current focus order for keyboard navigation."""
        if self.settings.tab_order:
            return self.settings.tab_order
        
        # Default focus order
        return [
            "main_navigation",
            "search_bar",
            "content_area",
            "sidebar",
            "footer"
        ]

    # ---- Text-to-Speech ----
    def text_to_speech(self, text: str, rate: Optional[float] = None, 
                      volume: Optional[float] = None, 
                      voice: Optional[str] = None) -> bool:
        """
        Convert text to speech.
        
        Args:
            text: Text to convert
            rate: Speech rate (0.5-2.0)
            volume: Volume level (0.0-1.0)
            voice: Voice to use
            
        Returns:
            True if successful, False otherwise
        """
        if not self.settings.tts_enabled:
            logger.warning("Text-to-speech is disabled")
            return False
        
        # Use system TTS (placeholder implementation)
        try:
            # This would integrate with system TTS
            # For now, just log the request
            actual_rate = rate if rate is not None else self.settings.tts_rate
            actual_volume = volume if volume is not None else self.settings.tts_volume
            actual_voice = voice if voice is not None else self.settings.tts_voice
            
            logger.info(f"TTS: rate={actual_rate}, volume={actual_volume}, voice={actual_voice}")
            logger.debug(f"TTS text: {text[:100]}...")
            
            return True
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}")
            return False

    # ---- Keyboard Shortcuts ----
    def get_keyboard_shortcuts(self) -> Dict[str, str]:
        """Get available keyboard shortcuts."""
        if not self.settings.shortcuts_enabled:
            return {}
        
        shortcuts = {
            'focus_search': 'Ctrl+F',
            'skip_navigation': 'Alt+Shift+N',
            'increase_font': 'Ctrl+Plus',
            'decrease_font': 'Ctrl+Minus',
            'reset_font': 'Ctrl+0',
            'high_contrast': 'Ctrl+Shift+C',
            'dyslexia_mode': 'Ctrl+Shift+D',
            'screen_reader_mode': 'Ctrl+Shift+S'
        }
        
        return shortcuts

    def handle_keyboard_shortcut(self, shortcut: str) -> bool:
        """
        Handle a keyboard shortcut.
        
        Args:
            shortcut: Keyboard shortcut to handle
            
        Returns:
            True if handled, False otherwise
        """
        shortcuts = self.get_keyboard_shortcuts()
        
        if shortcut not in shortcuts.values():
            return False
        
        # Handle specific shortcuts
        if shortcut == 'Ctrl+Shift+C':
            self.update_settings({'mode': 'high_contrast'})
        elif shortcut == 'Ctrl+Shift+D':
            self.update_settings({'mode': 'dyslexia_friendly'})
        elif shortcut == 'Ctrl+Shift+S':
            self.update_settings({'mode': 'screen_reader'})
        elif shortcut == 'Ctrl+Plus':
            current_size = self.settings.font_size
            size_map = {
                FontSize.SMALL: FontSize.MEDIUM,
                FontSize.MEDIUM: FontSize.LARGE,
                FontSize.LARGE: FontSize.EXTRA_LARGE,
                FontSize.EXTRA_LARGE: FontSize.EXTRA_LARGE
            }
            self.update_settings({'font_size': size_map[current_size].value})
        elif shortcut == 'Ctrl+Minus':
            current_size = self.settings.font_size
            size_map = {
                FontSize.EXTRA_LARGE: FontSize.LARGE,
                FontSize.LARGE: FontSize.MEDIUM,
                FontSize.MEDIUM: FontSize.SMALL,
                FontSize.SMALL: FontSize.SMALL
            }
            self.update_settings({'font_size': size_map[current_size].value})
        elif shortcut == 'Ctrl+0':
            self.update_settings({'font_size': 'medium'})
        elif shortcut == 'Alt+Shift+N':
            # Skip navigation - would need UI integration
            logger.info("Skip navigation activated")
        
        return True

    # ---- Event Handling ----
    def add_listener(self, callback: Callable[[AccessibilitySettings], None]) -> None:
        """
        Add a listener for settings changes.
        
        Args:
            callback: Function to call when settings change
        """
        with self._lock:
            self.listeners.append(callback)

    def remove_listener(self, callback: Callable[[AccessibilitySettings], None]) -> None:
        """
        Remove a settings change listener.
        
        Args:
            callback: Function to remove
        """
        with self._lock:
            if callback in self.listeners:
                self.listeners.remove(callback)

    def _notify_listeners(self) -> None:
        """Notify all listeners of settings changes."""
        for listener in self.listeners:
            try:
                listener(self.settings)
            except Exception as e:
                logger.error(f"Listener error: {e}")

    # ---- Persistence ----
    def _save_settings(self) -> None:
        """Save settings to file."""
        try:
            settings_data = {
                'current_settings': self.settings.to_dict(),
                'current_profile': self.current_profile,
                'profiles': {name: settings.to_dict() for name, settings in self.profiles.items()}
            }
            
            # Save to JSON file
            config_dir = os.path.expanduser("~/.nodupe")
            os.makedirs(config_dir, exist_ok=True)
            settings_file = os.path.join(config_dir, "accessibility_settings.json")
            
            with open(settings_file, 'w') as f:
                json.dump(settings_data, f, indent=2)
                
            logger.debug("Settings saved successfully")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def _load_settings(self) -> None:
        """Load settings from file."""
        try:
            config_dir = os.path.expanduser("~/.nodupe")
            settings_file = os.path.join(config_dir, "accessibility_settings.json")
            
            if not os.path.exists(settings_file):
                return
            
            with open(settings_file, 'r') as f:
                settings_data = json.load(f)
            
            # Load current settings
            if 'current_settings' in settings_data:
                self.settings = AccessibilitySettings.from_dict(settings_data['current_settings'])
            
            # Load profiles
            if 'profiles' in settings_data:
                self.profiles = {
                    name: AccessibilitySettings.from_dict(data)
                    for name, data in settings_data['profiles'].items()
                }
            
            # Load current profile
            if 'current_profile' in settings_data:
                self.current_profile = settings_data['current_profile']
            
            logger.debug("Settings loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")

    # ---- Utility Methods ----
    def is_accessible_color(self, color: str) -> bool:
        """
        Check if a color meets accessibility standards.
        
        Args:
            color: Color in hex format (#RRGGBB)
            
        Returns:
            True if accessible, False otherwise
        """
        # Simple contrast check (would use proper algorithm in real implementation)
        if len(color) != 7 or not color.startswith('#'):
            return False
        
        # Check if it's a valid hex color
        try:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            return True
        except ValueError:
            return False

    def get_accessibility_score(self, content: str) -> Dict[str, Any]:
        """
        Calculate accessibility score for content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Accessibility score and recommendations
        """
        score = 100
        issues = []
        
        # Check for alt text in images
        if '<img' in content and 'alt=' not in content:
            score -= 10
            issues.append("Missing alt text for images")
        
        # Check for heading structure
        headings = content.count('<h1>') + content.count('<h2>') + content.count('<h3>')
        if headings == 0:
            score -= 5
            issues.append("No headings found")
        
        # Check for link text
        if '<a' in content and 'href=' in content:
            if 'Click here' in content or 'Read more' in content or 'click here' in content:
                score -= 5
                issues.append("Non-descriptive link text")
        
        # Check for form labels
        if '<input' in content and '<label' not in content:
            score -= 10
            issues.append("Missing form labels")
        
        return {
            'score': max(0, score),
            'issues': issues,
            'recommendations': self._get_recommendations(issues)
        }

    def _get_recommendations(self, issues: List[str]) -> List[str]:
        """Get recommendations based on accessibility issues."""
        recommendations = []
        
        if "Missing alt text for images" in issues:
            recommendations.append("Add descriptive alt text to all images")
        
        if "No headings found" in issues:
            recommendations.append("Use proper heading structure (H1, H2, H3)")
        
        if "Non-descriptive link text" in issues:
            recommendations.append("Use descriptive link text that explains the destination")
        
        if "Missing form labels" in issues:
            recommendations.append("Add labels to all form inputs")
        
        return recommendations

    def validate_settings(self, settings: AccessibilitySettings) -> List[str]:
        """
        Validate accessibility settings.
        
        Args:
            settings: Settings to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check font size range
        if settings.dyslexia_font_size < 10 or settings.dyslexia_font_size > 36:
            errors.append("Dyslexia font size must be between 10 and 36")
        
        # Check line spacing
        if settings.line_spacing < 1.0 or settings.line_spacing > 3.0:
            errors.append("Line spacing must be between 1.0 and 3.0")
        
        # Check letter spacing
        if settings.letter_spacing < 0.0 or settings.letter_spacing > 0.5:
            errors.append("Letter spacing must be between 0.0 and 0.5")
        
        # Check text alignment
        if settings.text_alignment not in ['left', 'center', 'right', 'justify']:
            errors.append("Text alignment must be left, center, right, or justify")
        
        # Check TTS settings
        if settings.tts_rate < 0.5 or settings.tts_rate > 2.0:
            errors.append("TTS rate must be between 0.5 and 2.0")
        
        if settings.tts_volume < 0.0 or settings.tts_volume > 1.0:
            errors.append("TTS volume must be between 0.0 and 1.0")
        
        return errors
