# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun
# pylint: disable=broad-exception-caught,unused-argument

"""NoDupeLabs Core Loader - Minimal entry point with hard isolation.

This module provides the core loader functionality with complete isolation
from optional dependencies. It implements the minimal required functionality
for the application to start and manage plugins.

Key Features:
    - Minimal dependencies (standard library only)
    - Hard isolation from optional functionality
    - Plugin management system
    - Graceful degradation framework
    - Error handling with resilience focus

Dependencies:
    - Standard library only
"""

import sys
import argparse
import platform
import os
import multiprocessing
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import psutil
except ImportError:
    psutil = None

# Optional imports with graceful fallback
try:
    import yaml
except ImportError:
    yaml = None

try:
    from pluggy import PluginManager
except ImportError:
    PluginManager = None


class CoreLoader:
    """Core loader with hard isolation from optional functionality.

    Responsibilities:
    - Minimal CLI parsing
    - Plugin management
    - Dependency injection container
    - Error handling
    - Graceful degradation
    """

    def __init__(self) -> None:
        """Initialize core loader with minimal dependencies."""
        self.plugins: List[str] = []
        self.services: Dict[str, Any] = {}
        self.config: Dict[str, Any] = {}

    def load_config(self, config_path: str = "nodupe.yml") -> Dict[str, Any]:
        """Load configuration with graceful fallback and platform-specific autoconfiguration.

        Args:
            config_path: Path to configuration file

        Returns:
            Dictionary containing configuration
        """
        config: Dict[str, Any] = {}

        try:
            # Use top-level yaml import with graceful fallback
            if yaml:
                config_path_obj = Path(config_path)
                if config_path_obj.exists():
                    with open(config_path_obj, 'r', encoding='utf-8') as f:
                        yaml_config = yaml.safe_load(f) or {}
                        if isinstance(yaml_config, dict):
                            config.update(yaml_config)  # type: ignore[arg-type]
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[WARN] Config load error: {e}", file=sys.stderr)

        # Apply platform-specific autoconfiguration and merge with YAML config
        platform_config = self._apply_platform_autoconfig()
        platform_config.update(config)  # YAML config takes precedence
        return platform_config

    def _apply_platform_autoconfig(self) -> Dict[str, Any]:
        """Apply system resource-based autoconfiguration.

        Returns:
            Dictionary containing system resource-based configuration
        """
        config: Dict[str, Any] = {
            'db_path': 'output/index.db',
            'log_dir': 'logs',
            'plugins': {
                'directories': ['plugins', 'core/plugins'],
                'auto_load': True,
                'loading_order': [
                    'core',
                    'database',
                    'scan',
                    'similarity',
                    'apply']}}

        # System resource detection with graceful fallback
        system_info: Dict[str, Any] = self._detect_system_resources()
        config.update(**system_info)

        # Platform-specific configuration
        system_platform = platform.system().lower()
        machine_arch = platform.machine().lower()

        print(f"[INFO] Detected platform: {system_platform} ({machine_arch})")
        cpu_cores = system_info.get('cpu_cores', 'unknown')
        cpu_threads = system_info.get('cpu_threads', 'unknown')
        ram_gb = system_info.get('ram_gb', 'unknown')
        drive_type = system_info.get('drive_type', 'unknown')
        print(
            f"[INFO] System resources: CPU cores={cpu_cores}, threads={cpu_threads}, "
            f"RAM={ram_gb}GB, drive_type={drive_type}")

        # Platform-specific overrides
        if system_platform == 'windows':
            config.update({
                'db_path': os.path.join('output', 'index.db'),
                'use_symlinks': False  # Windows has issues with symlinks
            })
        else:  # Unix-like systems (Linux, macOS, etc.)
            config.update({
                'use_symlinks': True
            })

        # Environment-specific configuration
        if 'CI' in os.environ or 'GITHUB_ACTIONS' in os.environ:
            config['ci_mode'] = True
            config['verbose_logging'] = True
        else:
            config['ci_mode'] = False
            config['verbose_logging'] = False

        print("[INFO] Applied system resource-based configuration")
        return config

    def _detect_system_resources(self) -> Dict[str, Any]:
        """Detect system resources (CPU, RAM, drive type) with graceful fallback.

        Returns:
            Dictionary containing system resource information
        """
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
                # Default to cores if threads unknown
                system_info['cpu_threads'] = cpu_cores

            # Try to get logical CPU count (threads)
            try:
                cpu_threads = os.cpu_count()
                if cpu_threads:
                    system_info['cpu_threads'] = cpu_threads
            except (AttributeError, ValueError):
                pass

            # Detect thread restrictions (common in containers, mobile devices,
            # etc.)
            self._detect_thread_restrictions(system_info)

            # RAM Information
            try:
                if psutil and hasattr(psutil, 'virtual_memory'):
                    ram = psutil.virtual_memory()
                    ram_gb = round(ram.total / (1024 ** 3))
                    system_info['ram_gb'] = ram_gb
            except (ImportError, AttributeError, Exception):
                pass

            # Drive Type Detection
            try:
                if psutil and hasattr(psutil, 'disk_partitions'):
                    partitions = psutil.disk_partitions()
                    for partition in partitions:
                        # Check for Android SD card mount points
                        if ('/sdcard' in partition.mountpoint.lower() or
                                '/storage' in partition.mountpoint.lower()):
                            system_info['drive_type'] = 'sdcard'
                            break
                        elif partition.mountpoint == '/':
                            # Simple heuristic for drive type
                            opts_lower = partition.opts.lower()
                            device_lower = partition.device.lower()
                            if ('ssd' in opts_lower or
                                    'nvme' in device_lower):
                                system_info['drive_type'] = 'ssd'
                            else:
                                system_info['drive_type'] = 'hdd'
                            break
            except (ImportError, AttributeError, Exception):
                pass

            # System resource-based configuration
            self._configure_based_on_resources(system_info)

        except Exception as e:
            print(
                f"[WARN] System resource detection failed: {e}",
                file=sys.stderr)

        return system_info

    def _configure_based_on_resources(
            self, system_info: Dict[str, Any]) -> None:
        """Configure system parameters based on detected resources.

        Args:
            system_info: Dictionary containing system resource information
        """
        cpu_cores = system_info.get('cpu_cores', 1)
        ram_gb = system_info.get('ram_gb', 1)
        drive_type = system_info.get('drive_type', 'unknown')

        # Configure max workers based on CPU cores
        if cpu_cores <= 2:
            system_info['max_workers'] = 2
        elif cpu_cores <= 4:
            system_info['max_workers'] = 4
        elif cpu_cores <= 8:
            system_info['max_workers'] = 8
        elif cpu_cores <= 16:
            system_info['max_workers'] = 16
        else:
            # Cap at 32 workers for very high core counts
            system_info['max_workers'] = 32

        # Configure batch size based on RAM
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

        # Configure disk cache based on drive type
        if drive_type == 'ssd':
            system_info['disk_cache_size'] = '2GB'
            system_info['use_disk_cache'] = True
        elif drive_type == 'sdcard':
            # SD card specific configuration - more conservative
            system_info['disk_cache_size'] = '500MB'
            system_info['use_disk_cache'] = True
            system_info['sdcard_optimized'] = True
            system_info['low_power_mode'] = True
            system_info['reduce_writes'] = True
        else:  # HDD or unknown
            system_info['disk_cache_size'] = '1GB'
            system_info['use_disk_cache'] = True

        # Configure parallel processing strategy
        if cpu_cores >= 8 and ram_gb >= 16 and drive_type == 'ssd':
            system_info['processing_strategy'] = 'aggressive'
            system_info['concurrency_model'] = 'async'
        elif cpu_cores >= 4 and ram_gb >= 8:
            system_info['processing_strategy'] = 'balanced'
            system_info['concurrency_model'] = 'threaded'
        else:
            system_info['processing_strategy'] = 'conservative'
            system_info['concurrency_model'] = 'sequential'

        # Configure memory usage based on RAM
        if ram_gb >= 16:
            system_info['large_file_threshold'] = '1GB'
            system_info['memory_intensive_operations'] = True
        elif ram_gb >= 8:
            system_info['large_file_threshold'] = '500MB'
            system_info['memory_intensive_operations'] = True
        else:
            system_info['large_file_threshold'] = '100MB'
            system_info['memory_intensive_operations'] = False

    def _detect_thread_restrictions(self, system_info: Dict[str, Any]) -> None:
        """Detect and adapt to thread restrictions common in containers and mobile environments.

        Args:
            system_info: Dictionary containing system resource information
        """
        # Initialize variables
        thread_restrictions_detected = False
        restriction_reason: List[str] = []

        try:
            # Check for common thread restriction indicators

            # 1. Check environment variables that indicate thread restrictions
            if 'KUBERNETES_SERVICE_HOST' in os.environ:
                thread_restrictions_detected = True
                restriction_reason.append('kubernetes')
            if 'DOCKER_CONTAINER' in os.environ or 'CONTAINER' in os.environ:
                thread_restrictions_detected = True
                restriction_reason.append('container')
            if 'ANDROID_ROOT' in os.environ or 'ANDROID_DATA' in os.environ:
                thread_restrictions_detected = True
                restriction_reason.append('android')

            # 2. Check for cgroup restrictions (common in containers)
            try:
                if os.path.exists('/sys/fs/cgroup/cpu.max'):
                    with open('/sys/fs/cgroup/cpu.max', 'r') as f:
                        cpu_max = f.read().strip()
                        if ' ' in cpu_max:
                            quota, period = cpu_max.split()
                            if int(quota) < int(period):
                                thread_restrictions_detected = True
                                restriction_reason.append('cgroup_cpu_limit')
            except Exception:
                pass

            # 3. Check for low CPU core count (indicative of restricted
            # environment)
            cpu_cores = system_info.get('cpu_cores', 1)
            if cpu_cores <= 2:
                thread_restrictions_detected = True
                restriction_reason.append('low_cpu_cores')

            # 4. Check for mobile/embedded platforms
            system_platform = platform.system().lower()
            if system_platform in ['android', 'ios']:
                thread_restrictions_detected = True
                restriction_reason.append('mobile_platform')

        except Exception as e:
            print(
                f"[WARN] Thread restriction detection failed: {e}",
                file=sys.stderr)

        # Apply thread restriction adaptations if detected
        if thread_restrictions_detected:
            system_info['thread_restrictions_detected'] = True
            system_info['thread_restriction_reasons'] = restriction_reason

            # Reduce worker count to be more conservative
            current_max_workers = system_info.get('max_workers', 2)
            if current_max_workers > 4:
                system_info['max_workers'] = max(2, current_max_workers // 2)
            restriction_msg = ', '.join(restriction_reason)
            print(
                f"[INFO] Thread restrictions detected ({restriction_msg}), "
                f"reduced max_workers from {current_max_workers} to {system_info['max_workers']}")

            # Use more conservative processing strategy
            system_info['processing_strategy'] = 'conservative'
            system_info['concurrency_model'] = 'sequential'

            # Reduce batch size for memory efficiency
            current_batch_size = system_info.get('batch_size', 100)
            if current_batch_size > 100:
                system_info['batch_size'] = 100
                print(
                    f"[INFO] Reduced batch_size from {current_batch_size} "
                    f"to 100 due to thread restrictions")

            # Enable thread restriction optimizations
            system_info['thread_restriction_optimized'] = True
            system_info['aggressive_thread_management'] = False
            system_info['use_thread_pool'] = False

            print(f"[INFO] Adapted to thread restrictions: {restriction_msg}")

    def _apply_custom_performance_settings(
            self, args: argparse.Namespace) -> None:
        """Apply custom performance settings from command line arguments.

        Args:
            args: Parsed command line arguments
        """
        try:
            custom_settings_applied = False

            # Apply custom CPU cores if specified
            if args.cores is not None:
                original_cores = self.config.get('cpu_cores', 'auto')
                self.config['cpu_cores'] = args.cores
                print(
                    f"[INFO] Override: CPU cores set to {args.cores} (was: {original_cores})")
                custom_settings_applied = True

            # Apply custom CPU threads if specified
            if args.threads is not None:
                original_threads = self.config.get('cpu_threads', 'auto')
                self.config['cpu_threads'] = args.threads
                print(
                    f"[INFO] Override: CPU threads set to {args.threads} (was: {original_threads})")
                custom_settings_applied = True

            # Apply custom max workers if specified
            if args.max_workers is not None:
                original_workers = self.config.get('max_workers', 'auto')
                self.config['max_workers'] = args.max_workers
                print(
                    f"[INFO] Override: max_workers set to {args.max_workers} (was: {original_workers})")
                custom_settings_applied = True

            # Apply custom batch size if specified
            if args.batch_size is not None:
                original_batch = self.config.get('batch_size', 'auto')
                self.config['batch_size'] = args.batch_size
                print(
                    f"[INFO] Override: batch_size set to {args.batch_size} (was: {original_batch})")
                custom_settings_applied = True

            # Reconfigure based on custom settings if any were applied
            if custom_settings_applied:
                print("[INFO] Custom performance settings applied")
                # Update derived settings based on custom values
                self._update_derived_settings()

        except Exception as e:
            print(
                f"[WARN] Failed to apply custom performance settings: {e}",
                file=sys.stderr)

    def _update_derived_settings(self) -> None:
        """Update derived settings based on current core configuration.

        This method recalculates settings that depend on CPU cores, RAM, etc.
        after custom values have been applied.
        """
        try:
            # Update processing strategy based on current cores and RAM
            cpu_cores = self.config.get('cpu_cores', 1)
            ram_gb = self.config.get('ram_gb', 1)
            drive_type = self.config.get('drive_type', 'unknown')

            # Update processing strategy
            if (cpu_cores >= 8 and ram_gb >= 16 and
                    drive_type == 'ssd'):
                self.config['processing_strategy'] = 'aggressive'
                self.config['concurrency_model'] = 'async'
            elif cpu_cores >= 4 and ram_gb >= 8:
                self.config['processing_strategy'] = 'balanced'
                self.config['concurrency_model'] = 'threaded'
            else:
                self.config['processing_strategy'] = 'conservative'
                self.config['concurrency_model'] = 'sequential'

            print(
                f"[INFO] Updated processing strategy to: {self.config['processing_strategy']}")

        except Exception as e:
            print(
                f"[WARN] Failed to update derived settings: {e}",
                file=sys.stderr)

    def _try_import_yaml(self):
        """Try to import yaml with graceful fallback."""
        if yaml:
            return yaml
        print("[INFO] YAML not available, using fallback configuration")
        return None

    def initialize(self) -> bool:
        """Initialize core loader and essential services.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Check Python version compatibility
            if not self._check_python_version():
                return False

            # Load configuration
            self.config = self.load_config()

            # Initialize essential services
            self.services['config'] = self.config

            # Initialize plugin system
            plugin_manager = None
            if PluginManager:
                plugin_manager = PluginManager("nodupe")
                self.services['plugin_manager'] = plugin_manager
            else:
                print(
                    "[INFO] PluginManager not available, running without plugin system")
                self.services['plugin_manager'] = None

            # Load plugins if configured and plugin manager is available
            if (self.config.get('plugins', {}).get('auto_load', True) and
                    plugin_manager is not None):
                plugin_dirs = self.config.get(
                    'plugins', {}).get(
                    'directories', ['plugins'])

                # Pass configuration to plugin manager for loading order
                if hasattr(plugin_manager, 'set_config'):  # type: ignore[attr-defined]
                    plugin_manager.set_config(self.config)  # type: ignore[attr-defined]

                plugin_manager.load_plugins(plugin_dirs)  # type: ignore[attr-defined]

            return True

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[ERROR] Core initialization failed: {e}", file=sys.stderr)
            return False

    def _check_python_version(self) -> bool:
        """Check Python version compatibility.

        Returns:
            True if Python version is compatible, False otherwise
        """
        version_info = sys.version_info
        major = version_info.major
        minor = version_info.minor
        micro = version_info.micro

        # Require Python 3.9+
        if major < 3 or (major == 3 and minor < 9):
            print(
                f"[ERROR] NoDupeLabs requires Python 3.9+, "
                f"but found Python {major}.{minor}.{micro}",
                file=sys.stderr
            )
            return False

        print(f"[INFO] Using Python {major}.{minor}.{micro}")
        return True

    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the core application with minimal functionality.

        Args:
            args: Command line arguments

        Returns:
            Exit code (0 = success, non-zero = error)
        """
        # Initialize core
        if not self.initialize():
            return 1

        # Minimal CLI parsing
        parser = argparse.ArgumentParser(
            description="NoDupeLabs Core Loader",
            add_help=True
        )

        # Global debug flag
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug logging')

        # Performance tuning options
        parser.add_argument(
            '--cores',
            type=int,
            help='Override detected CPU cores')
        parser.add_argument(
            '--threads',
            type=int,
            help='Override detected CPU threads')
        parser.add_argument(
            '--max-workers',
            type=int,
            help='Override maximum worker count')
        parser.add_argument(
            '--batch-size',
            type=int,
            help='Override batch processing size')

        # Core commands (minimal functionality)
        subparsers = parser.add_subparsers(
            dest='command', help='Available commands')

        # Version command
        version_parser = subparsers.add_parser(
            'version', help='Show version information')
        version_parser.set_defaults(func=self._cmd_version)

        # Plugin command
        plugin_parser = subparsers.add_parser(
            'plugin', help='Plugin management')
        plugin_parser.add_argument(
            '--list',
            action='store_true',
            help='List loaded plugins')
        plugin_parser.set_defaults(func=self._cmd_plugin)

        # Load plugins and register their commands
        self._load_plugin_commands(subparsers)

        # Parse arguments
        try:
            parsed_args = parser.parse_args(args)
        except SystemExit:
            return 0  # Help was shown

        # Apply custom performance settings if provided
        self._apply_custom_performance_settings(parsed_args)

        # Check debug flag and setup logging
        if parsed_args.debug:
            self._setup_debug_logging()

        # Execute command
        if hasattr(parsed_args, 'func'):
            try:
                return parsed_args.func(parsed_args)
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"[ERROR] Command failed: {e}", file=sys.stderr)
                return 1

        # No command specified - show help
        parser.print_help()
        return 0

    def _cmd_version(self, args: argparse.Namespace) -> int:
        """Handle version command."""
        print("NoDupeLabs Core Loader v1.0.0")
        print("Minimal core with hard isolation")
        return 0

    def _cmd_plugin(self, args: argparse.Namespace) -> int:
        """Handle plugin command."""
        plugin_manager = self.services.get('plugin_manager')  # type: ignore[assignment]
        if not plugin_manager:
            print("[ERROR] Plugin manager not initialized", file=sys.stderr)
            return 1

        if args.list:
            plugins = plugin_manager.list_plugins()  # type: ignore[attr-defined]
            print(f"Loaded plugins: {len(plugins)}")
            for plugin in plugins:
                print(f"  - {plugin}")
            return 0

        return 0

    def _setup_debug_logging(self) -> None:
        """Setup debug logging to file."""
        try:
            import logging
            import datetime

            # Create logs directory if it doesn't exist
            logs_dir = Path('logs')
            logs_dir.mkdir(exist_ok=True)

            # Create log file with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = logs_dir / f"nodupe_debug_{timestamp}.log"

            # Configure logging
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )

            print(f"[DEBUG] Debug logging enabled. Writing to: {log_file}")

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(
                f"[WARN] Failed to setup debug logging: {e}",
                file=sys.stderr)

    def _load_plugin_commands(self, subparsers: Any) -> None:
        """Load and register plugin commands.

        Args:
            subparsers: Argument parser subparsers
        """
        plugin_manager = self.services.get('plugin_manager')
        if not plugin_manager:
            return

        # Try to import and load plugins from the plugins directory
        try:
            plugins_dir = Path(__file__).parent.parent / 'plugins'
            if plugins_dir.exists():
                # Import each plugin module
                for plugin_file in plugins_dir.glob('*.py'):
                    if plugin_file.name.startswith('_'):
                        continue

                    # Construct module name and import
                    module_name = f"nodupe.plugins.{plugin_file.stem}"
                    try:
                        module = __import__(module_name, fromlist=[''])
                        # Check if module has register_commands method
                        if hasattr(module, 'register_plugin'):
                            plugin = module.register_plugin()
                            if hasattr(plugin, 'register_commands'):
                                plugin.register_commands(subparsers)
                                print(
                                    f"[INFO] Registered plugin commands: {plugin_file.stem}")
                    except Exception as e:
                        print(
                            f"[WARN] Failed to load plugin {plugin_file.name}: {e}",
                            file=sys.stderr)

        except Exception as e:
            print(f"[WARN] Failed to load plugins: {e}", file=sys.stderr)


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for NoDupeLabs core loader.

    Args:
        args: Optional command line arguments

    Returns:
        Exit code
    """
    try:
        loader = CoreLoader()
        return loader.run(args)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"[ERROR] Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
