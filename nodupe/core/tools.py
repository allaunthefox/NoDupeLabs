# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""NoDupeLabs Core Plugins Module.

This module provides tool management functionality for the core system.
It serves as a compatibility layer and re-exports the tool system components.
"""

from .tool_system.registry import PluginRegistry


# Create tool manager instance
tool_manager = PluginRegistry()
PluginManager = PluginRegistry

__all__ = [
    'PluginManager',
    'tool_manager'
]
