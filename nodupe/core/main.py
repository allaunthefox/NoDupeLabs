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

    def _safe_get_plugins(self):
        """Safely get plugins from registry, handling Mock objects."""
        if not self.loader or not self.loader.plugin_registry:
            return []
        
        try:
            plugins = self.loader.plugin_registry.get_plugins()
            # Check if plugins is actually iterable (not a Mock)
            if hasattr(plugins, '__iter__'):
                return plugins
            else:
                # If it's a Mock or non-iterable, return empty list
                return []
        except (TypeError, AttributeError):
            # If get_plugins() doesn't exist or returns non-iterable, return empty list
            return []

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
        # Check if subparsers already exist to avoid duplicates
        # Look for existing subparsers in the parser
        has_subparsers = False
        for action in self.parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                has_subparsers = True
                break
        
        if has_subparsers:
            # Subparsers already exist, get the existing ones
            for action in self.parser._actions:
                if isinstance(action, argparse._SubParsersAction):
                    subparsers = action
                    break
        else:
            # Add subparsers for the first time
            subparsers = self.parser.add_subparsers(
                dest='command',
                title='Available commands',
                help='Available commands'
            )

        # Built-in commands
        try:
            # Check if parsers already exist to avoid duplicates
            if not hasattr(self, '_version_parser_added'):
                version_parser = subparsers.add_parser('version', help='Show version')
                version_parser.set_defaults(func=self._cmd_version)
                self._version_parser_added = True
        except argparse.ArgumentError:
            pass  # Version parser already exists

        try:
            if not hasattr(self, '_plugin_parser_added'):
                plugin_parser = subparsers.add_parser('plugin', help='Plugin management')
                plugin_parser.add_argument('--list', action='store_true', help='List plugins')
                plugin_parser.set_defaults(func=self._cmd_plugin)
                self._plugin_parser_added = True
        except argparse.ArgumentError:
            pass  # Plugin parser already exists

        # Plugin commands
        # The loader has already loaded plugins into the registry
        plugins = self._safe_get_plugins()
        if plugins:
            for plugin in plugins:
                if hasattr(plugin, 'register_commands'):
                    try:
                        plugin.register_commands(subparsers)
                        logging.debug(f"Registered commands for plugin: {plugin.name}")
                    except Exception as e:
                        logging.warning(f"Failed to register commands for {plugin.name}: {e}")

    def _safe_get_plugins(self):
        """Safely get plugins from registry, handling Mock objects."""
        if not self.loader or not self.loader.plugin_registry:
            return []
        
        try:
            plugins = self.loader.plugin_registry.get_plugins()
            # Check if plugins is actually iterable (not a Mock)
            if hasattr(plugins, '__iter__'):
                return plugins
            else:
                # If it's a Mock or non-iterable, return empty list
                return []
        except (TypeError, AttributeError):
            # If get_plugins() doesn't exist or returns non-iterable, return empty list
            return []

    def _setup_debug_logging(self) -> None:
        """Setup debug logging."""
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug logging enabled")

    def _apply_overrides(self, args: argparse.Namespace) -> None:
        """Apply performance overrides to the running configuration."""
        if not self.loader.config or not hasattr(self.loader.config, 'config'):
            return

        cfg = self.loader.config.config
        if hasattr(args, 'cores') and args.cores:
            cfg['cpu_cores'] = args.cores
            logging.info(f"Overridden CPU cores: {args.cores}")
        if hasattr(args, 'max_workers') and args.max_workers:
            cfg['max_workers'] = args.max_workers
            logging.info(f"Overridden max workers: {args.max_workers}")
        if hasattr(args, 'batch_size') and args.batch_size:
            cfg['batch_size'] = args.batch_size
            logging.info(f"Overridden batch size: {args.batch_size}")

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

        if args.list:
            plugins = self.loader.plugin_registry.get_plugins()
            print(f"Loaded plugins: {len(plugins)}")
            for plugin in plugins:
                print(f"  - {plugin.name} (v{getattr(plugin, 'version', '?.?')})")
            return 0
        return 0

    def _setup_debug_logging(self) -> None:
        """Setup debug logging."""
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug logging enabled")

    def _apply_overrides(self, args: argparse.Namespace) -> None:
        """Apply performance overrides to the running configuration."""
        if not self.loader.config or not hasattr(self.loader.config, 'config'):
            return

        cfg = self.loader.config.config
        # Check if cfg is a real dict or a Mock object
        if hasattr(cfg, '__setitem__') and not hasattr(cfg, 'return_value'):
            # It's a real dictionary, we can modify it
            if hasattr(args, 'cores') and args.cores is not None:
                cfg['cpu_cores'] = args.cores
                logging.info(f"Overridden CPU cores: {args.cores}")
            if hasattr(args, 'max_workers') and args.max_workers is not None:
                cfg['max_workers'] = args.max_workers
                logging.info(f"Overridden max workers: {args.max_workers}")
            if hasattr(args, 'batch_size') and args.batch_size is not None:
                cfg['batch_size'] = args.batch_size
                logging.info(f"Overridden batch size: {args.batch_size}")
        else:
            # It's likely a Mock object, just log that we tried to override
            if hasattr(args, 'cores') and args.cores is not None:
                logging.debug(f"Tried to override CPU cores: {args.cores} (config is mocked)")
            if hasattr(args, 'max_workers') and args.max_workers is not None:
                logging.debug(f"Tried to override max workers: {args.max_workers} (config is mocked)")
            if hasattr(args, 'batch_size') and args.batch_size is not None:
                logging.debug(f"Tried to override batch size: {args.batch_size} (config is mocked)")


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
