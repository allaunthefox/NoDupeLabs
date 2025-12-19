"""Plugin System Module.

Core infrastructure for plugin management.
"""

from .base import Plugin, PluginMetadata
from .registry import PluginRegistry
from .loader import PluginLoader
from .discovery import PluginDiscovery
from .security import PluginSecurity
from .lifecycle import PluginLifecycleManager
from .dependencies import DependencyResolver as PluginDependencies
from .compatibility import PluginCompatibility, PluginCompatibilityError
from .hot_reload import PluginHotReload

__all__ = [
    'Plugin',
    'PluginMetadata',
    'PluginRegistry',
    'PluginLoader',
    'PluginDiscovery',
    'PluginSecurity',
    'PluginLifecycleManager',
    'PluginDependencies',
    'PluginCompatibility',
    'PluginCompatibilityError',
    'PluginHotReload'
]
