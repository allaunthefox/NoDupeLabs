"""Plugin Base Class.

Abstract base class for all plugins.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class Plugin(ABC):
    """Abstract base class for all NoDupeLabs plugins"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version"""
        pass

    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        """List of plugin dependencies"""
        pass

    @abstractmethod
    def initialize(self, container: Any) -> None:
        """Initialize the plugin"""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the plugin"""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities"""
        pass
