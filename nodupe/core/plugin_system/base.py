"""Plugin Base Class.

Abstract base class for all plugins with UUID support.
"""

from abc import ABC, abstractmethod
from uuid import UUID, uuid4
from typing import List, Dict, Any, Optional
import re


class Plugin(ABC):
    """Abstract base class for all NoDupeLabs plugins with UUID support"""
    
    def __init__(self, metadata: Dict[str, Any]):
        """Initialize plugin with UUID-based metadata."""
        self._validate_metadata(metadata)
        self.uuid: UUID = UUID(metadata["uuid"])
        self._name: str = metadata["name"]
        self.display_name: str = metadata["display_name"]
        self._version: str = metadata["version"]
        self.description: str = metadata["description"]
        self.author: str = metadata["author"]
        self.category: str = metadata["category"]
        self._dependencies: List[str] = metadata.get("dependencies", [])
        self.tags: List[str] = metadata.get("tags", [])
        self.marketplace_id: str = metadata["marketplace_id"]
        self._initialized: bool = False

    @staticmethod
    def _validate_metadata(metadata: Dict[str, Any]) -> None:
        """Validate plugin metadata according to RFC 9562 UUID specification."""
        required_fields = [
            "uuid", "name", "display_name", "version", 
            "description", "author", "category", "compatibility",
            "marketplace_id"
        ]
        
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Missing required metadata field: {field}")
        
        # Validate UUID (RFC 9562 compliant)
        try:
            uuid_obj = UUID(metadata["uuid"])
            if uuid_obj.version != 4:
                raise ValueError("Plugin UUID must be version 4 (RFC 9562)")
            if uuid_obj.variant != 'specified in RFC 4122':
                raise ValueError("Plugin UUID must use RFC 4122 variant (RFC 9562)")
        except ValueError as e:
            raise ValueError(f"Invalid UUID format (RFC 9562): {e}")
        
        # Validate name format
        if not re.match(r'^[a-z][a-z0-9_]{1,49}$', metadata["name"]):
            raise ValueError("Plugin name must be 2-50 characters, lowercase letters, numbers, and underscores only")
        
        # Validate version format
        if not re.match(r'^v\d+\.\d+\.\d+$', metadata["version"]):
            raise ValueError("Version must follow semantic versioning format (v1.2.3)")
        
        # Validate marketplace_id UTF-8 compliance
        marketplace_id = metadata.get("marketplace_id", "")
        if not isinstance(marketplace_id, str):
            raise ValueError("Marketplace ID must be a string")
        
        # Validate UTF-8 encoding
        try:
            marketplace_id.encode('utf-8')
        except UnicodeEncodeError as e:
            raise ValueError(f"Marketplace ID contains non-UTF-8 characters: {e}")
        
        # Check for invalid characters in marketplace_id
        if '\x00' in marketplace_id:
            raise ValueError("Marketplace ID contains null bytes")
        
        # Check length limit (255 characters when UTF-8 encoded)
        utf8_length = len(marketplace_id.encode('utf-8'))
        if utf8_length > 255:
            raise ValueError(f"Marketplace ID too long: {utf8_length} bytes (max 255)")
        
        # Check for control characters (except tab, newline, carriage return which are generally safe)
        for char in marketplace_id:
            if ord(char) < 32 and char not in '\t\n\r':
                raise ValueError(f"Marketplace ID contains invalid control character: {ord(char)}")
            elif ord(char) == 127:  # DEL character
                raise ValueError("Marketplace ID contains DEL character")

    @classmethod
    def generate_uuid(cls) -> UUID:
        """Generate a new UUID v4 for plugin identification."""
        return uuid4()

    @classmethod
    def generate_filename(cls, name: str, version: str) -> str:
        """Generate a UUID-based filename for the plugin."""
        plugin_uuid = cls.generate_uuid()
        return f"{name}_{plugin_uuid}.v{version}.py"

    @property
    def name(self) -> str:
        """Plugin name"""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set plugin name (for testing purposes)"""
        if not isinstance(value, str):
            raise ValueError("Plugin name must be a string")
        if not re.match(r'^[a-z][a-z0-9_]{1,49}$', value):
            raise ValueError("Plugin name must be 2-50 characters, lowercase letters, numbers, and underscores only")
        self._name = value

    @property
    def version(self) -> str:
        """Plugin version"""
        return self._version

    @version.setter
    def version(self, value: str) -> None:
        """Set plugin version (for testing purposes)"""
        if not isinstance(value, str):
            raise ValueError("Plugin version must be a string")
        if not re.match(r'^v\d+\.\d+\.\d+$', value):
            raise ValueError("Version must follow semantic versioning format (v1.2.3)")
        self._version = value

    @property
    def dependencies(self) -> List[str]:
        """List of plugin dependencies"""
        return self._dependencies

    @dependencies.setter
    def dependencies(self, value: List[str]) -> None:
        """Set plugin dependencies (for testing purposes)"""
        if not isinstance(value, list):
            raise ValueError("Dependencies must be a list")
        for dep in value:
            if not isinstance(dep, str):
                raise ValueError("All dependencies must be strings")
        self._dependencies = value

    @property
    def uuid_str(self) -> str:
        """Plugin UUID as string"""
        return str(self.uuid)

    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized"""
        return self._initialized

    @abstractmethod
    def initialize(self, container: Any) -> None:
        """Initialize the plugin"""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the plugin"""

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities"""
