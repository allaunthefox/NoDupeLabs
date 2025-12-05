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

        # Create an asyncio event loop running in a dedicated background
        # thread. This allows the manager to dispatch coroutine callbacks
        # efficiently without allocating a new thread per callback.
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(
            target=self._run_loop, name="PluginManagerLoop", daemon=True
        )
        self._loop_thread.start()

    def register(self, event: str, callback: Callable):
        """Register a callback for an event."""
        with self._lock:
            if event not in self._hooks:
                self._hooks[event] = []
            self._hooks[event].append(callback)

    def _run_loop(self):
        """Background target: run the event loop forever.

        The method is executed on a dedicated thread and drives the
        asyncio event loop used to execute coroutine callbacks and run
        synchronous callbacks in the loop's executor.
        """
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_forever()
        finally:
            # Drain and close loop on shutdown
            pending = asyncio.all_tasks(loop=self._loop)
            for t in pending:
                t.cancel()
            try:
                self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            self._loop.close()

    def stop(self, wait: bool = True):
        """Stop the background event loop and join the loop thread.

        Args:
            wait: If True (default) join the background thread; otherwise
                  return immediately after requesting shutdown.
        """
        try:
            if self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)
        except Exception:
            pass

        if wait and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=5)

    def __del__(self):
        # Best-effort cleanup of background loop on GC
        try:
            self.stop(wait=False)
        except Exception:
            pass

    def emit(self, event: str, **kwargs: Any):
        """Emit an event, calling all registered callbacks."""
        # Copy callbacks under lock and invoke them without holding the lock
        # to avoid re-entrant deadlocks if callbacks register/unregister
        # other hooks.
        with self._lock:
            callbacks = list(self._hooks.get(event, ()))

        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    # Schedule the coroutine on the background loop and
                    # attach an error handler so exceptions get logged.
                    coro = callback(**kwargs)
                    fut = asyncio.run_coroutine_threadsafe(coro, self._loop)

                    def _done_check(f):
                        try:
                            _ = f.result()
                        except Exception as exc:  # pragma: no cover - best-effort logging
                            print(f"[plugin][WARN] Error in async hook '{event}': {exc}", file=sys.stderr)

                    fut.add_done_callback(_done_check)

                else:
                    # Wrap synchronous callbacks in the default executor so
                    # that blocking work doesn't stall the event loop.
                    async def _run_in_executor(cb, kw):
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(None, lambda: cb(**kw))

                    fut = asyncio.run_coroutine_threadsafe(
                        _run_in_executor(callback, kwargs), self._loop
                    )

                    def _done_check_sync(f):
                        try:
                            _ = f.result()
                        except Exception as exc:  # pragma: no cover - best-effort logging
                            print(f"[plugin][WARN] Error in sync hook '{event}': {exc}", file=sys.stderr)

                    fut.add_done_callback(_done_check_sync)
            except Exception as e:
                print(f"[plugin][WARN] Error scheduling hook '{event}': {e}", file=sys.stderr)

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
