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

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version"""

    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        """List of plugin dependencies"""

    @abstractmethod
    def initialize(self, container: Any) -> None:
        """Initialize the plugin"""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the plugin"""

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities"""
