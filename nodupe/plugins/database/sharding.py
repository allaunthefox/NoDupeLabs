"""
Database Sharding Plugin

Provides database sharding functionality for horizontal data partitioning.
"""

import sqlite3
import os
from typing import List, Optional, Dict, Any
import logging

from nodupe.core.plugin_system import Plugin, PluginMetadata


logger = logging.getLogger(__name__)


class DatabaseShardingPlugin(Plugin):
    """
    Database sharding functionality plugin.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}
        self._shards = {}
        logger.info("Database sharding plugin initialized")

    @property
    def name(self) -> str:
        return "DatabaseSharding"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> List[str]:
        return []

    def get_capabilities(self) -> dict:
        return {
            "sharding": True,
            "horizontal_partitioning": True,
            "create_shard": True,
        }

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name=self.name,
            version=self.version,
            description="Database sharding functionality for horizontal data partitioning",
            author="NoDupeLabs",
            license="Apache-2.0",
            dependencies=self.dependencies,
            tags=["database", "sharding", "partitioning"]
        )

    def create_shard(self, shard_name: str, db_path: str = None) -> str:
        if not self._is_valid_identifier(shard_name):
            raise ValueError(f"Invalid shard name: {shard_name}")
        
        if db_path is None:
            db_path = os.path.join(os.path.dirname(self.config.get('db_path', '.')), f"{shard_name}.db")
        
        shard_conn = sqlite3.connect(db_path)
        try:
            shard_conn.execute("""
                CREATE TABLE IF NOT EXISTS shard_data (
                    id INTEGER PRIMARY KEY,
                    key TEXT UNIQUE,
                    value BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            shard_conn.commit()
        finally:
            shard_conn.close()
        
        self._shards[shard_name] = db_path
        logger.info(f"Created shard '{shard_name}' at {db_path}")
        return db_path

    def _is_valid_identifier(self, name: str) -> bool:
        return bool(name and name.replace('_', '').replace('-', '').isalnum()
                   and not name.startswith('_') and len(name) <= 64)

    def list_shards(self) -> List[str]:
        return list(self._shards.keys())

    def initialize(self, container: Any) -> None:
        logger.info("Database sharding plugin initialized")

    def shutdown(self, container: Any) -> None:
        logger.info("Database sharding plugin shutdown")