"""Test loader module functionality."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from nodupe.core.container import ServiceContainer
from nodupe.core.errors import NoDupeError
from nodupe.core.loader import CoreLoader, bootstrap


class TestCoreLoaderInitialization:
    """Test CoreLoader initialization functionality."""

    def test_core_loader_creation(self):
        """Test CoreLoader instance creation."""
        loader = CoreLoader()
        assert loader is not None
        assert loader.config is None
        assert loader.container is None
        assert loader.tool_registry is None
        assert loader.tool_loader is None
        assert loader.tool_discovery is None
        assert loader.tool_lifecycle is None
        assert loader.hot_reload is None
        assert loader.database is None
        assert loader.initialized is False

    def test_double_initialization(self):
        """Test that double initialization is handled gracefully."""
        loader = CoreLoader()

        # Mock the initialization to avoid actual setup
        with (
            patch.object(
                loader, "_apply_platform_autoconfig"
            ) as mock_autoconfig,
            patch("nodupe.core.loader.load_config") as mock_load_config,
            patch("nodupe.core.loader.logging") as mock_logging,
        ):

            mock_autoconfig.return_value = {}
            mock_load_config.return_value = Mock(config={})
            mock_logging.info = MagicMock()
            mock_logging.error = MagicMock()

            # First initialization
            loader.initialize()
            assert loader.initialized is True

            # Second initialization should be skipped
            loader.initialize()
            assert loader.initialized is True

    def test_initialization_error_handling(self):
        """Test initialization error handling."""
        loader = CoreLoader()

        with (
            patch("nodupe.core.loader.load_config") as mock_load_config,
            patch("nodupe.core.loader.logging") as mock_logging,
        ):

            mock_load_config.side_effect = Exception("Config load failed")
            mock_logging.error = MagicMock()

            with pytest.raises(Exception):
                loader.initialize()

            assert loader.initialized is False


class TestCoreLoaderConfiguration:
    """Test CoreLoader configuration functionality."""

    def test_platform_autoconfig(self):
        """Test platform autoconfiguration."""
        loader = CoreLoader()

        with (
            patch("nodupe.core.loader.platform") as mock_platform,
            patch("nodupe.core.loader.os") as mock_os,
            patch("nodupe.core.loader.multiprocessing") as mock_multiprocessing,
            patch("nodupe.core.loader.psutil") as mock_psutil,
            patch("nodupe.core.loader.logging") as mock_logging,
        ):

            # Mock platform detection
            mock_platform.system.return_value = "Linux"
            mock_os.environ = {}
            mock_multiprocessing.cpu_count.return_value = 4
            mock_psutil.virtual_memory.return_value = Mock(total=8 * 1024**3)
            mock_psutil.disk_partitions.return_value = [
                Mock(mountpoint="/", device="/dev/sda1", opts="")
            ]
            mock_logging.info = MagicMock()

            config = loader._apply_platform_autoconfig()

            assert "db_path" in config
            assert "log_dir" in config
            assert "tools" in config
            assert "cpu_cores" in config
            assert "ram_gb" in config
            assert "drive_type" in config

    def test_platform_autoconfig_without_psutil_does_not_include_ram(self):
        """When psutil is not available, ram_gb should not be present."""
        loader = CoreLoader()

        with patch("nodupe.core.loader.psutil", None):
            cfg = loader._apply_platform_autoconfig()
            assert "ram_gb" not in cfg

    def test_config_merging(self):
        """Test configuration merging logic."""
        loader = CoreLoader()

        with (
            patch("nodupe.core.loader.load_config") as mock_load_config,
            patch.object(
                loader, "_apply_platform_autoconfig"
            ) as mock_autoconfig,
            patch("nodupe.core.loader.logging") as mock_logging,
        ):

            # Mock config with nested structure
            mock_config = Mock()
            mock_config.config = {
                "existing_key": "existing_value",
                "tools": {"directories": ["custom_tools"], "auto_load": False},
            }

            mock_autoconfig.return_value = {
                "new_key": "new_value",
                "tools": {
                    "hot_reload": True,
                    "loading_order": ["core", "database"],
                },
            }

            mock_load_config.return_value = mock_config
            mock_logging.info = MagicMock()

            # This should merge the configs
            loader.initialize()

            # Verify that platform config was merged into main config
            assert mock_config.config["new_key"] == "new_value"
            assert mock_config.config["tools"]["hot_reload"]
            assert mock_config.config["tools"]["loading_order"] == [
                "core",
                "database",
            ]
            # Original values should be preserved
            assert mock_config.config["tools"]["directories"] == [
                "custom_tools"
            ]
            assert not mock_config.config["tools"]["auto_load"]


class TestCoreLoaderToolSystem:
    """Test CoreLoader tool system functionality."""

    def test_tool_discovery_and_loading(self):
        """Test tool discovery and loading."""
        loader = CoreLoader()

        with (
            patch("nodupe.core.loader.load_config") as mock_load_config,
            patch.object(
                loader, "_apply_platform_autoconfig"
            ) as mock_autoconfig,
            patch("nodupe.core.loader.ToolRegistry") as mock_registry,
            patch("nodupe.core.loader.create_tool_loader") as mock_loader,
            patch("nodupe.core.loader.create_tool_discovery") as mock_discovery,
            patch(
                "nodupe.core.loader.create_lifecycle_manager"
            ) as mock_lifecycle,
            patch("nodupe.core.loader.ToolHotReload") as mock_hot_reload,
            patch("nodupe.core.loader.get_connection") as mock_db,
            patch("nodupe.core.loader.logging") as mock_logging,
            patch("nodupe.core.loader.Path") as mock_path,
        ):

            # Mock config
            mock_config = Mock()
            mock_config.config = {
                "tools": {
                    "directories": ["tools"],
                    "auto_load": True,
                    "loading_order": ["core"],
                }
            }

            # Mock path to return existing paths
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path.return_value = mock_path_instance

            # Mock tool discovery
            mock_discovery_instance = Mock()
            mock_discovery_instance.discover_tools_in_directory.return_value = [
                Mock(name="core", path="tools/core.py")
            ]
            mock_discovery_instance.get_discovered_tool.return_value = Mock(
                name="core", path="tools/core.py"
            )
            mock_discovery_instance.get_discovered_tools.return_value = [
                Mock(name="core", path="tools/core.py")
            ]
            mock_discovery.return_value = mock_discovery_instance

            # Mock tool loader
            mock_loader_instance = Mock()
            mock_loader_instance.load_tool_from_file.return_value = Mock
            mock_loader_instance.instantiate_tool.return_value = Mock(
                name="core"
            )
            mock_loader_instance.register_loaded_tool.return_value = None
            mock_loader.return_value = mock_loader_instance

            # Mock other components
            mock_registry_instance = Mock()
            mock_registry.return_value = mock_registry_instance

            mock_lifecycle_instance = Mock()
            mock_lifecycle.return_value = mock_lifecycle_instance

            mock_hot_reload_instance = Mock()
            mock_hot_reload.return_value = mock_hot_reload_instance

            mock_db_instance = Mock()
            mock_db.return_value = mock_db_instance

            # Set up mocks
            mock_load_config.return_value = mock_config
            mock_autoconfig.return_value = {}
            mock_logging.info = MagicMock()
            mock_logging.error = MagicMock()

            # Initialize
            loader.initialize()

            # Verify tool system was set up
            assert loader.tool_registry is not None
            assert loader.tool_loader is not None
            assert loader.tool_discovery is not None
            assert loader.tool_lifecycle is not None
            assert loader.hot_reload is not None

            # Verify tool discovery was called
            mock_discovery_instance.discover_tools_in_directory.assert_called()

    def test_tool_loading_disabled(self):
        """Test tool loading when disabled in config."""
        loader = CoreLoader()

        with (
            patch("nodupe.core.loader.load_config") as mock_load_config,
            patch.object(
                loader, "_apply_platform_autoconfig"
            ) as mock_autoconfig,
            patch("nodupe.core.loader.ToolRegistry"),
            patch("nodupe.core.loader.create_tool_loader"),
            patch("nodupe.core.loader.create_tool_discovery") as mock_discovery,
            patch("nodupe.core.loader.create_lifecycle_manager"),
            patch("nodupe.core.loader.ToolHotReload"),
            patch("nodupe.core.loader.get_connection"),
            patch("nodupe.core.loader.logging") as mock_logging,
        ):

            # Mock config with auto_load disabled
            mock_config = Mock()
            mock_config.config = {"tools": {"auto_load": False}}

            mock_load_config.return_value = mock_config
            mock_autoconfig.return_value = {}
            mock_logging.info = MagicMock()

            # Initialize
            loader.initialize()

            # Verify that tool discovery was not called
            mock_discovery.return_value.discover_tools_in_directory.assert_not_called()


    def test_discover_and_load_tools_falls_back_to_standard_paths(self):
        """If configured tool directories don't exist, the loader should
        fall back to standard locations (e.g. `nodupe/tools`, `tools`).
        """
        loader = CoreLoader()

        with (
            patch("nodupe.core.loader.load_config") as mock_load_config,
            patch("nodupe.core.loader.Path") as mock_path,
            patch("nodupe.core.loader.logging") as mock_logging,
        ):
            # Config points to a non-existent directory
            mock_config = Mock()
            mock_config.config = {
                "tools": {"directories": ["nonexistent_dir"], "auto_load": True}
            }
            mock_load_config.return_value = mock_config

            # Path(...) should indicate the provided directory does not exist
            # but the standard paths do exist.  Return objects whose resolve()
            # returns themselves so the loader can call .exists() later.
            def path_side_effect(arg):
                m = Mock()
                m.resolve.return_value = m
                if arg == "nonexistent_dir":
                    m.exists.return_value = False
                elif arg in ("nodupe/tools", "tools"):
                    m.exists.return_value = True
                else:
                    m.exists.return_value = False
                return m

            mock_path.side_effect = path_side_effect

            # Attach a mock discovery implementation so we can assert it was used
            loader.tool_discovery = Mock()
            loader.tool_discovery.discover_tools_in_directory.return_value = []

            # Call the discovery helper directly
            loader._discover_and_load_tools()

            # Should have attempted discovery against at least one standard path
            loader.tool_discovery.discover_tools_in_directory.assert_called()


    def test_load_single_tool_no_class_is_handled_gracefully(self):
        """If the loader cannot find a class in a tool file it should not
        attempt to instantiate or watch the tool and must not raise.
        """
        loader = CoreLoader()

        # Provide a mocked tool_loader that returns `None` for the class
        loader.tool_loader = Mock()
        loader.tool_loader.load_tool_from_file.return_value = None
        loader.tool_loader.instantiate_tool = Mock()

        # hot_reload should not be asked to watch anything
        loader.hot_reload = Mock()
        loader.hot_reload.watch_tool = Mock()

        # Ensure logger.exception is observable
        loader.logger = Mock()

        # Call with a synthetic tool_info
        tool_info = Mock(name="nope", path="/path/to/nope.py")
        loader._load_single_tool(tool_info)

        loader.tool_loader.load_tool_from_file.assert_called_once_with(
            "/path/to/nope.py"
        )
        loader.tool_loader.instantiate_tool.assert_not_called()
        loader.hot_reload.watch_tool.assert_not_called()
        loader.logger.exception.assert_not_called()


class TestCoreLoaderDatabase:
    """Test CoreLoader database functionality."""

    def test_database_initialization(self):
        """Test database initialization."""
        loader = CoreLoader()

        with (
            patch("nodupe.core.loader.load_config") as mock_load_config,
            patch.object(
                loader, "_apply_platform_autoconfig"
            ) as mock_autoconfig,
            patch("nodupe.core.loader.ToolRegistry"),
            patch("nodupe.core.loader.create_tool_loader"),
            patch("nodupe.core.loader.create_tool_discovery"),
            patch("nodupe.core.loader.create_lifecycle_manager"),
            patch("nodupe.core.loader.ToolHotReload"),
            patch("nodupe.core.loader.get_connection") as mock_db,
            patch("nodupe.core.loader.logging") as mock_logging,
        ):

            # Mock config
            mock_config = Mock()
            mock_config.config = {}

            # Mock database
            mock_db_instance = Mock()
            mock_db.return_value = mock_db_instance

            mock_load_config.return_value = mock_config
            mock_autoconfig.return_value = {}
            mock_logging.info = MagicMock()

            # Initialize
            loader.initialize()

            # Verify database was initialized
            mock_db_instance.initialize_database.assert_called_once()
            assert loader.database is mock_db_instance

    def test_database_initialization_skips_on_error(self):
        """If DB connection/init fails, initialize() should continue."""
        loader = CoreLoader()

        with (
            patch("nodupe.core.loader.load_config") as mock_load_config,
            patch.object(loader, "_apply_platform_autoconfig") as mock_autoconfig,
            patch("nodupe.core.loader.ToolRegistry"),
            patch("nodupe.core.loader.create_tool_loader"),
            patch("nodupe.core.loader.create_tool_discovery"),
            patch("nodupe.core.loader.create_lifecycle_manager"),
            patch("nodupe.core.loader.ToolHotReload"),
            patch("nodupe.core.loader.get_connection") as mock_db,
            patch("nodupe.core.loader.logging") as mock_logging,
        ):
            mock_config = Mock()
            mock_config.config = {}

            # Simulate connection/init raising
            mock_db.side_effect = Exception("cannot connect")

            mock_load_config.return_value = mock_config
            mock_autoconfig.return_value = {}
            mock_logging.info = MagicMock()
            mock_logging.debug = MagicMock()

            # Should not raise even though DB setup failed
            # Override instance logger so we can assert the exception-path was hit
            loader.logger = Mock()

            loader.initialize()
            assert loader.database is None
            loader.logger.debug.assert_called()


class TestCoreLoaderHashAutotuning:
    """Test CoreLoader hash autotuning functionality."""

    def test_hash_autotuning(self):
        """Test hash algorithm autotuning."""
        loader = CoreLoader()

        with (
            patch("nodupe.core.loader.load_config") as mock_load_config,
            patch.object(
                loader, "_apply_platform_autoconfig"
            ) as mock_autoconfig,
            patch("nodupe.core.loader.ToolRegistry"),
            patch("nodupe.core.loader.create_tool_loader"),
            patch("nodupe.core.loader.create_tool_discovery"),
            patch("nodupe.core.loader.create_lifecycle_manager"),
            patch("nodupe.core.loader.ToolHotReload"),
            patch("nodupe.core.loader.get_connection"),
            patch(
                "nodupe.core.loader.autotune_hash_algorithm"
            ) as mock_autotune,
            patch("nodupe.core.loader.create_autotuned_hasher") as mock_hasher,
            patch("nodupe.core.loader.logging") as mock_logging,
        ):

            # Mock config
            mock_config = Mock()
            mock_config.config = {}

            # Mock autotune results
            mock_autotune.return_value = {
                "optimal_algorithm": "blake3",
                "benchmark_results": {"blake3": 0.1, "sha256": 0.2},
                "available_algorithms": ["blake3", "sha256"],
                "has_blake3": True,
                "has_xxhash": False,
            }

            # Mock hasher
            mock_hasher_instance = Mock()
            mock_hasher.return_value = (mock_hasher_instance, {})

            mock_load_config.return_value = mock_config
            mock_autoconfig.return_value = {}
            mock_logging.info = MagicMock()

            # Initialize
            loader.initialize()

            # Verify autotuning was called
            mock_autotune.assert_called_once()

            # Verify hasher was registered in container
            assert (
                loader.container.get_service("hasher") is mock_hasher_instance
            )
            assert (
                loader.container.get_service("hash_autotune_results")
                is not None
            )

    def test_hash_autotuning_fallback(self):
        """Test hash autotuning fallback on error."""
        loader = CoreLoader()

        with (
            patch("nodupe.core.loader.load_config") as mock_load_config,
            patch.object(
                loader, "_apply_platform_autoconfig"
            ) as mock_autoconfig,
            patch("nodupe.core.loader.ToolRegistry"),
            patch("nodupe.core.loader.create_tool_loader"),
            patch("nodupe.core.loader.create_tool_discovery"),
            patch("nodupe.core.loader.create_lifecycle_manager"),
            patch("nodupe.core.loader.ToolHotReload"),
            patch("nodupe.core.loader.get_connection"),
            patch(
                "nodupe.core.loader.autotune_hash_algorithm"
            ) as mock_autotune,
            patch("nodupe.core.loader.logging") as mock_logging,
        ):

            # Mock config
            mock_config = Mock()
            mock_config.config = {}

            # Mock autotune to fail
            mock_autotune.side_effect = Exception("Autotune failed")

            mock_load_config.return_value = mock_config
            mock_autoconfig.return_value = {}
            mock_logging.info = MagicMock()
            mock_logging.error = MagicMock()

            # Initialize
            loader.initialize()

            # Verify fallback was used
            mock_logging.error.assert_called_with(
                "Hash autotuning failed: Autotune failed"
            )
            assert loader.container.get_service("hasher") is not None

    def test_hash_autotuning_results_applied_to_existing_hasher(self):
        """When `autotune_hash_algorithm` returns results and no creator
        is available, the loader should store results and configure an
        existing hasher service (call set_algorithm).
        """
        loader = CoreLoader()

        # Use a fresh container so the test is isolated
        loader.container = ServiceContainer()

        # Register a mock hasher that exposes `set_algorithm`
        hasher_mock = Mock()
        hasher_mock.set_algorithm = Mock()
        loader.container.register_service("hasher", hasher_mock)

        # Patch autotune results and ensure `create_autotuned_hasher` is
        # absent so the `results` branch is exercised.
        with (
            patch("nodupe.core.loader.autotune_hash_algorithm") as mock_autotune,
            patch("nodupe.core.loader.create_autotuned_hasher", new=None),
            patch("nodupe.core.loader.logging") as mock_logging,
        ):

            mock_autotune.return_value = {"optimal_algorithm": "sha256"}

            # Invoke autotuning helper directly
            loader._perform_hash_autotuning()

            # Results should be registered and applied to the existing hasher
            assert loader.container.get_service("hash_autotune_results") == {
                "optimal_algorithm": "sha256"
            }
            hasher_mock.set_algorithm.assert_called_once_with("sha256")


class TestCoreLoaderShutdown:
    """Test CoreLoader shutdown functionality."""

    def test_shutdown(self):
        """Test shutdown functionality."""
        loader = CoreLoader()

        with (
            patch("nodupe.core.loader.load_config") as mock_load_config,
            patch.object(
                loader, "_apply_platform_autoconfig"
            ) as mock_autoconfig,
            patch("nodupe.core.loader.ToolRegistry"),
            patch("nodupe.core.loader.create_tool_loader"),
            patch("nodupe.core.loader.create_tool_discovery"),
            patch("nodupe.core.loader.create_lifecycle_manager"),
            patch("nodupe.core.loader.ToolHotReload"),
            patch("nodupe.core.loader.get_connection"),
            patch("nodupe.core.loader.logging") as mock_logging,
        ):

            # Mock config
            mock_config = Mock()
            mock_config.config = {}

            mock_load_config.return_value = mock_config
            mock_autoconfig.return_value = {}
            mock_logging.info = MagicMock()

            # Initialize
            loader.initialize()

            # Mock shutdown methods
            loader.tool_lifecycle.shutdown_all_tools = MagicMock()
            loader.hot_reload.stop = MagicMock()
            loader.database.close = MagicMock()
            loader.tool_registry.shutdown = MagicMock()

            # Shutdown
            loader.shutdown()

            # Verify shutdown sequence
            loader.tool_lifecycle.shutdown_all_tools.assert_called_once()
            loader.hot_reload.stop.assert_called_once()
            loader.database.close.assert_called_once()
            loader.tool_registry.shutdown.assert_called_once()
            assert loader.initialized is False

    def test_shutdown_not_initialized(self):
        """Test shutdown when not initialized."""
        loader = CoreLoader()

        with patch("nodupe.core.loader.logging") as mock_logging:
            mock_logging.info = MagicMock()

            # Shutdown without initialization
            loader.shutdown()

            # Should not raise error
            assert loader.initialized is False

    def test_shutdown_stops_ipc_server(self):
        """Shutdown must stop the IPC server when present."""
        loader = CoreLoader()
        loader.initialized = True

        # Small set of components we care about for this test
        loader.ipc_server = Mock()
        loader.ipc_server.stop = Mock()
        loader.tool_lifecycle = None
        loader.hot_reload = None
        loader.tool_registry = None
        loader.database = None

        # Perform shutdown
        loader.shutdown()

        loader.ipc_server.stop.assert_called_once()
        assert loader.initialized is False

    def test_shutdown_uses_log_compressor_when_available(self, tmp_path):
        """If the maintenance LogCompressor is importable, shutdown should
        call its compress_old_logs() method with the configured log_dir.
        """
        loader = CoreLoader()
        loader.initialized = True

        # Minimal environment so shutdown proceeds to the maintenance import
        loader.tool_lifecycle = None
        loader.hot_reload = None
        loader.ipc_server = None
        loader.tool_registry = None
        loader.database = None

        # Provide a config with a real temporary log dir
        loader.config = Mock()
        loader.config.config = {"log_dir": str(tmp_path)}

        # Patch the LogCompressor class in its module
        with patch("nodupe.tools.maintenance.log_compressor.LogCompressor") as mock_comp:
            mock_comp.compress_old_logs = Mock()

            loader.shutdown()

            mock_comp.compress_old_logs.assert_called_once_with(str(tmp_path))

    def test_shutdown_handles_database_close_exceptions(self):
        """If database.close() raises, shutdown should catch and continue."""
        loader = CoreLoader()
        loader.initialized = True

        # Provide a database whose close() raises
        bad_db = Mock()
        bad_db.close.side_effect = Exception("close failed")
        loader.database = bad_db

        # Ensure other components won't interfere
        loader.tool_lifecycle = None
        loader.hot_reload = None
        loader.ipc_server = None
        loader.tool_registry = None

        # Should not raise despite close() failure
        loader.shutdown()
        assert loader.initialized is False


class TestCoreLoaderSystemDetection:
    """Test CoreLoader system detection functionality."""

    def test_system_resource_detection(self):
        """Test system resource detection."""
        loader = CoreLoader()

        with (
            patch("nodupe.core.loader.multiprocessing") as mock_multiprocessing,
            patch("nodupe.core.loader.os") as mock_os,
            patch("nodupe.core.loader.psutil") as mock_psutil,
            patch("nodupe.core.loader.logging") as mock_logging,
        ):

            # Mock system resources
            mock_multiprocessing.cpu_count.return_value = 8
            mock_os.cpu_count.return_value = 8
            mock_os.environ = {}

            # Mock psutil
            mock_virtual_memory = Mock()
            mock_virtual_memory.total = 16 * 1024**3
            mock_psutil.virtual_memory.return_value = mock_virtual_memory

            mock_disk_partition = Mock()
            mock_disk_partition.mountpoint = "/"
            mock_disk_partition.device = "/dev/nvme0n1"
            mock_disk_partition.opts = ""
            mock_psutil.disk_partitions.return_value = [mock_disk_partition]

            mock_logging.warning = MagicMock()

            system_info = loader._detect_system_resources()

            assert system_info["cpu_cores"] == 8
            assert system_info["cpu_threads"] == 8
            assert system_info["ram_gb"] == 16
            assert system_info["drive_type"] == "ssd"
            assert system_info["max_workers"] == 16
            assert system_info["batch_size"] == 500

    def test_thread_restriction_detection(self):
        """Test thread restriction detection."""
        loader = CoreLoader()

        with (
            patch("nodupe.core.loader.os") as mock_os,
            patch("nodupe.core.loader.logging"),
        ):

            # Test Kubernetes detection
            mock_os.environ = {"KUBERNETES_SERVICE_HOST": "localhost"}
            system_info = {"cpu_cores": 8}

            loader._detect_thread_restrictions(system_info)

            assert system_info["thread_restrictions_detected"] is True
            assert "kubernetes" in system_info["thread_restriction_reasons"]

            # Test Docker detection
            mock_os.environ = {"DOCKER_CONTAINER": "true"}
            system_info = {"cpu_cores": 8}

            loader._detect_thread_restrictions(system_info)

            assert system_info["thread_restrictions_detected"] is True
            assert "container" in system_info["thread_restriction_reasons"]


class TestBootstrapFunction:
    """Test bootstrap function."""

    def test_bootstrap(self):
        """Test bootstrap function."""
        with (
            patch(
                "nodupe.core.loader.logging.basicConfig"
            ) as mock_basic_config,
            patch("nodupe.core.loader.CoreLoader") as mock_core_loader,
        ):

            # Mock CoreLoader
            mock_loader_instance = Mock()
            mock_loader_instance.initialize.return_value = None
            mock_core_loader.return_value = mock_loader_instance

            # Call bootstrap
            result = bootstrap()

            # Verify
            mock_basic_config.assert_called_once()
            mock_loader_instance.initialize.assert_called_once()
            assert result is mock_loader_instance


class TestCoreLoaderIntegration:
    """Test CoreLoader integration scenarios."""

    def test_complete_initialization_workflow(self):
        """Test complete initialization workflow."""
        loader = CoreLoader()

        with (
            patch("nodupe.core.loader.load_config") as mock_load_config,
            patch.object(
                loader, "_apply_platform_autoconfig"
            ) as mock_autoconfig,
            patch("nodupe.core.loader.ToolRegistry") as mock_registry,
            patch("nodupe.core.loader.create_tool_loader") as mock_loader,
            patch("nodupe.core.loader.create_tool_discovery") as mock_discovery,
            patch(
                "nodupe.core.loader.create_lifecycle_manager"
            ) as mock_lifecycle,
            patch("nodupe.core.loader.ToolHotReload") as mock_hot_reload,
            patch("nodupe.core.loader.get_connection") as mock_db,
            patch(
                "nodupe.core.loader.autotune_hash_algorithm"
            ) as mock_autotune,
            patch("nodupe.core.loader.create_autotuned_hasher") as mock_hasher,
            patch("nodupe.core.loader.logging") as mock_logging,
            patch("nodupe.core.loader.Path") as mock_path,
        ):

            # Mock config
            mock_config = Mock()
            mock_config.config = {
                "tools": {
                    "directories": ["tools"],
                    "auto_load": True,
                    "hot_reload": True,
                    "loading_order": ["core"],
                }
            }

            # Mock path
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path.return_value = mock_path_instance

            # Mock tool discovery
            mock_discovery_instance = Mock()
            mock_discovery_instance.discover_tools_in_directory.return_value = [
                Mock(name="core", path="tools/core.py")
            ]
            mock_discovery_instance.get_discovered_tool.return_value = Mock(
                name="core", path="tools/core.py"
            )
            mock_discovery_instance.get_discovered_tools.return_value = [
                Mock(name="core", path="tools/core.py")
            ]
            mock_discovery.return_value = mock_discovery_instance

            # Mock tool loader
            mock_loader_instance = Mock()
            mock_loader_instance.load_tool_from_file.return_value = Mock
            mock_loader_instance.instantiate_tool.return_value = Mock(
                name="core"
            )
            mock_loader_instance.register_loaded_tool.return_value = None
            mock_loader.return_value = mock_loader_instance

            # Mock other components
            mock_registry_instance = Mock()
            mock_registry.return_value = mock_registry_instance

            mock_lifecycle_instance = Mock()
            mock_lifecycle.return_value = mock_lifecycle_instance

            mock_hot_reload_instance = Mock()
            mock_hot_reload.return_value = mock_hot_reload_instance

            mock_db_instance = Mock()
            mock_db.return_value = mock_db_instance

            # Mock autotune
            mock_autotune.return_value = {
                "optimal_algorithm": "blake3",
                "benchmark_results": {},
                "available_algorithms": ["blake3"],
                "has_blake3": True,
                "has_xxhash": False,
            }

            # Mock hasher
            mock_hasher_instance = Mock()
            mock_hasher.return_value = (mock_hasher_instance, {})

            # Set up mocks
            mock_load_config.return_value = mock_config
            mock_autoconfig.return_value = {}
            mock_logging.info = MagicMock()
            mock_logging.error = MagicMock()

            # Initialize
            loader.initialize()

            # Verify all components were initialized
            assert loader.config is mock_config
            assert loader.container is not None
            assert loader.tool_registry is not None
            assert loader.tool_loader is not None
            assert loader.tool_discovery is not None
            assert loader.tool_lifecycle is not None
            assert loader.hot_reload is not None
            assert loader.database is mock_db_instance
            assert loader.initialized is True

            # Verify services were registered in container
            assert loader.container.get_service("config") is mock_config
            assert (
                loader.container.get_service("tool_registry")
                is mock_registry_instance
            )
            assert (
                loader.container.get_service("tool_loader")
                is mock_loader_instance
            )
            assert (
                loader.container.get_service("tool_discovery")
                is mock_discovery_instance
            )
            assert (
                loader.container.get_service("tool_lifecycle")
                is mock_lifecycle_instance
            )
            assert (
                loader.container.get_service("hot_reload")
                is mock_hot_reload_instance
            )
            assert loader.container.get_service("database") is mock_db_instance
            assert (
                loader.container.get_service("hasher") is mock_hasher_instance
            )

            # Test shutdown
            loader.shutdown()
            assert loader.initialized is False
