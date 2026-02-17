from types import SimpleNamespace
from unittest.mock import Mock

from nodupe.core.loader import CoreLoader


def test_load_single_tool_success_registers_and_watches():
    loader = CoreLoader()

    # prepare mocks
    loader.tool_loader = Mock()
    tool_class = object
    tool_instance = Mock()
    tool_instance.name = "example"
    # tool instance indicates ISO accessibility by exposing method
    tool_instance.get_ipc_socket_documentation = lambda: "doc"

    loader.tool_loader.load_tool_from_file.return_value = tool_class
    loader.tool_loader.instantiate_tool.return_value = tool_instance
    loader.tool_loader.register_loaded_tool = Mock()

    loader.hot_reload = Mock()
    loader.logger = Mock()

    fake_tool_info = SimpleNamespace(name="example", path="tools/example.py")

    # exercise
    loader._load_single_tool(fake_tool_info)

    loader.tool_loader.load_tool_from_file.assert_called_with(fake_tool_info.path)
    loader.tool_loader.instantiate_tool.assert_called_with(tool_class)
    loader.tool_loader.register_loaded_tool.assert_called_with(tool_instance, fake_tool_info.path)
    loader.hot_reload.watch_tool.assert_called_with("example", fake_tool_info.path)
    # ISO message should be logged via logger.info
    assert loader.logger.info.called


def test_discover_and_load_tools_invokes_discovery_and_loads_each_tool(tmp_path):
    loader = CoreLoader()

    # ensure a real `tools` directory exists for discovery path check
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()

    # fake config pointing to our temp tools dir
    loader.config = SimpleNamespace(config={"tools": {"directories": [str(tools_dir)]}})

    # fake discovery returns two tool infos
    ti1 = SimpleNamespace(name="t1", path=str(tools_dir / "t1.py"))
    ti2 = SimpleNamespace(name="t2", path=str(tools_dir / "t2.py"))

    loader.tool_discovery = Mock()
    loader.tool_discovery.discover_tools_in_directory.return_value = [ti1, ti2]

    loader.tool_loader = Mock()
    loader.tool_loader.load_tool_from_file.return_value = object
    loader.tool_loader.instantiate_tool.return_value = Mock()
    loader.tool_loader.register_loaded_tool = Mock()

    loader.hot_reload = Mock()

    # exercise
    loader._discover_and_load_tools()

    # discovery called for our tools_dir
    loader.tool_discovery.discover_tools_in_directory.assert_called()
    # loader invoked for each returned tool
    assert loader.tool_loader.instantiate_tool.call_count == 2
    assert loader.tool_loader.register_loaded_tool.call_count == 2
    assert loader.hot_reload.watch_tool.call_count == 2
