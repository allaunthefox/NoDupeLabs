# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""NoDupeLabs command-line interface.

This module provides the main entry point for the ``nodupe`` CLI.
It coordinates bootstrapping, argument parsing, and command dispatch
using focused classes for each concern.

Exit Codes:
    0: Success
    1: General error
    10: Startup linting failed
    130: Interrupted by user
"""
import sys
from pathlib import Path

# Inject vendor libs into sys.path for fallback
_VENDOR_LIBS = Path(__file__).parent / "vendor" / "libs"
if _VENDOR_LIBS.exists():
    sys.path.append(str(_VENDOR_LIBS))

from .config import load_config, get_available_presets  # noqa: E402
from .plugins import pm  # noqa: E402
from .commands import COMMANDS  # noqa: E402
from .commands import (  # noqa: F401, E402
    check_scan_requirements  # re-export for tests / external use
)
from .cli.bootstrapper import CLIBootstrapper  # noqa: E402
from .cli.parser import ArgumentBuilder  # noqa: E402
from .cli.router import CommandRouter  # noqa: E402

__version__ = "0.1.0"


def main(argv=None):
    """Entry point for the nodupe CLI."""
    # Bootstrap (deps + linting)
    bootstrapper = CLIBootstrapper()
    rc = bootstrapper.bootstrap()
    if rc != 0:
        return rc

    # Load configuration
    cfg = load_config()

    # Load plugins
    plugin_dirs = ["plugins"]
    if "plugins_dir" in cfg:
        plugin_dirs = list(dict.fromkeys(plugin_dirs + [cfg["plugins_dir"]]))

    pm.load_plugins(plugin_dirs)
    pm.emit("startup", cfg=cfg)

    # Build argument parser
    builder = ArgumentBuilder(
        prog="nodupe",
        version=__version__,
        presets=get_available_presets()
    )
    parser = builder.build(COMMANDS)

    # Parse arguments
    args = parser.parse_args(argv)

    # Dispatch command
    router = CommandRouter(plugin_manager=pm)
    return router.dispatch(args, cfg)


if __name__ == "__main__":
    sys.exit(main())
