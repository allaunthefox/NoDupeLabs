"""Errors Module.

Custom exception hierarchy.
"""


class NoDupeError(Exception):
    """Base exception for NoDupeLabs"""


class SecurityError(NoDupeError):
    """Security-related exceptions"""


class ValidationError(NoDupeError):
    """Input validation exceptions"""


class PluginError(NoDupeError):
    """Plugin-related exceptions"""


class DatabaseError(NoDupeError):
    """Database-related exceptions"""
