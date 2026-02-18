import pytest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from nodupe.core.loader import CoreLoader


class DummyContainer:
    def __init__(self):
        self.services = {}

    def register_service(self, name, svc):
        self.services[name] = svc

    def get_service(self, name):
        return self.services.get(name)


def _make_base_patches():
    """Helper to patch commonly-used loader dependencies."""
    patches = {
        'load_config': patch('nodupe.core.loader.load_config'),
        'ToolRegistry': patch('nodupe.core.loader.ToolRegistry'),
        'create_tool_loader': patch('nodupe.core.loader.create_tool_loader'),
        'create_tool_discovery': patch('nodupe.core.loader.create_tool_discovery'),
        'create_lifecycle_manager': patch('nodupe.core.loader.create_lifecycle_manager'),
        'ToolHotReload': patch('nodupe.core.loader.ToolHotReload'),
        'ToolIPCServer': patch('nodupe.core.loader.ToolIPCServer'),
        'get_connection': patch('nodupe.core.loader.get_connection'),
        'global_container': patch('nodupe.core.loader.global_container', new=DummyContainer()),
    }
    return patches


def test_initialize_registers_services_and_runs_lifecycle_and_autotune():
    patches = _make_base_patches()
    with (
        patches['load_config'] as mock_load_config,
        patches['ToolRegistry'] as MockRegistryClass,
        patches['create_tool_loader'] as mock_create_loader,
        patches['create_tool_discovery'] as mock_create_discovery,
        patches['create_lifecycle_manager'] as mock_create_lifecycle,
        patches['ToolHotReload'] as MockHotReloadClass,
        patches['ToolIPCServer'] as MockIPCServerClass,
        patches['get_connection'] as mock_get_conn,
        patches['global_container'] as dummy_container,
        patch.object(CoreLoader, '_perform_hash_autotuning') as mock_autotune,
    ):
        # config with auto_load True and explicit db_path
        mock_cfg = SimpleNamespace(config={'tools': {'auto_load': True}, 'db_path': 'output/test.db'})
        mock_load_config.return_value = mock_cfg

        registry_mock = Mock()
        MockRegistryClass.return_value = registry_mock

        tool_loader_mock = Mock()
        mock_create_loader.return_value = tool_loader_mock

        discovery_mock = Mock()
        discovery_mock.discover_tools_in_directory.return_value = []
        mock_create_discovery.return_value = discovery_mock

        lifecycle_mock = Mock()
        mock_create_lifecycle.return_value = lifecycle_mock

        hot_reload_inst = Mock()
        MockHotReloadClass.return_value = hot_reload_inst

        ipc_inst = Mock()
        MockIPCServerClass.return_value = ipc_inst

        db_mock = Mock()
        db_mock.initialize_database = Mock()
        mock_get_conn.return_value = db_mock

        loader = CoreLoader()
        loader.initialize()

        # container got populated
        assert dummy_container.services['config'] is mock_cfg
        assert dummy_container.services['tool_registry'] is registry_mock
        assert dummy_container.services['tool_loader'] is tool_loader_mock
        assert dummy_container.services['tool_discovery'] is discovery_mock
        assert dummy_container.services['tool_lifecycle'] is lifecycle_mock
        assert dummy_container.services['hot_reload'] is hot_reload_inst
        assert dummy_container.services['ipc_server'] is ipc_inst
        assert dummy_container.services['database'] is db_mock

        # lifecycle initialization and autotune executed
        lifecycle_mock.initialize_all_tools.assert_called()
        mock_autotune.assert_called_once()

        # starts were called exactly once
        hot_reload_inst.start.assert_called_once()
        ipc_inst.start.assert_called_once()
        db_mock.initialize_database.assert_called_once()


def test_initialize_respects_auto_load_flag():
    patches = _make_base_patches()
    with (
        patches['load_config'] as mock_load_config,
        patches['ToolRegistry'] as MockRegistryClass,
        patches['create_tool_loader'] as mock_create_loader,
        patches['create_tool_discovery'] as mock_create_discovery,
        patches['create_lifecycle_manager'] as mock_create_lifecycle,
        patches['ToolHotReload'] as MockHotReloadClass,
        patches['ToolIPCServer'] as MockIPCServerClass,
        patches['get_connection'] as mock_get_conn,
        patches['global_container'] as dummy_container,
        patch.object(CoreLoader, '_discover_and_load_tools') as mock_discover,
    ):
        # auto_load disabled in config
        mock_cfg = SimpleNamespace(config={'tools': {'auto_load': False}})
        mock_load_config.return_value = mock_cfg

        # basic stubs
        MockRegistryClass.return_value = Mock()
        mock_create_loader.return_value = Mock()
        discovery_mock = Mock()
        discovery_mock.discover_tools_in_directory.return_value = []
        mock_create_discovery.return_value = discovery_mock
        mock_create_lifecycle.return_value = Mock()
        MockHotReloadClass.return_value = Mock()
        MockIPCServerClass.return_value = Mock()
        mock_get_conn.side_effect = Exception('db not configured')

        loader = CoreLoader()
        loader.initialize()

        # discover_and_load_tools should NOT be called
        mock_discover.assert_not_called()


def test_initialize_is_idempotent():
    patches = _make_base_patches()
    with (
        patches['load_config'] as mock_load_config,
        patches['ToolRegistry'] as MockRegistryClass,
        patches['create_tool_loader'] as mock_create_loader,
        patches['create_tool_discovery'] as mock_create_discovery,
        patches['create_lifecycle_manager'] as mock_create_lifecycle,
        patches['ToolHotReload'] as MockHotReloadClass,
        patches['ToolIPCServer'] as MockIPCServerClass,
        patches['get_connection'] as mock_get_conn,
        patches['global_container'] as dummy_container,
    ):
        mock_cfg = SimpleNamespace(config={'tools': {'auto_load': True}})
        mock_load_config.return_value = mock_cfg

        MockRegistryClass.return_value = Mock()
        mock_create_loader.return_value = Mock()
        discovery_mock = Mock()
        discovery_mock.discover_tools_in_directory.return_value = []
        mock_create_discovery.return_value = discovery_mock
        mock_create_lifecycle.return_value = Mock()
        MockHotReloadClass.return_value = Mock()
        MockIPCServerClass.return_value = Mock()
        mock_get_conn.side_effect = Exception('no db')

        loader = CoreLoader()
        loader.initialize()
        # second call should be a no-op and not re-call constructors
        loader.initialize()

        assert mock_create_loader.call_count == 1
        assert MockHotReloadClass.call_count == 1


def test_shutdown_closes_database_and_stops_services_and_handles_errors():
    loader = CoreLoader()
    loader.initialized = True

    lifecycle_mock = Mock()
    hot_reload_mock = Mock()
    ipc_mock = Mock()
    registry_mock = Mock()
    db_mock = Mock()

    loader.tool_lifecycle = lifecycle_mock
    loader.hot_reload = hot_reload_mock
    loader.ipc_server = ipc_mock
    loader.tool_registry = registry_mock
    loader.database = db_mock

    # normal shutdown path
    loader.shutdown()

    lifecycle_mock.shutdown_all_tools.assert_called_once()
    hot_reload_mock.stop.assert_called_once()
    ipc_mock.stop.assert_called_once()
    registry_mock.shutdown.assert_called_once()
    db_mock.close.assert_called_once()
    assert loader.initialized is False

    # ensure exceptions from db.close are swallowed and shutdown completes
    loader.initialized = True
    db_mock.close.side_effect = Exception('boom')
    # should not raise
    loader.shutdown()
    assert loader.initialized is False
