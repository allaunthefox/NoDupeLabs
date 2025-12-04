# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""NoDupeLabs command-line interface.

This module provides the main entry point for the ``nodupe`` CLI.
It orchestrates configuration loading, plugin management, dependency
installation, and command dispatching.

Key Features:
    - Automatic dependency installation and graceful degradation
    - Plugin system with event hooks (startup, shutdown, etc.)
    - Startup/shutdown code linting for integrity checking
    - Command registration and argument parsing
    - Configuration management with preset support

Available Commands:
    - init: Initialize configuration with presets
    - scan: Scan directories and build file index
    - plan: Generate deduplication plan
    - apply: Execute deduplication plan with checkpointing
    - rollback: Undo previous apply operation
    - verify: Validate checkpoint against filesystem
    - mount: Mount database as FUSE filesystem (Linux only)
    - archive: Inspect and extract archive files
    - similarity: Build/query/update similarity indices

Architecture:
    The CLI uses a plugin-based architecture where plugins can register event
    handlers for lifecycle events (startup, shutdown, tool use). Commands are
    implemented in separate modules under nodupe.commands.

Exit Codes:
    0: Success
    1: General error
    10: Startup linting failed
    Other: Command-specific errors
"""

import argparse
import sys
import atexit
from pathlib import Path

# Inject vendor libs into sys.path for fallback
_VENDOR_LIBS = Path(__file__).parent / "vendor" / "libs"
if _VENDOR_LIBS.exists():
    sys.path.append(str(_VENDOR_LIBS))

from .bootstrap import lint_tree  # noqa: E402
from .deps import init_deps  # noqa: E402
from .config import load_config, get_available_presets  # noqa: E402
from .plugins import pm  # noqa: E402

# Import command registry and utilities
from .commands import COMMANDS  # noqa: E402
from .commands import (  # noqa: F401, E402
    check_scan_requirements  # re-export for tests / external use
)

__version__ = "0.1.0"


def main(argv=None):
    """Entry point for the nodupe CLI."""
    # Initialize dependency auto-installer
    init_deps(auto_install=True, silent=False)

    # Startup linting
    module_dir = Path(__file__).parent
    try:
        lint_tree(module_dir)
    except SyntaxError as e:
        print(f"[fatal] Startup linting failed: {e}", file=sys.stderr)
        return 10

    # Register shutdown linting
    def shutdown_lint():
        try:
            lint_tree(module_dir)
        except Exception as e:  # pylint: disable=broad-except
            print(f"[warn] Shutdown linting failed: {e}", file=sys.stderr)

    atexit.register(shutdown_lint)

    # Load configuration
    cfg = load_config()

    # Load plugins
    # We look in a local 'plugins' folder by default, or user configured path
    plugin_dirs = ["plugins"]
    if "plugins_dir" in cfg:
        # preserve order but avoid duplicates
        plugin_dirs = list(dict.fromkeys(plugin_dirs + [cfg["plugins_dir"]]))

    pm.load_plugins(plugin_dirs)
    pm.emit("startup", cfg=cfg)

    parser = argparse.ArgumentParser(prog="nodupe")
    parser.add_argument(
        '--version', action='version', version=f'%(prog)s {__version__}'
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Init
    p_init = sub.add_parser("init", help="Initialize configuration")
    p_init.add_argument(
        "--preset", choices=get_available_presets(), default="default",
        help="Configuration preset"
    )
    p_init.add_argument(
        "--force", action="store_true", help="Overwrite existing config"
    )
    p_init.set_defaults(_run=COMMANDS["init"])

    # Scan
    p_scan = sub.add_parser("scan")
    p_scan.add_argument("--root", action="append", required=True)
    p_scan.add_argument(
        "--progress", choices=("auto", "quiet", "interactive"), default=None,
        help="Control ffmpeg/test progress UI (auto|quiet|interactive). "
             "Overrides NO_DUPE_PROGRESS"
    )
    p_scan.set_defaults(_run=COMMANDS["scan"])

    # Plan
    p_plan = sub.add_parser("plan")
    p_plan.add_argument("--out", required=True)
    p_plan.set_defaults(_run=COMMANDS["plan"])

    # Apply
    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--plan", required=True)
    p_apply.add_argument("--checkpoint", required=True)
    p_apply.add_argument("--force", action="store_true")
    p_apply.set_defaults(_run=COMMANDS["apply"])

    # Rollback
    p_rb = sub.add_parser("rollback")
    p_rb.add_argument("--checkpoint", required=True)
    p_rb.set_defaults(_run=COMMANDS["rollback"])

    # Verify
    p_vf = sub.add_parser("verify")
    p_vf.add_argument("--checkpoint", required=True)
    p_vf.set_defaults(_run=COMMANDS["verify"])

    # Mount
    p_mnt = sub.add_parser("mount")
    p_mnt.add_argument("mountpoint", help="Directory to mount the filesystem")
    p_mnt.set_defaults(_run=COMMANDS["mount"])

    # Archive
    p_arch = sub.add_parser("archive")
    p_arch_sub = p_arch.add_subparsers(dest="archive_cmd", required=True)

    p_l = p_arch_sub.add_parser("list")
    p_l.add_argument("file")
    p_l.set_defaults(_run=COMMANDS["archive:list"])

    p_e = p_arch_sub.add_parser("extract")
    p_e.add_argument("file")
    p_e.add_argument("--dest", required=True)
    p_e.set_defaults(_run=COMMANDS["archive:extract"])

    # Similarity
    p_sim = sub.add_parser("similarity")
    p_sim_sub = p_sim.add_subparsers(dest="sim_cmd", required=True)

    p_sim_build = p_sim_sub.add_parser("build")
    p_sim_build.add_argument("--dim", type=int, default=16)
    p_sim_build.add_argument(
        "--out",
        help="Optional output index file "
             "(.index/.faiss, .npz, .json, or .jsonl)"
    )
    p_sim_build.set_defaults(_run=COMMANDS["similarity:build"])

    p_sim_query = p_sim_sub.add_parser("query")
    p_sim_query.add_argument("file")
    p_sim_query.add_argument("--dim", type=int, default=16)
    p_sim_query.add_argument("-k", type=int, default=5)
    p_sim_query.add_argument(
        "--index-file", help="Optional index file to load for faster queries"
    )
    p_sim_query.set_defaults(_run=COMMANDS["similarity:query"])

    p_sim_update = p_sim_sub.add_parser("update")
    p_sim_update.add_argument(
        "--index-file", required=True,
        help="Index file to update (.index/.faiss, .npz, .json, or .jsonl)"
    )
    p_sim_update.add_argument(
        "--rebuild", action="store_true",
        help="Rebuild index from DB (remove missing / stale entries)"
    )
    p_sim_update.set_defaults(_run=COMMANDS["similarity:update"])

    args = parser.parse_args(argv)

    try:
        rc = args._run(args, cfg)  # pylint: disable=protected-access
    except KeyboardInterrupt:
        print("\n[fatal] Interrupted by user", file=sys.stderr)
        pm.emit("shutdown", reason="interrupt")
        return 130
    except Exception as e:  # pylint: disable=broad-except
        print(f"[fatal] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        pm.emit("shutdown", reason="error", error=e)
        return 10

    pm.emit("shutdown", reason="success")
    return rc


if __name__ == "__main__":
    sys.exit(main())
