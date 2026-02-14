"""Test plugin compatibility functionality."""

import pytest
from unittest.mock import MagicMock
from nodupe.core.plugin_system.compatibility import PluginCompatibility, PluginCompatibilityError
from nodupe.core.plugin_system.base import Plugin


class TestPluginCompatibility:
    """Test plugin compatibility core functionality."""

    def test_plugin_compatibility_initialization(self):
        """Test plugin compatibility initialization."""
        compatibility = PluginCompatibility()
        assert compatibility is not None
        assert isinstance(compatibility, PluginCompatibility)

        # Test that it has expected attributes
        assert hasattr(compatibility, 'check_compatibility')
        assert hasattr(compatibility, 'get_compatibility_report')
        assert hasattr(compatibility, 'initialize')
        assert hasattr(compatibility, 'shutdown')

    def test_plugin_compatibility_with_container(self):
        """Test plugin compatibility with dependency container."""
        from nodupe.core.container import ServiceContainer

        compatibility = PluginCompatibility()
        container = ServiceContainer()

        # Initialize compatibility with container
        compatibility.initialize(container)
        assert compatibility.container is container

    def test_plugin_compatibility_lifecycle(self):
        """Test plugin compatibility lifecycle operations."""
        from nodupe.core.container import ServiceContainer

        compatibility = PluginCompatibility()
        container = ServiceContainer()

        # Test initialization
        compatibility.initialize(container)
        assert compatibility.container is container

        # Test shutdown
        compatibility.shutdown()
        assert compatibility.container is None

        # Test re-initialization
        compatibility.initialize(container)
        assert compatibility.container is container


class TestPluginCompatibilityOperations:
    """Test plugin compatibility operations."""

    def test_check_compatibility(self):
        """Test checking plugin compatibility."""
        compatibility = PluginCompatibility()

        # Create a test plugin
        class TestPlugin(Plugin):
            def __init__(self):
                self.name = "test_plugin"
                self.version = "1.0.0"
                self.dependencies = ["core>=1.0.0"]
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        test_plugin = TestPlugin()

        # Check compatibility
        report = compatibility.check_compatibility(test_plugin)
        assert report is not None
        assert isinstance(report, dict)

        # Verify report structure
        assert "compatible" in report
        assert "issues" in report
        assert "warnings" in report

    def test_get_compatibility_report(self):
        """Test getting compatibility report."""
        compatibility = PluginCompatibility()

        # Create a test plugin
        class TestPlugin(Plugin):
            def __init__(self):
                self.name = "test_plugin"
                self.version = "1.0.0"
                self.dependencies = ["core>=1.0.0"]
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        test_plugin = TestPlugin()

        # Get compatibility report
        report = compatibility.get_compatibility_report(test_plugin)
        assert report is not None
        assert isinstance(report, dict)

        # Verify report structure
        assert "plugin_name" in report
        assert "plugin_version" in report
        assert "compatibility_status" in report
        assert "compatibility_issues" in report
        assert "compatibility_warnings" in report

    def test_check_compatible_plugin(self):
        """Test checking compatible plugin."""
        compatibility = PluginCompatibility()

        # Create a compatible test plugin
        class CompatiblePlugin(Plugin):
            def __init__(self):
                self.name = "compatible_plugin"
                self.version = "1.0.0"
                self.dependencies = ["core>=1.0.0"]
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        compatible_plugin = CompatiblePlugin()

        # Check compatibility
        report = compatibility.check_compatibility(compatible_plugin)
        assert report["compatible"] is True
        assert len(report["issues"]) == 0

    def test_check_incompatible_plugin(self):
        """Test checking incompatible plugin."""
        compatibility = PluginCompatibility()

        # Create an incompatible test plugin
        class IncompatiblePlugin(Plugin):
            def __init__(self):
                self.name = "incompatible_plugin"
                self.version = "1.0.0"
                self.dependencies = ["nonexistent>=1.0.0"]
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        incompatible_plugin = IncompatiblePlugin()

        # Check compatibility
        report = compatibility.check_compatibility(incompatible_plugin)
        assert report["compatible"] is False
        assert len(report["issues"]) > 0


class TestPluginCompatibilityEdgeCases:
    """Test plugin compatibility edge cases."""

    def test_check_plugin_with_no_dependencies(self):
        """Test checking plugin with no dependencies."""
        compatibility = PluginCompatibility()

        # Create a plugin with no dependencies
        class NoDepsPlugin(Plugin):
            def __init__(self):
                self.name = "no_deps_plugin"
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        no_deps_plugin = NoDepsPlugin()

        # Check compatibility
        report = compatibility.check_compatibility(no_deps_plugin)
        assert report is not None
        assert report["compatible"] is True

    def test_check_plugin_with_empty_name(self):
        """Test checking plugin with empty name."""
        compatibility = PluginCompatibility()

        # Create a plugin with empty name
        class EmptyNamePlugin(Plugin):
            def __init__(self):
                self.name = ""
                self.version = "1.0.0"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        empty_name_plugin = EmptyNamePlugin()

        # Check compatibility
        report = compatibility.check_compatibility(empty_name_plugin)
        assert report is not None
        assert report["compatible"] is False
        assert len(report["issues"]) > 0

    def test_check_plugin_with_invalid_version(self):
        """Test checking plugin with invalid version."""
        compatibility = PluginCompatibility()

        # Create a plugin with invalid version
        class InvalidVersionPlugin(Plugin):
            def __init__(self):
                self.name = "invalid_version_plugin"
                self.version = "invalid_version"
                self.dependencies = []
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        invalid_version_plugin = InvalidVersionPlugin()

        # Check compatibility
        report = compatibility.check_compatibility(invalid_version_plugin)
        assert report is not None
        assert report["compatible"] is False
        assert len(report["issues"]) > 0

    def test_check_plugin_with_missing_methods(self):
        """Test checking plugin with missing required methods."""
        compatibility = PluginCompatibility()

        # Create a plugin missing required methods
        class IncompletePlugin(Plugin):
            def __init__(self):
                self.name = "incomplete_plugin"
                self.version = "1.0.0"
                self.dependencies = []
                # Missing initialize and shutdown methods

        incomplete_plugin = IncompletePlugin()

        # Check compatibility
        report = compatibility.check_compatibility(incomplete_plugin)
        assert report is not None
        assert report["compatible"] is False
        assert len(report["issues"]) > 0


class TestPluginCompatibilityPerformance:
    """Test plugin compatibility performance."""

    def test_mass_plugin_compatibility_checking(self):
        """Test mass plugin compatibility checking."""
        compatibility = PluginCompatibility()

        # Create many test plugins
        plugins = []
        for i in range(100):
            class TestPlugin(Plugin):
                def __init__(self, plugin_id):
                    self.name = f"test_plugin_{plugin_id}"
                    self.version = "1.0.0"
                    self.dependencies = ["core>=1.0.0"]
                    self.initialized = False

                def initialize(self, container):
                    self.initialized = True

                def shutdown(self):
                    pass

                def get_capabilities(self):
                    return {"test": True}

            test_plugin = TestPlugin(i)
            plugins.append(test_plugin)

        # Check compatibility for all plugins
        for plugin in plugins:
            report = compatibility.check_compatibility(plugin)
            assert report is not None
            assert isinstance(report, dict)

    def test_plugin_compatibility_performance(self):
        """Test plugin compatibility performance."""
        import time

        compatibility = PluginCompatibility()

        # Create many test plugins
        plugins = []
        for i in range(1000):
            class TestPlugin(Plugin):
                def __init__(self, plugin_id):
                    self.name = f"perf_plugin_{plugin_id}"
                    self.version = "1.0.0"
                    self.dependencies = ["core>=1.0.0"]
                    self.initialized = False

                def initialize(self, container):
                    self.initialized = True

                def shutdown(self):
                    pass

                def get_capabilities(self):
                    return {"test": True}

            test_plugin = TestPlugin(i)
            plugins.append(test_plugin)

        # Test compatibility checking performance
        start_time = time.time()
        for plugin in plugins:
            compatibility.check_compatibility(plugin)
        compatibility_time = time.time() - start_time

        # Should be fast operation
        assert compatibility_time < 1.0


class TestPluginCompatibilityIntegration:
    """Test plugin compatibility integration scenarios."""

    def test_compatibility_with_registry(self):
        """Test compatibility integration with registry."""
        from nodupe.core.plugin_system.registry import PluginRegistry

        compatibility = PluginCompatibility()
        registry = PluginRegistry()

        # Create a test plugin
        class TestPlugin(Plugin):
            def __init__(self):
                self.name = "test_plugin"
                self.version = "1.0.0"
                self.dependencies = ["core>=1.0.0"]
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        test_plugin = TestPlugin()
        registry.register(test_plugin)

        # Check compatibility
        report = compatibility.check_compatibility(test_plugin)
        assert report is not None
        assert isinstance(report, dict)

    def test_compatibility_with_loader(self):
        """Test compatibility integration with loader."""
        from nodupe.core.plugin_system.loader import PluginLoader
        from nodupe.core.plugin_system.registry import PluginRegistry

        compatibility = PluginCompatibility()
        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # Create a test plugin
        class TestPlugin(Plugin):
            def __init__(self):
                self.name = "test_plugin"
                self.version = "1.0.0"
                self.dependencies = ["core>=1.0.0"]
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        test_plugin = TestPlugin()

        # Load plugin
        loaded_plugin = loader.load_plugin(test_plugin)

        # Check compatibility
        report = compatibility.check_compatibility(loaded_plugin)
        assert report is not None
        assert isinstance(report, dict)


class TestPluginCompatibilityErrorHandling:
    """Test plugin compatibility error handling."""

    def test_check_compatibility_with_invalid_plugin(self):
        """Test checking compatibility with invalid plugin."""
        compatibility = PluginCompatibility()

        # Create an invalid plugin (not inheriting from Plugin)
        class InvalidPlugin:
            def __init__(self):
                self.name = "invalid_plugin"

        invalid_plugin = InvalidPlugin()

        # Check compatibility
        with pytest.raises(PluginCompatibilityError):
            compatibility.check_compatibility(invalid_plugin)

    def test_check_compatibility_with_none_plugin(self):
        """Test checking compatibility with None plugin."""
        compatibility = PluginCompatibility()

        # Check compatibility with None
        with pytest.raises(PluginCompatibilityError):
            compatibility.check_compatibility(None)

    def test_check_compatibility_with_missing_attributes(self):
        """Test checking compatibility with plugin missing attributes."""
        compatibility = PluginCompatibility()

        # Create a plugin missing required attributes
        class IncompletePlugin(Plugin):
            def __init__(self):
                # Missing name, version, dependencies
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        incomplete_plugin = IncompletePlugin()

        # Check compatibility
        report = compatibility.check_compatibility(incomplete_plugin)
        assert report is not None
        assert report["compatible"] is False
        assert len(report["issues"]) > 0


class TestPluginCompatibilityAdvanced:
    """Test advanced plugin compatibility functionality."""

    def test_compatibility_with_complex_dependencies(self):
        """Test compatibility with complex dependencies."""
        compatibility = PluginCompatibility()

        # Create a plugin with complex dependencies
        class ComplexDepsPlugin(Plugin):
            def __init__(self):
                self.name = "complex_deps_plugin"
                self.version = "1.0.0"
                self.dependencies = [
                    "core>=1.0.0",
                    "utils>=2.0.0",
                    "network>=1.5.0",
                    "ml>=3.0.0"
                ]
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        complex_deps_plugin = ComplexDepsPlugin()

        # Check compatibility
        report = compatibility.check_compatibility(complex_deps_plugin)
        assert report is not None
        assert isinstance(report, dict)

        # Verify dependencies are checked
        assert len(report["issues"]) > 0 or len(report["warnings"]) > 0

    def test_compatibility_with_version_constraints(self):
        """Test compatibility with version constraints."""
        compatibility = PluginCompatibility()

        # Create a plugin with version constraints
        class VersionConstrainedPlugin(Plugin):
            def __init__(self):
                self.name = "version_constrained_plugin"
                self.version = "1.0.0"
                self.dependencies = [
                    "core>=1.0.0,<2.0.0",
                    "utils>=2.0.0,<=3.0.0"
                ]
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        version_constrained_plugin = VersionConstrainedPlugin()

        # Check compatibility
        report = compatibility.check_compatibility(version_constrained_plugin)
        assert report is not None
        assert isinstance(report, dict)

    def test_compatibility_with_conditional_checking(self):
        """Test compatibility with conditional checking."""
        compatibility = PluginCompatibility()

        # Create plugins with different compatibility profiles
        plugins = []

        # Compatible plugin
        class CompatiblePlugin(Plugin):
            def __init__(self):
                self.name = "compatible_plugin"
                self.version = "1.0.0"
                self.dependencies = ["core>=1.0.0"]
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        # Incompatible plugin
        class IncompatiblePlugin(Plugin):
            def __init__(self):
                self.name = "incompatible_plugin"
                self.version = "1.0.0"
                self.dependencies = ["nonexistent>=1.0.0"]
                self.initialized = False

            def initialize(self, container):
                self.initialized = True

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        plugins.append(CompatiblePlugin())
        plugins.append(IncompatiblePlugin())

        # Check compatibility for all plugins
        results = []
        for plugin in plugins:
            report = compatibility.check_compatibility(plugin)
            results.append(report)

        # Verify different results
        assert results[0]["compatible"] is True
        assert results[1]["compatible"] is False

    def test_compatibility_with_dynamic_dependency_management(self):
        """Test compatibility with dynamic dependency management."""
        compatibility = PluginCompatibility()

        # Create a plugin with dynamic dependencies
        class DynamicDepsPlugin(Plugin):
            def __init__(self):
                self.name = "dynamic_deps_plugin"
                self.version = "1.0.0"
                self.dependencies = ["core>=1.0.0"]
                self.initialized = False
                self.dynamic_dependencies = []

            def initialize(self, container):
                self.initialized = True
                # Add dynamic dependencies during initialization
                self.dynamic_dependencies = ["utils>=2.0.0", "network>=1.0.0"]

            def shutdown(self):
                pass

            def get_capabilities(self):
                return {"test": True}

        dynamic_deps_plugin = DynamicDepsPlugin()

        # Check compatibility before initialization
        report1 = compatibility.check_compatibility(dynamic_deps_plugin)
        assert report1 is not None

        # Initialize plugin
        dynamic_deps_plugin.initialize(MagicMock())

        # Check compatibility after initialization
        report2 = compatibility.check_compatibility(dynamic_deps_plugin)
        assert report2 is not None

        # Compare reports
        assert report1 != report2
