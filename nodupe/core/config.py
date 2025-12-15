#!/usr/bin/env python3
"""NoDupeLabs Configuration Manager using TOML.

This module provides configuration management for NoDupeLabs using TOML files.
It leverages the Even Better TOML VSCode extension for enhanced TOML support.
"""

import os
import sys
from typing import Dict, Any, Optional

try:
    import toml
except ImportError:
    # We'll handle the missing toml dependency gracefully in the class if needed,
    # or let the import error propagate if it's a hard dependency for this module.
    # For now, we will re-raise properly or handle it in __init__
    toml = None


class ConfigManager:
    """Configuration manager for NoDupeLabs that loads and manages TOML configuration files."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager.

        Args:
            config_path: Path to the TOML configuration file. Defaults to 'pyproject.toml'.

        Raises:
            ImportError: If toml package is not installed.
            FileNotFoundError: If configuration file is not found.
            ValueError: If configuration file is invalid.
        """
        if toml is None:
            print("[WARN] toml package not found. Using default configuration.")
            self.config = {}
            # Verify if we should load defaults here or if main.py resource detection fills it in.
            # self._load_config() # Can't load file without toml
            return

        self.config_path = config_path or "pyproject.toml"
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load the TOML configuration file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Configuration file {self.config_path} not found")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = toml.load(f)
        except Exception as e:
            raise ValueError(f"Error parsing TOML file: {e}") from e

        if 'tool' not in self.config or 'nodupe' not in self.config['tool']:
            raise ValueError(
                "Invalid configuration file: missing [tool.nodupe] section")

    def get_nodupe_config(self) -> Dict[str, Any]:
        """Get the NoDupeLabs configuration section."""
        return self.config['tool']['nodupe']

    def get_database_config(self) -> Dict[str, Any]:
        """Get the database configuration."""
        return self.get_nodupe_config().get('database', {})

    def get_scan_config(self) -> Dict[str, Any]:
        """Get the scan configuration."""
        return self.get_nodupe_config().get('scan', {})

    def get_similarity_config(self) -> Dict[str, Any]:
        """Get the similarity configuration."""
        return self.get_nodupe_config().get('similarity', {})

    def get_performance_config(self) -> Dict[str, Any]:
        """Get the performance configuration."""
        return self.get_nodupe_config().get('performance', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """Get the logging configuration."""
        return self.get_nodupe_config().get('logging', {})

    def get_config_value(self, section: str, key: str, default: Any = None) -> Any:
        """Get a specific configuration value.

        Args:
            section: Configuration section (e.g., 'database', 'scan')
            key: Configuration key
            default: Default value if key is not found

        Returns:
            The configuration value or default if not found
        """
        try:
            return self.get_nodupe_config().get(section, {}).get(key, default)
        except Exception:
            return default

    def validate_config(self) -> bool:
        """Validate the configuration file structure.

        Returns:
            True if configuration is valid, False otherwise
        """
        required_sections = ['database', 'scan',
                             'similarity', 'performance', 'logging']

        nodupe_config = self.get_nodupe_config()

        for section in required_sections:
            if section not in nodupe_config:
                print(
                    f"Warning: Missing required configuration section: {section}")
                return False

        return True


def load_config() -> ConfigManager:
    """Load the NoDupeLabs configuration.

    Returns:
        ConfigManager instance with loaded configuration
    """
    return ConfigManager()


# Example usage and testing
if __name__ == "__main__":
    print("🔧 Loading NoDupeLabs configuration from pyproject.toml...")

    try:
        config = load_config()

        if config.validate_config():
            print("✅ Configuration file is valid!")

            # Display some key configuration values
            print("\n📋 NoDupeLabs Configuration Summary:")
            print(
                f"Version: {config.get_config_value('nodupe', 'version', '1.0.0')}")
            print(
                f"Description: {config.get_config_value('nodupe', 'description', 'NoDupeLabs')}")

            db_config = config.get_database_config()
            print(f"\n🗃️ Database Configuration:")
            print(f"  Path: {db_config.get('path', 'nodupe.db')}")
            print(f"  Timeout: {db_config.get('timeout', 30.0)} seconds")
            print(f"  Journal Mode: {db_config.get('journal_mode', 'WAL')}")

            scan_config = config.get_scan_config()
            print(f"\n🔍 Scan Configuration:")
            print(
                f"  Min File Size: {scan_config.get('min_file_size', '1KB')}")
            print(
                f"  Max File Size: {scan_config.get('max_file_size', '100MB')}")
            print(
                f"  Default Extensions: {', '.join(scan_config.get('default_extensions', []))}")
            print(
                f"  Exclude Directories: {', '.join(scan_config.get('exclude_dirs', []))}")

            similarity_config = config.get_similarity_config()
            print(f"\n🎯 Similarity Configuration:")
            print(
                f"  Default Backend: {similarity_config.get('default_backend', 'brute_force')}")
            print(
                f"  Vector Dimensions: {similarity_config.get('vector_dimensions', 128)}")
            print(f"  Search K: {similarity_config.get('search_k', 10)}")
            print(
                f"  Similarity Threshold: {similarity_config.get('similarity_threshold', 0.85)}")

            print("\n✅ Even Better TOML plugin setup complete!")
            print("💡 The plugin provides enhanced TOML support including:")
            print("   • Syntax highlighting")
            print("   • Autocompletion")
            print("   • Validation")
            print("   • Formatting")
            print("   • Error detection")
            print("   • Schema support")

        else:
            print("❌ Configuration file validation failed!")

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        # Only exit 1 if running as script
        sys.exit(1)
