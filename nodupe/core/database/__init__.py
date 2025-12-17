# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""NoDupeLabs Database Layer - SQLite with hard isolation.

This module provides the database layer functionality with complete isolation
from optional dependencies, using only standard library SQLite.

Key Features:
    - SQLite database connection management
    - Connection pooling with standard library
    - File repository interface
    - Transaction management
    - Basic indexing support

Dependencies:
    - sqlite3 (standard library only)
"""

from .connection import DatabaseConnection, get_connection
from .files import FileRepository
from .embeddings import EmbeddingRepository
from .database import Database, DatabaseError

__all__ = [
    'Database',
    'DatabaseError',
    'DatabaseConnection',
    'get_connection',
    'FileRepository',
    'EmbeddingRepository'
]
