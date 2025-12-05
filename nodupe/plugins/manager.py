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
        # Executor used by the event loop for running sync callbacks.
        # It is bounded by `executor_max_workers` to avoid unbounded thread
        # growth when many blocking callbacks are executed.
        self._executor_max_workers = 8
        from concurrent.futures import ThreadPoolExecutor
        self._executor = ThreadPoolExecutor(
            max_workers=self._executor_max_workers)
        self._loop_thread = threading.Thread(
            target=self._run_loop, name="PluginManagerLoop", daemon=True
        )
        self._loop_thread.start()
        # Monitoring metrics. Use the same RLock for thread-safety.
        self._metrics = {
            "scheduled": 0,
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "executor_max_workers": self._executor_max_workers,
        }

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
        # Set the loop's default executor to our bounded ThreadPoolExecutor
        try:
            self._loop.set_default_executor(self._executor)
        except Exception:
            # Older Python versions may not support setting default executor
            pass
        try:
            self._loop.run_forever()
        finally:
            # Drain and close loop on shutdown
            pending = asyncio.all_tasks(loop=self._loop)
            for t in pending:
                t.cancel()
            try:
                self._loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            self._loop.close()

    def set_executor_max_workers(self, max_workers: int):
        """Change the executor max worker count.

        This will replace the existing executor with a new bounded one.
        """
        if max_workers <= 0:
            raise ValueError("max_workers must be positive")

        with self._lock:
            # Shutdown existing executor and replace
            try:
                self._executor.shutdown(wait=False)
            except Exception:
                pass
            from concurrent.futures import ThreadPoolExecutor
            self._executor_max_workers = max_workers
            self._executor = ThreadPoolExecutor(
                max_workers=self._executor_max_workers)
            # update observable metric
            with self._lock:
                self._metrics["executor_max_workers"] = (
                    self._executor_max_workers
                )
            try:
                self._loop.set_default_executor(self._executor)
            except Exception:
                pass

    def metrics(self) -> dict:
        """Return a snapshot of internal metrics for monitoring.

        Metrics include counts for scheduled tasks, pending tasks, completed
        tasks, and failed tasks.
        """
        with self._lock:
            # Return a shallow copy so callers can't mutate our internal state
            return dict(self._metrics)

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
        """Best-effort cleanup when the manager is garbage-collected.

        The background asyncio loop and its thread are cleaned up if still
        running. This is a best-effort operation — callers should prefer
        explicit lifecycle management and call :meth:`stop` during shutdown
        to ensure deterministic cleanup.
        """
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
                # Try to register the task in metrics first. We'll roll back
                # the registration if scheduling fails.
                with self._lock:
                    self._metrics["scheduled"] += 1
                    self._metrics["pending"] += 1

                if asyncio.iscoroutinefunction(callback):
                    # Wrap the coroutine so we can maintain
                    # running/completed/failed
                    # counters in a deterministic way.
                    # Bind callback and kwargs via default args to avoid
                    # closure issues
                    async def _wrapped_coro(cb=callback, kw=kwargs):
                        with self._lock:
                            self._metrics["running"] += 1
                            # an item moved from pending -> running
                            self._metrics["pending"] = max(
                                0, self._metrics["pending"] - 1)
                        try:
                            result = await cb(**kw)
                        except Exception:
                            with self._lock:
                                self._metrics["failed"] += 1
                            raise
                        else:
                            with self._lock:
                                self._metrics["completed"] += 1
                            return result
                        finally:
                            with self._lock:
                                # running finished
                                self._metrics["running"] = max(
                                    0, self._metrics["running"] - 1)

                    fut = asyncio.run_coroutine_threadsafe(
                        _wrapped_coro(), self._loop)

                    def _done_check(f, ev=event):
                        try:
                            _ = f.result()
                        except Exception as exc:  # pragma: no cover
                            print(
                                f"[plugin][WARN] Error in async hook '{ev}': "
                                f"{exc}", file=sys.stderr)

                    fut.add_done_callback(_done_check)

                else:
                    # Wrap synchronous callbacks so we can update metrics when
                    # they actually run in the executor thread.
                    # Bind callback and kwargs via default args to avoid
                    # closure issues
                    def _callable(cb=callback, kw=kwargs):
                        # Running begins here (executor thread)
                        with self._lock:
                            self._metrics["running"] += 1
                            self._metrics["pending"] = max(
                                0, self._metrics["pending"] - 1)
                        try:
                            cb(**kw)
                        except Exception:
                            with self._lock:
                                self._metrics["failed"] += 1
                            raise
                        else:
                            with self._lock:
                                self._metrics["completed"] += 1
                        finally:
                            with self._lock:
                                self._metrics["running"] = max(
                                    0, self._metrics["running"] - 1)

                    async def _run_in_executor(call=_callable):
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(None, call)

                    fut = asyncio.run_coroutine_threadsafe(
                        _run_in_executor(), self._loop
                    )

                    def _done_check_sync(f, ev=event):
                        try:
                            _ = f.result()
                        except Exception as exc:  # pragma: no cover
                            print(
                                f"[plugin][WARN] Error in sync hook '{ev}': "
                                f"{exc}", file=sys.stderr)

                    fut.add_done_callback(_done_check_sync)
            except Exception as e:
                # Ensure metrics reflect the failed scheduling attempt
                with self._lock:
                    self._metrics["scheduled"] = max(
                        0, self._metrics["scheduled"] - 1)
                    self._metrics["pending"] = max(
                        0, self._metrics["pending"] - 1)
                print(
                    f"[plugin][WARN] Error scheduling hook '{event}': {e}",
                    file=sys.stderr)

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
                    except Exception as e:
                        self.logger.warning(
                            f"Error loading plugin {module_name} "
                            f"from {filepath}: {e}"
                        )


# Global instance
pm = PluginManager()
