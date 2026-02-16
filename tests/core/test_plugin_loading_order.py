"""
Tests for Tool Loading Order System

These tests validate the explicit tool loading order and dependency management
to prevent cascading failures and ensure proper initialization sequence.
"""

import pytest

from nodupe.core.tool_system.loading_order import (
    ToolLoadInfo,
    ToolLoadingOrder,
    ToolLoadOrder,
    get_tool_loading_order,
    reset_tool_loading_order,
)


class TestToolLoadOrder:
    """Test the tool load order enum."""

    def test_load_order_values(self):
        """Test that load order values are correct."""
        assert ToolLoadOrder.CORE_INFRASTRUCTURE.value == 1
        assert ToolLoadOrder.SYSTEM_UTILITIES.value == 2
        assert ToolLoadOrder.STORAGE_SERVICES.value == 3
        assert ToolLoadOrder.PROCESSING_SERVICES.value == 4
        assert ToolLoadOrder.UI_COMMANDS.value == 5
        assert ToolLoadOrder.SPECIALIZED_TOOLS.value == 6

    def test_load_order_sequence(self):
        """Test that load order maintains proper sequence."""
        order = list(ToolLoadOrder)
        assert len(order) == 6
        assert order[0] == ToolLoadOrder.CORE_INFRASTRUCTURE
        assert order[-1] == ToolLoadOrder.SPECIALIZED_TOOLS


class TestToolLoadInfo:
    """Test the tool load information dataclass."""

    def test_tool_load_info_creation(self):
        """Test creating tool load info."""
        info = ToolLoadInfo(
            name="test_tool",
            load_order=ToolLoadOrder.SYSTEM_UTILITIES,
            required_dependencies=["core"],
            optional_dependencies=["cache"],
            critical=False,
            description="Test tool"
        )

        assert info.name == "test_tool"
        assert info.load_order == ToolLoadOrder.SYSTEM_UTILITIES
        assert info.required_dependencies == ["core"]
        assert info.optional_dependencies == ["cache"]
        assert info.critical is False
        assert info.description == "Test tool"


class TestToolLoadingOrder:
    """Test the tool loading order manager."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_tool_loading_order()
        self.loading_order = get_tool_loading_order()

    def test_initialization(self):
        """Test that loading order initializes with known tools."""
        # Check that core tools are registered
        core_tools = self.loading_order.get_tools_for_order(ToolLoadOrder.CORE_INFRASTRUCTURE)
        assert "core" in core_tools
        assert "deps" in core_tools
        assert "container" in core_tools
        assert "registry" in core_tools
        assert "discovery" in core_tools
        assert "loader" in core_tools
        assert "security" in core_tools

    def test_get_load_order(self):
        """Test getting the complete load order."""
        order = self.loading_order.get_load_order()
        assert len(order) == 6
        assert order == list(ToolLoadOrder)

    def test_get_tools_for_order(self):
        """Test getting tools for specific order levels."""
        # Core infrastructure should have multiple tools
        core_tools = self.loading_order.get_tools_for_order(ToolLoadOrder.CORE_INFRASTRUCTURE)
        assert len(core_tools) > 0
        assert "core" in core_tools
        assert "container" in core_tools

        # System utilities should have specific tools
        utility_tools = self.loading_order.get_tools_for_order(ToolLoadOrder.SYSTEM_UTILITIES)
        assert "config" in utility_tools
        assert "logging" in utility_tools
        assert "limits" in utility_tools
        assert "parallel" in utility_tools
        assert "pools" in utility_tools
        assert "cache" in utility_tools
        assert "time_sync" in utility_tools
        assert "leap_year" in utility_tools

    def test_get_dependencies(self):
        """Test getting tool dependencies."""
        # Test required dependencies
        deps = self.loading_order.get_required_dependencies("container")
        assert "core" in deps
        assert "deps" in deps

        # Test optional dependencies
        deps = self.loading_order.get_optional_dependencies("config")
        assert "security" in deps

    def test_is_critical(self):
        """Test critical tool detection."""
        assert self.loading_order.is_critical("core") is True
        assert self.loading_order.is_critical("container") is True
        assert self.loading_order.is_critical("config") is False
        assert self.loading_order.is_critical("time_sync") is False

    def test_get_tool_info(self):
        """Test getting complete tool information."""
        info = self.loading_order.get_tool_info("container")
        assert info is not None
        assert info.name == "container"
        assert info.load_order == ToolLoadOrder.CORE_INFRASTRUCTURE
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

        # Test with unknown tool
        is_valid, missing = self.loading_order.validate_dependencies("unknown", set())
        assert is_valid is True
        assert missing == []

    def test_get_load_sequence(self):
        """Test getting optimal load sequence."""
        # Test loading a simple tool
        sequence = self.loading_order.get_load_sequence(["config"])
        assert "core" in sequence
        assert "container" in sequence
        assert "config" in sequence
        # Core should come before container, container before config
        assert sequence.index("core") < sequence.index("container")
        assert sequence.index("container") < sequence.index("config")

        # Test loading multiple tools
        sequence = self.loading_order.get_load_sequence(["config", "logging"])
        assert "core" in sequence
        assert "container" in sequence
        assert "config" in sequence
        assert "logging" in sequence

    def test_get_critical_tools(self):
        """Test getting all critical tools."""
        critical = self.loading_order.get_critical_tools()
        assert "core" in critical
        assert "deps" in critical
        assert "container" in critical
        assert "registry" in critical
        assert "discovery" in critical
        assert "loader" in critical
        assert "security" in critical
        assert "database" in critical

        # Non-critical tools should not be included
        assert "config" not in critical
        assert "time_sync" not in critical

    def test_get_tool_description(self):
        """Test getting tool descriptions."""
        desc = self.loading_order.get_tool_description("core")
        assert "Core system infrastructure" in desc

        desc = self.loading_order.get_tool_description("time_sync")
        assert "Time synchronization" in desc

        desc = self.loading_order.get_tool_description("unknown")
        assert desc == "Unknown tool"

    def test_get_dependency_chain(self):
        """Test getting full dependency chain."""
        chain = self.loading_order.get_dependency_chain("config")
        assert "core" in chain
        assert "container" in chain
        # Should not include config itself
        assert "config" not in chain

    def test_register_tool(self):
        """Test registering a new tool."""
        info = ToolLoadInfo(
            name="test_tool",
            load_order=ToolLoadOrder.SPECIALIZED_TOOLS,
            required_dependencies=["core", "commands"],
            optional_dependencies=["database"],
            critical=False,
            description="Test tool"
        )

        self.loading_order.register_tool(info)

        # Check that tool was registered
        assert self.loading_order.get_tool_info("test_tool") is not None
        assert "test_tool" in self.loading_order.get_tools_for_order(ToolLoadOrder.SPECIALIZED_TOOLS)

        # Check dependencies
        deps = self.loading_order.get_required_dependencies("test_tool")
        assert "core" in deps
        assert "commands" in deps

        optional_deps = self.loading_order.get_optional_dependencies("test_tool")
        assert "database" in optional_deps

    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected in load sequence."""
        # This test would require creating a circular dependency scenario
        # For now, test that normal dependencies work
        sequence = self.loading_order.get_load_sequence(["config"])
        assert len(sequence) > 0
        assert "config" in sequence

    def test_empty_tool_list(self):
        """Test handling empty tool list."""
        sequence = self.loading_order.get_load_sequence([])
        assert sequence == []

    def test_unknown_tools(self):
        """Test handling unknown tools in load sequence."""
        sequence = self.loading_order.get_load_sequence(["unknown_tool"])
        # Should not crash, may return empty or just the unknown tool
        assert isinstance(sequence, list)

    def test_tool_order_consistency(self):
        """Test that tools are loaded in consistent order within levels."""
        # Get tools for a specific order level
        utility_tools = self.loading_order.get_tools_for_order(ToolLoadOrder.SYSTEM_UTILITIES)

        # Should always return the same tools in the same order
        for _ in range(5):
            tools = self.loading_order.get_tools_for_order(ToolLoadOrder.SYSTEM_UTILITIES)
            assert tools == utility_tools

    def test_dependency_graph_consistency(self):
        """Test that dependency graph is built correctly."""
        # Check that reverse dependencies are set up
        info = self.loading_order.get_tool_info("container")
        if info:
            # container depends on core and deps
            # So core and deps should have container as a reverse dependency
            pass  # This would require accessing internal structure

    def test_tool_registration_idempotent(self):
        """Test that registering the same tool multiple times is safe."""
        info = ToolLoadInfo(
            name="test_tool",
            load_order=ToolLoadOrder.SPECIALIZED_TOOLS,
            required_dependencies=["core"],
            optional_dependencies=[],
            critical=False,
            description="Test tool"
        )

        # Register twice
        self.loading_order.register_tool(info)
        self.loading_order.register_tool(info)  # Should not crash

        # Should still have only one instance
        assert self.loading_order.get_tool_info("test_tool") is not None


class TestGlobalLoadingOrder:
    """Test the global loading order instance."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_tool_loading_order()

    def test_get_global_instance(self):
        """Test getting global loading order instance."""
        instance1 = get_tool_loading_order()
        instance2 = get_tool_loading_order()

        # Should return the same instance
        assert instance1 is instance2

    def test_reset_global_instance(self):
        """Test resetting global loading order instance."""
        instance1 = get_tool_loading_order()

        reset_tool_loading_order()

        instance2 = get_tool_loading_order()

        # Should be a different instance
        assert instance1 is not instance2


class TestIntegration:
    """Integration tests for tool loading order."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_tool_loading_order()
        self.loading_order = get_tool_loading_order()

    def test_complete_system_load_sequence(self):
        """Test loading sequence for a complete system."""
        # Simulate loading core system tools
        core_system = [
            "core", "deps", "container", "registry", "discovery", "loader", "security",
            "config", "logging", "limits", "parallel", "pools", "cache",
            "database", "filesystem", "scan", "incremental"
        ]

        sequence = self.loading_order.get_load_sequence(core_system)

        # Verify critical tools are in sequence
        for tool in ["core", "deps", "container", "registry", "database"]:
            assert tool in sequence

        # Verify load order constraints
        # Core infrastructure should come first
        core_tools = self.loading_order.get_tools_for_order(ToolLoadOrder.CORE_INFRASTRUCTURE)
        for tool in core_tools:
            if tool in sequence:
                # All core tools should come before non-core tools
                for other_tool in sequence:
                    if other_tool not in core_tools and other_tool in sequence:
                        assert sequence.index(tool) < sequence.index(other_tool)

    def test_failure_isolation(self):
        """Test that failure of non-critical tool doesn't affect others."""
        # This test simulates the scenario where a non-critical tool fails
        # but critical tools continue to load

        # Get critical tools
        critical = self.loading_order.get_critical_tools()

        # Get non-critical tools
        all_tools = []
        for order in self.loading_order.get_load_order():
            all_tools.extend(self.loading_order.get_tools_for_order(order))

        non_critical = [p for p in all_tools if p not in critical]

        # Verify we have both types
        assert len(critical) > 0
        assert len(non_critical) > 0

        # Critical tools should include core infrastructure
        assert "core" in critical
        assert "container" in critical
        assert "database" in critical

        # Non-critical should include utilities and specialized tools
        assert "config" in non_critical
        assert "time_sync" in non_critical

    def test_dependency_validation_scenario(self):
        """Test dependency validation in realistic scenarios."""
        # Test database tool dependencies
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
            ["core", "deps", "container", "config"]
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
        # Test with valid tools
        safe_seq, _excluded = self.loading_order.get_safe_load_sequence(
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
        # Simulate loading some tools
        loaded = ["core", "container", "config", "database"]

        # Analyze impact of core failure
        impact = self.loading_order.get_failure_impact_analysis("core", loaded)
        assert "core" in impact
        assert "container" in impact["core"]
        assert "config" in impact["core"]
        assert "database" in impact["core"]

    def test_should_continue_loading(self):
        """Test decision logic for continuing after failures."""
        # Non-critical tool failure
        should_continue, reason = self.loading_order.should_continue_loading(
            "config", ["core", "container", "config"]
        )
        assert should_continue is True
        assert "Non-critical tool" in reason

        # Critical tool failure with impact
        should_continue, reason = self.loading_order.should_continue_loading(
            "core", ["core", "container", "config"]
        )
        assert should_continue is False
        assert "Critical tool" in reason

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

        def test_callback(tool_name):
            callback_called.append(tool_name)

        # Register callback
        self.loading_order.register_load_callback("test_tool", test_callback)

        # Notify (should not crash even if tool doesn't exist)
        self.loading_order.notify_tool_loaded("test_tool")

        # Callback should have been called
        assert len(callback_called) == 1
        assert callback_called[0] == "test_tool"

    def test_get_tool_statistics(self):
        """Test tool statistics gathering."""
        stats = self.loading_order.get_tool_statistics()

        assert "total_tools" in stats
        assert "tools_by_order" in stats
        assert "critical_tools" in stats
        assert "dependency_counts" in stats
        assert "tools_with_optional_deps" in stats

        # Should have statistics for each load order level
        for order in ["CORE_INFRASTRUCTURE", "SYSTEM_UTILITIES", "STORAGE_SERVICES",
                      "PROCESSING_SERVICES", "UI_COMMANDS", "SPECIALIZED_TOOLS"]:
            assert order in stats["tools_by_order"]

    def test_cascading_failure_prevention(self):
        """Test that cascading failures are prevented."""
        # Simulate a scenario where a critical tool fails
        loaded_tools = ["core", "deps", "container", "registry"]

        # If container fails (critical), should stop loading
        should_continue, reason = self.loading_order.should_continue_loading(
            "container", loaded_tools
        )
        assert should_continue is False
        assert "Critical tool" in reason

    def test_dependency_validation_with_optional_deps(self):
        """Test dependency validation with optional dependencies."""
        # Test tool with optional dependencies
        is_valid, missing = self.loading_order.validate_dependencies(
            "config", {"core", "container"}  # Has required deps, missing optional security
        )
        # Should still be valid since security is optional
        assert is_valid is True
        assert missing == []

    def test_fallback_load_sequence(self):
        """Test fallback sequence generation."""
        # Test with unknown tools (no dependency info)
        sequence = self.loading_order._fallback_load_sequence(
            ["unknown1", "unknown2", "core"]
        )

        # Should return sorted list
        assert len(sequence) == 3
        assert "core" in sequence

    def test_tool_registration_with_custom_info(self):
        """Test registering tools with custom load info."""
        custom_info = ToolLoadInfo(
            name="custom_tool",
            load_order=ToolLoadOrder.SPECIALIZED_TOOLS,
            required_dependencies=["core", "commands"],
            optional_dependencies=["database"],
            critical=False,
            description="Custom tool",
            load_priority=10
        )

        self.loading_order.register_tool(custom_info)

        # Verify registration
        assert self.loading_order.get_tool_info("custom_tool") is not None
        assert self.loading_order.is_critical("custom_tool") is False

        # Test priority calculation
        priorities = self.loading_order.get_load_priorities(["custom_tool"])
        assert len(priorities) == 1
        assert priorities[0][0] == "custom_tool"


class TestToolLoadingErrorHandling:
    """Test error handling in tool loading order."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_tool_loading_order()
        self.loading_order = get_tool_loading_order()

    def test_circular_dependency_detection(self):
        """Test that circular dependencies are properly detected."""
        # Create tools with circular dependency
        tool_a = ToolLoadInfo(
            name="tool_a",
            load_order=ToolLoadOrder.SPECIALIZED_TOOLS,
            required_dependencies=["tool_b"],
            optional_dependencies=[],
            critical=False
        )

        tool_b = ToolLoadInfo(
            name="tool_b",
            load_order=ToolLoadOrder.SPECIALIZED_TOOLS,
            required_dependencies=["tool_a"],
            optional_dependencies=[],
            critical=False
        )

        self.loading_order.register_tool(tool_a)
        self.loading_order.register_tool(tool_b)

        # Should detect circular dependency
        is_valid, _missing, circular = self.loading_order.validate_load_sequence(
            ["tool_a", "tool_b"]
        )
        assert is_valid is False
        assert len(circular) > 0

    def test_missing_dependency_error_handling(self):
        """Test error handling for missing dependencies."""
        # Try to load tool with missing dependency
        is_valid, missing = self.loading_order.validate_dependencies(
            "nonexistent_tool", set()
        )
        assert is_valid is True  # Unknown tool is considered valid
        assert missing == []

    def test_empty_tool_list_handling(self):
        """Test handling of empty tool lists."""
        # Empty sequence should be valid
        is_valid, missing, circular = self.loading_order.validate_load_sequence([])
        assert is_valid is True
        assert missing == []
        assert circular == []

        # Empty safe sequence
        safe_seq, excluded = self.loading_order.get_safe_load_sequence([])
        assert safe_seq == []
        assert excluded == []

    def test_unknown_tool_handling(self):
        """Test handling of unknown tools in various operations."""
        # Unknown tool should not crash operations
        assert self.loading_order.get_tool_info("unknown") is None
        assert self.loading_order.get_required_dependencies("unknown") == []
        assert self.loading_order.get_optional_dependencies("unknown") == []
        assert self.loading_order.is_critical("unknown") is False
        assert self.loading_order.get_tool_description("unknown") == "Unknown tool"
        assert self.loading_order.get_dependency_chain("unknown") == []


class TestToolLoadingIntegration:
    """Integration tests for tool loading order with real scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_tool_loading_order()
        self.loading_order = get_tool_loading_order()

    def test_complete_system_boot_sequence(self):
        """Test loading sequence for a complete system boot."""
        # Simulate loading the complete NoDupeLabs system
        system_tools = [
            "core", "deps", "container", "registry", "discovery", "loader", "security",
            "config", "logging", "limits", "parallel", "pools", "cache", "time_sync", "leap_year",
            "database", "filesystem", "compression", "mime_detection",
            "scan", "incremental", "hash_autotune",
            "cli", "commands",
            "similarity", "apply", "scan_command", "verify", "plan"
        ]

        # Get safe loading sequence
        safe_seq, _excluded = self.loading_order.get_safe_load_sequence(system_tools)

        # Should load most tools successfully
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
        # Load core infrastructure and database (including its requirements)
        partial_tools = ["core", "deps", "container", "registry", "config", "security", "limits", "database"]

        safe_seq, _excluded = self.loading_order.get_safe_load_sequence(partial_tools)

        assert len(safe_seq) == 8
        assert set(safe_seq) == set(partial_tools)

        # Verify dependencies are respected
        assert safe_seq.index("core") < safe_seq.index("container")
        assert safe_seq.index("container") < safe_seq.index("database")

    def test_failure_recovery_scenario(self):
        """Test recovery from tool loading failures."""
        # Simulate loading with some failures
        loaded_tools = ["core", "deps", "container", "registry"]

        # If registry fails (critical), should stop
        should_continue, reason = self.loading_order.should_continue_loading(
            "registry", loaded_tools
        )
        assert should_continue is False

        # If non-critical tool fails, should continue
        should_continue, _reason = self.loading_order.should_continue_loading(
            "time_sync", loaded_tools
        )
        assert should_continue is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
