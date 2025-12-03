# SPDX-License-Identifier: Apache-2.0
from typing import Callable, Dict, List, Any
import sys


class PluginManager:
    """Simple event-based plugin manager."""

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
