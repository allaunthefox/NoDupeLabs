# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""NoDupeLabs Database Layer - SQLite with hard isolation.

This module provides the database layer functionality with complete isolation
From optional dependencies, using only standard library SQLite.

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
from .embeddings import EmbeddingRepository
from .files import FileRepository
from .schema import DatabaseSchema, SchemaError
from .transactions import (
    DatabaseTransaction,
    DatabaseTransactions,
    IsolationLevel,
    TransactionError,
)
from .wrapper import (  # Updated: uses refactored wrapper.py
    Database,
    DatabaseError,
)

__all__ = [
    "Database",
    "DatabaseConnection",
    "DatabaseError",
    "DatabaseSchema",
    "DatabaseTransaction",
    "DatabaseTransactions",
    "EmbeddingRepository",
    "FileRepository",
    "IsolationLevel",
    "SchemaError",
    "TransactionError",
    "get_connection",
]
