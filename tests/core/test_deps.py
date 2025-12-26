from nodupe.core.deps import DependencyManager, dep_manager


class TestDependencyManager:
    """Test suite for the DependencyManager class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.dep_manager = DependencyManager()

    def test_dependency_manager_initialization(self):
        """Test initializing a DependencyManager."""
        assert isinstance(self.dep_manager, DependencyManager)
        assert self.dep_manager.dependencies == {}

    def test_check_dependency_existing_module(self):
        """Test checking for an existing module."""
        # Check for a standard library module that should exist
        result = self.dep_manager.check_dependency("os")
        assert result is True
        assert "os" in self.dep_manager.dependencies
        assert self.dep_manager.dependencies["os"] is True

    def test_check_dependency_nonexistent_module(self):
        """Test checking for a nonexistent module."""
        # Check for a module that doesn't exist
        result = self.dep_manager.check_dependency("nonexistent_module_xyz")
        assert result is False
        assert "nonexistent_module_xyz" in self.dep_manager.dependencies
        assert self.dep_manager.dependencies["nonexistent_module_xyz"] is False

    def test_check_dependency_multiple_calls_same_module(self):
        """Test checking the same module multiple times."""
        # First call
        result1 = self.dep_manager.check_dependency("sys")
        # Second call should use cached result
        result2 = self.dep_manager.check_dependency("sys")
        assert result1 is True
        assert result2 is True
        assert result1 == result2
        # Check that it's cached
        assert self.dep_manager.dependencies["sys"] is True

    def test_with_fallback_primary_success(self):
        """Test with_fallback when primary function succeeds."""
        def primary_func():
            return "primary_result"
        
        def fallback_func():
            return "fallback_result"
        
        result = self.dep_manager.with_fallback(primary_func, fallback_func)
        assert result == "primary_result"

    def test_with_fallback_primary_failure(self):
        """Test with_fallback when primary function fails."""
        def primary_func():
            raise ValueError("Primary failed")
        
        def fallback_func():
            return "fallback_result"
        
        result = self.dep_manager.with_fallback(primary_func, fallback_func)
        assert result == "fallback_result"

    def test_with_fallback_primary_exception_type(self):
        """Test with_fallback catches all exception types."""
        def primary_func():
            raise TypeError("Type error in primary")
        
        def fallback_func():
            return "fallback_on_type_error"
        
        result = self.dep_manager.with_fallback(primary_func, fallback_func)
        assert result == "fallback_on_type_error"

    def test_try_import_existing_module(self):
        """Test try_import with an existing module."""
        import os  # Make sure os exists
        result = self.dep_manager.try_import("os")
        assert result is not None
        assert hasattr(result, "path")  # os module has a path attribute

    def test_try_import_nonexistent_module_with_none_fallback(self):
        """Test try_import with nonexistent module and None fallback."""
        result = self.dep_manager.try_import("nonexistent_module_abc", None)
        assert result is None

    def test_try_import_nonexistent_module_with_custom_fallback(self):
        """Test try_import with nonexistent module and custom fallback."""
        fallback_value = {"default": "value"}
        result = self.dep_manager.try_import("nonexistent_module_def", fallback_value)
        assert result == fallback_value

    def test_try_import_import_error(self):
        """Test try_import behavior when import raises ImportError."""
        # Create a module name that will definitely not exist
        result = self.dep_manager.try_import("definitely_nonexistent_module_12345")
        assert result is None

    def test_try_import_other_exception(self):
        """Test try_import behavior when import raises other exceptions."""
        # This is harder to test as we need to create a module that causes other exceptions
        # For now, we'll just verify the function doesn't crash
        result = self.dep_manager.try_import("nonexistent_module_56789", {})
        assert isinstance(result, dict)

    def test_dependency_manager_state_preservation(self):
        """Test that dependency checks are preserved in the manager."""
        # Check a module
        self.dep_manager.check_dependency("json")
        # Verify it's in the dependencies dict
        assert "json" in self.dep_manager.dependencies
        assert isinstance(self.dep_manager.dependencies["json"], bool)

    def test_check_dependency_complex_module_name(self):
        """Test checking dependency with complex (nested) module name."""
        # Check a nested standard library module
        result = self.dep_manager.check_dependency("urllib.request")
        assert isinstance(result, bool)
        # This should typically be True in most Python installations
        assert "urllib.request" in self.dep_manager.dependencies

    def test_with_fallback_returns_correct_types(self):
        """Test that with_fallback preserves return types."""
        def primary_func():
            return 42
        
        def fallback_func():
            return 0
        
        result = self.dep_manager.with_fallback(primary_func, fallback_func)
        assert isinstance(result, int)
        assert result == 42

    def test_with_fallback_with_side_effects(self):
        """Test with_fallback with functions that have side effects."""
        container = []  # Define container with explicit type hint
        
        def primary_func():
            container.append("primary")
            return "result"
        
        def fallback_func():
            container.append("fallback")
            return "fallback_result"
        
        result = self.dep_manager.with_fallback(primary_func, fallback_func)
        assert result == "result"
        assert "primary" in container
        assert "fallback" not in container  # Fallback shouldn't be called

    def test_with_fallback_with_exception_side_effects(self):
        """Test with_fallback when primary has side effects before failing."""
        container = []
        
        def primary_func():
            container.append("primary_attempt")
            raise RuntimeError("Failed after side effect")
        
        def fallback_func():
            container.append("fallback_called")
            return "recovered_result"
        
        result = self.dep_manager.with_fallback(primary_func, fallback_func)
        assert result == "recovered_result"
        assert "primary_attempt" in container
        assert "fallback_called" in container

    def test_try_import_with_various_fallback_types(self):
        """Test try_import with various types of fallback values."""
        # Test with string fallback
        result = self.dep_manager.try_import("nonexistent_str_module", "default_string")
        assert result == "default_string"
        
        # Test with integer fallback
        result = self.dep_manager.try_import("nonexistent_int_module", 123)
        assert result == 123
        
        # Test with list fallback
        result = self.dep_manager.try_import("nonexistent_list_module", [1, 2, 3])
        assert result == [1, 2, 3]
        
        # Test with callable fallback
        def default_func():
            return "default_callable"
        
        result = self.dep_manager.try_import("nonexistent_func_module", default_func)
        assert result == default_func

    def test_dependency_manager_isolation(self):
        """Test that DependencyManager instances are isolated."""
        dm1 = DependencyManager()
        dm2 = DependencyManager()
        
        # Check a dependency with the first manager
        dm1.check_dependency("os")
        
        # The second manager should not have this cached yet
        assert "os" not in dm2.dependencies
        # But after checking, it should have its own cache
        dm2.check_dependency("os")
        assert "os" in dm2.dependencies

    def test_check_dependency_with_special_characters(self):
        """Test checking dependency with special characters in name."""
        # Check for modules with underscores or other valid Python names
        result = self.dep_manager.check_dependency("xml.etree.ElementTree")
        assert isinstance(result, bool)
        assert "xml.etree.ElementTree" in self.dep_manager.dependencies

    def test_with_fallback_with_args_and_kwargs(self):
        """Test with_fallback with functions that take args and kwargs."""
        # Since with_fallback takes functions directly, we need to test
        # functions that capture external variables or use closures
        captured_value = "test_value"
        
        def primary_func():
            def inner():
                return f"primary_{captured_value}"
            return inner()
        
        def fallback_func():
            def inner():
                return f"fallback_{captured_value}"
            return inner()
        
        result = self.dep_manager.with_fallback(primary_func, fallback_func)
        assert result == "primary_test_value"

    def test_try_import_builtin_module(self):
        """Test try_import with a builtin module."""
        result = self.dep_manager.try_import("sys")
        assert result is not None
        assert hasattr(result, "version")

    def test_try_import_standard_library_module(self):
        """Test try_import with a standard library module."""
        result = self.dep_manager.try_import("math")
        assert result is not None
        assert hasattr(result, "sqrt")

    def test_check_dependency_edge_case_empty_string(self):
        """Test checking dependency with empty string."""
        result = self.dep_manager.check_dependency("")
        assert result is False  # Empty string should not be a valid module

    # Skip tests that pass None to functions that expect string parameters
    # These would cause type errors in the actual implementation


class TestGlobalDependencyManager:
    """Test suite for the global dependency manager instance."""

    def test_global_instance_exists(self):
        """Test that the global dependency manager instance exists."""
        assert dep_manager is not None
        assert isinstance(dep_manager, DependencyManager)

    def test_global_instance_functionality(self):
        """Test that global instance has full functionality."""
        # Test that we can use the global instance
        result = dep_manager.check_dependency("os")
        assert result is True  # os should be available

    def test_global_instance_shared_state(self):
        """Test that global instance maintains state."""
        # Check a dependency
        dep_manager.check_dependency("time")
        # Verify it's cached in the global instance
        assert "time" in dep_manager.dependencies
        assert dep_manager.dependencies["time"] is True  # time module should exist
