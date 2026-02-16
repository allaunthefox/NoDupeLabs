"""Compatibility shim providing ArchiveHandler at `nodupe.core.archive_handler`.

Re-exports the concrete ArchiveHandler implementation from
`nodupe.tools.archive.archive_logic` so legacy imports continue to work.
"""
from nodupe.tools.archive.archive_logic import ArchiveHandler, ArchiveHandlerError

__all__ = ["ArchiveHandler", "ArchiveHandlerError"]
