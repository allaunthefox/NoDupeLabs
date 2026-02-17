import pytest
from unittest.mock import Mock, MagicMock, patch

from nodupe.core.loader import CoreLoader


def test_load_single_tool_handles_missing_tool_class():
    loader = CoreLoader()

    # inject a mock tool_loader that returns None for load_tool_from_file
    loader.tool_loader = Mock()
    loader.tool_loader.load_tool_from_file.return_value = None
    loader.tool_loader.instantiate_tool.return_value = None
    loader.hot_reload = Mock()

    fake_tool_info = Mock()
    fake_tool_info.name = "no_tool"
    fake_tool_info.path = "/nonexistent/path.py"

    # Should not raise and should simply skip
    loader._load_single_tool(fake_tool_info)
    loader.tool_loader.load_tool_from_file.assert_called()


def test_load_single_tool_instantiation_failure_logged():
    loader = CoreLoader()

    # tool_loader.load_tool_from_file returns a class-like object
    loader.tool_loader = Mock()
    loader.tool_loader.load_tool_from_file.return_value = object
    # instantiate_tool raises
    loader.tool_loader.instantiate_tool.side_effect = Exception("boom")
    loader.hot_reload = Mock()

    fake_tool_info = Mock()
    fake_tool_info.name = "broken"
    fake_tool_info.path = "tools/broken.py"

    with patch.object(loader, "logger") as mock_logger:
        mock_logger.exception = MagicMock()
        # Should not propagate exception
        loader._load_single_tool(fake_tool_info)
        mock_logger.exception.assert_called()


def test_initialize_skips_database_when_get_connection_fails():
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
        mock_load_config.return_value = mock_config
        mock_autoconfig.return_value = {}

        # Simulate get_connection raising during initialization
        mock_db.side_effect = Exception("db fail")

        # Should not raise from initialize
        loader.initialize()

        # database attribute should remain None (initialization skipped)
        assert loader.database is None


def test_load_single_tool_register_failure_is_logged():
    """If register_loaded_tool() raises, the loader should catch and
    log the exception without propagating it.
    """
    loader = CoreLoader()

    # tool_loader returns a class and an instance but register() fails
    loader.tool_loader = Mock()
    loader.tool_loader.load_tool_from_file.return_value = object
    inst = Mock()
    inst.name = "example"
    loader.tool_loader.instantiate_tool.return_value = inst
    loader.tool_loader.register_loaded_tool.side_effect = Exception("register failed")

    loader.hot_reload = Mock()

    fake_tool_info = Mock()
    fake_tool_info.name = "example"
    fake_tool_info.path = "tools/example.py"

    with patch.object(loader, "logger") as mock_logger:
        mock_logger.exception = MagicMock()

        # Should not raise
        loader._load_single_tool(fake_tool_info)

        # Exception should have been logged
        mock_logger.exception.assert_called_once()


def test_discover_and_load_tools_no_paths_exist_is_noop():
    """When neither configured tool dirs nor standard locations exist,
    discovery should be a no-op (no calls to the discovery backend).
    """
    loader = CoreLoader()

    # Provide a config that points to a non-existent directory
    loader.config = Mock()
    loader.config.config = {"tools": {"directories": ["nonexistent_dir"], "auto_load": True}}

    # Patch Path so all resolves exist() -> False (including standard paths)
    with patch("nodupe.core.loader.Path") as mock_path:
        def path_side_effect(arg):
            m = Mock()
            m.resolve.return_value = m
            m.exists.return_value = False
            return m

        mock_path.side_effect = path_side_effect

        # Provide a mock discovery backend so we can assert it wasn't invoked
        loader.tool_discovery = Mock()

        # Exercise
        loader._discover_and_load_tools()

        # No discovery calls should have been made
        loader.tool_discovery.discover_tools_in_directory.assert_not_called()


def test_platform_autoconfig_and_resource_detection(monkeypatch):
    loader = CoreLoader()

    platform_cfg = loader._apply_platform_autoconfig()
    # Basic keys should always be present
    assert "db_path" in platform_cfg
    assert "log_dir" in platform_cfg
    assert "tools" in platform_cfg
    assert "cpu_cores" in platform_cfg
    assert "drive_type" in platform_cfg

    # _detect_system_resources should include derived keys
    sysinfo = loader._detect_system_resources()
    assert "cpu_cores" in sysinfo
    assert "cpu_threads" in sysinfo
    assert "max_workers" in sysinfo
    assert sysinfo["max_workers"] >= 1
    assert sysinfo["batch_size"] == 500

    # thread restriction detection responds to env vars
    info = {}
    monkeypatch.setenv("KUBERNETES_SERVICE_HOST", "1")
    monkeypatch.setenv("CONTAINER", "1")
    loader._detect_thread_restrictions(info)
    assert info["thread_restrictions_detected"] is True
    assert "kubernetes" in info["thread_restriction_reasons"] or "container" in info["thread_restriction_reasons"]


def test_perform_hash_autotuning_branches(monkeypatch):
    from nodupe.core.container import ServiceContainer

    loader = CoreLoader()
    loader.container = ServiceContainer()

    # Case A: create_autotuned_hasher is available and returns a hasher
    class DummyHasher:
        def __init__(self):
            self._alg = "sha256"

        def set_algorithm(self, a):
            self._alg = a

    def fake_create():
        return DummyHasher(), {"optimal_algorithm": "sha256", "benchmark_results": {"sha256": 0.001}}

    monkeypatch.setattr("nodupe.core.loader.create_autotuned_hasher", fake_create)

    loader._perform_hash_autotuning()
    assert isinstance(loader.container.get_service("hasher"), DummyHasher)
    assert loader.container.get_service("hash_autotune_results")["optimal_algorithm"] == "sha256"

    # Case B: autotune results available but create_autotuned_hasher raises
    monkeypatch.setattr("nodupe.core.loader.create_autotuned_hasher", None)

    def fake_autotune():
        return {"optimal_algorithm": "sha256", "benchmark_results": {"sha256": 0.002}}

    monkeypatch.setattr("nodupe.core.loader.autotune_hash_algorithm", fake_autotune)

    # register a hasher that records set_algorithm calls
    class Recorder:
        def __init__(self):
            self.called_with = None

        def set_algorithm(self, algo):
            self.called_with = algo

    rec = Recorder()
    loader.container.register_service("hasher", rec)

    loader._perform_hash_autotuning()
    assert loader.container.get_service("hash_autotune_results")["optimal_algorithm"] == "sha256"
    assert rec.called_with == "sha256"

    # Case C: neither autotune function present -> fallback FileHasher is registered
    monkeypatch.setattr("nodupe.core.loader.autotune_hash_algorithm", None)
    from nodupe.tools.hashing.hasher_logic import FileHasher

    # Clear container and run again
    loader.container = ServiceContainer()
    loader._perform_hash_autotuning()
    hasher = loader.container.get_service("hasher")
    assert isinstance(hasher, FileHasher)
    assert isinstance(loader.container.get_service("hash_autotune_results"), dict)


def test_shutdown_calls_components_and_compress_logs(monkeypatch):
    loader = CoreLoader()
    loader.initialized = True

    # Create mocks for components
    loader.tool_lifecycle = Mock()
    loader.tool_lifecycle.shutdown_all_tools = Mock()

    loader.hot_reload = Mock()
    loader.hot_reload.stop = Mock()

    loader.ipc_server = Mock()
    loader.ipc_server.stop = Mock()

    loader.tool_registry = Mock()
    loader.tool_registry.shutdown = Mock()

    loader.database = Mock()
    loader.database.close = Mock()

    # Provide a config with a log_dir so compressor will be invoked
    loader.config = Mock()
    loader.config.config = {"log_dir": "logs"}

    # Patch LogCompressor.compress_old_logs to avoid filesystem activity
    monkeypatch.setattr(
        "nodupe.core.loader.LogCompressor",
        Mock(compress_old_logs=Mock()),
        raising=False,
    )

    loader.shutdown()

    # Verify that component shutdown methods were called
    loader.tool_lifecycle.shutdown_all_tools.assert_called()
    loader.hot_reload.stop.assert_called()
    loader.ipc_server.stop.assert_called()
    loader.tool_registry.shutdown.assert_called()
    loader.database.close.assert_called()
    assert loader.initialized is False
