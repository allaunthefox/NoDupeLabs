"""Compatibility shim for `nodupe.core.security`.

Re-export `Security` and `SecurityError` from the tools implementation so
legacy imports used by tests remain valid.
"""
from nodupe.tools.security_audit.security_logic import Security, SecurityError

__all__ = ["Security", "SecurityError"]
