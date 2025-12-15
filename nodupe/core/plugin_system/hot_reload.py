"""Plugin Hot Reload Module.

Support for hot reloading plugins during development using standard library only.

Key Features:
    - Polling-based file monitoring
    - Automatic plugin reloading on change
    - Thread-safe operation
    - Graceful error handling
    - Standard library only (no external dependencies like watchdog)

Dependencies:
    - threading
    - time
    - pathlib
"""

import time
import threading
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from .loader import PluginLoader
from .lifecycle import PluginLifecycleManager

class PluginHotReload:
    """Handle plugin hot reloading via file polling.
    
    Monitors plugin files for changes and triggers reload sequence:
    Shutdown -> Unload -> Reload Code -> Instantiate -> Register -> Initialize
    """

    def __init__(
        self, 
        loader: PluginLoader, 
        lifecycle: PluginLifecycleManager, 
        container: Any, 
        poll_interval: float = 1.0
    ):
        """Initialize hot reload manager.

        Args:
            loader: Plugin loader instance
            lifecycle: Plugin lifecycle manager
            container: Dependency container for re-initialization
            poll_interval: Seconds between checks
        """
        self.loader = loader
        self.lifecycle = lifecycle
        self.container = container
        self.poll_interval = poll_interval
        
        self._watched_plugins: Dict[str, Dict[str, Any]] = {}
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

    def watch_plugin(self, plugin_name: str, plugin_path: Path) -> None:
        """Register a plugin to be watched.

        Args:
            plugin_name: Name of plugin
            plugin_path: Path to plugin file
        """
        if not plugin_path.exists():
            return
        
        with self._lock:
            try:
                self._watched_plugins[plugin_name] = {
                    'path': plugin_path,
                    'mtime': plugin_path.stat().st_mtime
                }
                self.logger.debug(f"Watching plugin {plugin_name} at {plugin_path}")
            except OSError as e:
                self.logger.warning(f"Could not watch plugin {plugin_name}: {e}")

    def start(self) -> None:
        """Start the hot reload polling thread."""
        if self._thread is not None:
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._poll_loop, 
            name="PluginHotReloadThread", 
            daemon=True
        )
        self._thread.start()
        self.logger.info("Plugin hot reload started")

    def stop(self) -> None:
        """Stop the hot reload polling thread."""
        if self._thread is None:
            return

        self._stop_event.set()
        self._thread.join(timeout=2.0)
        self._thread = None
        self.logger.info("Plugin hot reload stopped")

    def _poll_loop(self) -> None:
        """Main polling loop running in background thread."""
        while not self._stop_event.is_set():
            time.sleep(self.poll_interval)
            
            # Create a safe copy of items to iterate
            with self._lock:
                items = list(self._watched_plugins.items())

            for name, info in items:
                # Check if we should stop mid-iteration
                if self._stop_event.is_set():
                    break
                    
                path = info['path']
                last_mtime = info['mtime']
                
                try:
                    # Check file modification time
                    current_mtime = path.stat().st_mtime
                    
                    # If modified more recently than last check
                    if current_mtime > last_mtime:
                        self.logger.info(f"Detected change in plugin {name}, reloading...")
                        
                        # Perform reload
                        self._reload_plugin(name, path)
                        
                        # Update mtime
                        with self._lock:
                            if name in self._watched_plugins:
                                self._watched_plugins[name]['mtime'] = current_mtime
                                
                except FileNotFoundError:
                    self.logger.warning(f"Plugin file {path} disappeared, stopping watch")
                    with self._lock:
                        self._watched_plugins.pop(name, None)
                except Exception as e:
                    self.logger.error(f"Error watching plugin {name}: {e}")

    def _reload_plugin(self, name: str, path: Path) -> None:
        """Reload a specific plugin.

        Args:
            name: Plugin name
            path: Plugin file path
        """
        try:
            # 1. Shutdown existing plugin
            self.logger.info(f"Shutting down plugin {name}...")
            shutdown_success = self.lifecycle.shutdown_plugin(name)
            if not shutdown_success:
                self.logger.warning(f"Plugin {name} was not running or failed to shutdown")
            
            # 2. Unload from loader (clears sys.modules cache)
            self.loader.unload_plugin(name)
            
            # 3. Re-load from file
            self.logger.info(f"Reloading plugin {name} from {path}...")
            plugin_class = self.loader.load_plugin_from_file(path)
            if not plugin_class:
                self.logger.error(f"Failed to load plugin class for {name} during reload")
                return

            # 4. Instantiate
            plugin_instance = self.loader.instantiate_plugin(plugin_class)
            
            # 5. Register
            self.loader.register_loaded_plugin(plugin_instance, path)
            
            # 6. Initialize
            self.logger.info(f"Initializing plugin {name}...")
            # Note: We re-use the original container. 
            # Dependencies are assumed to be satisfied as we don't unload valid dependencies.
            success = self.lifecycle.initialize_plugin(plugin_instance, self.container)
            
            if success:
                self.logger.info(f"Plugin {name} hot reloaded successfully")
            else:
                self.logger.error(f"Plugin {name} failed initialization after reload")

        except Exception as e:
            self.logger.error(f"Failed to hot reload plugin {name}: {e}")
            # Try to restore state? For now, just log.
