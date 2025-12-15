# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Similarity plugin for NoDupeLabs.

This plugin provides the similarity search functionality as a plugin that can be
loaded by the core system. It demonstrates how to convert existing
modules to plugins.

Key Features:
    - Similarity search
    - Multiple metrics
    - Result formatting
    - Plugin integration

Dependencies:
    - Core modules
"""

import argparse
from typing import Any, Dict

# Plugin manager is injected by the core system
PM: Any = None


from nodupe.core.plugin_system.base import Plugin
from nodupe.core.container import container as global_container

class SimilarityCommandPlugin(Plugin):
    """Similarity command plugin implementation."""

    name = "similarity_command"
    version = "1.0.0"
    dependencies = ["similarity_backend"]

    def __init__(self):
        """Initialize similarity plugin."""
        self.description = "Find similar files using various metrics"
        # Hook registration moved to initialize

    def initialize(self, container: Any) -> None:
        """Initialize the plugin."""
        # Retrieve PM from container if available
        pass

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        pass

    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities."""
        return {'commands': ['similarity']}

    def _on_similarity_start(self, **kwargs: Any) -> None:
        """Handle similarity start event."""
        print(f"[PLUGIN] Similarity search started: {kwargs.get('metric', 'unknown')}")

    def _on_similarity_complete(self, **kwargs: Any) -> None:
        """Handle similarity complete event."""
        print(f"[PLUGIN] Similarity search completed: {kwargs.get('pairs_found', 0)} similar pairs found")

    def register_commands(self, subparsers: Any) -> None:
        """Register similarity command with argument parser."""
        similarity_parser = subparsers.add_parser(
            'similarity', help='Find similar files')
        similarity_parser.add_argument(
            '--metric',
            choices=['name', 'size', 'hash', 'content', 'vector'],
            default='name',
            help='Similarity metric'
        )
        similarity_parser.add_argument(
            '--threshold',
            type=float,
            default=0.8,
            help='Similarity threshold'
        )
        similarity_parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum results per file'
        )
        similarity_parser.add_argument(
            '--output',
            choices=['text', 'json', 'csv'],
            default='text',
            help='Output format'
        )
        similarity_parser.set_defaults(func=self.execute_similarity)

    def execute_similarity(self, args: argparse.Namespace) -> int:
        """Execute similarity command."""
        try:
            print(f"[PLUGIN] Executing similarity command: {args.metric} metric")
            
            # 1. Get services
            container = getattr(args, 'container', None)
            if not container:
                # Fallback to global if arg injection fail
                from nodupe.core.container import container as global_container
                container = global_container
            
            db = container.get_service('database')
            if not db:
                 print("[ERROR] Database service not available (required for file access)")
                 # Attempt default connection?
                 from nodupe.core.database.connection import DatabaseConnection
                 db = DatabaseConnection.get_instance()
            
            # Import needed classes locally to avoid circular top-level imports if any
            from nodupe.core.database.files import FileRepository
            
            repo = FileRepository(db)
            files = repo.get_all_files()
            
            if not files:
                print("[PLUGIN] No files in database to analyze.")
                return 0
                
            print(f"[PLUGIN] Analyzing {len(files)} files using metric: {args.metric}")
            
            pairs_found = 0
            
            if args.metric in ['hash', 'size', 'name']:
                # Use in-memory grouping for exact matches
                field_map = {'hash': 'hash', 'size': 'size', 'name': 'name'}
                field = field_map.get(args.metric)
                
                # Grouping
                groups = {}
                for f in files:
                    val = f.get(field)
                    if not val: continue
                    if val not in groups: groups[val] = []
                    groups[val].append(f)
                
                # Detect
                for val, group in groups.items():
                    if len(group) > 1:
                        # Found duplicates
                        pairs_found += len(group) - 1
                        
                        # Sort by path length (shorter is "original" usually, or random)
                        group.sort(key=lambda x: len(x['path'])) 
                        # Or sort by time? group.sort(key=lambda x: x['created_time'])
                        # Let's keep it simple: first found (id) or shortest path is original.
                        
                        original = group[0]
                        duplicates = group[1:]
                        
                        # Update DB
                        for dup in duplicates:
                            repo.mark_as_duplicate(dup['id'], original['id'])
                            if hasattr(args, 'verbose') and args.verbose:
                                print(f"  [DUP] {dup['path']} == {original['path']}")
                                
            elif args.metric == 'vector':
                 print("[PLUGIN] Vector similarity search not yet implemented (requires embedding generation)")
                 # Future: Use SimilarityManager here
            
            print(f"[PLUGIN] Analysis complete.")
            print(f"[PLUGIN] Marked {pairs_found} files as duplicates.")
            
            self._on_similarity_complete(pairs_found=pairs_found)
            return 0
            
        except Exception as e:
            print(f"[PLUGIN ERROR] Similarity search failed: {e}")
            if hasattr(args, 'verbose') and args.verbose:
                import traceback
                traceback.print_exc()
            return 1

# Create plugin instance when module is loaded
similarity_plugin = SimilarityCommandPlugin()

def register_plugin():
    """Register plugin with core system."""
    return similarity_plugin


# Export plugin interface
__all__ = ['similarity_plugin', 'register_plugin']
