# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Standard Database Tool for NoDupeLabs.

Provides SQLite-based data storage as a tool.
"""

from typing import List, Dict, Any, Optional, Callable
from nodupe.core.tool_system.base import Tool, ToolMetadata
from .connection import DatabaseConnection

class StandardDatabaseTool(Tool):
    """Standard database tool (SQLite implementation)."""

    @property
    def name(self) -> str:
        return "database_standard"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> List[str]:
        return []

    @property
    def metadata(self) -> ToolMetadata:
        """Get tool metadata (ISO 19770-2 compliant)."""
        return ToolMetadata(
            name=self.name,
            version=self.version,
            software_id=f"org.nodupe.tool.{self.name.lower()}",
            description="SQLite-based permanent storage for file metadata and duplicate records.",
            author="NoDupeLabs",
            license="Apache-2.0",
            dependencies=self.dependencies,
            tags=["database", "sqlite", "storage", "metadata"]
        )

    @property
    def api_methods(self) -> Dict[str, Callable[..., Any]]:
        # Expose relevant database methods
        return {
            'initialize': self.db.initialize_database,
            'get_connection': lambda: self.db,
            'close': self.db.close
        }

    def __init__(self):
        """Initialize the tool."""
        self.db = DatabaseConnection()

    def initialize(self, container: Any) -> None:
        """Initialize the tool and register services."""
        try:
            self.db.initialize_database()
            container.register_service('database', self.db)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to initialize database: {e}")

    def shutdown(self) -> None:
        """Shutdown the tool."""
        self.db.close()

    def run_standalone(self, args: List[str]) -> int:
        """Stand-alone database check."""
        print(f"Database Path: {self.db.db_path}")
        try:
            self.db.initialize_database()
            print("Database initialized successfully.")
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def describe_usage(self) -> str:
        """Plain language description."""
        return (
            "This component acts like a library or filing cabinet. "
            "It saves information about your files so the software "
            "can remember them later and find duplicates quickly."
        )

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            'engine': 'SQLite',
            'path': self.db.db_path,
            'features': ['connection_pooling', 'transactions']
        }

def register_tool():
    """Register the database tool."""
    return StandardDatabaseTool()

if __name__ == "__main__":
    import sys
    tool = StandardDatabaseTool()
    sys.exit(tool.run_standalone(sys.argv[1:]))
