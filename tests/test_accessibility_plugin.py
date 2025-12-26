"""
Unit tests for the Accessibility Plugin.

Tests all functionality including:
- Basic plugin operations
- Dyslexia support features
- Visual accessibility settings
- Screen reader support
- Keyboard navigation
- Text-to-speech functionality
- Profile management
- Custom font size and spacing
- Settings validation
- Event handling
- Persistence
"""

import unittest
import tempfile
import os
import json
from unittest.mock import Mock, patch
from pathlib import Path

from nodupe.plugins.accessibility import (
    AccessibilityPlugin,
    AccessibilitySettings,
    AccessibilityMode,
    FontSize,
    ContrastLevel
)


class TestAccessibilityPlugin(unittest.TestCase):
    """Test cases for the AccessibilityPlugin class."""

    def setUp(self):
        """Set up test fixtures."""
        self.plugin = AccessibilityPlugin()
        self.plugin.initialize(None)
        # Reset to default settings for each test
        self.plugin.reset_settings()

    def tearDown(self):
        """Clean up after tests."""
        # Clean up any test profiles that were created
        try:
            profiles_to_delete = []
            for profile_name in self.plugin.list_profiles():
                if profile_name not in ['default', 'high_contrast', 'dyslexia_friendly', 
                                      'screen_reader', 'keyboard_only', 'simplified']:
                    profiles_to_delete.append(profile_name)
            
            for profile_name in profiles_to_delete:
                try:
                    self.plugin.delete_profile(profile_name)
                except ValueError:
                    pass  # Profile might not exist
        except Exception:
            pass  # Ignore errors during cleanup
        
        try:
            self.plugin.shutdown()
        except Exception:
            pass  # Ignore errors during shutdown

    def test_plugin_initialization(self):
        """Test plugin initialization."""
        self.assertEqual(self.plugin.name, "accessibility")
        self.assertEqual(self.plugin.version, "1.0")
        self.assertEqual(self.plugin.dependencies, [])
        self.assertIsNotNone(self.plugin.settings)
        self.assertEqual(len(self.plugin.profiles), 6)  # 6 default profiles

    def test_get_settings(self):
        """Test getting current settings."""
        settings = self.plugin.get_settings()
        self.assertIsInstance(settings, AccessibilitySettings)
        self.assertTrue(settings.enabled)
        self.assertEqual(settings.mode, AccessibilityMode.NORMAL)
        self.assertEqual(settings.font_size, FontSize.MEDIUM)

    def test_update_settings(self):
        """Test updating settings."""
        initial_mode = self.plugin.settings.mode
        
        # Update settings
        self.plugin.update_settings({'mode': 'high_contrast'})
        
        # Verify changes
        self.assertEqual(self.plugin.settings.mode, AccessibilityMode.HIGH_CONTRAST)
        self.assertNotEqual(self.plugin.settings.mode, initial_mode)

    def test_reset_settings(self):
        """Test resetting settings to default."""
        # Change a setting
        self.plugin.update_settings({'mode': 'high_contrast'})
        self.assertEqual(self.plugin.settings.mode, AccessibilityMode.HIGH_CONTRAST)
        
        # Reset settings
        self.plugin.reset_settings()
        
        # Verify reset
        self.assertEqual(self.plugin.settings.mode, AccessibilityMode.NORMAL)

    def test_get_capabilities(self):
        """Test getting plugin capabilities."""
        capabilities = self.plugin.get_capabilities()
        
        self.assertIn('features', capabilities)
        self.assertIn('modes', capabilities)
        self.assertIn('font_sizes', capabilities)
        self.assertIn('contrast_levels', capabilities)
        self.assertIn('max_profiles', capabilities)
        
        self.assertIn('dyslexia_support', capabilities['features'])
        self.assertIn('visual_accessibility', capabilities['features'])
        self.assertIn('screen_reader_support', capabilities['features'])
        self.assertIn('keyboard_navigation', capabilities['features'])
        self.assertIn('cognitive_accessibility', capabilities['features'])
        self.assertIn('text_to_speech', capabilities['features'])
        self.assertIn('high_contrast', capabilities['features'])
        self.assertIn('customizable_profiles', capabilities['features'])

    def test_format_text_for_dyslexia(self):
        """Test dyslexia-friendly text formatting."""
        text = "This is a difficult sentence with complex words."
        formatted = self.plugin.format_text_for_dyslexia(text)
        
        # Check that difficult words are replaced
        self.assertIn("hard", formatted)
        self.assertIn("simple", formatted)
        self.assertNotIn("difficult", formatted)
        self.assertNotIn("complex", formatted)

    def test_simplify_text(self):
        """Test text simplification for cognitive accessibility."""
        text = "This is a difficult sentence with complex words."
        
        # Test level 2 simplification
        simplified = self.plugin.simplify_text(text, level=2)
        self.assertIn("hard", simplified)
        self.assertIn("simple", simplified)
        
        # Test level 3 simplification
        simplified = self.plugin.simplify_text(text, level=3)
        self.assertIn("get", simplified)  # "understand" -> "get"
        self.assertIn("hard", simplified)

    def test_add_aria_labels(self):
        """Test adding ARIA labels to text."""
        text = "Important information"
        context = "Alert message"
        
        # With ARIA labels enabled
        labeled = self.plugin.add_aria_labels(text, context)
        self.assertIn('aria-label', labeled)
        self.assertIn('role', labeled)
        self.assertIn(text, labeled)
        
        # With ARIA labels disabled
        self.plugin.update_settings({'aria_labels': False})
        unlabeled = self.plugin.add_aria_labels(text, context)
        self.assertEqual(unlabeled, text)

    def test_get_contrast_colors(self):
        """Test getting contrast color schemes."""
        # Normal contrast
        colors = self.plugin.get_contrast_colors(ContrastLevel.NORMAL)
        self.assertIn('background', colors)
        self.assertIn('text', colors)
        self.assertEqual(colors['background'], '#FFFFFF')
        self.assertEqual(colors['text'], '#000000')
        
        # High contrast
        colors = self.plugin.get_contrast_colors(ContrastLevel.HIGH)
        self.assertEqual(colors['background'], '#000000')
        self.assertEqual(colors['text'], '#FFFFFF')

    def test_get_font_settings(self):
        """Test getting font settings."""
        font_settings = self.plugin.get_font_settings()
        
        self.assertIn('size', font_settings)
        self.assertIn('family', font_settings)
        self.assertIn('line_spacing', font_settings)
        self.assertIn('letter_spacing', font_settings)
        self.assertIn('alignment', font_settings)
        
        # Default values
        self.assertEqual(font_settings['size'], 14)  # Medium font size
        self.assertEqual(font_settings['family'], 'Arial')
        self.assertEqual(font_settings['line_spacing'], 1.5)
        self.assertEqual(font_settings['letter_spacing'], 0.12)
        self.assertEqual(font_settings['alignment'], 'left')

    def test_custom_font_size(self):
        """Test custom font size functionality."""
        # Set custom font size
        self.plugin.set_custom_font_size(20)
        
        # Check that custom size is set
        font_settings = self.plugin.get_font_settings()
        self.assertEqual(font_settings['custom_font_size'], 20)
        self.assertEqual(font_settings['size'], 20)  # Should use custom size
        
        # Test validation
        with self.assertRaises(ValueError):
            self.plugin.set_custom_font_size(5)  # Too small
        
        with self.assertRaises(ValueError):
            self.plugin.set_custom_font_size(100)  # Too large

    def test_custom_line_spacing(self):
        """Test custom line spacing functionality."""
        # Set custom line spacing
        self.plugin.set_custom_line_spacing(2.0)
        
        # Check that custom spacing is set
        font_settings = self.plugin.get_font_settings()
        self.assertEqual(font_settings['custom_line_spacing'], 2.0)
        self.assertEqual(font_settings['line_spacing'], 2.0)
        
        # Test validation
        with self.assertRaises(ValueError):
            self.plugin.set_custom_line_spacing(0.5)  # Too small
        
        with self.assertRaises(ValueError):
            self.plugin.set_custom_line_spacing(4.0)  # Too large

    def test_custom_letter_spacing(self):
        """Test custom letter spacing functionality."""
        # Set custom letter spacing
        self.plugin.set_custom_letter_spacing(0.20)
        
        # Check that custom spacing is set
        font_settings = self.plugin.get_font_settings()
        self.assertEqual(font_settings['custom_letter_spacing'], 0.20)
        self.assertEqual(font_settings['letter_spacing'], 0.20)
        
        # Test validation
        with self.assertRaises(ValueError):
            self.plugin.set_custom_letter_spacing(-0.1)  # Too small
        
        with self.assertRaises(ValueError):
            self.plugin.set_custom_letter_spacing(0.8)  # Too large

    def test_clear_custom_font_settings(self):
        """Test clearing custom font settings."""
        # Set custom settings
        self.plugin.set_custom_font_size(24)
        self.plugin.set_custom_line_spacing(2.0)
        self.plugin.set_custom_letter_spacing(0.20)
        
        # Clear custom settings
        self.plugin.clear_custom_font_settings()
        
        # Check that custom settings are cleared
        font_settings = self.plugin.get_font_settings()
        self.assertIsNone(font_settings['custom_font_size'])
        self.assertIsNone(font_settings['custom_line_spacing'])
        self.assertIsNone(font_settings['custom_letter_spacing'])
        
        # Should revert to enum-based settings
        self.assertEqual(font_settings['size'], 14)  # Medium font size default
        self.assertEqual(font_settings['line_spacing'], 1.5)
        self.assertEqual(font_settings['letter_spacing'], 0.12)

    def test_get_keyboard_shortcuts(self):
        """Test getting keyboard shortcuts."""
        shortcuts = self.plugin.get_keyboard_shortcuts()
        
        self.assertIn('focus_search', shortcuts)
        self.assertIn('skip_navigation', shortcuts)
        self.assertIn('increase_font', shortcuts)
        self.assertIn('decrease_font', shortcuts)
        self.assertIn('reset_font', shortcuts)
        self.assertIn('high_contrast', shortcuts)
        self.assertIn('dyslexia_mode', shortcuts)
        self.assertIn('screen_reader_mode', shortcuts)
        
        # Check specific shortcuts
        self.assertEqual(shortcuts['focus_search'], 'Ctrl+F')
        self.assertEqual(shortcuts['skip_navigation'], 'Alt+Shift+N')

    def test_handle_keyboard_shortcut(self):
        """Test handling keyboard shortcuts."""
        # Test font size increase
        self.plugin.handle_keyboard_shortcut('Ctrl+Plus')
        self.assertEqual(self.plugin.settings.font_size, FontSize.LARGE)
        
        # Test font size decrease
        self.plugin.handle_keyboard_shortcut('Ctrl+Minus')
        self.assertEqual(self.plugin.settings.font_size, FontSize.MEDIUM)
        
        # Test font size reset
        self.plugin.handle_keyboard_shortcut('Ctrl+0')
        self.assertEqual(self.plugin.settings.font_size, FontSize.MEDIUM)
        
        # Test mode shortcuts
        self.plugin.handle_keyboard_shortcut('Ctrl+Shift+C')
        self.assertEqual(self.plugin.settings.mode, AccessibilityMode.HIGH_CONTRAST)

    def test_text_to_speech(self):
        """Test text-to-speech functionality."""
        text = "Hello, this is a test message."
        
        # Test with TTS enabled
        self.plugin.update_settings({'tts_enabled': True})
        result = self.plugin.text_to_speech(text)
        self.assertTrue(result)
        
        # Test with TTS disabled
        self.plugin.update_settings({'tts_enabled': False})
        result = self.plugin.text_to_speech(text)
        self.assertFalse(result)

    def test_profile_management(self):
        """Test profile creation, loading, and deletion."""
        # Get the current number of profiles
        initial_profiles = self.plugin.list_profiles()
        
        # Create a custom profile (this should fail if we're at the limit)
        custom_settings = AccessibilitySettings(
            mode=AccessibilityMode.HIGH_CONTRAST,
            font_size=FontSize.LARGE,
            dyslexia_font=True,
            line_spacing=2.0,
            contrast=ContrastLevel.MAXIMUM
        )
        
        # If we're at the limit, this should raise an error
        if len(initial_profiles) >= 6:
            with self.assertRaises(ValueError):
                self.plugin.create_profile('test_profile', custom_settings)
            
            # Delete one of the default profiles to make room for our test profile
            self.plugin.delete_profile('simplified')
        
        # Now we should be able to create a profile
        self.plugin.create_profile('test_profile', custom_settings)
        
        # List profiles
        profiles = self.plugin.list_profiles()
        self.assertIn('test_profile', profiles)
        
        # Get profile
        profile_settings = self.plugin.get_profile('test_profile')
        self.assertEqual(profile_settings.mode, AccessibilityMode.HIGH_CONTRAST)
        self.assertEqual(profile_settings.font_size, FontSize.LARGE)
        
        # Load profile
        self.plugin.load_profile('test_profile')
        self.assertEqual(self.plugin.settings.mode, AccessibilityMode.HIGH_CONTRAST)
        
        # Delete profile
        self.plugin.delete_profile('test_profile')
        profiles = self.plugin.list_profiles()
        self.assertNotIn('test_profile', profiles)

    def test_profile_validation(self):
        """Test profile validation."""
        # Test maximum profiles limit
        for i in range(6):
            custom_settings = AccessibilitySettings()
            self.plugin.create_profile(f'profile_{i}', custom_settings)
        
        # Should raise error when trying to create 7th profile
        custom_settings = AccessibilitySettings()
        with self.assertRaises(ValueError):
            self.plugin.create_profile('profile_6', custom_settings)

    def test_event_handling(self):
        """Test settings change event handling."""
        # Create a mock listener
        mock_listener = Mock()
        self.plugin.add_listener(mock_listener)
        
        # Update settings (should trigger listener)
        self.plugin.update_settings({'mode': 'high_contrast'})
        
        # Verify listener was called
        mock_listener.assert_called_once()
        args = mock_listener.call_args[0]
        self.assertIsInstance(args[0], AccessibilitySettings)

    def test_settings_validation(self):
        """Test settings validation."""
        # Create invalid settings
        invalid_settings = AccessibilitySettings(
            dyslexia_font_size=40,  # Too large
            line_spacing=0.5,       # Too small
            letter_spacing=0.8,     # Too large
            text_alignment='invalid'  # Invalid alignment
        )
        
        errors = self.plugin.validate_settings(invalid_settings)
        
        self.assertIn('Dyslexia font size must be between 10 and 36', errors)
        self.assertIn('Line spacing must be between 1.0 and 3.0', errors)
        self.assertIn('Letter spacing must be between 0.0 and 0.5', errors)
        self.assertIn('Text alignment must be left, center, right, or justify', errors)

    def test_accessibility_score(self):
        """Test accessibility content scoring."""
        content = """
        <h1>Main Title</h1>
        <p>This is a paragraph with a <a href="#">click here</a> link.</p>
        <img src="image.jpg">
        """
        
        score = self.plugin.get_accessibility_score(content)
        
        self.assertIn('score', score)
        self.assertIn('issues', score)
        self.assertIn('recommendations', score)
        
        # Should detect missing alt text and non-descriptive link
        self.assertLess(score['score'], 100)
        self.assertIn('Missing alt text for images', score['issues'])
        self.assertIn('Non-descriptive link text', score['issues'])

    def test_screen_reader_text_generation(self):
        """Test screen reader text generation."""
        content = "Click here to continue"
        context = "Navigation link"
        
        # With screen reader enabled
        self.plugin.update_settings({'screen_reader_enabled': True})
        sr_text = self.plugin.generate_screen_reader_text(content, context)
        self.assertIn(context, sr_text)
        self.assertIn(content, sr_text)
        
        # With skip navigation enabled
        self.plugin.update_settings({'skip_navigation': True})
        sr_text = self.plugin.generate_screen_reader_text(content, context)
        self.assertIn('Alt+Shift+N', sr_text)

    def test_focus_order(self):
        """Test focus order management."""
        # Default focus order
        focus_order = self.plugin.get_focus_order()
        expected_order = ['main_navigation', 'search_bar', 'content_area', 'sidebar', 'footer']
        self.assertEqual(focus_order, expected_order)
        
        # Custom focus order
        custom_order = ['search_bar', 'main_navigation', 'content_area']
        self.plugin.update_settings({'tab_order': custom_order})
        focus_order = self.plugin.get_focus_order()
        self.assertEqual(focus_order, custom_order)

    def test_persistence(self):
        """Test settings persistence."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the config directory
            with patch('os.path.expanduser') as mock_expanduser:
                mock_expanduser.return_value = temp_dir
                
                # Set some settings
                self.plugin.update_settings({
                    'mode': 'high_contrast',
                    'font_size': 'large',
                    'dyslexia_font': True
                })
                
                # Save settings
                self.plugin._save_settings()
                
                # Create new plugin instance
                new_plugin = AccessibilityPlugin()
                
                # Load settings
                new_plugin._load_settings()
                
                # Verify settings were loaded
                self.assertEqual(new_plugin.settings.mode, AccessibilityMode.HIGH_CONTRAST)
                self.assertEqual(new_plugin.settings.font_size, FontSize.LARGE)
                self.assertTrue(new_plugin.settings.dyslexia_font)

    def test_thread_safety(self):
        """Test thread safety of plugin operations."""
        import threading
        import time
        
        # Create multiple threads that update settings
        def update_settings():
            for i in range(10):
                self.plugin.update_settings({'font_size': 'large'})
                self.plugin.update_settings({'font_size': 'medium'})
                time.sleep(0.001)
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=update_settings)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should not raise any threading errors
        self.assertIn(self.plugin.settings.font_size, [FontSize.MEDIUM, FontSize.LARGE])

    def test_settings_to_dict_and_from_dict(self):
        """Test settings serialization and deserialization."""
        # Create custom settings
        original_settings = AccessibilitySettings(
            enabled=True,
            mode=AccessibilityMode.DYSLEXIA_FRIENDLY,
            font_size=FontSize.LARGE,
            contrast=ContrastLevel.HIGH,
            dyslexia_font=True,
            line_spacing=1.8,
            letter_spacing=0.15,
            custom_font_size=20,
            custom_line_spacing=2.0,
            custom_letter_spacing=0.20,
            text_alignment='left',
            screen_reader_enabled=True,
            aria_labels=True,
            keyboard_navigation=True,
            shortcuts_enabled=True,
            simplified_ui=True,
            clear_instructions=True,
            progress_indicators=True,
            error_messages=True,
            tts_enabled=True,
            tts_rate=1.2,
            tts_volume=0.8,
            tts_voice='test_voice'
        )
        
        # Convert to dict and back
        settings_dict = original_settings.to_dict()
        restored_settings = AccessibilitySettings.from_dict(settings_dict)
        
        # Verify all settings were preserved
        self.assertEqual(original_settings.enabled, restored_settings.enabled)
        self.assertEqual(original_settings.mode, restored_settings.mode)
        self.assertEqual(original_settings.font_size, restored_settings.font_size)
        self.assertEqual(original_settings.contrast, restored_settings.contrast)
        self.assertEqual(original_settings.dyslexia_font, restored_settings.dyslexia_font)
        self.assertEqual(original_settings.line_spacing, restored_settings.line_spacing)
        self.assertEqual(original_settings.letter_spacing, restored_settings.letter_spacing)
        self.assertEqual(original_settings.custom_font_size, restored_settings.custom_font_size)
        self.assertEqual(original_settings.custom_line_spacing, restored_settings.custom_line_spacing)
        self.assertEqual(original_settings.custom_letter_spacing, restored_settings.custom_letter_spacing)
        self.assertEqual(original_settings.text_alignment, restored_settings.text_alignment)
        self.assertEqual(original_settings.screen_reader_enabled, restored_settings.screen_reader_enabled)
        self.assertEqual(original_settings.aria_labels, restored_settings.aria_labels)
        self.assertEqual(original_settings.keyboard_navigation, restored_settings.keyboard_navigation)
        self.assertEqual(original_settings.shortcuts_enabled, restored_settings.shortcuts_enabled)
        self.assertEqual(original_settings.simplified_ui, restored_settings.simplified_ui)
        self.assertEqual(original_settings.clear_instructions, restored_settings.clear_instructions)
        self.assertEqual(original_settings.progress_indicators, restored_settings.progress_indicators)
        self.assertEqual(original_settings.error_messages, restored_settings.error_messages)
        self.assertEqual(original_settings.tts_enabled, restored_settings.tts_enabled)
        self.assertEqual(original_settings.tts_rate, restored_settings.tts_rate)
        self.assertEqual(original_settings.tts_volume, restored_settings.tts_volume)
        self.assertEqual(original_settings.tts_voice, restored_settings.tts_voice)

    def test_default_profiles(self):
        """Test that default profiles are properly set up."""
        default_profiles = ['default', 'high_contrast', 'dyslexia_friendly', 
                          'screen_reader', 'keyboard_only', 'simplified']
        
        profiles = self.plugin.list_profiles()
        for profile in default_profiles:
            self.assertIn(profile, profiles)
        
        # Test specific profile settings
        high_contrast_profile = self.plugin.get_profile('high_contrast')
        self.assertEqual(high_contrast_profile.mode, AccessibilityMode.HIGH_CONTRAST)
        self.assertEqual(high_contrast_profile.font_size, FontSize.LARGE)
        self.assertEqual(high_contrast_profile.contrast, ContrastLevel.MAXIMUM)
        
        dyslexia_profile = self.plugin.get_profile('dyslexia_friendly')
        self.assertEqual(dyslexia_profile.mode, AccessibilityMode.DYSLEXIA_FRIENDLY)
        self.assertTrue(dyslexia_profile.dyslexia_font)
        self.assertEqual(dyslexia_profile.line_spacing, 1.8)
        self.assertEqual(dyslexia_profile.letter_spacing, 0.15)


if __name__ == '__main__':
    unittest.main()
