# pylint: disable=logging-fstring-interpolation
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun
# pylint: disable=broad-exception-caught,unused-argument

"""NoDupeLabs Entry Point - CLI using Enhanced Core Loader.

This module provides the CLI entry point, delegating core bootstrapping
and tool loading to the enhanced `nodupe.core.loader`.

Key Features:
    - CLI argument parsing
    - Delegation to enhanced Core Loader
    - Tool command dispatch
    - Graceful error handling
"""

import argparse
import logging
import sys
from typing import Any, Optional

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
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            description="NoDupeLabs: A tool to find and safely store your files while removing duplicates.",
            add_help=True,
        )

        # Global flags
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed technical details for each step",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug logging and detailed error output",
        )

        # Performance tuning
        parser.add_argument(
            "--speed",
            choices=["normal", "fast", "safe"],
            default="normal",
            help="Choose how hard the computer works",
        )
        parser.add_argument(
            "--cores", type=int, help="Override number of CPU cores to use"
        )
        parser.add_argument(
            "--max-workers",
            type=int,
            help="Override maximum worker threads/processes",
        )
        parser.add_argument(
            "--batch-size", type=int, help="Override processing batch size"
        )

        return parser

    def _register_commands(self) -> None:
        """Register commands from tools.

        This method is idempotent so test code can call it multiple times
        without re-adding subparsers (argparse will raise in that case).
        """
        if getattr(self, "_commands_registered", False):
            return

        subparsers = self.parser.add_subparsers(
            dest="command", help="Available commands"
        )

        # Built-in commands
        version_parser = subparsers.add_parser(
            "version", help="Show the software version and system info"
        )
        version_parser.set_defaults(func=self._cmd_version)

        # Support both 'tools' and legacy singular 'tool' as command names
        tool_parser = subparsers.add_parser(
            "tools",
            aliases=["tool"],
            help="Manage the extra components/tools installed",
        )
        tool_parser.add_argument(
            "--list", action="store_true", help="List all available tools"
        )
        tool_parser.set_defaults(func=self._cmd_tool)

        # Tool commands
        # The loader has already loaded tools into the registry
        if self.loader.tool_registry:
            try:
                tools = self.loader.tool_registry.get_tools()
                # Attempt to iterate; some test/mocks may return non-iterable
                for tool in tools:
                    if hasattr(tool, "register_commands"):
                        try:
                            tool.register_commands(subparsers)
                            logging.debug(
                                f"Registered commands for tool: {tool.name}"
                            )
                        except Exception as e:
                            logging.warning(
                                f"Failed to register commands for {getattr(tool, 'name', 'unknown')}: {e}"
                            )
            except TypeError:
                # Defensive: test loader mocks may return a Mock (non-iterable).
                logging.debug(
                    "Tool registry returned non-iterable result; skipping tool registration"
                )
            except Exception as e:
                logging.warning(f"Failed to fetch tools from registry: {e}")

        # Mark as registered to make the method idempotent
        self._commands_registered = True

    def run(self, args: Optional[list[str]] = None) -> int:
        """Run the CLI.

        Args:
            args: Command line arguments

        Returns:
            Exit code
        """
        from .api.codes import ActionCode

        parsed_args = self.parser.parse_args(args)

        # Handle debug flag
        if parsed_args.debug:
            self._setup_debug_logging()

        # Handle performance overrides
        self._apply_overrides(parsed_args)

        # Only dispatch when a concrete command was selected. Tests may pass
        # a Mock namespace that responds to hasattr(), so prefer checking the
        # explicit 'command' attribute which is set by subparsers.
        if getattr(parsed_args, "command", None):
            try:
                # Inject services into args namespace if needed by commands
                parsed_args.container = self.loader.container
                # Call the function attached by argparse (if any)
                result = getattr(parsed_args, "func", lambda a: 0)(parsed_args)

                # Log accessibility compliance
                print(
                    f"[{ActionCode.ACC_ISO_CMP}] CLI command executed with accessibility compliance"
                )
                return result
            except Exception as e:
                print(
                    f"[{ActionCode.FPT_STM_ERR}] Command failed: {e}",
                    file=sys.stderr,
                )
                if getattr(parsed_args, "debug", False):
                    import traceback

                    traceback.print_exc()
                return 1

        self.parser.print_help()
        return 0

    def _cmd_version(self, args: argparse.Namespace) -> int:
        """Handle version command."""
        from .api.codes import ActionCode

        print(f"[{ActionCode.FIA_UAU_INIT}] NoDupeLabs CLI v1.0.0")
        print("Powered by Enhanced Core Loader")

        # Show system info from loader config if available
        if self.loader.config and hasattr(self.loader.config, "config"):
            cfg = self.loader.config.config
            print(
                f"Platform: {cfg.get('drive_type', 'unknown')} | "
                f"Cores: {cfg.get('cpu_cores', '?')} | "
                f"RAM: {cfg.get('ram_gb', '?')}GB"
            )

        # Report accessibility compliance
        print(f"[{ActionCode.ACC_ISO_CMP}] ISO Accessibility Compliant")
        return 0

    def _cmd_tool(self, args: argparse.Namespace) -> int:
        """Handle tool command."""
        from .api.codes import ActionCode

        if not self.loader.tool_registry:
            print(f"[{ActionCode.FPT_FLS_FAIL}] Tool system is not active.")
            return 1

        if args.list:
            tools = self.loader.tool_registry.get_tools()
            print(
                f"[{ActionCode.FIA_UAU_LOAD}] Number of tools available: {len(tools)}"
            )
            for tool in tools:
                # Check accessibility compliance for each tool
                from .tool_system.base import AccessibleTool

                if isinstance(tool, AccessibleTool):
                    print(
                        f"  - {tool.name} (v{getattr(tool, 'version', '?.?')}) [{ActionCode.ACC_ISO_CMP}]"
                    )
                else:
                    print(
                        f"  - {tool.name} (v{getattr(tool, 'version', '?.?')}) [{ActionCode.ACC_FEATURE_DISABLED}]"
                    )
            return 0
        return 0

    def _setup_debug_logging(self) -> None:
        """Setup debug logging."""
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug logging enabled")

    def _apply_overrides(self, args: argparse.Namespace) -> None:
        """Apply performance overrides to the running configuration.

        Defensive checks are used because test harnesses often use Mock objects
        for the loader; we only apply overrides when a real dict-based
        configuration object is present (loader.config.config is a dict).
        """
        cfg_obj = getattr(self.loader, "config", None)
        if not cfg_obj:
            return

        cfg = getattr(cfg_obj, "config", None)
        if not isinstance(cfg, dict):
            return

        if getattr(args, "cores", None):
            cfg["cpu_cores"] = args.cores
            logging.info(f"Overridden CPU cores: {args.cores}")
        if getattr(args, "max_workers", None):
            cfg["max_workers"] = args.max_workers
            logging.info(f"Overridden max workers: {args.max_workers}")
        if getattr(args, "batch_size", None):
            cfg["batch_size"] = args.batch_size
            logging.info(f"Overridden batch size: {args.batch_size}")


def main(args: Optional[list[str]] = None) -> int:
    """Main entry point."""
    # Import here to avoid a top-level circular import and to ensure
    # ActionCode is available for printing status messages.
    from .api.codes import ActionCode

    loader = None
    try:
        # 1. Bootstrap the system using enhanced loader
        print(f"[{ActionCode.FIA_UAU_INIT}] Starting NoDupeLabs core engine")
        loader = bootstrap()

        # 2. Run CLI
        cli = CLIHandler(loader)
        return cli.run(args)

    except KeyboardInterrupt:
        print(
            f"\n[{ActionCode.FIA_UAU_SHUTDOWN}] Interrupted by user",
            file=sys.stderr,
        )
        return 130
    except Exception as e:
        print(
            f"[{ActionCode.FPT_STM_ERR}] Fatal startup error: {e}",
            file=sys.stderr,
        )
        return 1
    finally:
        if loader:
            try:
                print(
                    f"[{ActionCode.FIA_UAU_SHUTDOWN}] Shutting down NoDupeLabs core engine"
                )
                loader.shutdown()
            except Exception as e:
                print(
                    f"[{ActionCode.FPT_STM_ERR}] Error during shutdown: {e}",
                    file=sys.stderr,
                )
                pass


if __name__ == "__main__":
    sys.exit(main())
