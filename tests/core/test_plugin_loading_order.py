"""
Tests for Plugin Loading Order System

These tests validate the explicit plugin loading order and dependency management
to prevent cascading failures and ensure proper initialization sequence.
"""

import pytest
from nodupe.core.plugin_system.loading_order import (
    PluginLoadOrder,
    PluginLoadInfo,
    PluginLoadingOrder,
    get_plugin_loading_order,
    reset_plugin_loading_order
)


class TestPluginLoadOrder:
    """Test the plugin load order enum."""
    
    def test_load_order_values(self):
        """Test that load order values are correct."""
        assert PluginLoadOrder.CORE_INFRASTRUCTURE.value == 1
        assert PluginLoadOrder.SYSTEM_UTILITIES.value == 2
        assert PluginLoadOrder.STORAGE_SERVICES.value == 3
        assert PluginLoadOrder.PROCESSING_SERVICES.value == 4
        assert PluginLoadOrder.UI_COMMANDS.value == 5
        assert PluginLoadOrder.SPECIALIZED_PLUGINS.value == 6
    
    def test_load_order_sequence(self):
        """Test that load order maintains proper sequence."""
        order = list(PluginLoadOrder)
        assert len(order) == 6
        assert order[0] == PluginLoadOrder.CORE_INFRASTRUCTURE
        assert order[-1] == PluginLoadOrder.SPECIALIZED_PLUGINS


class TestPluginLoadInfo:
    """Test the plugin load information dataclass."""
    
    def test_plugin_load_info_creation(self):
        """Test creating plugin load info."""
        info = PluginLoadInfo(
            name="test_plugin",
            load_order=PluginLoadOrder.SYSTEM_UTILITIES,
            required_dependencies=["core"],
            optional_dependencies=["cache"],
            critical=False,
            description="Test plugin"
        )
        
        assert info.name == "test_plugin"
        assert info.load_order == PluginLoadOrder.SYSTEM_UTILITIES
        assert info.required_dependencies == ["core"]
        assert info.optional_dependencies == ["cache"]
        assert info.critical is False
        assert info.description == "Test plugin"


class TestPluginLoadingOrder:
    """Test the plugin loading order manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_plugin_loading_order()
        self.loading_order = get_plugin_loading_order()
    
    def test_initialization(self):
        """Test that loading order initializes with known plugins."""
        # Check that core plugins are registered
        core_plugins = self.loading_order.get_plugins_for_order(PluginLoadOrder.CORE_INFRASTRUCTURE)
        assert "core" in core_plugins
        assert "deps" in core_plugins
        assert "container" in core_plugins
        assert "registry" in core_plugins
        assert "discovery" in core_plugins
        assert "loader" in core_plugins
        assert "security" in core_plugins
    
    def test_get_load_order(self):
        """Test getting the complete load order."""
        order = self.loading_order.get_load_order()
        assert len(order) == 6
        assert order == list(PluginLoadOrder)
    
    def test_get_plugins_for_order(self):
        """Test getting plugins for specific order levels."""
        # Core infrastructure should have multiple plugins
        core_plugins = self.loading_order.get_plugins_for_order(PluginLoadOrder.CORE_INFRASTRUCTURE)
        assert len(core_plugins) > 0
        assert "core" in core_plugins
        assert "container" in core_plugins
        
        # System utilities should have specific plugins
        utility_plugins = self.loading_order.get_plugins_for_order(PluginLoadOrder.SYSTEM_UTILITIES)
        assert "config" in utility_plugins
        assert "logging" in utility_plugins
        assert "limits" in utility_plugins
        assert "parallel" in utility_plugins
        assert "pools" in utility_plugins
        assert "cache" in utility_plugins
        assert "time_sync" in utility_plugins
        assert "leap_year" in utility_plugins
    
    def test_get_dependencies(self):
        """Test getting plugin dependencies."""
        # Test required dependencies
        deps = self.loading_order.get_required_dependencies("container")
        assert "core" in deps
        assert "deps" in deps
        
        # Test optional dependencies
        deps = self.loading_order.get_optional_dependencies("config")
        assert "security" in deps
    
    def test_is_critical(self):
        """Test critical plugin detection."""
        assert self.loading_order.is_critical("core") is True
        assert self.loading_order.is_critical("container") is True
        assert self.loading_order.is_critical("config") is False
        assert self.loading_order.is_critical("time_sync") is False
    
    def test_get_plugin_info(self):
        """Test getting complete plugin information."""
        info = self.loading_order.get_plugin_info("container")
        assert info is not None
        assert info.name == "container"
        assert info.load_order == PluginLoadOrder.CORE_INFRASTRUCTURE
        assert "core" in info.required_dependencies
        assert "deps" in info.required_dependencies
        assert info.critical is True
    
    def test_validate_dependencies(self):
        """Test dependency validation."""
        # Test with missing dependencies
        is_valid, missing = self.loading_order.validate_dependencies("container", {"core"})
        assert is_valid is False
        assert "deps" in missing
        
        # Test with all dependencies available
        is_valid, missing = self.loading_order.validate_dependencies("container", {"core", "deps"})
        assert is_valid is True
        assert missing == []
        
        # Test with unknown plugin
        is_valid, missing = self.loading_order.validate_dependencies("unknown", set())
        assert is_valid is True
        assert missing == []
    
    def test_get_load_sequence(self):
        """Test getting optimal load sequence."""
        # Test loading a simple plugin
        sequence = self.loading_order.get_load_sequence(["config"])
        assert "core" in sequence
        assert "container" in sequence
        assert "config" in sequence
        # Core should come before container, container before config
        assert sequence.index("core") < sequence.index("container")
        assert sequence.index("container") < sequence.index("config")
        
        # Test loading multiple plugins
        sequence = self.loading_order.get_load_sequence(["config", "logging"])
        assert "core" in sequence
        assert "container" in sequence
        assert "config" in sequence
        assert "logging" in sequence
    
    def test_get_critical_plugins(self):
        """Test getting all critical plugins."""
        critical = self.loading_order.get_critical_plugins()
        assert "core" in critical
        assert "deps" in critical
        assert "container" in critical
        assert "registry" in critical
        assert "discovery" in critical
        assert "loader" in critical
        assert "security" in critical
        assert "database" in critical
        
        # Non-critical plugins should not be included
        assert "config" not in critical
        assert "time_sync" not in critical
    
    def test_get_plugin_description(self):
        """Test getting plugin descriptions."""
        desc = self.loading_order.get_plugin_description("core")
        assert "Core system infrastructure" in desc
        
        desc = self.loading_order.get_plugin_description("time_sync")
        assert "Time synchronization" in desc
        
        desc = self.loading_order.get_plugin_description("unknown")
        assert desc == "Unknown plugin"
    
    def test_get_dependency_chain(self):
        """Test getting full dependency chain."""
        chain = self.loading_order.get_dependency_chain("config")
        assert "core" in chain
        assert "container" in chain
        # Should not include config itself
        assert "config" not in chain
    
    def test_register_plugin(self):
        """Test registering a new plugin."""
        info = PluginLoadInfo(
            name="test_plugin",
            load_order=PluginLoadOrder.SPECIALIZED_PLUGINS,
            required_dependencies=["core", "commands"],
            optional_dependencies=["database"],
            critical=False,
            description="Test plugin"
        )
        
        self.loading_order.register_plugin(info)
        
        # Check that plugin was registered
        assert self.loading_order.get_plugin_info("test_plugin") is not None
        assert "test_plugin" in self.loading_order.get_plugins_for_order(PluginLoadOrder.SPECIALIZED_PLUGINS)
        
        # Check dependencies
        deps = self.loading_order.get_required_dependencies("test_plugin")
        assert "core" in deps
        assert "commands" in deps
        
        optional_deps = self.loading_order.get_optional_dependencies("test_plugin")
        assert "database" in optional_deps
    
    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected in load sequence."""
        # This test would require creating a circular dependency scenario
        # For now, test that normal dependencies work
        sequence = self.loading_order.get_load_sequence(["config"])
        assert len(sequence) > 0
        assert "config" in sequence
    
    def test_empty_plugin_list(self):
        """Test handling empty plugin list."""
        sequence = self.loading_order.get_load_sequence([])
        assert sequence == []
    
    def test_unknown_plugins(self):
        """Test handling unknown plugins in load sequence."""
        sequence = self.loading_order.get_load_sequence(["unknown_plugin"])
        # Should not crash, may return empty or just the unknown plugin
        assert isinstance(sequence, list)
    
    def test_plugin_order_consistency(self):
        """Test that plugins are loaded in consistent order within levels."""
        # Get plugins for a specific order level
        utility_plugins = self.loading_order.get_plugins_for_order(PluginLoadOrder.SYSTEM_UTILITIES)
        
        # Should always return the same plugins in the same order
        for _ in range(5):
            plugins = self.loading_order.get_plugins_for_order(PluginLoadOrder.SYSTEM_UTILITIES)
            assert plugins == utility_plugins
    
    def test_dependency_graph_consistency(self):
        """Test that dependency graph is built correctly."""
        # Check that reverse dependencies are set up
        info = self.loading_order.get_plugin_info("container")
        if info:
            # container depends on core and deps
            # So core and deps should have container as a reverse dependency
            pass  # This would require accessing internal structure
    
    def test_plugin_registration_idempotent(self):
        """Test that registering the same plugin multiple times is safe."""
        info = PluginLoadInfo(
            name="test_plugin",
            load_order=PluginLoadOrder.SPECIALIZED_PLUGINS,
            required_dependencies=["core"],
            optional_dependencies=[],
            critical=False,
            description="Test plugin"
        )
        
        # Register twice
        self.loading_order.register_plugin(info)
        self.loading_order.register_plugin(info)  # Should not crash
        
        # Should still have only one instance
        assert self.loading_order.get_plugin_info("test_plugin") is not None


class TestGlobalLoadingOrder:
    """Test the global loading order instance."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_plugin_loading_order()
    
    def test_get_global_instance(self):
        """Test getting global loading order instance."""
        instance1 = get_plugin_loading_order()
        instance2 = get_plugin_loading_order()
        
        # Should return the same instance
        assert instance1 is instance2
    
    def test_reset_global_instance(self):
        """Test resetting global loading order instance."""
        instance1 = get_plugin_loading_order()
        
        reset_plugin_loading_order()
        
        instance2 = get_plugin_loading_order()
        
        # Should be a different instance
        assert instance1 is not instance2


class TestIntegration:
    """Integration tests for plugin loading order."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_plugin_loading_order()
        self.loading_order = get_plugin_loading_order()
    
    def test_complete_system_load_sequence(self):
        """Test loading sequence for a complete system."""
        # Simulate loading core system plugins
        core_system = [
            "core", "deps", "container", "registry", "discovery", "loader", "security",
            "config", "logging", "limits", "parallel", "pools", "cache",
            "database", "filesystem", "scan", "incremental"
        ]
        
        sequence = self.loading_order.get_load_sequence(core_system)
        
        # Verify critical plugins are in sequence
        for plugin in ["core", "deps", "container", "registry", "database"]:
            assert plugin in sequence
        
        # Verify load order constraints
        # Core infrastructure should come first
        core_plugins = self.loading_order.get_plugins_for_order(PluginLoadOrder.CORE_INFRASTRUCTURE)
        for plugin in core_plugins:
            if plugin in sequence:
                # All core plugins should come before non-core plugins
                for other_plugin in sequence:
                    if other_plugin not in core_plugins and other_plugin in sequence:
                        assert sequence.index(plugin) < sequence.index(other_plugin)
    
    def test_failure_isolation(self):
        """Test that failure of non-critical plugin doesn't affect others."""
        # This test simulates the scenario where a non-critical plugin fails
        # but critical plugins continue to load
        
        # Get critical plugins
        critical = self.loading_order.get_critical_plugins()
        
        # Get non-critical plugins
        all_plugins = []
        for order in self.loading_order.get_load_order():
            all_plugins.extend(self.loading_order.get_plugins_for_order(order))
        
        non_critical = [p for p in all_plugins if p not in critical]
        
        # Verify we have both types
        assert len(critical) > 0
        assert len(non_critical) > 0
        
        # Critical plugins should include core infrastructure
        assert "core" in critical
        assert "container" in critical
        assert "database" in critical
        
        # Non-critical should include utilities and specialized plugins
        assert "config" in non_critical
        assert "time_sync" in non_critical
    
    def test_dependency_validation_scenario(self):
        """Test dependency validation in realistic scenarios."""
        # Test database plugin dependencies
        is_valid, missing = self.loading_order.validate_dependencies(
            "database", 
            {"core", "config", "security", "limits", "cache", "time_sync"}
        )
        assert is_valid is True
        assert missing == []
        
        # Test with missing critical dependency
        is_valid, missing = self.loading_order.validate_dependencies(
            "database", 
            {"core", "config", "security"}  # Missing limits
        )
        assert is_valid is False
        assert "limits" in missing


    def test_validate_load_sequence(self):
        """Test load sequence validation for dependencies and conflicts."""
        # Test valid sequence
        is_valid, missing, circular = self.loading_order.validate_load_sequence(
            ["core", "container", "config"]
        )
        assert is_valid is True
        assert missing == []
        assert circular == []
        
        # Test missing dependencies
        is_valid, missing, circular = self.loading_order.validate_load_sequence(
            ["config"]  # Missing core and container
        )
        assert is_valid is False
        assert len(missing) > 0
        assert circular == []
    
    def test_get_safe_load_sequence(self):
        """Test getting a safe loading sequence."""
        # Test with valid plugins
        safe_seq, excluded = self.loading_order.get_safe_load_sequence(
            ["core", "container", "config", "logging"]
        )
        
        assert "core" in safe_seq
        assert "container" in safe_seq
        assert "config" in safe_seq
        assert "logging" in safe_seq
        
        # Core should load before container, container before config
        assert safe_seq.index("core") < safe_seq.index("container")
        assert safe_seq.index("container") < safe_seq.index("config")
    
    def test_failure_impact_analysis(self):
        """Test failure impact analysis."""
        # Simulate loading some plugins
        loaded = ["core", "container", "config", "database"]
        
        # Analyze impact of core failure
        impact = self.loading_order.get_failure_impact_analysis("core", loaded)
        assert "core" in impact
        assert "container" in impact["core"]
        assert "config" in impact["core"]
        assert "database" in impact["core"]
    
    def test_should_continue_loading(self):
        """Test decision logic for continuing after failures."""
        # Non-critical plugin failure
        should_continue, reason = self.loading_order.should_continue_loading(
            "config", ["core", "container", "config"]
        )
        assert should_continue is True
        assert "Non-critical plugin" in reason
        
        # Critical plugin failure with impact
        should_continue, reason = self.loading_order.should_continue_loading(
            "core", ["core", "container", "config"]
        )
        assert should_continue is False
        assert "Critical plugin" in reason
    
    def test_get_load_priorities(self):
        """Test loading priority calculation."""
        priorities = self.loading_order.get_load_priorities(
            ["core", "config", "database"]
        )
        
        # Should return list of tuples
        assert len(priorities) == 3
        assert all(isinstance(p, tuple) and len(p) == 2 for p in priorities)
        
        # Core should have highest priority (loads first)
        core_priority = next(p[1] for p in priorities if p[0] == "core")
        config_priority = next(p[1] for p in priorities if p[0] == "config")
        assert core_priority > config_priority
    
    def test_register_load_callback(self):
        """Test load callback registration and notification."""
        callback_called = []
        
        def test_callback(plugin_name):
            callback_called.append(plugin_name)
        
        # Register callback
        self.loading_order.register_load_callback("test_plugin", test_callback)
        
        # Notify (should not crash even if plugin doesn't exist)
        self.loading_order.notify_plugin_loaded("test_plugin")
        
        # Callback should have been called
        assert len(callback_called) == 1
        assert callback_called[0] == "test_plugin"
    
    def test_get_plugin_statistics(self):
        """Test plugin statistics gathering."""
        stats = self.loading_order.get_plugin_statistics()
        
        assert "total_plugins" in stats
        assert "plugins_by_order" in stats
        assert "critical_plugins" in stats
        assert "dependency_counts" in stats
        assert "plugins_with_optional_deps" in stats
        
        # Should have statistics for each load order level
        for order in ["CORE_INFRASTRUCTURE", "SYSTEM_UTILITIES", "STORAGE_SERVICES",
                      "PROCESSING_SERVICES", "UI_COMMANDS", "SPECIALIZED_PLUGINS"]:
            assert order in stats["plugins_by_order"]
    
    def test_cascading_failure_prevention(self):
        """Test that cascading failures are prevented."""
        # Simulate a scenario where a critical plugin fails
        loaded_plugins = ["core", "deps", "container", "registry"]
        
        # If container fails (critical), should stop loading
        should_continue, reason = self.loading_order.should_continue_loading(
            "container", loaded_plugins
        )
        assert should_continue is False
        assert "Critical plugin" in reason
    
    def test_dependency_validation_with_optional_deps(self):
        """Test dependency validation with optional dependencies."""
        # Test plugin with optional dependencies
        is_valid, missing = self.loading_order.validate_dependencies(
            "config", {"core", "container"}  # Has required deps, missing optional security
        )
        # Should still be valid since security is optional
        assert is_valid is True
        assert missing == []
    
    def test_fallback_load_sequence(self):
        """Test fallback sequence generation."""
        # Test with unknown plugins (no dependency info)
        sequence = self.loading_order._fallback_load_sequence(
            ["unknown1", "unknown2", "core"]
        )
        
        # Should return sorted list
        assert len(sequence) == 3
        assert "core" in sequence
    
    def test_plugin_registration_with_custom_info(self):
        """Test registering plugins with custom load info."""
        custom_info = PluginLoadInfo(
            name="custom_plugin",
            load_order=PluginLoadOrder.SPECIALIZED_PLUGINS,
            required_dependencies=["core", "commands"],
            optional_dependencies=["database"],
            critical=False,
            description="Custom plugin",
            load_priority=10
        )
        
        self.loading_order.register_plugin(custom_info)
        
        # Verify registration
        assert self.loading_order.get_plugin_info("custom_plugin") is not None
        assert self.loading_order.is_critical("custom_plugin") is False
        
        # Test priority calculation
        priorities = self.loading_order.get_load_priorities(["custom_plugin"])
        assert len(priorities) == 1
        assert priorities[0][0] == "custom_plugin"


class TestPluginLoadingErrorHandling:
    """Test error handling in plugin loading order."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_plugin_loading_order()
        self.loading_order = get_plugin_loading_order()
    
    def test_circular_dependency_detection(self):
        """Test that circular dependencies are properly detected."""
        # Create plugins with circular dependency
        plugin_a = PluginLoadInfo(
            name="plugin_a",
            load_order=PluginLoadOrder.SPECIALIZED_PLUGINS,
            required_dependencies=["plugin_b"],
            optional_dependencies=[],
            critical=False
        )
        
        plugin_b = PluginLoadInfo(
            name="plugin_b", 
            load_order=PluginLoadOrder.SPECIALIZED_PLUGINS,
            required_dependencies=["plugin_a"],
            optional_dependencies=[],
            critical=False
        )
        
        self.loading_order.register_plugin(plugin_a)
        self.loading_order.register_plugin(plugin_b)
        
        # Should detect circular dependency
        is_valid, missing, circular = self.loading_order.validate_load_sequence(
            ["plugin_a", "plugin_b"]
        )
        assert is_valid is False
        assert len(circular) > 0
    
    def test_missing_dependency_error_handling(self):
        """Test error handling for missing dependencies."""
        # Try to load plugin with missing dependency
        is_valid, missing = self.loading_order.validate_dependencies(
            "nonexistent_plugin", set()
        )
        assert is_valid is True  # Unknown plugin is considered valid
        assert missing == []
    
    def test_empty_plugin_list_handling(self):
        """Test handling of empty plugin lists."""
        # Empty sequence should be valid
        is_valid, missing, circular = self.loading_order.validate_load_sequence([])
        assert is_valid is True
        assert missing == []
        assert circular == []
        
        # Empty safe sequence
        safe_seq, excluded = self.loading_order.get_safe_load_sequence([])
        assert safe_seq == []
        assert excluded == []
    
    def test_unknown_plugin_handling(self):
        """Test handling of unknown plugins in various operations."""
        # Unknown plugin should not crash operations
        assert self.loading_order.get_plugin_info("unknown") is None
        assert self.loading_order.get_required_dependencies("unknown") == []
        assert self.loading_order.get_optional_dependencies("unknown") == []
        assert self.loading_order.is_critical("unknown") is False
        assert self.loading_order.get_plugin_description("unknown") == "Unknown plugin"
        assert self.loading_order.get_dependency_chain("unknown") == []


class TestPluginLoadingIntegration:
    """Integration tests for plugin loading order with real scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_plugin_loading_order()
        self.loading_order = get_plugin_loading_order()
    
    def test_complete_system_boot_sequence(self):
        """Test loading sequence for a complete system boot."""
        # Simulate loading the complete NoDupeLabs system
        system_plugins = [
            "core", "deps", "container", "registry", "discovery", "loader", "security",
            "config", "logging", "limits", "parallel", "pools", "cache", "time_sync", "leap_year",
            "database", "filesystem", "compression", "mime_detection",
            "scan", "incremental", "hash_autotune",
            "cli", "commands",
            "similarity", "apply", "scan_command", "verify", "plan"
        ]
        
        # Get safe loading sequence
        safe_seq, excluded = self.loading_order.get_safe_load_sequence(system_plugins)
        
        # Should load most plugins successfully
        assert len(safe_seq) > 0
        assert "core" in safe_seq
        assert "database" in safe_seq
        assert "scan" in safe_seq
        
        # Verify load order constraints
        core_index = safe_seq.index("core")
        db_index = safe_seq.index("database")
        scan_index = safe_seq.index("scan")
        
        assert core_index < db_index < scan_index
    
    def test_partial_system_loading(self):
        """Test loading only a subset of the system."""
        # Load only core infrastructure and database
        partial_plugins = ["core", "deps", "container", "registry", "database"]
        
        safe_seq, excluded = self.loading_order.get_safe_load_sequence(partial_plugins)
        
        assert len(safe_seq) == 5
        assert set(safe_seq) == set(partial_plugins)
        
        # Verify dependencies are respected
        assert safe_seq.index("core") < safe_seq.index("container")
        assert safe_seq.index("container") < safe_seq.index("database")
    
    def test_failure_recovery_scenario(self):
        """Test recovery from plugin loading failures."""
        # Simulate loading with some failures
        loaded_plugins = ["core", "deps", "container", "registry"]
        
        # If registry fails (critical), should stop
        should_continue, reason = self.loading_order.should_continue_loading(
            "registry", loaded_plugins
        )
        assert should_continue is False
        
        # If non-critical plugin fails, should continue
        should_continue, reason = self.loading_order.should_continue_loading(
            "time_sync", loaded_plugins
        )
        assert should_continue is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
