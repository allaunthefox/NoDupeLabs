"""
Plugin System Module
Core infrastructure for plugin management
"""

from .base import Plugin
from .registry import PluginRegistry
from .loader import PluginLoader
from .discovery import PluginDiscovery
from .security import PluginSecurity
from .lifecycle import PluginLifecycle
from .dependencies import PluginDependencies
from .compatibility import PluginCompatibility
from .hot_reload import PluginHotReload

__all__ = [
    'Plugin',
    'PluginRegistry',
    'PluginLoader',
    'PluginDiscovery',
    'PluginSecurity',
    'PluginLifecycle',
    'PluginDependencies',
    'PluginCompatibility',
    'PluginHotReload'
]
