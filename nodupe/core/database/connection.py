"""Compatibility shim for legacy imports from nodupe.core.database.connection.

This module re-exports the implementation moved to nodupe.tools.databases.connection
so older import paths used throughout tests and some modules continue to work.
"""
from nodupe.tools.databases.connection import DatabaseConnection, get_connection

__all__ = ["DatabaseConnection", "get_connection"]
