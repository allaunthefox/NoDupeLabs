"""
Plugin Loading Order Management

This module defines explicit plugin loading order and dependency management
to prevent cascading failures and ensure proper initialization sequence.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Dict, List, Set, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


class PluginLoadOrder(Enum):
    """Explicit plugin loading order levels."""
    
    # Core infrastructure - must load first
    CORE_INFRASTRUCTURE = 1
    
    # System utilities - depend on core infrastructure
    SYSTEM_UTILITIES = 2
    
    # Database and storage - depend on system utilities
    STORAGE_SERVICES = 3
    
    # Processing and analysis - depend on storage
    PROCESSING_SERVICES = 4
    
    # User interface and commands - depend on processing
    UI_COMMANDS = 5
    
    # Specialized plugins - depend on UI/commands
    SPECIALIZED_PLUGINS = 6


@dataclass
class PluginLoadInfo:
    """Information about plugin loading requirements."""
    name: str
    load_order: PluginLoadOrder
    required_dependencies: List[str]
    optional_dependencies: List[str]
    critical: bool = False  # If True, failure prevents loading other plugins
    description: str = ""
    load_priority: int = 0  # Higher priority loads first within same order level


class PluginLoadingError(Exception):
    """Exception raised when plugin loading fails."""
    pass


class PluginDependencyError(PluginLoadingError):
    """Exception raised when plugin dependencies cannot be resolved."""
    pass


class PluginLoadingOrder:
    """Manages explicit plugin loading order and dependencies."""
    
    def __init__(self):
        """Initialize the plugin loading order manager."""
        self._plugin_info: Dict[str, PluginLoadInfo] = {}
        self._load_order_groups: Dict[PluginLoadOrder, List[str]] = {
            order: [] for order in PluginLoadOrder
        }
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._reverse_dependencies: Dict[str, Set[str]] = {}
        self._load_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # Initialize known plugin order
        self._initialize_known_plugins()
    
    def _initialize_known_plugins(self):
        """Initialize known plugin loading order and dependencies."""
        
        # Core Infrastructure (must load first)
        core_plugins = [
            PluginLoadInfo(
                name="core",
                load_order=PluginLoadOrder.CORE_INFRASTRUCTURE,
                required_dependencies=[],
                optional_dependencies=[],
                critical=True,
                description="Core system infrastructure"
            ),
            PluginLoadInfo(
                name="deps",
                load_order=PluginLoadOrder.CORE_INFRASTRUCTURE,
                required_dependencies=[],
                optional_dependencies=[],
                critical=True,
                description="Dependency management"
            ),
            PluginLoadInfo(
                name="container",
                load_order=PluginLoadOrder.CORE_INFRASTRUCTURE,
                required_dependencies=["core", "deps"],
                optional_dependencies=[],
                critical=True,
                description="Dependency injection container"
            ),
            PluginLoadInfo(
                name="registry",
                load_order=PluginLoadOrder.CORE_INFRASTRUCTURE,
                required_dependencies=["core", "container"],
                optional_dependencies=[],
                critical=True,
                description="Plugin registry"
            ),
            PluginLoadInfo(
                name="discovery",
                load_order=PluginLoadOrder.CORE_INFRASTRUCTURE,
                required_dependencies=["core", "registry"],
                optional_dependencies=[],
                critical=True,
                description="Plugin discovery"
            ),
            PluginLoadInfo(
                name="loader",
                load_order=PluginLoadOrder.CORE_INFRASTRUCTURE,
                required_dependencies=["core", "registry", "discovery"],
                optional_dependencies=[],
                critical=True,
                description="Plugin loader"
            ),
            PluginLoadInfo(
                name="security",
                load_order=PluginLoadOrder.CORE_INFRASTRUCTURE,
                required_dependencies=["core"],
                optional_dependencies=[],
                critical=True,
                description="Security services"
            ),
        ]
        
        # System Utilities (depend on core infrastructure)
        utility_plugins = [
            PluginLoadInfo(
                name="config",
                load_order=PluginLoadOrder.SYSTEM_UTILITIES,
                required_dependencies=["core", "container"],
                optional_dependencies=["security"],
                critical=False,
                description="Configuration management"
            ),
            PluginLoadInfo(
                name="logging",
                load_order=PluginLoadOrder.SYSTEM_UTILITIES,
                required_dependencies=["core", "config"],
                optional_dependencies=[],
                critical=False,
                description="Logging services"
            ),
            PluginLoadInfo(
                name="limits",
                load_order=PluginLoadOrder.SYSTEM_UTILITIES,
                required_dependencies=["core", "config"],
                optional_dependencies=[],
                critical=False,
                description="System limits"
            ),
            PluginLoadInfo(
                name="parallel",
                load_order=PluginLoadOrder.SYSTEM_UTILITIES,
                required_dependencies=["core", "limits"],
                optional_dependencies=[],
                critical=False,
                description="Parallel processing"
            ),
            PluginLoadInfo(
                name="pools",
                load_order=PluginLoadOrder.SYSTEM_UTILITIES,
                required_dependencies=["core", "parallel"],
                optional_dependencies=[],
                critical=False,
                description="Resource pools"
            ),
            PluginLoadInfo(
                name="cache",
                load_order=PluginLoadOrder.SYSTEM_UTILITIES,
                required_dependencies=["core", "pools"],
                optional_dependencies=[],
                critical=False,
                description="Caching services"
            ),
            PluginLoadInfo(
                name="time_sync",
                load_order=PluginLoadOrder.SYSTEM_UTILITIES,
                required_dependencies=["core", "cache"],
                optional_dependencies=["security"],
                critical=False,
                description="Time synchronization"
            ),
            PluginLoadInfo(
                name="leap_year",
                load_order=PluginLoadOrder.SYSTEM_UTILITIES,
                required_dependencies=["core"],
                optional_dependencies=[],
                critical=False,
                description="Leap year calculations"
            ),
        ]
        
        # Storage Services (depend on system utilities)
        storage_plugins = [
            PluginLoadInfo(
                name="database",
                load_order=PluginLoadOrder.STORAGE_SERVICES,
                required_dependencies=["core", "config", "security", "limits"],
                optional_dependencies=["cache", "time_sync"],
                critical=True,
                description="Database services"
            ),
            PluginLoadInfo(
                name="filesystem",
                load_order=PluginLoadOrder.STORAGE_SERVICES,
                required_dependencies=["core", "limits"],
                optional_dependencies=["cache"],
                critical=False,
                description="File system operations"
            ),
            PluginLoadInfo(
                name="compression",
                load_order=PluginLoadOrder.STORAGE_SERVICES,
                required_dependencies=["core", "filesystem"],
                optional_dependencies=[],
                critical=False,
                description="Compression utilities"
            ),
            PluginLoadInfo(
                name="mime_detection",
                load_order=PluginLoadOrder.STORAGE_SERVICES,
                required_dependencies=["core", "filesystem"],
                optional_dependencies=[],
                critical=False,
                description="MIME type detection"
            ),
        ]
        
        # Processing Services (depend on storage)
        processing_plugins = [
            PluginLoadInfo(
                name="scan",
                load_order=PluginLoadOrder.PROCESSING_SERVICES,
                required_dependencies=["core", "filesystem", "limits", "parallel"],
                optional_dependencies=["mime_detection", "compression"],
                critical=False,
                description="File scanning"
            ),
            PluginLoadInfo(
                name="incremental",
                load_order=PluginLoadOrder.PROCESSING_SERVICES,
                required_dependencies=["core", "database", "scan"],
                optional_dependencies=["time_sync"],
                critical=False,
                description="Incremental processing"
            ),
            PluginLoadInfo(
                name="hash_autotune",
                load_order=PluginLoadOrder.PROCESSING_SERVICES,
                required_dependencies=["core", "limits", "parallel"],
                optional_dependencies=[],
                critical=False,
                description="Hash autotuning"
            ),
        ]
        
        # UI/Commands (depend on processing)
        ui_plugins = [
            PluginLoadInfo(
                name="cli",
                load_order=PluginLoadOrder.UI_COMMANDS,
                required_dependencies=["core", "config", "logging"],
                optional_dependencies=["database", "scan"],
                critical=False,
                description="Command line interface"
            ),
            PluginLoadInfo(
                name="commands",
                load_order=PluginLoadOrder.UI_COMMANDS,
                required_dependencies=["core", "cli", "database"],
                optional_dependencies=["scan", "incremental"],
                critical=False,
                description="Command implementations"
            ),
        ]
        
        # Specialized Plugins (depend on UI/commands)
        specialized_plugins = [
            PluginLoadInfo(
                name="similarity",
                load_order=PluginLoadOrder.SPECIALIZED_PLUGINS,
                required_dependencies=["core", "commands", "database"],
                optional_dependencies=["scan", "incremental"],
                critical=False,
                description="Similarity detection"
            ),
            PluginLoadInfo(
                name="apply",
                load_order=PluginLoadOrder.SPECIALIZED_PLUGINS,
                required_dependencies=["core", "commands", "database"],
                optional_dependencies=["scan"],
                critical=False,
                description="Apply operations"
            ),
            PluginLoadInfo(
                name="scan_command",
                load_order=PluginLoadOrder.SPECIALIZED_PLUGINS,
                required_dependencies=["core", "commands", "scan"],
                optional_dependencies=["database"],
                critical=False,
                description="Scan command"
            ),
            PluginLoadInfo(
                name="verify",
                load_order=PluginLoadOrder.SPECIALIZED_PLUGINS,
                required_dependencies=["core", "commands", "database"],
                optional_dependencies=["scan"],
                critical=False,
                description="Verification tools"
            ),
            PluginLoadInfo(
                name="plan",
                load_order=PluginLoadOrder.SPECIALIZED_PLUGINS,
                required_dependencies=["core", "commands", "database"],
                optional_dependencies=["scan"],
                critical=False,
                description="Plan operations"
            ),
        ]
        
        # Register all plugins
        all_plugins = (
            core_plugins + utility_plugins + storage_plugins + 
            processing_plugins + ui_plugins + specialized_plugins
        )
        
        for plugin_info in all_plugins:
            self.register_plugin(plugin_info)
    
    def register_plugin(self, plugin_info: PluginLoadInfo) -> None:
        """Register a plugin with its loading requirements.
        
        Args:
            plugin_info: Plugin loading information
        """
        self._plugin_info[plugin_info.name] = plugin_info
        self._load_order_groups[plugin_info.load_order].append(plugin_info.name)
        
        # Build dependency graph
        self._dependency_graph[plugin_info.name] = set(plugin_info.required_dependencies)
        self._reverse_dependencies[plugin_info.name] = set()
        
        # Update reverse dependencies
        for dep in plugin_info.required_dependencies:
            if dep not in self._reverse_dependencies:
                self._reverse_dependencies[dep] = set()
            self._reverse_dependencies[dep].add(plugin_info.name)
    
    def get_load_order(self) -> List[PluginLoadOrder]:
        """Get the plugin loading order levels.
        
        Returns:
            List of load order levels in sequence
        """
        return list(PluginLoadOrder)
    
    def get_plugins_for_order(self, order: PluginLoadOrder) -> List[str]:
        """Get plugins that should be loaded at a specific order level.
        
        Args:
            order: Load order level
            
        Returns:
            List of plugin names for this order level
        """
        return self._load_order_groups.get(order, [])
    
    def get_required_dependencies(self, plugin_name: str) -> List[str]:
        """Get required dependencies for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            List of required dependency names
        """
        if plugin_name not in self._plugin_info:
            return []
        return self._plugin_info[plugin_name].required_dependencies
    
    def get_optional_dependencies(self, plugin_name: str) -> List[str]:
        """Get optional dependencies for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            List of optional dependency names
        """
        if plugin_name not in self._plugin_info:
            return []
        return self._plugin_info[plugin_name].optional_dependencies
    
    def is_critical(self, plugin_name: str) -> bool:
        """Check if a plugin is critical (failure prevents other plugins).
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            True if plugin is critical
        """
        if plugin_name not in self._plugin_info:
            return False
        return self._plugin_info[plugin_name].critical
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginLoadInfo]:
        """Get plugin loading information.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            PluginLoadInfo if found, None otherwise
        """
        return self._plugin_info.get(plugin_name)
    
    def validate_dependencies(self, plugin_name: str, available_plugins: Set[str]) -> Tuple[bool, List[str]]:
        """Validate that all required dependencies are available.
        
        Args:
            plugin_name: Name of the plugin to validate
            available_plugins: Set of currently available plugins
            
        Returns:
            Tuple of (is_valid, missing_dependencies)
        """
        if plugin_name not in self._plugin_info:
            return True, []
        
        required_deps = set(self._plugin_info[plugin_name].required_dependencies)
        missing = required_deps - available_plugins
        
        return len(missing) == 0, list(missing)
    
    def get_load_sequence(self, plugin_names: List[str]) -> List[str]:
        """Get the optimal loading sequence for a set of plugins.
        
        Args:
            plugin_names: List of plugin names to load
            
        Returns:
            Ordered list of plugin names for loading (includes dependencies)
        """
        # Build complete set including all dependencies
        all_required = set(plugin_names)
        
        # Add all dependencies recursively
        for plugin_name in plugin_names:
            if plugin_name in self._plugin_info:
                deps = self.get_dependency_chain(plugin_name)
                all_required.update(deps)
        
        # Build dependency graph for all required plugins
        requested_set = all_required
        load_sequence = []
        visited = set()
        temp_mark = set()
        
        def visit(node: str) -> None:
            """TODO: Document visit."""
            if node in temp_mark:
                raise ValueError(f"Circular dependency detected involving {node}")
            
            if node not in visited:
                temp_mark.add(node)
                
                # Visit dependencies first
                if node in self._dependency_graph:
                    for dep in self._dependency_graph[node]:
                        if dep in requested_set:
                            visit(dep)
                
                temp_mark.remove(node)
                visited.add(node)
                load_sequence.append(node)
        
        # Sort plugins by load order first, then process
        plugins_by_order = {}
        for plugin_name in requested_set:
            if plugin_name in self._plugin_info:
                order = self._plugin_info[plugin_name].load_order
                if order not in plugins_by_order:
                    plugins_by_order[order] = []
                plugins_by_order[order].append(plugin_name)
        
        # Process in load order
        for order in self.get_load_order():
            if order in plugins_by_order:
                for plugin_name in plugins_by_order[order]:
                    visit(plugin_name)
        
        return load_sequence
    
    def get_critical_plugins(self) -> List[str]:
        """Get all critical plugins that must load successfully.
        
        Returns:
            List of critical plugin names
        """
        return [name for name, info in self._plugin_info.items() if info.critical]
    
    def get_plugin_description(self, plugin_name: str) -> str:
        """Get plugin description.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin description
        """
        if plugin_name in self._plugin_info:
            return self._plugin_info[plugin_name].description
        return "Unknown plugin"
    
    def get_dependency_chain(self, plugin_name: str) -> List[str]:
        """Get the full dependency chain for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            List of dependencies in loading order
        """
        chain = []
        visited = set()
        
        def add_deps(name: str) -> None:
            """TODO: Document add_deps."""
            if name in visited:
                return
            visited.add(name)
            
            if name in self._dependency_graph:
                for dep in self._dependency_graph[name]:
                    add_deps(dep)
            
            if name in self._plugin_info:
                chain.append(name)
        
        add_deps(plugin_name)
        return chain[:-1]  # Remove the plugin itself, return only dependencies
    
    def validate_load_sequence(self, plugin_names: List[str]) -> Tuple[bool, List[str], List[str]]:
        """Validate a complete plugin load sequence for dependencies and conflicts.
        
        Args:
            plugin_names: List of plugin names to load
            
        Returns:
            Tuple of (is_valid, missing_dependencies, circular_dependencies)
        """
        missing_deps = []
        circular_deps = []
        
        # Check for circular dependencies
        try:
            self.get_load_sequence(plugin_names)
        except ValueError as e:
            if "Circular dependency" in str(e):
                circular_deps.append(str(e))
        
        # Check all dependencies are available
        for plugin_name in plugin_names:
            if plugin_name in self._plugin_info:
                required_deps = self._plugin_info[plugin_name].required_dependencies
                for dep in required_deps:
                    if dep not in plugin_names and dep not in self._plugin_info:
                        missing_deps.append(f"{plugin_name} requires {dep}")
        
        return len(missing_deps) == 0 and len(circular_deps) == 0, missing_deps, circular_deps
    
    def get_safe_load_sequence(self, plugin_names: List[str]) -> Tuple[List[str], List[str]]:
        """Get a safe loading sequence that handles failures gracefully.
        
        Args:
            plugin_names: List of plugin names to load
            
        Returns:
            Tuple of (safe_sequence, excluded_plugins_due_to_missing_deps)
        """
        # First, get the optimal sequence
        try:
            optimal_sequence = self.get_load_sequence(plugin_names)
        except ValueError:
            # If there are circular dependencies, fall back to simple ordering
            optimal_sequence = self._fallback_load_sequence(plugin_names)
        
        # Group by load order and criticality
        safe_sequence = []
        excluded = []
        
        # Process by load order levels
        for order in self.get_load_order():
            order_plugins = [p for p in optimal_sequence if p in self._load_order_groups[order]]
            
            # Separate critical and non-critical plugins
            critical_plugins = [p for p in order_plugins if self.is_critical(p)]
            non_critical_plugins = [p for p in order_plugins if not self.is_critical(p)]
            
            # Load critical plugins first (they must succeed)
            safe_sequence.extend(critical_plugins)
            
            # Load non-critical plugins after critical ones
            safe_sequence.extend(non_critical_plugins)
        
        # Check for missing dependencies and exclude plugins that can't load
        available_for_validation = set(safe_sequence)
        for plugin_name in list(safe_sequence):
            is_valid, missing = self.validate_dependencies(plugin_name, available_for_validation - {plugin_name})
            if not is_valid:
                safe_sequence.remove(plugin_name)
                excluded.append(f"{plugin_name} (missing: {', '.join(missing)})")
        
        return safe_sequence, excluded
    
    def _fallback_load_sequence(self, plugin_names: List[str]) -> List[str]:
        """Fallback sequence generator when optimal fails."""
        # Sort by load order, then by name for deterministic ordering
        sorted_plugins = sorted(
            plugin_names,
            key=lambda name: (
                self._plugin_info.get(name, PluginLoadInfo(name, PluginLoadOrder.CORE_INFRASTRUCTURE, [], [])).load_order.value,
                name
            )
        )
        return sorted_plugins
    
    def get_failure_impact_analysis(self, failed_plugin: str, loaded_plugins: List[str]) -> Dict[str, List[str]]:
        """Analyze the impact of a plugin failure on other plugins.
        
        Args:
            failed_plugin: Name of the failed plugin
            loaded_plugins: List of plugins that have been loaded
            
        Returns:
            Dict mapping plugin names to lists of affected dependencies
        """
        impact = {}
        
        # Find plugins that depend on the failed plugin
        for plugin_name in loaded_plugins:
            if plugin_name == failed_plugin:
                continue
                
            if plugin_name in self._plugin_info:
                deps = self._plugin_info[plugin_name].required_dependencies
                if failed_plugin in deps:
                    if failed_plugin not in impact:
                        impact[failed_plugin] = []
                    impact[failed_plugin].append(plugin_name)
        
        return impact
    
    def should_continue_loading(self, failed_plugin: str, loaded_plugins: List[str]) -> Tuple[bool, str]:
        """Determine if loading should continue after a plugin failure.
        
        Args:
            failed_plugin: Name of the failed plugin
            loaded_plugins: List of plugins that have been loaded
            
        Returns:
            Tuple of (should_continue, reason)
        """
        if not self.is_critical(failed_plugin):
            return True, f"Non-critical plugin {failed_plugin} failed, continuing"
        
        # Critical plugin failed - analyze impact
        impact = self.get_failure_impact_analysis(failed_plugin, loaded_plugins)
        affected_critical = []
        
        for affected_plugin in impact.get(failed_plugin, []):
            if self.is_critical(affected_plugin):
                affected_critical.append(affected_plugin)
        
        if affected_critical:
            return False, f"Critical plugin {failed_plugin} failed, affecting: {', '.join(affected_critical)}"
        
        return True, f"Critical plugin {failed_plugin} failed but no other critical plugins depend on it"
    
    def get_load_priorities(self, plugin_names: List[str]) -> List[Tuple[str, int]]:
        """Get loading priorities for plugins based on dependencies and criticality.
        
        Args:
            plugin_names: List of plugin names
            
        Returns:
            List of (plugin_name, priority) tuples sorted by priority (higher = loads first)
        """
        priorities = []
        
        for plugin_name in plugin_names:
            if plugin_name not in self._plugin_info:
                continue
                
            info = self._plugin_info[plugin_name]
            
            # Base priority on load order (lower order = higher priority)
            base_priority = (6 - info.load_order.value) * 100
            
            # Add criticality bonus
            critical_bonus = 50 if info.critical else 0
            
            # Add dependency count bonus (plugins with more dependents should load first)
            dependency_bonus = len(self._reverse_dependencies.get(plugin_name, set())) * 10
            
            # Add configured priority
            configured_priority = info.load_priority
            
            total_priority = base_priority + critical_bonus + dependency_bonus + configured_priority
            priorities.append((plugin_name, total_priority))
        
        # Sort by priority descending
        priorities.sort(key=lambda x: x[1], reverse=True)
        return priorities
    
    def register_load_callback(self, plugin_name: str, callback: Callable) -> None:
        """Register a callback to be called when a plugin is loaded.
        
        Args:
            plugin_name: Name of the plugin
            callback: Function to call when plugin loads
        """
        self._load_callbacks[plugin_name].append(callback)
    
    def notify_plugin_loaded(self, plugin_name: str) -> None:
        """Notify all callbacks that a plugin has been loaded.
        
        Args:
            plugin_name: Name of the loaded plugin
        """
        for callback in self._load_callbacks.get(plugin_name, []):
            try:
                callback(plugin_name)
            except Exception as e:
                logger.error(f"Error in load callback for {plugin_name}: {e}")
    
    def get_plugin_statistics(self) -> Dict[str, Any]:
        """Get statistics about the plugin loading order configuration.
        
        Returns:
            Dict containing plugin statistics
        """
        stats = {
            'total_plugins': len(self._plugin_info),
            'plugins_by_order': {},
            'critical_plugins': self.get_critical_plugins(),
            'dependency_counts': {},
            'plugins_with_optional_deps': []
        }
        
        # Count plugins by order
        for order in self.get_load_order():
            stats['plugins_by_order'][order.name] = len(self.get_plugins_for_order(order))
        
        # Count dependencies
        for plugin_name, deps in self._dependency_graph.items():
            stats['dependency_counts'][plugin_name] = len(deps)
        
        # Find plugins with optional dependencies
        for plugin_name, info in self._plugin_info.items():
            if info.optional_dependencies:
                stats['plugins_with_optional_deps'].append(plugin_name)
        
        return stats


# Global plugin loading order instance
_global_loading_order = None


def get_plugin_loading_order() -> PluginLoadingOrder:
    """Get the global plugin loading order instance.
    
    Returns:
        PluginLoadingOrder instance
    """
    global _global_loading_order
    if _global_loading_order is None:
        _global_loading_order = PluginLoadingOrder()
    return _global_loading_order


def reset_plugin_loading_order():
    """Reset the global plugin loading order instance."""
    global _global_loading_order
    _global_loading_order = PluginLoadingOrder()
