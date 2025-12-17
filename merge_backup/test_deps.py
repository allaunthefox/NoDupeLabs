"""Test deps module functionality."""

import pytest
from unittest.mock import patch, MagicMock
from nodupe.core.deps import DependencyManager, dep_manager


class TestDependencyManager:
    """Test DependencyManager class functionality."""

    def test_initialization(self):
        """Test DependencyManager initialization."""
        dm = DependencyManager()
        assert hasattr(dm, 'dependencies')
        assert isinstance(dm.dependencies, dict)
        assert len(dm.dependencies) == 0

    def test_check_dependency_available(self):
        """Test checking available dependency."""
        dm = DependencyManager()

        # Test with a standard library module that should be available
        result = dm.check_dependency('json')
        assert result is True
        assert 'json' in dm.dependencies
        assert dm.dependencies['json'] is True

    def test_check_dependency_unavailable(self):
        """Test checking unavailable dependency."""
        dm = DependencyManager()

        # Test with a module that doesn't exist
        result = dm.check_dependency('nonexistent_module_12345')
        assert result is False
        assert 'nonexistent_module_12345' in dm.dependencies
        assert dm.dependencies['nonexistent_module_12345'] is False

    def test_check_dependency_caching(self):
        """Test dependency checking caching."""
        dm = DependencyManager()

        # First check
        result1 = dm.check_dependency('json')
        assert result1 is True

        # Second check should use cache
        result2 = dm.check_dependency('json')
        assert result2 is True

        # Should only have one entry in dependencies
        assert len(dm.dependencies) == 1

    def test_with_fallback_success(self):
        """Test with_fallback with successful primary function."""
        dm = DependencyManager()

        def primary():
            return "primary_result"

        def fallback():
            return "fallback_result"

        result = dm.with_fallback(primary, fallback)
        assert result == "primary_result"

    def test_with_fallback_failure(self):
        """Test with_fallback with failing primary function."""
        dm = DependencyManager()

        def primary():
            raise Exception("Primary failed")

        def fallback():
            return "fallback_result"

        result = dm.with_fallback(primary, fallback)
        assert result == "fallback_result"

    def test_with_fallback_exception_handling(self):
        """Test with_fallback exception handling."""
        dm = DependencyManager()

        def primary():
            raise ValueError("Test error")

        def fallback():
            return "fallback_result"

        # Should not raise exception, should return fallback
        result = dm.with_fallback(primary, fallback)
        assert result == "fallback_result"

    def test_try_import_success(self):
        """Test try_import with successful import."""
        dm = DependencyManager()

        result = dm.try_import('json')
        assert result is not None
        assert hasattr(result, '__name__')
        assert result.__name__ == 'json'

    def test_try_import_failure(self):
        """Test try_import with failed import."""
        dm = DependencyManager()

        result = dm.try_import('nonexistent_module_12345')
        assert result is None

    def test_try_import_with_fallback(self):
        """Test try_import with fallback value."""
        dm = DependencyManager()

        fallback_value = {"status": "fallback"}
        result = dm.try_import('nonexistent_module_12345', fallback_value)
        assert result is fallback_value
        assert result["status"] == "fallback"

    def test_try_import_exception_handling(self):
        """Test try_import with unexpected exception."""
        dm = DependencyManager()

        # Mock importlib to raise unexpected exception
        with patch('importlib.import_module') as mock_import:
            mock_import.side_effect = RuntimeError("Unexpected error")

            fallback_value = {"status": "fallback"}
            result = dm.try_import('test_module', fallback_value)

            assert result is fallback_value
            assert result["status"] == "fallback"


class TestGlobalDependencyManager:
    """Test global dependency manager instance."""

    def test_global_dep_manager_instance(self):
        """Test that global dep_manager is a DependencyManager instance."""
        assert isinstance(dep_manager, DependencyManager)
        assert hasattr(dep_manager, 'dependencies')

    def test_global_dep_manager_isolation(self):
        """Test that global dep_manager maintains isolation."""
        # Clear any cached dependencies for clean test
        dep_manager.dependencies.clear()

        # Test dependency checking
        result = dep_manager.check_dependency('json')
        assert result is True
        assert 'json' in dep_manager.dependencies

        # Clean up
        dep_manager.dependencies.clear()


class TestDependencyManagerIntegration:
    """Test dependency manager integration scenarios."""

    def test_dependency_workflow(self):
        """Test complete dependency management workflow."""
        dm = DependencyManager()

        # Check available dependency
        json_available = dm.check_dependency('json')
        assert json_available is True

        # Check unavailable dependency
        fake_available = dm.check_dependency('fake_module_12345')
        assert fake_available is False

        # Use with_fallback for resilient operation
        def primary_operation():
            # This would use the optional dependency
            import json
            return json.dumps({"status": "success"})

        def fallback_operation():
            return '{"status": "fallback"}'

        result = dm.with_fallback(primary_operation, fallback_operation)
        assert result is not None

        # Test try_import
        json_module = dm.try_import('json')
        assert json_module is not None

        fake_module = dm.try_import('fake_module_12345', {"fallback": True})
        assert fake_module == {"fallback": True}

    def test_graceful_degradation_scenario(self):
        """Test graceful degradation scenario."""
        dm = DependencyManager()

        # Simulate a scenario where we try to use an optional dependency
        def use_optional_dependency():
            # This would normally use an optional dependency
            import nonexistent_module
            return nonexistent_module.some_function()

        def use_standard_library():
            import json
            return json.dumps({"status": "using_standard_library"})

        # Should gracefully fall back to standard library
        result = dm.with_fallback(
            use_optional_dependency,
            use_standard_library)
        assert result is not None
        assert "using_standard_library" in result


class TestDependencyManagerEdgeCases:
    """Test dependency manager edge cases."""

    def test_check_dependency_with_import_error(self):
        """Test check_dependency with import error."""
        dm = DependencyManager()

        # Mock importlib to raise ImportError
        with patch('importlib.util.find_spec') as mock_find_spec:
            mock_find_spec.side_effect = ImportError("Mocked import error")

            result = dm.check_dependency('test_module')
            assert result is False
            assert 'test_module' in dm.dependencies
            assert dm.dependencies['test_module'] is False

    def test_with_fallback_both_fail(self):
        """Test with_fallback when both primary and fallback fail."""
        dm = DependencyManager()

        def primary():
            raise Exception("Primary failed")

        def fallback():
            raise Exception("Fallback also failed")

        # Should still return None (fallback's exception is not caught)
        with pytest.raises(Exception, match="Fallback also failed"):
            dm.with_fallback(primary, fallback)

    def test_try_import_with_non_import_exception(self):
        """Test try_import with non-ImportError exception."""
        dm = DependencyManager()

        # Mock importlib to raise unexpected exception
        with patch('importlib.import_module') as mock_import:
            mock_import.side_effect = RuntimeError(
                "Unexpected error during import")

            fallback_value = {"status": "fallback"}
            result = dm.try_import('test_module', fallback_value)

            assert result is fallback_value
            assert result["status"] == "fallback"
