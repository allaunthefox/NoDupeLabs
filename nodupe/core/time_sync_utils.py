"""Compatibility shim for `nodupe.core.time_sync_utils`.

Re-exports utilities from `nodupe.tools.time_sync.sync_utils`.
"""
from nodupe.tools.time_sync.sync_utils import *  # noqa: F401,F403 - explicit compatibility shim

__all__ = [name for name in globals().keys() if not name.startswith("_")]
