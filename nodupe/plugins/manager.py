# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Event-based plugin system.

This module implements a lightweight plugin manager that allows extending
application functionality through event hooks. Plugins can register callbacks
for specific events (e.g., 'scan_start', 'file_processed') and are loaded
dynamically from a specified directory.

Key Features:
    - Event-driven architecture (register/emit)
    - Dynamic plugin loading from .py files
    - Fault tolerance (plugin errors don't crash the app)
    - Global singleton instance for easy access

Classes:
    - PluginManager: Core plugin management logic

Attributes:
    - pm: Global PluginManager instance
"""

import sys
from typing import Callable, Dict, List, Any


class PluginManager:
    """Simple event-based plugin manager.

    Manages plugin lifecycle and event dispatching. Plugins are Python
    scripts that are loaded at runtime and can register callbacks for
    various application events.
    """

    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = {}
        self._loaded_plugins: List[str] = []

    def register(self, event: str, callback: Callable):
        """Register a callback for an event."""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)

    def emit(self, event: str, **kwargs: Any):
        """Emit an event, calling all registered callbacks."""
        if event not in self._hooks:
            return

        for callback in self._hooks[event]:
            try:
                callback(**kwargs)
            except Exception as e:
                print(
                    f"[plugin][WARN] Error in hook '{event}': {e}",
                    file=sys.stderr
                )

    def load_plugins(self, paths: List[str]):
        """Load plugins from specified paths."""
        import importlib.util
        import os

        for path in paths:
            if not os.path.exists(path):
                continue

            # Load all .py files in the directory
            for filename in os.listdir(path):
                if filename.endswith(".py") and not filename.startswith("_"):
                    filepath = os.path.join(path, filename)
                    module_name = f"nodupe_plugin_{filename[:-3]}"

                    try:
                        spec = importlib.util.spec_from_file_location(
                            module_name, filepath
                        )
                        if spec and spec.loader:
                            mod = importlib.util.module_from_spec(spec)
                            # Inject the manager so plugins can register
                            mod.pm = self
                            sys.modules[module_name] = mod
                            spec.loader.exec_module(mod)
                            self._loaded_plugins.append(module_name)
                            # print(f"[plugin] Loaded {module_name}")
                    except Exception as e:
                        print(
                            f"[plugin][WARN] Failed to load {filename}: {e}",
                            file=sys.stderr
                        )


# Global instance
pm = PluginManager()
