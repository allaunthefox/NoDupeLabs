"""Compatibility shim for nodupe.core.database.files

Re-exports the FileRepository implementation from the new location under
`nodupe.tools.databases.files`.
"""
from nodupe.tools.databases.files import FileRepository

__all__ = ["FileRepository"]
