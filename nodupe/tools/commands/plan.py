# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Plan tool for NoDupeLabs.

This tool bridges the gap between 'scan' and 'apply' by creating
an execution plan based on duplicate detection results.
"""

from nodupe.core.tool_system.base import Tool
from typing import Any, Dict
import argparse
import json

# Tool manager is injected by the core system
PM = None


class PlanTool(Tool):
    """Plan tool implementation.

    Responsibilities:
    - Register with tool manager
    - Provide plan functionality
    - Handle strategy selection
    """

    name = "plan"
    version = "1.0.0"
    dependencies = ["scan", "database"]

    def __init__(self):
        """Initialize plan tool."""
        self.description = "Create execution plan from scan results"
        # Hook registration moved to initialize

    def initialize(self, container: Any) -> None:
        """Initialize the tool."""
        # Retrieve PM from container if available
        # But global PM usage in this file is legacy.
        # Ideally we use container.get_service('tool_manager')

    def shutdown(self) -> None:
        """Shutdown the tool."""

    def get_capabilities(self) -> Dict[str, Any]:
        """Get tool capabilities."""
        return {'commands': ['plan'], 'strategies': ['newest', 'oldest', 'interactive']}

    @property
    def api_methods(self) -> Dict[str, Any]:
        """Programmatic API methods exposed by this tool."""
        return {'execute_plan': self.execute_plan}

    def describe_usage(self) -> str:
        """Human readable usage description for the tool."""
        return "Create an execution plan from duplicate detection results."

    def run_standalone(self, args: list) -> int:
        """Run the command as a standalone CLI entry point."""
        parser = argparse.ArgumentParser(description=self.describe_usage())
        parser.add_argument('--strategy', choices=['newest', 'oldest', 'interactive'], default='newest')
        parser.add_argument('--output', '-o', default='plan.json')
        parsed = parser.parse_args(args)
        # Provide a minimal namespace compatible with execute_plan
        ns = argparse.Namespace(strategy=parsed.strategy, output=parsed.output, container=None)
        return self.execute_plan(ns)

    def _on_plan_start(self, **kwargs: Any) -> None:
        """Handle plan start event."""
        print(f"[TOOL] Planning started with strategy: {kwargs.get('strategy', 'unknown')}")

    def _on_plan_complete(self, **kwargs: Any) -> None:
        """Handle plan complete event."""
        print(f"[TOOL] Planning completed. Actions generated: {kwargs.get('action_count', 0)}")

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
            print(f"[TOOL] Executing plan with strategy: {args.strategy}")

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

            # Import the concrete FileRepository implementation from tools
            from nodupe.tools.databases.files import FileRepository
            repo = FileRepository(db)

            # Stream duplicate groups from the database (avoid full table load)
            duplicate_hashes = repo.get_duplicate_hashes()
            if not duplicate_hashes:
                print("[TOOL] No duplicate groups found in database to plan.")
                return 0

            action_plan = []
            stats = {"total_groups": 0, "duplicates_found": 0, "reassigned": 0}

            # 3. Apply Strategy (operate per-group, DB-side)
            print(f"[TOOL] Applying strategy '{args.strategy}' on {len(duplicate_hashes)} duplicate hashes...")
            for h in duplicate_hashes:
                group = repo.find_duplicates_by_hash(h)
                if len(group) < 2:
                    continue

                stats["total_groups"] += 1

                # Sort group based on strategy (same logic as before)
                if args.strategy == 'newest':
                    group.sort(key=lambda x: x.get('modified_time', 0), reverse=True)
                elif args.strategy == 'oldest':
                    group.sort(key=lambda x: x.get('modified_time', 0))
                else:
                    group.sort(key=lambda x: len(x['path']))

                keeper = group[0]
                duplicates = group[1:]

                stats["duplicates_found"] += len(duplicates)

                # Ensure keeper is NOT marked as duplicate
                if keeper.get('is_duplicate'):
                    repo.mark_as_original(keeper['id'])
                    stats["reassigned"] += 1

                action_plan.append({
                    "type": "KEEP",
                    "path": keeper['path'],
                    "reason": f"Selected by {args.strategy} strategy (id={keeper['id']})"
                })

                # Batch update duplicates to point at keeper
                dup_ids = [d['id'] for d in duplicates]
                updated = repo.batch_mark_as_duplicate(dup_ids, keeper['id'])

                for dup in duplicates:
                    action_plan.append({
                        "type": "DELETE",
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

            print(f"[TOOL] Plan saved to {args.output}")
            print(
                f"[TOOL] Summary: {stats['duplicates_found']} duplicates identified in {stats['total_groups']} groups.")
            if stats['reassigned'] > 0:
                print(
                    f"[TOOL] Reassigned {stats['reassigned']} files as originals based on strategy.")

            self._on_plan_complete(action_count=len(action_plan))
            return 0

        except Exception as e:
            print(f"[TOOL ERROR] Plan failed: {e}")
            return 1


# Create tool instance when module is loaded
plan_tool = PlanTool()


def register_tool():
    """Register tool with core system."""
    return plan_tool


# Export tool interface
__all__ = ['plan_tool', 'register_tool']
