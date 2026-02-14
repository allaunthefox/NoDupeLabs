# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""NoDupeLabs Core Plugins Module.

This module provides plugin management functionality for the core system.
It serves as a compatibility layer and re-exports the plugin system components.
"""

from .plugin_system.registry import PluginRegistry

# Create plugin manager instance
plugin_manager = PluginRegistry()
PluginManager = PluginRegistry

__all__ = [
    'PluginManager',
    'plugin_manager'
]
