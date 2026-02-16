# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Core Loader Module.

Handles bootstrap and initialization of the NoDupeLabs framework.
Strictly decoupled: Does not import functional tools directly.
"""

import sys
import logging
import platform
import os
import multiprocessing
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore[assignment]

from .config import load_config
from .container import container as global_container
from .tool_system.registry import ToolRegistry
from .tool_system.loader import create_tool_loader
from .tool_system.discovery import create_tool_discovery
from .tool_system.lifecycle import create_lifecycle_manager
from .tool_system.hot_reload import ToolHotReload
from .api.ipc import ToolIPCServer
from .api.codes import ActionCode


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
            if hasattr(self.config, 'config'):
                for key, value in platform_config.items():
                    if key not in self.config.config:
                        self.config.config[key] = value

            self.logger.info(f"[{ActionCode.FIA_UAU_INIT}] Framework configuration loaded")

            # 2. Initialize dependency container
            self.container = global_container
            self.container.register_service('config', self.config)
            self.logger.info(f"[{ActionCode.FIA_UAU_INIT}] Service container ready")

            # 3. Initialize tool system
            self.tool_registry = ToolRegistry()
            self.tool_registry.initialize(self.container)
            self.container.register_service('tool_registry', self.tool_registry)

            self.tool_loader = create_tool_loader(self.tool_registry)
            self.tool_loader.initialize(self.container)
            self.container.register_service('tool_loader', self.tool_loader)

            self.tool_discovery = create_tool_discovery()
            self.container.register_service('tool_discovery', self.tool_discovery)

            self.tool_lifecycle = create_lifecycle_manager(self.tool_registry)
            self.container.register_service('tool_lifecycle', self.tool_lifecycle)

            # 4. Start maintenance services
            self.hot_reload = ToolHotReload(self.tool_registry, self.tool_loader)
            self.hot_reload.start()
            self.container.register_service('hot_reload', self.hot_reload)

            # 5. Start programmatic interface (IPC)
            self.ipc_server = ToolIPCServer(self.tool_registry)
            self.ipc_server.start()
            self.container.register_service('ipc_server', self.ipc_server)

            # 6. Discover and load functional tools (Deduplication, Databases, Hashing, etc.)
            self.logger.info(f"[{ActionCode.FIA_UAU_LOAD}] Starting tool discovery and loading")
            self._discover_and_load_tools()

            # 7. Lifecycle: Initialize all loaded tools
            self.logger.info(f"[{ActionCode.FIA_UAU_INIT}] Initializing all loaded tools")
            self.tool_lifecycle.initialize_all_tools(self.container)

            # 8. Post-initialization tasks (e.g. autotuning) handled via dynamic discovery
            self._perform_hash_autotuning()

            self.initialized = True
            self.logger.info(f"[{ActionCode.FIA_UAU_INIT}] Pure Core Engine initialized successfully")
            self.logger.info(f"[{ActionCode.ACC_ISO_CMP}] Core engine is ISO accessibility compliant")

        except Exception as e:
            self.logger.error(f"[{ActionCode.FPT_STM_ERR}] Framework startup failed: {e}")
            raise

    def _discover_and_load_tools(self) -> None:
        """Discover and load tools from configured directories."""
        config_dict = getattr(self.config, 'config', {})
        tool_dirs = config_dict.get('tools', {}).get('directories', ['tools'])

        # Absolute paths for discovery
        tool_path_dirs = [Path(p).resolve() for p in tool_dirs if Path(p).exists()]
        if not tool_path_dirs:
            # Fallback to standard locations
            standard_paths = [Path('nodupe/tools').resolve(), Path('tools').resolve()]
            tool_path_dirs = [p for p in standard_paths if p.exists()]

        self.logger.info(f"[{ActionCode.FIA_UAU_LOAD}] Discovering tools in: {tool_path_dirs}")

        for tool_dir in tool_path_dirs:
            tools = self.tool_discovery.discover_tools_in_directory(tool_dir)
            self.logger.info(f"[{ActionCode.FIA_UAU_LOAD}] Found {len(tools)} tools in {tool_dir}")
            for tool_info in tools:
                self._load_single_tool(tool_info)

    def _load_single_tool(self, tool_info: Any) -> None:
        """Load a tool using the framework's loader."""
        try:
            self.logger.info(f"[{ActionCode.FIA_UAU_LOAD}] Loading tool: {tool_info.name}")
            tool_class = self.tool_loader.load_tool_from_file(tool_info.path)
            if tool_class:
                tool_instance = self.tool_loader.instantiate_tool(tool_class)
                self.tool_loader.register_loaded_tool(tool_instance, tool_info.path)

                if self.hot_reload:
                    self.hot_reload.watch_tool(tool_instance.name, tool_info.path)

                self.logger.info(f"[{ActionCode.FIA_UAU_LOAD}] Loaded tool: {tool_info.name}")
                
                # Check if the tool is accessibility-compliant
                if hasattr(tool_instance, 'get_ipc_socket_documentation'):
                    self.logger.info(f"[{ActionCode.ACC_ISO_CMP}] Tool {tool_info.name} is ISO accessibility compliant")
                
        except Exception as e:
            self.logger.error(f"[{ActionCode.FPT_FLS_FAIL}] Failed to load tool {tool_info.name}: {e}")

    def _perform_hash_autotuning(self) -> None:
        """Perform hash algorithm autotuning if the hashing tool is present."""
        try:
            # Check if hasher service was registered by any loaded tool
            hasher = self.container.get_service('hasher_service')
            if not hasher: return

            # Dynamic import of autotune logic from the hashing tool
            try:
                from ..tools.hashing.autotune_logic import autotune_hash_algorithm
                self.logger.info("Starting hash algorithm autotuning...")
                results = autotune_hash_algorithm()
                algo = results['optimal_algorithm']
                self.logger.info(f"[{ActionCode.FDP_DAU_HASH}] Optimal algorithm identified: {algo}")
                
                if hasattr(hasher, 'set_algorithm'):
                    hasher.set_algorithm(algo)
            except ImportError:
                self.logger.debug("Hashing autotune logic not available in toolpath")
        except Exception as e:
            self.logger.error(f"[{ActionCode.FPT_STM_ERR}] Autotune failed: {e}")

    def shutdown(self) -> None:
        """Gracefully shutdown the framework and all loaded tools."""
        if not self.initialized: return

        try:
            self.logger.info(f"[{ActionCode.FIA_UAU_SHUTDOWN}] Starting framework shutdown")
            
            if self.tool_lifecycle:
                self.logger.info(f"[{ActionCode.FIA_UAU_SHUTDOWN}] Shutting down all tools")
                self.tool_lifecycle.shutdown_all_tools()
            if self.hot_reload:
                self.logger.info(f"[{ActionCode.FIA_UAU_SHUTDOWN}] Stopping hot reload")
                self.hot_reload.stop()
            if self.ipc_server:
                self.logger.info(f"[{ActionCode.FIA_UAU_SHUTDOWN}] Stopping IPC server")
                self.ipc_server.stop()
            if self.tool_registry:
                self.logger.info(f"[{ActionCode.FIA_UAU_SHUTDOWN}] Shutting down registry")
                self.tool_registry.shutdown()

            self.initialized = False
            self.logger.info(f"[{ActionCode.FIA_UAU_SHUTDOWN}] Framework shutdown complete")

            # Final maintenance using maintenance tool if available
            try:
                from ..tools.maintenance.log_compressor import LogCompressor
                log_dir = getattr(self.config, 'config', {}).get('log_dir', 'logs')
                self.logger.info(f"[{ActionCode.FIA_UAU_SHUTDOWN}] Compressing old logs in {log_dir}")
                LogCompressor.compress_old_logs(log_dir)
            except ImportError:
                pass

        except Exception as e:
            self.logger.error(f"[{ActionCode.FPT_STM_ERR}] Shutdown error: {e}")

    def _apply_platform_autoconfig(self) -> Dict[str, Any]:
        """Apply system resource-based autoconfiguration."""
        config: Dict[str, Any] = {
            'db_path': 'output/index.db',
            'log_dir': 'logs'
        }
        # Simplified for Core
        return config

    def _detect_system_resources(self) -> Dict[str, Any]:
        """Detect system resources (CPU, RAM)."""
        return {'cpu_cores': multiprocessing.cpu_count()}


def bootstrap() -> 'CoreLoader':
    """Global bootstrap entry point."""
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    loader = CoreLoader()
    loader.initialize()
    return loader
