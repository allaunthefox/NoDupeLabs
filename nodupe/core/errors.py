"""Errors Module.

Custom exception hierarchy.
"""

class NoDupeError(Exception):
    """Base exception for NoDupeLabs"""
    pass

class SecurityError(NoDupeError):
    """Security-related exceptions"""
    pass

class ValidationError(NoDupeError):
    """Input validation exceptions"""
    pass

class PluginError(NoDupeError):
    """Plugin-related exceptions"""
    pass

class DatabaseError(NoDupeError):
    """Database-related exceptions"""
    pass
