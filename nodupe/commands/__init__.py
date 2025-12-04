# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Command implementations for the NoDupe CLI.

This package contains the implementation of individual CLI commands.
Each module corresponds to a subcommand (e.g., 'scan', 'plan', 'apply').
The commands are registered and dispatched by the main CLI entry point
in nodupe.cli.

Modules:
    - scan: File scanning and indexing
    - plan: Deduplication planning
    - apply: Plan execution
    - rollback: Operation reversal
    - verify: Checkpoint verification
    - init: Configuration initialization
    - mount: FUSE filesystem mounting
    - archive: Archive handling
    - similarity: Similarity search operations
"""

from typing import Callable, Dict

# Import all command functions
from .init import cmd_init
from .scan import cmd_scan, check_scan_requirements
from .plan import cmd_plan
from .apply import cmd_apply
from .rollback import cmd_rollback
from .verify import cmd_verify
from .mount import cmd_mount
from .archive import cmd_archive_list, cmd_archive_extract
from .similarity import (
    cmd_similarity_build,
    cmd_similarity_query,
    cmd_similarity_update
)

# Command registry mapping command names to their implementations
COMMANDS: Dict[str, Callable] = {
    "init": cmd_init,
    "scan": cmd_scan,
    "plan": cmd_plan,
    "apply": cmd_apply,
    "rollback": cmd_rollback,
    "verify": cmd_verify,
    "mount": cmd_mount,
    "archive:list": cmd_archive_list,
    "archive:extract": cmd_archive_extract,
    "similarity:build": cmd_similarity_build,
    "similarity:query": cmd_similarity_query,
    "similarity:update": cmd_similarity_update,
}

# Public API
__all__ = [
    # Command registry
    "COMMANDS",
    # Individual commands
    "cmd_init",
    "cmd_scan",
    "cmd_plan",
    "cmd_apply",
    "cmd_rollback",
    "cmd_verify",
    "cmd_mount",
    "cmd_archive_list",
    "cmd_archive_extract",
    "cmd_similarity_build",
    "cmd_similarity_query",
    "cmd_similarity_update",
    # Utilities
    "check_scan_requirements",
]
