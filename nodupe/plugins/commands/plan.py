# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Plan plugin for NoDupeLabs.

This plugin bridges the gap between 'scan' and 'apply' by creating
an execution plan based on duplicate detection results.
"""

from nodupe.core.plugin_system.base import Plugin
from typing import Any, Dict
import argparse
import json

# Plugin manager is injected by the core system
PM = None


class PlanPlugin(Plugin):
    """Plan plugin implementation.

    Responsibilities:
    - Register with plugin manager
    - Provide plan functionality
    - Handle strategy selection
    """

    name = "plan"
    version = "1.0.0"
    dependencies = ["scan", "database"]

    def __init__(self):
        """Initialize plan plugin."""
        self.description = "Create execution plan from scan results"
        # Hook registration moved to initialize

    def initialize(self, container: Any) -> None:
        """Initialize the plugin."""
        # Retrieve PM from container if available
        # But global PM usage in this file is legacy.
        # Ideally we use container.get_service('plugin_manager')

    def shutdown(self) -> None:
        """Shutdown the plugin."""

    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities."""
        return {'commands': ['plan'], 'strategies': ['newest', 'oldest', 'interactive']}

    def _on_plan_start(self, **kwargs: Any) -> None:
        """Handle plan start event."""
        print(f"[PLUGIN] Planning started with strategy: {kwargs.get('strategy', 'unknown')}")

    def _on_plan_complete(self, **kwargs: Any) -> None:
        """Handle plan complete event."""
        print(f"[PLUGIN] Planning completed. Actions generated: {kwargs.get('action_count', 0)}")

    def register_commands(self, subparsers: Any) -> None:
        """Register plan command with argument parser.

        Args:
            subparsers: Argument parser subparsers
        """
        parser = subparsers.add_parser('plan', help='Create execution plan from scan results')
        parser.add_argument('--strategy', choices=['newest', 'oldest', 'interactive'],
                            default='newest', help='Strategy to select keeper file')
        parser.add_argument('--output', '-o', default='plan.json', help='Output plan file path')
        parser.set_defaults(func=self.execute_plan)

    def execute_plan(self, args: argparse.Namespace) -> int:
        """Execute plan command.

        Args:
            args: Parsed arguments

        Returns:
            Exit code
        """

        try:
            print(f"[PLUGIN] Executing plan with strategy: {args.strategy}")

            # 1. Get Services
            container = getattr(args, 'container', None)
            if not container:
                from nodupe.core.container import container as global_container
                container = global_container

            db = container.get_service('database')
            if not db:
                print("[ERROR] Database service not available")
                from nodupe.core.database.connection import DatabaseConnection
                db = DatabaseConnection.get_instance()

            from nodupe.core.database.files import FileRepository
            repo = FileRepository(db)
            files = repo.get_all_files()

            if not files:
                print("[PLUGIN] No files in database to plan.")
                return 0

            # 2. Group by Hash
            print(f"[PLUGIN] Grouping {len(files)} files by hash...")
            groups = {}
            for f in files:
                if not f.get('hash'):
                    continue
                if f['hash'] not in groups:
                    groups[f['hash']] = []
                groups[f['hash']].append(f)

            action_plan = []
            stats = {"total_groups": 0, "duplicates_found": 0, "reassigned": 0}

            # 3. Apply Strategy
            print(f"[PLUGIN] Applying strategy '{args.strategy}'...")
            for file_hash, group in groups.items():
                if len(group) < 2:
                    continue

                stats["total_groups"] += 1

                # Sort group based on strategy
                # The first item in sorted list will be the KEEPER (Original)
                if args.strategy == 'newest':
                    # Keep newest modified: Sort descending by mtime
                    group.sort(key=lambda x: x.get('modified_time', 0), reverse=True)
                elif args.strategy == 'oldest':
                    # Keep oldest modified: Sort ascending by mtime
                    group.sort(key=lambda x: x.get('modified_time', 0))
                else:
                    # Default/Interactive: Keep shortest path length (preferred usually)
                    group.sort(key=lambda x: len(x['path']))

                keeper = group[0]
                duplicates = group[1:]

                stats["duplicates_found"] += len(duplicates)

                # 4. Generate Actions & Update DB
                # Ensure keeper is NOT marked as duplicate
                if keeper.get('is_duplicate'):
                    repo.mark_as_original(keeper['id'])
                    stats["reassigned"] += 1

                action_plan.append({
                    "type": "KEEP",
                    "path": keeper['path'],
                    "reason": f"Selected by {args.strategy} strategy (id={keeper['id']})"
                })

                for dup in duplicates:
                    # Update DB to point to new keeper
                    repo.mark_as_duplicate(dup['id'], keeper['id'])

                    action_plan.append({
                        "type": "DELETE",  # Or implies 'process'
                        "path": dup['path'],
                        "duplicate_of": keeper['path'],
                        "reason": f"Duplicate of {keeper['path']}"
                    })

            # 5. Output JSON Plan
            plan_data = {
                "metadata": {
                    "strategy": args.strategy,
                    "version": "1.0",
                    "generated_at": "2025-12-14",
                    "stats": stats
                },
                "actions": action_plan
            }

            with open(args.output, 'w') as f:
                json.dump(plan_data, f, indent=2)

            print(f"[PLUGIN] Plan saved to {args.output}")
            print(
                f"[PLUGIN] Summary: {stats['duplicates_found']} duplicates identified in {stats['total_groups']} groups.")
            if stats['reassigned'] > 0:
                print(
                    f"[PLUGIN] Reassigned {stats['reassigned']} files as originals based on strategy.")

            self._on_plan_complete(action_count=len(action_plan))
            return 0

        except Exception as e:
            print(f"[PLUGIN ERROR] Plan failed: {e}")
            return 1


# Create plugin instance when module is loaded
plan_plugin = PlanPlugin()


def register_plugin():
    """Register plugin with core system."""
    return plan_plugin


# Export plugin interface
__all__ = ['plan_plugin', 'register_plugin']
