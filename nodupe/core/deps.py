# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun
# pylint: disable=broad-exception-caught

"""Graceful degradation framework with hard isolation.

This module provides mechanisms for handling optional dependencies
with graceful fallback to standard library.

Key Features:
    - Dependency availability checking
    - Graceful fallback mechanisms
    - Error isolation
    - Resilience-focused design

Dependencies:
    - Standard library only
"""

import importlib
import importlib.util
from typing import Dict, Any, Optional, Callable


class DependencyManager:
    """Dependency manager with graceful degradation.

    Responsibilities:
    - Check dependency availability
    - Provide fallback mechanisms
    - Isolate errors
    - Maintain resilience
    """

    def __init__(self):
        """Initialize dependency manager."""
        self.dependencies: Dict[str, bool] = {}

    def check_dependency(self, module_name: str) -> bool:
        """Check if a dependency is available.

        Args:
            module_name: Name of the module to check

        Returns:
            True if available, False otherwise
        """
        if module_name in self.dependencies:
            return self.dependencies[module_name]

        try:
            spec = importlib.util.find_spec(module_name)
            available = spec is not None
            self.dependencies[module_name] = available
            return available
        except Exception:
            self.dependencies[module_name] = False
            return False

    def with_fallback(self, primary: Callable[[], Any], fallback: Callable[[], Any]) -> Any:
        """Execute primary function with fallback on failure.

        Args:
            primary: Primary function to execute
            fallback: Fallback function if primary fails

        Returns:
            Result from primary or fallback function
        """
        try:
            return primary()
        except Exception as e:
            print(f"[WARN] Primary function failed, using fallback: {e}")
            return fallback()

    def try_import(self, module_name: str, fallback: Optional[Any] = None) -> Optional[Any]:
        """Try to import a module with fallback.

        Args:
            module_name: Module name to import
            fallback: Fallback value if import fails

        Returns:
            Imported module or fallback value
        """
        try:
            module = importlib.import_module(module_name)
            return module
        except ImportError:
            print(f"[WARN] Failed to import {module_name}, using fallback")
            return fallback
        except Exception as e:
            print(f"[ERROR] Unexpected error importing {module_name}: {e}")
            return fallback


# Global dependency manager instance
dep_manager = DependencyManager()
