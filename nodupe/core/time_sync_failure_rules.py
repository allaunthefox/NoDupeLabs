"""Compatibility shim for `nodupe.core.time_sync_failure_rules`.

Re-exports the failure rules implementation from `nodupe.tools.time_sync.failure_rules`.
"""
from nodupe.tools.time_sync.failure_rules import *  # re-export for backwards-compat

__all__ = [name for name in globals().keys() if not name.startswith("_")]
