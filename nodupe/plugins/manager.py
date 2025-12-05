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
import asyncio
import threading
from typing import Callable, Dict, List, Any


class PluginManager:
    """Simple event-based plugin manager.

    Manages plugin lifecycle and event dispatching. Plugins are Python
    scripts that are loaded at runtime and can register callbacks for
    various application events.
    """

    def __init__(self):
        """Create a new PluginManager.

        The manager stores hooks and a list of loaded plugins. Methods are
        thread-safe via an internal RLock.
        """
        self._hooks: Dict[str, List[Callable]] = {}
        self._loaded_plugins: List[str] = []
        # Lock to ensure register/emit/load_plugins are safe when used across
        # threads. Plugins are generally loaded at startup, but emit may be
        # called from worker threads during scans.
        self._lock = threading.RLock()

    def register(self, event: str, callback: Callable):
        """Register a callback for an event."""
        with self._lock:
            if event not in self._hooks:
                self._hooks[event] = []
            self._hooks[event].append(callback)

    def emit(self, event: str, **kwargs: Any):
        """Emit an event, calling all registered callbacks."""
        # Copy callbacks under lock and invoke them without holding the lock
        # to avoid re-entrant deadlocks if callbacks register/unregister
        # other hooks.
        with self._lock:
            callbacks = list(self._hooks.get(event, ()))

        for callback in callbacks:
            try:
                # Support synchronous and asynchronous callbacks. If the
                # callback is a coroutine function, run it in a separate
                # thread via asyncio.run so callbacks can use async I/O.
                if asyncio.iscoroutinefunction(callback):
                    coro = callback(**kwargs)

                    def _run():
                        """Run the coroutine `coro` in an asyncio event loop.

                        Executed on a background thread to keep emit() non-blocking.
                        Exceptions are logged to stderr by the caller.
                        """
                        try:
                            asyncio.run(coro)
                        except Exception as e:
                            print(
                                f"[plugin][WARN] Error in async hook '{event}': {e}",
                                file=sys.stderr
                            )

                    # Spawn a thread to run the coroutine so emit remains
                    # non-blocking; this keeps backward compatibility with
                    # synchronous usage.
                    import threading

                    t = threading.Thread(target=_run, daemon=True)
                    t.start()
                else:
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
                            with self._lock:
                                self._loaded_plugins.append(module_name)
                            # print(f"[plugin] Loaded {module_name}")
                    except Exception as e:
                        print(
                            f"[plugin][WARN] Failed to load {filename}: {e}",
                            file=sys.stderr
                        )


# Global instance
pm = PluginManager()
