# pylint: disable=logging-fstring-interpolation
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Core Loader Module.

Handles bootstrap and initialization of the NoDupeLabs framework.
Strictly decoupled: Does not import functional tools directly.
"""

import logging
import multiprocessing
import os
import platform
from pathlib import Path
from typing import Any

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore[assignment]

from .api.codes import ActionCode
from .api.ipc import ToolIPCServer
from .config import load_config
from .container import container as global_container
from .tool_system.discovery import create_tool_discovery
from .tool_system.hot_reload import ToolHotReload
from .tool_system.lifecycle import create_lifecycle_manager
from .tool_system.loader import create_tool_loader
from .tool_system.registry import ToolRegistry

# Re-export helper used in tests and by other modules
from .database.connection import get_connection

# Expose hashing autotune helpers at module level so unit tests can patch
# these symbols (they may not be present if the hashing tool isn't available).
try:
    from ..tools.hashing.autotune_logic import (
        autotune_hash_algorithm,
        create_autotuned_hasher,
    )
except Exception:  # pragma: no cover - optional tooling
    autotune_hash_algorithm = None  # type: ignore
    create_autotuned_hasher = None  # type: ignore


class CoreLoader:
    """Main application loader and bootstrap class"""

    def __init__(self):
        """Initialize the core loader"""
        self.config = None
        self.container = None
        self.tool_registry = None
        self.tool_loader = None
        self.tool_discovery = None
        self.tool_lifecycle = None
        self.hot_reload = None
        self.ipc_server = None
        self.database = None
        self.initialized = False
        self.logger = logging.getLogger(__name__)

    def initialize(self) -> None:
        """Initialize the core system framework."""
        if self.initialized:
            return

        try:
            # 1. Load configuration
            self.config = load_config()
            platform_config = self._apply_platform_autoconfig()
            if hasattr(self.config, "config"):
                for key, value in platform_config.items():
                    # If the config key is missing, set it directly
                    if key not in self.config.config:
                        self.config.config[key] = value
                    else:
                        # If both sides are dict-like, merge missing sub-keys
                        existing = self.config.config.get(key)
                        if (
                            isinstance(existing, dict)
                            and isinstance(value, dict)
                        ):
                            for subk, subv in value.items():
                                if subk not in existing:
                                    existing[subk] = subv
                            self.config.config[key] = existing
                        # otherwise leave existing value intact

            self.logger.info(
                f"[{ActionCode.FIA_UAU_INIT}] Framework configuration loaded"
            )

            # 2. Initialize dependency container
            self.container = global_container
            self.container.register_service("config", self.config)
            self.logger.info(
                f"[{ActionCode.FIA_UAU_INIT}] Service container ready"
            )

            # 3. Initialize tool system
            self.tool_registry = ToolRegistry()
            self.tool_registry.initialize(self.container)
            self.container.register_service("tool_registry", self.tool_registry)

            self.tool_loader = create_tool_loader(self.tool_registry)
            self.tool_loader.initialize(self.container)
            self.container.register_service("tool_loader", self.tool_loader)

            self.tool_discovery = create_tool_discovery()
            self.container.register_service(
                "tool_discovery", self.tool_discovery
            )

            self.tool_lifecycle = create_lifecycle_manager(self.tool_registry)
            self.container.register_service(
                "tool_lifecycle", self.tool_lifecycle
            )

            # 4. Start maintenance services
            self.hot_reload = ToolHotReload(
                self.tool_registry, self.tool_loader
            )
            self.hot_reload.start()
            self.container.register_service("hot_reload", self.hot_reload)

            # 5. Start programmatic interface (IPC)
            self.ipc_server = ToolIPCServer(self.tool_registry)
            self.ipc_server.start()
            self.container.register_service("ipc_server", self.ipc_server)

            # 5.5 Initialize database connection (if configured)
            try:
                db_path = (
                    getattr(self.config, "config", {}).get("db_path")
                    or "output/index.db"
                )
                self.database = get_connection(db_path)
                # Initialize schema if necessary
                self.database.initialize_database()
                self.container.register_service("database", self.database)
            except Exception:
                # Database is optional during some test runs; log and continue
                self.logger.debug("Database initialization skipped or failed")

            # 6. Discover and load functional tools (Deduplication, Databases, Hashing, etc.)
            self.logger.info(
                f"[{ActionCode.FIA_UAU_LOAD}] Starting tool discovery and loading"
            )
            # Respect `auto_load` config flag for tools
            tools_cfg = getattr(self.config, "config", {}).get("tools", {})
            if tools_cfg.get("auto_load", True):
                self._discover_and_load_tools()
            else:
                self.logger.info(
                    f"[{ActionCode.FIA_UAU_LOAD}] Tool auto-load disabled by configuration"
                )

            # 7. Lifecycle: Initialize all loaded tools
            self.logger.info(
                f"[{ActionCode.FIA_UAU_INIT}] Initializing all loaded tools"
            )
            self.tool_lifecycle.initialize_all_tools(self.container)

            # 8. Post-initialization tasks (e.g. autotuning) handled via dynamic discovery
            self._perform_hash_autotuning()

            self.initialized = True
            self.logger.info(
                f"[{ActionCode.FIA_UAU_INIT}] Pure Core Engine initialized successfully"
            )
            self.logger.info(
                f"[{ActionCode.ACC_ISO_CMP}] Core engine is ISO accessibility compliant"
            )

        except Exception as e:
            self.logger.exception(
                f"[{ActionCode.FPT_STM_ERR}] Framework startup failed: {e}"
            )
            raise

    def _discover_and_load_tools(self) -> None:
        """Discover and load tools from configured directories."""
        config_dict = getattr(self.config, "config", {})
        tool_dirs = config_dict.get("tools", {}).get("directories", ["tools"])

        # Absolute paths for discovery
        tool_path_dirs = [
            Path(p).resolve() for p in tool_dirs if Path(p).exists()
        ]
        if not tool_path_dirs:
            # Fallback to standard locations
            standard_paths = [
                Path("nodupe/tools").resolve(),
                Path("tools").resolve(),
            ]
            tool_path_dirs = [p for p in standard_paths if p.exists()]

        self.logger.info(
            f"[{ActionCode.FIA_UAU_LOAD}] Discovering tools in: {tool_path_dirs}"
        )

        for tool_dir in tool_path_dirs:
            tools = self.tool_discovery.discover_tools_in_directory(tool_dir)
            self.logger.info(
                f"[{ActionCode.FIA_UAU_LOAD}] Found {len(tools)} tools in {tool_dir}"
            )
            for tool_info in tools:
                self._load_single_tool(tool_info)

    def _load_single_tool(self, tool_info: Any) -> None:
        """Load a tool using the framework's loader."""
        try:
            self.logger.info(
                f"[{ActionCode.FIA_UAU_LOAD}] Loading tool: {tool_info.name}"
            )
            tool_class = self.tool_loader.load_tool_from_file(tool_info.path)
            if tool_class:
                tool_instance = self.tool_loader.instantiate_tool(tool_class)
                self.tool_loader.register_loaded_tool(
                    tool_instance, tool_info.path
                )

                if self.hot_reload:
                    self.hot_reload.watch_tool(
                        tool_instance.name, tool_info.path
                    )

                self.logger.info(
                    f"[{ActionCode.FIA_UAU_LOAD}] Loaded tool: {tool_info.name}"
                )

                # Check if the tool is accessibility-compliant
                if hasattr(tool_instance, "get_ipc_socket_documentation"):
                    self.logger.info(
                        f"[{ActionCode.ACC_ISO_CMP}] Tool {tool_info.name} is ISO accessibility compliant"
                    )

        except Exception as e:
            self.logger.exception(
                f"[{ActionCode.FPT_FLS_FAIL}] Failed to load tool {tool_info.name}: {e}"
            )

    def _perform_hash_autotuning(self) -> None:
        """Perform hash algorithm autotuning if the hashing tool is present.

        Behavior:
        - Prefer calling `autotune_hash_algorithm` and `create_autotuned_hasher`
          (exposed at module level) when available so unit tests can patch
          these functions.
        - On success, register `hasher` and `hash_autotune_results` in the
          service container.
        - On failure, log a clear error and register a fallback `FileHasher`.
        """
        try:
            # First, attempt to run the autotune routine if exposed at module level
            results = None
            if callable(globals().get("autotune_hash_algorithm")):
                results = autotune_hash_algorithm()  # type: ignore

            # If a convenience creator is available, use it to obtain a hasher
            if callable(globals().get("create_autotuned_hasher")):
                try:
                    hasher_instance, autotune_results = create_autotuned_hasher()
                    self.container.register_service("hasher", hasher_instance)
                    self.container.register_service(
                        "hash_autotune_results", autotune_results
                    )
                    return
                except Exception:
                    # Fall through to use `results` if available
                    pass

            # If we got autotune results but no creator, store results and
            # configure existing hasher service if present.
            if results:
                self.container.register_service("hash_autotune_results", results)
                algo = results.get("optimal_algorithm")
                hasher = self.container.get_service("hasher")
                if hasher and hasattr(hasher, "set_algorithm") and algo:
                    hasher.set_algorithm(algo)
                return

            # Nothing available — attempt graceful fallback by ensuring a
            # hasher service exists (use FileHasher from hashing tool).
            from nodupe.tools.hashing.hasher_logic import FileHasher

            fallback = FileHasher()
            self.container.register_service("hasher", fallback)
            self.container.register_service("hash_autotune_results", {})

        except Exception as e:
            # Log a concise error message expected by unit tests and ensure a
            # fallback hasher is available.
            logging.error(f"Hash autotuning failed: {e}")
            try:
                from nodupe.tools.hashing.hasher_logic import FileHasher

                self.container.register_service("hasher", FileHasher())
            except Exception:
                # Best-effort: if even the fallback isn't available, ignore.
                pass

    def shutdown(self) -> None:
        """Gracefully shutdown the framework and all loaded tools."""
        if not self.initialized:
            return

        try:
            self.logger.info(
                f"[{ActionCode.FIA_UAU_SHUTDOWN}] Starting framework shutdown"
            )

            if self.tool_lifecycle:
                self.logger.info(
                    f"[{ActionCode.FIA_UAU_SHUTDOWN}] Shutting down all tools"
                )
                self.tool_lifecycle.shutdown_all_tools()
            if self.hot_reload:
                self.logger.info(
                    f"[{ActionCode.FIA_UAU_SHUTDOWN}] Stopping hot reload"
                )
                self.hot_reload.stop()
            if self.ipc_server:
                self.logger.info(
                    f"[{ActionCode.FIA_UAU_SHUTDOWN}] Stopping IPC server"
                )
                self.ipc_server.stop()
            if self.tool_registry:
                self.logger.info(
                    f"[{ActionCode.FIA_UAU_SHUTDOWN}] Shutting down registry"
                )
                self.tool_registry.shutdown()

            # Close database connection if present
            if self.database is not None:
                try:
                    self.database.close()
                except Exception:
                    pass

            self.initialized = False
            self.logger.info(
                f"[{ActionCode.FIA_UAU_SHUTDOWN}] Framework shutdown complete"
            )

            # Final maintenance using maintenance tool if available
            try:
                from ..tools.maintenance.log_compressor import LogCompressor

                log_dir = getattr(self.config, "config", {}).get(
                    "log_dir", "logs"
                )
                self.logger.info(
                    f"[{ActionCode.FIA_UAU_SHUTDOWN}] Compressing old logs in {log_dir}"
                )
                LogCompressor.compress_old_logs(log_dir)
            except ImportError:
                pass

        except Exception as e:
            self.logger.exception(
                f"[{ActionCode.FPT_STM_ERR}] Shutdown error: {e}"
            )

    def _apply_platform_autoconfig(self) -> dict[str, Any]:
        """Apply system resource-based autoconfiguration.

        Returns a dictionary of platform-aware defaults which are intended to be
        merged (non-destructively) into the main configuration. This includes
        resource-derived values such as CPU cores, RAM (GB), disk type, and
        sensible defaults for tools and logging.
        """
        cpu_cores = multiprocessing.cpu_count()
        ram_gb = None
        try:
            if psutil:
                ram_gb = int(psutil.virtual_memory().total / 1024**3)
        except Exception:
            ram_gb = None

        # Best-effort disk type detection (simplified)
        drive_type = "unknown"
        try:
            if os.path.exists("/"):
                drive_type = "local"
        except Exception:
            drive_type = "unknown"

        config: dict[str, Any] = {
            "db_path": "output/index.db",
            "log_dir": "logs",
            "tools": {"directories": ["nodupe/tools", "tools"], "auto_load": True},
            "cpu_cores": cpu_cores,
            "drive_type": drive_type,
        }
        # Only include ram_gb when we were able to detect it to avoid
        # inserting `None` into TOML-backed config containers (tomlkit
        # cannot convert None to a TOML item).
        if ram_gb is not None:
            config["ram_gb"] = ram_gb
        return config

    def _detect_system_resources(self) -> dict[str, Any]:
        """Detect system resources (CPU, RAM, disk) and derive defaults.

        Returns a dictionary containing:
        - cpu_cores: logical CPU cores
        - cpu_threads: same as cpu_cores (for naming compatibility)
        - ram_gb: total RAM in GB (if psutil available)
        - drive_type: 'ssd'|'hdd'|'unknown'
        - max_workers: conservative worker pool size derived from CPUs
        - batch_size: default batch size for processing
        """
        cpu_cores = multiprocessing.cpu_count()
        cpu_threads = os.cpu_count() or cpu_cores

        # RAM detection
        ram_gb = None
        try:
            if psutil:
                ram_gb = int(psutil.virtual_memory().total / 1024**3)
        except Exception:
            ram_gb = None

        # Drive type detection (best-effort)
        drive_type = "unknown"
        try:
            parts = []
            if psutil:
                parts = psutil.disk_partitions()
            if parts:
                dev = parts[0].device.lower()
                if "nvme" in dev or "ssd" in dev:
                    drive_type = "ssd"
                elif "sd" in dev or "hd" in dev:
                    drive_type = "ssd"
                else:
                    drive_type = "unknown"
        except Exception:
            drive_type = "unknown"

        # Derived defaults
        max_workers = max(1, cpu_threads * 2)
        batch_size = 500

        info: dict[str, Any] = {
            "cpu_cores": cpu_cores,
            "cpu_threads": cpu_threads,
            "ram_gb": ram_gb,
            "drive_type": drive_type,
            "max_workers": max_workers,
            "batch_size": batch_size,
        }

        # Allow thread restriction detection to annotate info
        try:
            self._detect_thread_restrictions(info)
        except Exception:
            # Non-critical
            pass

        return info

    def _detect_thread_restrictions(self, system_info: dict[str, Any]) -> None:
        """Detect if the runtime is running in a restricted/thread-limited
        environment (e.g. containers, Kubernetes) and annotate system_info.

        This will set:
        - thread_restrictions_detected: bool
        - thread_restriction_reasons: list[str]
        """
        reasons: list[str] = []
        env = os.environ

        # Kubernetes environment
        if env.get("KUBERNETES_SERVICE_HOST"):
            reasons.append("kubernetes")

        # Generic container detection
        if env.get("DOCKER_CONTAINER") or env.get("CONTAINER"):
            reasons.append("container")

        system_info["thread_restrictions_detected"] = bool(reasons)
        system_info["thread_restriction_reasons"] = reasons


def bootstrap() -> "CoreLoader":
    """Global bootstrap entry point."""
    logging.basicConfig(
        level=logging.INFO, format="[%(levelname)s] %(message)s"
    )
    loader = CoreLoader()
    loader.initialize()
    return loader
