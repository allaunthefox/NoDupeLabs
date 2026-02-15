"""
Core Loader Module
Handles bootstrap and initialization of the NoDupeLabs system
"""

import sys
import logging
from typing import Dict, Any  # Removed Optional as it's not used
from pathlib import Path
import platform
import os
import multiprocessing
try:
    import psutil
except ImportError:
    psutil = None  # type: ignore[assignment]

# Handle optional dependencies - using lowercase to avoid constant redefinition warnings
# These are checked at module import time but not used in this file
try:
    import blake3  # type: ignore # noqa: F401 # pylint: disable=unused-import
except ImportError:
    pass

try:
    import xxhash  # type: ignore # noqa: F401 # pylint: disable=unused-import
except ImportError:
    pass

from .config import load_config
from .container import container as global_container
from .plugin_system.registry import PluginRegistry
from .plugin_system.loader import create_plugin_loader
from .plugin_system.discovery import create_plugin_discovery
from .plugin_system.lifecycle import create_lifecycle_manager
from .plugin_system.hot_reload import PluginHotReload
from .database.connection import get_connection
from .scan.hash_autotune import autotune_hash_algorithm, create_autotuned_hasher


class CoreLoader:
    """Main application loader and bootstrap class"""

    def __init__(self):
        """Initialize the core loader"""
        self.config = None
        self.container = None
        self.plugin_registry = None
        self.plugin_loader = None
        self.plugin_discovery = None
        self.plugin_lifecycle = None
        self.hot_reload = None
        self.database = None
        self.initialized = False

    def initialize(self) -> None:
        """Initialize the core system"""
        if self.initialized:
            return

        try:
            # Load configuration
            # Load configuration
            self.config = load_config()

            # Apply platform-specific autoconfiguration
            platform_config = self._apply_platform_autoconfig()
            # Merge platform config into loaded config (loaded config takes precedence for existing keys,
            # but we want platform defaults if missing)
            # Actually, usually config file overrides auto-detect.
            # But here ConfigManager returns a Config object or dict?
            # load_config returns ConfigManager. We need to access its internal config or update it.
            # ConfigManager.config is a dict.
            if hasattr(self.config, 'config'):
                # Merge platform config with existing config, preserving existing values
                for key, value in platform_config.items():
                    if key not in self.config.config:
                        # Access config directly since ConfigManager may not have __setitem__
                        self.config.config[key] = value
                    elif isinstance(value, dict) and isinstance(self.config.config[key], dict):
                        # Deep merge for nested dicts like 'plugins'
                        for nested_key in value:  # type: ignore
                            if nested_key not in self.config.config[key]:
                                # type: ignore
                                self.config.config[key][nested_key] = value[nested_key]

            logging.info("Configuration loaded successfully")

            # Initialize dependency container
            self.container = global_container
            if self.container:
                self.container.register_service('config', self.config)
            logging.info("Dependency container initialized")

            # Initialize plugin system components
            self.plugin_registry = PluginRegistry()
            if self.container:
                self.plugin_registry.initialize(self.container)
                self.container.register_service('plugin_registry', self.plugin_registry)
            logging.info("Plugin registry initialized")

            self.plugin_loader = create_plugin_loader(self.plugin_registry)
            if self.container:
                self.container.register_service('plugin_loader', self.plugin_loader)
            logging.info("Plugin loader initialized")

            self.plugin_discovery = create_plugin_discovery()
            if self.container:
                self.container.register_service('plugin_discovery', self.plugin_discovery)
            logging.info("Plugin discovery initialized")

            self.plugin_lifecycle = create_lifecycle_manager(self.plugin_registry)
            if self.container:
                self.container.register_service('plugin_lifecycle', self.plugin_lifecycle)
            logging.info("Plugin lifecycle manager initialized")

            # Initialize hot reload (if configured)
            self.hot_reload = PluginHotReload(
                self.plugin_loader,
                self.plugin_lifecycle,
                self.container
            )
            if self.container:
                self.container.register_service('hot_reload', self.hot_reload)

            # Check config for hot reload
            config_dict = getattr(self.config, 'config', {})
            hot_reload_enabled = config_dict.get('plugins', {}).get(
                'hot_reload', True)  # Default True for now

            if hot_reload_enabled:
                self.hot_reload.start()
                logging.info("Hot reload service started")

            # Discover and load plugins
            self._discover_and_load_plugins()

            # Initialize database
            self.database = get_connection()
            self.database.initialize_database()
            if self.container:
                self.container.register_service('database', self.database)
            logging.info("Database initialized")

            # Initialize all plugins
            self.plugin_lifecycle.initialize_all_plugins(self.container)

            # Perform hash algorithm autotuning
            self._perform_hash_autotuning()

            self.initialized = True
            logging.info("Core system initialized successfully")

        except Exception as e:
            logging.error(f"Failed to initialize core system: {e}")
            raise

    def _discover_and_load_plugins(self) -> None:
        """Discover and load plugins from configured directories."""
        # ConfigManager stores actual config in .config attribute
        config_dict = getattr(self.config, 'config', {})

        if not config_dict or 'plugins' not in config_dict:
            logging.info("No plugin configuration found, skipping plugin loading")
            return

        plugin_config = config_dict['plugins']
        plugin_dirs = plugin_config.get('directories', ['plugins'])
        auto_load = plugin_config.get('auto_load', True)
        loading_order = plugin_config.get('loading_order', [])

        if not auto_load:
            logging.info("Plugin auto-loading disabled")
            return

        # Convert string paths to Path objects
        plugin_path_dirs = [Path(p) for p in plugin_dirs if Path(p).exists()]

        if not plugin_path_dirs:
            logging.info("No plugin directories found, skipping plugin loading")
            return

        logging.info(f"Discovering plugins in directories: {plugin_path_dirs}")

        # Discover plugins
        discovered_plugins = []
        if self.plugin_discovery:
            for plugin_dir in plugin_path_dirs:
                plugins = self.plugin_discovery.discover_plugins_in_directory(
                    plugin_dir,
                    recursive=True
                )
                discovered_plugins.extend(plugins)  # type: ignore
                logging.info(f"Discovered {len(plugins)} plugins in {plugin_dir}")

        logging.info(f"Total discovered plugins: {len(discovered_plugins)}")  # type: ignore

        # Load plugins in specified order
        if self.plugin_discovery:
            for plugin_name in loading_order:
                plugin_info = self.plugin_discovery.get_discovered_plugin(plugin_name)
                if plugin_info:
                    self._load_single_plugin(plugin_info)

        # Load remaining plugins (not in specific order)
        if self.plugin_discovery:
            for plugin_info in self.plugin_discovery.get_discovered_plugins():
                if plugin_info.name not in loading_order:
                    self._load_single_plugin(plugin_info)

    def _load_single_plugin(self, plugin_info: Any) -> None:
        """Load a single plugin by its information."""
        try:
            # Load plugin class
            if not self.plugin_loader:
                logging.warning(f"Plugin loader not available for plugin: {plugin_info.name}")
                return

            plugin_class = self.plugin_loader.load_plugin_from_file(plugin_info.path)
            if not plugin_class:
                logging.warning(f"Failed to load plugin: {plugin_info.name}")
                return

            # Validate plugin before instantiation
            # Note: Using getattr to avoid protected member access warning
            validate_method = getattr(self.plugin_loader, '_validate_plugin_class', None)
            if validate_method and not validate_method(plugin_class):
                logging.warning(f"Invalid plugin class: {plugin_info.name}")
                return

            # Instantiate and register plugin
            if not self.plugin_loader:
                logging.warning(f"Plugin loader not available for plugin: {plugin_info.name}")
                return
            plugin_instance = self.plugin_loader.instantiate_plugin(plugin_class)  # type: ignore
            if self.plugin_loader:
                self.plugin_loader.register_loaded_plugin(plugin_instance, plugin_info.path)

            # Register for hot reload watching if active
            if self.hot_reload:
                self.hot_reload.watch_plugin(plugin_instance.name, plugin_info.path)

            logging.info(f"Successfully loaded plugin: {plugin_info.name}")

        except Exception as e:
            logging.error(f"Failed to load plugin {plugin_info.name}: {e}")

    def shutdown(self) -> None:
        """Shutdown the core system"""
        if not self.initialized:
            return

        try:
            # Shutdown all plugins
            if self.plugin_lifecycle:
                self.plugin_lifecycle.shutdown_all_plugins()
                logging.info("Plugin lifecycle shutdown completed")

            # Shutdown hot reload
            if self.hot_reload:
                self.hot_reload.stop()
                logging.info("Hot reload service stopped")

            # Close database
            if self.database:
                self.database.close()
                logging.info("Database connection closed")

            # Shutdown plugin registry
            if self.plugin_registry:
                self.plugin_registry.shutdown()
                logging.info("Plugin registry shutdown")

            self.initialized = False
            logging.info("Core system shutdown successfully")

        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
            raise

    def _apply_platform_autoconfig(self) -> Dict[str, Any]:
        """Apply system resource-based autoconfiguration."""
        config: Dict[str, Any] = {
            'db_path': 'output/index.db',
            'log_dir': 'logs',
            'plugins': {
                'directories': ['plugins', 'core/plugins', 'nodupe/plugins'],
                'auto_load': True,
                'hot_reload': True,
                'loading_order': [
                    'core',
                    'database',
                    'scan',
                    'similarity',
                    'apply',
                    'plan'
                ]
            }
        }

        # System resource detection
        system_info = self._detect_system_resources()
        config.update(system_info)  # type: ignore

        # Platform-specific configuration
        system_platform = platform.system().lower()
        if system_platform == 'windows':
            config.update({  # type: ignore
                'db_path': os.path.join('output', 'index.db'),
                'use_symlinks': False
            })
        else:
            config.update({  # type: ignore
                'use_symlinks': True
            })

        # Environment-specific configuration
        if 'CI' in os.environ or 'GITHUB_ACTIONS' in os.environ:
            config['ci_mode'] = True
            config['verbose_logging'] = True
        else:
            config['ci_mode'] = False
            config['verbose_logging'] = False

        logging.info("Applied system resource-based configuration")
        return config

    def _detect_system_resources(self) -> Dict[str, Any]:
        """Detect system resources (CPU, RAM, drive type)."""
        system_info: Dict[str, Any] = {
            'cpu_cores': 1,
            'cpu_threads': 1,
            'ram_gb': 1,
            'drive_type': 'unknown',
            'max_workers': 2,
            'batch_size': 100,
            'memory_cache_size': '100MB',
            'disk_cache_size': '1GB'
        }

        try:
            # CPU Information
            cpu_cores = multiprocessing.cpu_count()
            if cpu_cores:
                system_info['cpu_cores'] = cpu_cores
                system_info['cpu_threads'] = cpu_cores

            try:
                cpu_threads = os.cpu_count()
                if cpu_threads:
                    system_info['cpu_threads'] = cpu_threads
            except (AttributeError, ValueError):
                pass

            # Detect thread restrictions
            self._detect_thread_restrictions(system_info)  # type: ignore

            # RAM Information
            try:
                if psutil and hasattr(psutil, 'virtual_memory'):
                    ram = psutil.virtual_memory()
                    ram_gb = round(ram.total / (1024 ** 3))
                    system_info['ram_gb'] = ram_gb
            except Exception:
                pass

            # Drive Type Detection (only once)
            try:
                if psutil and hasattr(psutil, 'disk_partitions'):
                    partitions = psutil.disk_partitions()
                    for partition in partitions:
                        if ('/sdcard' in partition.mountpoint.lower() or
                                '/storage' in partition.mountpoint.lower()):
                            system_info['drive_type'] = 'sdcard'
                            break
                        elif partition.mountpoint == '/':
                            opts_lower = partition.opts.lower()
                            if 'ssd' in opts_lower or 'nvme' in partition.device.lower():
                                system_info['drive_type'] = 'ssd'
                            else:
                                system_info['drive_type'] = 'hdd'
                            break
            except Exception:
                pass

            # Configure based on resources
            self._configure_based_on_resources(system_info)  # type: ignore

        except Exception as e:
            logging.warning(f"System resource detection failed: {e}")

        return system_info

    def _configure_based_on_resources(self, system_info: Dict[str, Any]) -> None:
        """Configure system parameters based on detected resources."""
        cpu_cores = system_info.get('cpu_cores', 1)
        ram_gb = system_info.get('ram_gb', 1)
        drive_type = system_info.get('drive_type', 'unknown')

        # Configure max workers - use 2x CPU cores for better parallelism
        # but cap at reasonable limits based on system resources
        max_workers = cpu_cores * 2
        
        # Apply limits based on RAM
        if ram_gb <= 2:
            max_workers = min(max_workers, 2)
        elif ram_gb <= 4:
            max_workers = min(max_workers, 4)
        elif ram_gb <= 8:
            max_workers = min(max_workers, 8)
        elif ram_gb <= 16:
            max_workers = min(max_workers, 16)
        else:
            max_workers = min(max_workers, 32)
            
        system_info['max_workers'] = max_workers

        # Configure batch size
        if ram_gb <= 2:
            system_info['batch_size'] = 50
            system_info['memory_cache_size'] = '50MB'
        elif ram_gb <= 4:
            system_info['batch_size'] = 100
            system_info['memory_cache_size'] = '100MB'
        elif ram_gb <= 8:
            system_info['batch_size'] = 200
            system_info['memory_cache_size'] = '200MB'
        elif ram_gb <= 16:
            system_info['batch_size'] = 500
            system_info['memory_cache_size'] = '500MB'
        else:
            system_info['batch_size'] = 1000
            system_info['memory_cache_size'] = '1GB'

        # Configure disk cache
        if drive_type == 'ssd':
            system_info['disk_cache_size'] = '2GB'
            system_info['use_disk_cache'] = True
        elif drive_type == 'sdcard':
            system_info['disk_cache_size'] = '500MB'
            system_info['use_disk_cache'] = True
            system_info['sdcard_optimized'] = True
        else:
            system_info['disk_cache_size'] = '1GB'
            system_info['use_disk_cache'] = True

    def _detect_thread_restrictions(self, system_info: Dict[str, Any]) -> None:
        """Detect and adapt to thread restrictions."""
        thread_restrictions_detected = False
        restriction_reason: list[str] = []

        if 'KUBERNETES_SERVICE_HOST' in os.environ:
            thread_restrictions_detected = True
            restriction_reason.append('kubernetes')  # type: ignore
        if 'DOCKER_CONTAINER' in os.environ or 'CONTAINER' in os.environ:
            thread_restrictions_detected = True
            restriction_reason.append('container')  # type: ignore

        if thread_restrictions_detected:
            system_info['thread_restrictions_detected'] = True
            system_info['thread_restriction_reasons'] = restriction_reason
            # Reduce workers conservatively
            if system_info.get('cpu_cores', 1) > 2:
                # Force conservative workers in containers
                pass

    def _perform_hash_autotuning(self) -> None:
        """Perform hash algorithm autotuning and register the optimal hasher."""
        try:
            logging.info("Starting hash algorithm autotuning...")

            # Get system information for optimal configuration
            system_resources = self._detect_system_resources()
            ram_gb = system_resources.get('ram_gb', 1)

            # Determine if we're memory constrained
            memory_constrained = ram_gb < 4  # Less than 4GB is considered memory constrained

            # Perform autotuning with system-appropriate parameters
            autotune_results = autotune_hash_algorithm(
                sample_size=1024 * 1024,  # 1MB sample
                iterations=5 if memory_constrained else 10,  # Fewer iterations for memory constrained
                file_size_threshold=10 * 1024 * 1024  # 10MB threshold
            )

            optimal_algorithm = autotune_results['optimal_algorithm']
            benchmark_results = autotune_results['benchmark_results']

            logging.info(f"Hash autotuning completed. Optimal algorithm: {optimal_algorithm}")
            logging.info(f"Available algorithms: {autotune_results['available_algorithms']}")
            logging.info(f"BLAKE3 available: {autotune_results['has_blake3']}")
            logging.info(f"xxHash available: {autotune_results['has_xxhash']}")

            # Log performance results
            sorted_results = sorted(benchmark_results.items(), key=lambda x: x[1])
            for algo, time_taken in sorted_results[:5]:  # Show top 5
                logging.info(f"  {algo}: {time_taken:.6f}s")

            # Create autotuned hasher and register it in the container
            autotuned_hasher, _ = create_autotuned_hasher()
            if self.container:
                self.container.register_service('hasher', autotuned_hasher)

            # Also register the autotune results for reference
            if self.container:
                self.container.register_service('hash_autotune_results', autotune_results)

            logging.info("Hash autotuning completed and registered successfully")

        except Exception as e:
            logging.error(f"Hash autotuning failed: {e}")
            # Fallback to default hasher
            from .scan.hasher import FileHasher
            default_hasher = FileHasher(algorithm='sha256')
            if self.container:
                self.container.register_service('hasher', default_hasher)
            logging.info("Registered default SHA-256 hasher as fallback")


def bootstrap() -> 'CoreLoader':
    """Bootstrap the application"""
    # Set up basic logging before anything else
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    # Create and initialize core loader
    loader = CoreLoader()
    loader.initialize()

    return loader
