# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""NoDupeLabs Core Module.

This module provides the core functionality with hard isolation
from optional dependencies.

Key Features:
    - Minimal core loader
    - Plugin management
    - Dependency injection
    - Graceful degradation

Dependencies:
    - Standard library only
"""

from .main import CoreLoader, main
from .container import ServiceContainer, container
from .plugins import PluginManager, plugin_manager

__all__ = [
    'CoreLoader',
    'main',
    'ServiceContainer',
    'container',
    'PluginManager',
    'plugin_manager'
]
