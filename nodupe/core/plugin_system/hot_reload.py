"""Plugin Hot Reload Module.

Support for hot reloading plugins during development using standard library only.

Key Features:
    - Efficient file monitoring (inotify on Linux, polling fallback)
    - Automatic plugin reloading on change
    - Thread-safe operation
    - Graceful error handling
    - Standard library only (no external dependencies like watchdog)

Dependencies:
    - threading
    - time
    - pathlib
    - select (Linux only for inotify)
"""

import time
import threading
import logging
import sys
import os
from pathlib import Path
from typing import Set
# Set removedDict, Optional, Any, Set
from .loader import PluginLoader
from .lifecycle import PluginLifecycleManager

# Linux inotify constants
IN_MODIFY = 0x00000002
IN_MOVED_TO = 0x00000080
IN_CREATE = 0x00000100
IN_DELETE = 0x00000200
IN_MOVE_SELF = 0x00000800
IN_DELETE_SELF = 0x00000400


class PluginHotReload:
    """Handle plugin hot reloading via file polling.

    Monitors plugin files for changes and triggers reload sequence:
    Shutdown -> Unload -> Reload Code -> Instantiate -> Register -> Initialize
    
    Uses inotify on Linux for efficient file monitoring, falls back to polling
    on other platforms or if inotify is unavailable.
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
            poll_interval: Seconds between checks (used for polling fallback)
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
        
        # Inotify support (Linux only)
        self._inotify_fd: Optional[int] = None
        self._watch_descriptors: Dict[int, Dict[str, Any]] = {}
        self._use_inotify = self._init_inotify()

    def _init_inotify(self) -> bool:
        """Initialize inotify on Linux if available.
        
        Returns:
            True if inotify is available and initialized, False otherwise
        """
        if not sys.platform.startswith('linux'):
            return False
            
        try:
            # fcntl removed
            # struct removed
            
            # Create inotify file descriptor
            self._inotify_fd = os.open('/proc/sys/kernel/osrelease', os.O_RDONLY)
            os.close(self._inotify_fd)
            
            # Try to create inotify instance
            self._inotify_fd = os.open('/dev/null', os.O_RDONLY)
            os.close(self._inotify_fd)
            
            # Actually create inotify fd
            self._inotify_fd = os.open('/proc/sys/kernel/osrelease', os.O_RDONLY)
            os.close(self._inotify_fd)
            
            # Use inotify_init1 system call
            import ctypes
            libc = ctypes.CDLL('libc.so.6', use_errno=True)
            IN_NONBLOCK = 0x800
            fd = libc.inotify_init1(IN_NONBLOCK)
            
            if fd < 0:
                return False
                
            self._inotify_fd = fd
            
            # Set non-blocking
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            
            self.logger.debug("Initialized inotify for file monitoring")
            return True
            
        except (ImportError, OSError, AttributeError):
            self.logger.debug("inotify not available, using polling fallback")
            return False

    def _add_inotify_watch(self, plugin_name: str, path: Path) -> None:
        """Add an inotify watch for a plugin file.
        
        Args:
            plugin_name: Name of plugin
            path: Path to plugin file
        """
        if not self._use_inotify or self._inotify_fd is None:
            return
            
        try:
            import ctypes
            # fcntl removed
            
            libc = ctypes.CDLL('libc.so.6', use_errno=True)
            
            # Watch for file modifications and moves
            mask = IN_MODIFY | IN_MOVED_TO | IN_CREATE | IN_DELETE | IN_MOVE_SELF | IN_DELETE_SELF
            
            # Add watch
            wd = libc.inotify_add_watch(
                self._inotify_fd,
                str(path.parent).encode(),
                mask
            )
            
            if wd >= 0:
                self._watch_descriptors[wd] = {
                    'plugin_name': plugin_name,
                    'path': path,
                    'filename': path.name
                }
                self.logger.debug(f"Added inotify watch for {plugin_name}")
                
        except Exception as e:
            self.logger.warning(f"Failed to add inotify watch for {plugin_name}: {e}")

    def _remove_inotify_watch(self, plugin_name: str) -> None:
        """Remove inotify watch for a plugin.
        
        Args:
            plugin_name: Name of plugin to remove watch for
        """
        if not self._use_inotify or self._inotify_fd is None:
            return
            
        try:
            import ctypes
            
            libc = ctypes.CDLL('libc.so.6', use_errno=True)
            
            # Find and remove watch
            wds_to_remove = []
            for wd, info in self._watch_descriptors.items():
                if info['plugin_name'] == plugin_name:
                    wds_to_remove.append(wd)
            
            for wd in wds_to_remove:
                libc.inotify_rm_watch(self._inotify_fd, wd)
                del self._watch_descriptors[wd]
                self.logger.debug(f"Removed inotify watch for {plugin_name}")
                
        except Exception as e:
            self.logger.warning(f"Failed to remove inotify watch for {plugin_name}: {e}")

    def _check_inotify_events(self) -> None:
        """Check for inotify events and handle file changes."""
        if not self._use_inotify or self._inotify_fd is None:
            return
            
        try:
            import ctypes
            # struct removed
            
            # Read events (non-blocking)
            event_size = 16  # sizeof(struct inotify_event)
            buffer = ctypes.create_string_buffer(4096)
            
            bytes_read = os.read(self._inotify_fd, buffer)
            if not bytes_read:
                return
                
            # Parse events
            offset = 0
            while offset < len(bytes_read):
                # Parse inotify_event structure
                wd, mask, cookie, name_len = struct.unpack_from('iIII', bytes_read, offset)
                offset += event_size
                
                # Get filename if present
                filename = ""
                if name_len > 0:
                    filename = bytes_read[offset:offset + name_len].rstrip(b'\0').decode()
                    offset += name_len
                
                # Check if this event matches any of our watched files
                if wd in self._watch_descriptors:
                    info = self._watch_descriptors[wd]
                    
                    # Only reload if the specific file was modified
                    if filename == info['filename'] and mask & (IN_MODIFY | IN_MOVED_TO | IN_CREATE):
                        plugin_name = info['plugin_name']
                        self.logger.info(f"Detected change in plugin {plugin_name} via inotify, reloading...")
                        
                        # Perform reload
                        self._reload_plugin(plugin_name, info['path'])
                        
                        # Update mtime to prevent duplicate reloads
                        try:
                            with self._lock:
                                if plugin_name in self._watched_plugins:
                                    self._watched_plugins[plugin_name]['mtime'] = info['path'].stat().st_mtime
                        except:
                            pass
                        
        except (OSError, UnicodeDecodeError):
            # No events or read error, ignore
            pass

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
            # Use longer intervals when using inotify since we get immediate notifications
            sleep_time = self.poll_interval if not self._use_inotify else max(self.poll_interval, 2.0)
            time.sleep(sleep_time)

            # Check inotify events first if available
            if self._use_inotify:
                self._check_inotify_events()

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
