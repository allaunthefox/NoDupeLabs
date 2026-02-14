# Add these methods to the PluginDiscovery class in discovery.py
# Insert after line 54 (after __init__ method)

    def initialize(self, container) -> None:
        """Initialize plugin discovery with dependency container.

        Args:
            container: Dependency injection container
        """
        self.container = container

    def shutdown(self) -> None:
        """Shutdown plugin discovery and cleanup resources."""
        self.container = None
        self._discovered_plugins.clear()
