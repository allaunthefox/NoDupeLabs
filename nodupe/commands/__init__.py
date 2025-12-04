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
