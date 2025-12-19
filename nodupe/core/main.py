# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun
# pylint: disable=broad-exception-caught,unused-argument

"""NoDupeLabs Entry Point - CLI using Enhanced Core Loader.

This module provides the CLI entry point, delegating core bootstrapping
and plugin loading to the enhanced `nodupe.core.loader`.

Key Features:
    - CLI argument parsing
    - Delegation to enhanced Core Loader
    - Plugin command dispatch
    - Graceful error handling
"""

import sys
import argparse
import logging
import time
from typing import Optional, List, Any

# Import the enhanced core loader bootstrap
from nodupe.core.loader import bootstrap


class CLIHandler:
    """Handles CLI argument parsing and command dispatch."""

    def __init__(self, loader: Any) -> None:
        """Initialize CLI handler with bootstrapped loader.

        Args:
            loader: Initialized CoreLoader instance
        """
        self.loader = loader
        self.parser = self._create_parser()
        self._register_commands()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser.

        Returns:
            Configured ArgumentParser
        """
        parser = argparse.ArgumentParser(
            description="NoDupeLabs CLI",
            add_help=True
        )

        # Global flags
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug logging'
        )

        # Performance tuning overrides (passed to config if needed)
        parser.add_argument('--cores', type=int, help='Override detected CPU cores')
        parser.add_argument('--threads', type=int, help='Override detected CPU threads')
        parser.add_argument('--max-workers', type=int, help='Override max workers')
        parser.add_argument('--batch-size', type=int, help='Override batch size')

        return parser

    def _register_commands(self) -> None:
        """Register commands from plugins."""
        subparsers = self.parser.add_subparsers(
            dest='command',
            help='Available commands'
        )

        # Built-in commands
        version_parser = subparsers.add_parser('version', help='Show version')
        version_parser.set_defaults(func=self._cmd_version)

        # Plugin command with subcommands
        plugin_parser = subparsers.add_parser('plugin', help='Plugin management')
        plugin_subparsers = plugin_parser.add_subparsers(dest='subcommand', help='Plugin subcommands')

        # Plugin subcommands
        plugin_install = plugin_subparsers.add_parser('install', help='Install a plugin')
        plugin_install.add_argument('plugin_name', help='Plugin name or UUID to install')

        plugin_enable = plugin_subparsers.add_parser('enable', help='Enable a plugin')
        plugin_enable.add_argument('plugin_name', help='Plugin name or UUID to enable')

        plugin_disable = plugin_subparsers.add_parser('disable', help='Disable a plugin')
        plugin_disable.add_argument('plugin_name', help='Plugin name or UUID to disable')

        plugin_list = plugin_subparsers.add_parser('list', help='List installed plugins')

        # Default to list if no subcommand specified
        plugin_parser.set_defaults(func=self._cmd_plugin, subcommand='list')

        # Plugin commands
        # The loader has already loaded plugins into the registry
        if self.loader.plugin_registry:
            plugins = self.loader.plugin_registry.get_plugins()
            for plugin in plugins:
                if hasattr(plugin, 'register_commands'):
                    try:
                        plugin.register_commands(subparsers)
                        logging.debug(f"Registered commands for plugin: {plugin.name}")
                    except Exception as e:
                        logging.warning(f"Failed to register commands for {plugin.name}: {e}")

    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI.

        Args:
            args: Command line arguments

        Returns:
            Exit code
        """
        parsed_args = self.parser.parse_args(args)

        # Handle debug flag
        if parsed_args.debug:
            self._setup_debug_logging()

        # Handle performance overrides
        self._apply_overrides(parsed_args)

        if hasattr(parsed_args, 'func'):
            try:
                # Inject services into args namespace if needed by commands
                parsed_args.container = self.loader.container
                return parsed_args.func(parsed_args)
            except Exception as e:
                print(f"[ERROR] Command failed: {e}", file=sys.stderr)
                if parsed_args.debug:
                    import traceback
                    traceback.print_exc()
                return 1

        self.parser.print_help()
        return 0

    def _cmd_version(self, args: argparse.Namespace) -> int:
        """Handle version command."""
        print("NoDupeLabs CLI v1.0.0")
        print("Powered by Enhanced Core Loader")

        # Show system info from loader config if available
        if self.loader.config and hasattr(self.loader.config, 'config'):
            cfg = self.loader.config.config
            print(f"Platform: {cfg.get('drive_type', 'unknown')} | "
                  f"Cores: {cfg.get('cpu_cores', '?')} | "
                  f"RAM: {cfg.get('ram_gb', '?')}GB")
        return 0

    def _cmd_plugin(self, args: argparse.Namespace) -> int:
        """Handle plugin command."""
        if not self.loader.plugin_registry:
            print("Plugin system not active.")
            return 1

        # Get database connection from container
        db = self.loader.container.get_service('database')
        if not db:
            print("Database not available.")
            return 1

        # Handle subcommands
        if hasattr(args, 'subcommand'):
            subcommand = args.subcommand
        else:
            # Default to list if no subcommand specified
            subcommand = 'list'

        if subcommand == 'list':
            return self._cmd_plugin_list(db)
        elif subcommand == 'install':
            if not hasattr(args, 'plugin_name') or not args.plugin_name:
                print("Error: plugin install requires plugin name or UUID")
                return 1
            return self._cmd_plugin_install(db, args.plugin_name)
        elif subcommand == 'enable':
            if not hasattr(args, 'plugin_name') or not args.plugin_name:
                print("Error: plugin enable requires plugin name or UUID")
                return 1
            return self._cmd_plugin_enable(db, args.plugin_name)
        elif subcommand == 'disable':
            if not hasattr(args, 'plugin_name') or not args.plugin_name:
                print("Error: plugin disable requires plugin name or UUID")
                return 1
            return self._cmd_plugin_disable(db, args.plugin_name)
        else:
            print(f"Unknown plugin command: {subcommand}")
            return 1

    def _cmd_plugin_list(self, db) -> int:
        """List all plugins."""
        try:
            plugins = self.loader.plugin_registry.get_plugins()
            print(f"Loaded plugins: {len(plugins)}")
            for plugin in plugins:
                status = "enabled" if getattr(plugin, 'enabled', True) else "disabled"
                print(f"  - {plugin.name} (v{getattr(plugin, 'version', '?.?')}) [{status}]")
            return 0
        except Exception as e:
            print(f"Error listing plugins: {e}")
            return 1

    def _cmd_plugin_install(self, db, plugin_identifier: str) -> int:
        """Install a plugin by name or UUID."""
        try:
            # Get the actual SQLite connection
            connection = db.get_connection()
            cursor = connection.cursor()

            # Check if plugin already exists in database
            cursor.execute(
                "SELECT id, name, version, enabled FROM plugins WHERE name = ? OR id = ?",
                (plugin_identifier, plugin_identifier)
            )
            existing = cursor.fetchone()

            if existing:
                plugin_id, name, version, enabled = existing
                status = "enabled" if enabled else "disabled"
                print(f"Plugin '{name}' (ID: {plugin_id}) already installed (v{version}) [{status}]")
                return 0

            # Check if plugin exists in registry
            plugins = self.loader.plugin_registry.get_plugins()
            target_plugin = None
            for plugin in plugins:
                if plugin.name == plugin_identifier or str(getattr(plugin, 'id', '')) == plugin_identifier:
                    target_plugin = plugin
                    break

            if not target_plugin:
                print(f"Plugin '{plugin_identifier}' not found in registry")
                return 1

            # Install plugin
            plugin_id = self._install_plugin_to_db(db, target_plugin)
            print(f"Plugin '{target_plugin.name}' installed successfully (ID: {plugin_id})")
            return 0

        except Exception as e:
            print(f"Error installing plugin: {e}")
            return 1

    def _cmd_plugin_enable(self, db, plugin_identifier: str) -> int:
        """Enable a plugin by name or UUID."""
        try:
            plugin_id = self._resolve_plugin_identifier(db, plugin_identifier)
            if not plugin_id:
                print(f"Plugin '{plugin_identifier}' not found")
                return 1

            # Get the actual SQLite connection
            connection = db.get_connection()
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE plugins SET enabled = 1, updated_at = ? WHERE id = ?",
                (int(time.time()), plugin_id)
            )
            connection.commit()

            # Get plugin name for display
            cursor.execute("SELECT name FROM plugins WHERE id = ?", (plugin_id,))
            name = cursor.fetchone()[0]
            print(f"Plugin '{name}' enabled successfully")
            return 0

        except Exception as e:
            print(f"Error enabling plugin: {e}")
            return 1

    def _cmd_plugin_disable(self, db, plugin_identifier: str) -> int:
        """Disable a plugin by name or UUID."""
        try:
            plugin_id = self._resolve_plugin_identifier(db, plugin_identifier)
            if not plugin_id:
                print(f"Plugin '{plugin_identifier}' not found")
                return 1

            # Get the actual SQLite connection
            connection = db.get_connection()
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE plugins SET enabled = 0, updated_at = ? WHERE id = ?",
                (int(time.time()), plugin_id)
            )
            connection.commit()

            # Get plugin name for display
            cursor.execute("SELECT name FROM plugins WHERE id = ?", (plugin_id,))
            name = cursor.fetchone()[0]
            print(f"Plugin '{name}' disabled successfully")
            return 0

        except Exception as e:
            print(f"Error disabling plugin: {e}")
            return 1

    def _resolve_plugin_identifier(self, db, identifier: str) -> Optional[int]:
        """Resolve plugin identifier to database ID."""
        # Get the actual SQLite connection
        connection = db.get_connection()
        cursor = connection.cursor()

        # Try as UUID (ID)
        try:
            plugin_id = int(identifier)
            cursor.execute("SELECT id FROM plugins WHERE id = ?", (plugin_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
        except ValueError:
            pass

        # Try as name
        cursor.execute("SELECT id FROM plugins WHERE name = ?", (identifier,))
        result = cursor.fetchone()
        if result:
            return result[0]

        return None

    def _install_plugin_to_db(self, db, plugin) -> int:
        """Install plugin to database."""
        # Get the actual SQLite connection
        connection = db.get_connection()
        cursor = connection.cursor()
        current_time = int(time.time())

        cursor.execute(
            "INSERT INTO plugins (name, version, type, status, enabled, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                plugin.name,
                getattr(plugin, 'version', '1.0.0'),
                getattr(plugin, 'type', 'unknown'),
                'installed',
                True,
                current_time,
                current_time
            )
        )
        connection.commit()
        return cursor.lastrowid

    def _setup_debug_logging(self) -> None:
        """Setup debug logging."""
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug logging enabled")

    def _apply_overrides(self, args: argparse.Namespace) -> None:
        """Apply performance overrides to the running configuration."""
        if not self.loader.config or not hasattr(self.loader.config, 'config'):
            return

        cfg = self.loader.config.config
        if args.cores:
            cfg['cpu_cores'] = args.cores
            logging.info(f"Overridden CPU cores: {args.cores}")
        if args.max_workers:
            cfg['max_workers'] = args.max_workers
            logging.info(f"Overridden max workers: {args.max_workers}")
        if args.batch_size:
            cfg['batch_size'] = args.batch_size
            logging.info(f"Overridden batch size: {args.batch_size}")


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point."""
    try:
        # 1. Bootstrap the system using enhanced loader
        loader = bootstrap()

        # 2. Run CLI
        cli = CLIHandler(loader)
        return cli.run(args)

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"[ERROR] Fatal startup error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
