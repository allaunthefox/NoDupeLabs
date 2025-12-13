"""
Core Loader Module
Handles bootstrap and initialization of the NoDupeLabs system
"""

import sys
import logging
from typing import Optional
from pathlib import Path

from .config import load_config
from .container import ServiceContainer
from .plugin_system.registry import PluginRegistry
from .database.connection import DatabaseConnection, get_connection

class CoreLoader:
    """Main application loader and bootstrap class"""

    def __init__(self):
        """Initialize the core loader"""
        self.config = None
        self.container = None
        self.plugin_registry = None
        self.database = None
        self.initialized = False

    def initialize(self) -> None:
        """Initialize the core system"""
        if self.initialized:
            return

        try:
            # Load configuration
            self.config = load_config()
            logging.info("Configuration loaded successfully")

            # Initialize dependency container
            self.container = ServiceContainer()
            self.container.register_service('config', self.config)
            logging.info("Dependency container initialized")

            # Initialize plugin system
            self.plugin_registry = PluginRegistry()
            self.container.register_service('plugin_registry', self.plugin_registry)
            logging.info("Plugin registry initialized")

            # Initialize database
            self.database = get_connection()
            self.database.initialize_database()
            self.container.register_service('database', self.database)
            logging.info("Database initialized")

            self.initialized = True
            logging.info("Core system initialized successfully")

        except Exception as e:
            logging.error(f"Failed to initialize core system: {e}")
            raise

    def shutdown(self) -> None:
        """Shutdown the core system"""
        if not self.initialized:
            return

        try:
            if self.database:
                self.database.close()
                logging.info("Database connection closed")

            if self.plugin_registry:
                self.plugin_registry.shutdown()
                logging.info("Plugin registry shutdown")

            self.initialized = False
            logging.info("Core system shutdown successfully")

        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
            raise

def bootstrap() -> CoreLoader:
    """Bootstrap the application"""
    # Set up basic logging before anything else
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    # Create and initialize core loader
    loader = CoreLoader()
    loader.initialize()

    return loader
