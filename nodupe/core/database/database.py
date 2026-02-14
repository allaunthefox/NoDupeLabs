# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Database Module - Backward Compatibility Wrapper.

This module provides backward compatibility for code that imports from
nodupe.core.database.database. The actual implementation is in wrapper.py.

This module re-exports all classes from wrapper.py for backward compatibility.

DEPRECATED: Import directly from nodupe.core.database instead:
    from nodupe.core.database import Database
"""

# Re-export from wrapper.py for backward compatibility
from .wrapper import Database, DatabaseError

__all__ = [
    'Database',
    'DatabaseError',
]
