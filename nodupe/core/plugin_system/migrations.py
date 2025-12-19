"""Plugin System Migrations.

Database migration utilities for plugin schema changes.
"""

import sqlite3
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def migrate_plugin_schema(connection: sqlite3.Connection) -> None:
    """Add missing fields to plugins table.

    This function adds the new plugin fields (plugin_path, entry_point, dependencies, description)
    to existing databases while maintaining backward compatibility.

    Args:
        connection: SQLite database connection
    """
    try:
        cursor = connection.cursor()

        # Check if new columns already exist
        cursor.execute("PRAGMA table_info(plugins)")
        columns = [column[1] for column in cursor.fetchall()]

        # Add missing columns
        if 'plugin_path' not in columns:
            cursor.execute("ALTER TABLE plugins ADD COLUMN plugin_path TEXT")
            logger.info("Added plugin_path column to plugins table")

        if 'entry_point' not in columns:
            cursor.execute("ALTER TABLE plugins ADD COLUMN entry_point TEXT")
            logger.info("Added entry_point column to plugins table")

        if 'dependencies' not in columns:
            cursor.execute("ALTER TABLE plugins ADD COLUMN dependencies TEXT")
            logger.info("Added dependencies column to plugins table")

        if 'description' not in columns:
            cursor.execute("ALTER TABLE plugins ADD COLUMN description TEXT")
            logger.info("Added description column to plugins table")

        connection.commit()
        logger.info("Plugin schema migration completed successfully")

    except sqlite3.Error as e:
        connection.rollback()
        logger.error(f"Failed to migrate plugin schema: {e}")
        raise

def create_plugin_metadata_table(connection: sqlite3.Connection) -> None:
    """Create plugin metadata table if needed.

    This function creates a separate table for plugin metadata if it doesn't exist.

    Args:
        connection: SQLite database connection
    """
    try:
        cursor = connection.cursor()

        # Check if table already exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='plugin_metadata'"
        )
        if cursor.fetchone():
            logger.info("Plugin metadata table already exists")
            return

        # Create plugin metadata table
        cursor.execute("""
            CREATE TABLE plugin_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plugin_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                updated_at INTEGER NOT NULL,
                UNIQUE(plugin_id, key),
                FOREIGN KEY (plugin_id) REFERENCES plugins(id) ON DELETE CASCADE
            )
        """)

        # Create index
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_plugin_metadata_plugin_id ON plugin_metadata(plugin_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_plugin_metadata_key ON plugin_metadata(key)")

        connection.commit()
        logger.info("Created plugin metadata table successfully")

    except sqlite3.Error as e:
        connection.rollback()
        logger.error(f"Failed to create plugin metadata table: {e}")
        raise

def update_existing_plugins_metadata(connection: sqlite3.Connection) -> None:
    """Update existing plugins with metadata if missing.

    This function updates existing plugin records with default metadata values.

    Args:
        connection: SQLite database connection
    """
    try:
        cursor = connection.cursor()

        # Get all plugins that are missing metadata
        cursor.execute("""
            SELECT id, name FROM plugins
            WHERE plugin_path IS NULL OR plugin_path = ''
        """)

        plugins_to_update = cursor.fetchall()
        if not plugins_to_update:
            logger.info("No plugins need metadata updates")
            return

        logger.info(f"Updating metadata for {len(plugins_to_update)} plugins")

        for plugin_id, plugin_name in plugins_to_update:
            # Set default values based on plugin name
            plugin_path = f"nodupe/plugins/{plugin_name.lower()}"
            entry_point = f"{plugin_name.lower()}.plugin:PluginClass"
            dependencies = json.dumps([])
            description = f"Plugin for {plugin_name} functionality"

            cursor.execute("""
                UPDATE plugins
                SET plugin_path = ?, entry_point = ?, dependencies = ?, description = ?
                WHERE id = ?
            """, (plugin_path, entry_point, dependencies, description, plugin_id))

        connection.commit()
        logger.info(f"Updated metadata for {len(plugins_to_update)} plugins")

    except sqlite3.Error as e:
        connection.rollback()
        logger.error(f"Failed to update plugin metadata: {e}")
        raise

def run_plugin_migrations(connection: sqlite3.Connection) -> None:
    """Run all plugin migrations.

    This function runs all necessary plugin migrations in the correct order.

    Args:
        connection: SQLite database connection
    """
    try:
        logger.info("Starting plugin migrations")

        # 1. Migrate plugin schema
        migrate_plugin_schema(connection)

        # 2. Create metadata table
        create_plugin_metadata_table(connection)

        # 3. Update existing plugins
        update_existing_plugins_metadata(connection)

        logger.info("All plugin migrations completed successfully")

    except Exception as e:
        logger.error(f"Plugin migrations failed: {e}")
        raise

def get_plugin_schema_version(connection: sqlite3.Connection) -> Optional[str]:
    """Get the current plugin schema version.

    Args:
        connection: SQLite database connection

    Returns:
        Plugin schema version or None if not set
    """
    try:
        cursor = connection.cursor()

        # Check if plugin_schema_version table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='plugin_schema_version'"
        )
        if not cursor.fetchone():
            return None

        # Get latest version
        cursor.execute(
            "SELECT version FROM plugin_schema_version ORDER BY applied_at DESC LIMIT 1"
        )
        result = cursor.fetchone()
        return result[0] if result else None

    except sqlite3.Error as e:
        logger.error(f"Failed to get plugin schema version: {e}")
        return None

def set_plugin_schema_version(connection: sqlite3.Connection, version: str) -> None:
    """Set the plugin schema version.

    Args:
        connection: SQLite database connection
        version: Plugin schema version to set
    """
    try:
        cursor = connection.cursor()

        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plugin_schema_version (
                version TEXT PRIMARY KEY,
                applied_at INTEGER NOT NULL,
                description TEXT
            )
        """)

        # Set version
        import time
        current_time = int(time.time())
        cursor.execute(
            "INSERT OR REPLACE INTO plugin_schema_version (version, applied_at, description) "
            "VALUES (?, ?, ?)",
            (version, current_time, "Plugin schema migration")
        )

        connection.commit()
        logger.info(f"Set plugin schema version to {version}")

    except sqlite3.Error as e:
        connection.rollback()
        logger.error(f"Failed to set plugin schema version: {e}")
        raise
