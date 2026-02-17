import pytest

from nodupe.core.tool_system.loading_order import (
    ToolLoadInfo,
    ToolLoadOrder,
    ToolLoadingOrder,
    get_tool_loading_order,
    reset_tool_loading_order,
)


def test_default_tools_registered_and_statistics():
    reset_tool_loading_order()
    ordering = get_tool_loading_order()

    stats = ordering.get_tool_statistics()
    assert stats["total_tools"] > 0
    assert "CORE_INFRASTRUCTURE" in stats["tools_by_order"]
    assert isinstance(stats["critical_tools"], list)
    # core should be critical and present
    assert "core" in stats["critical_tools"]


def test_get_tools_for_order_and_tool_info():
    reset_tool_loading_order()
    ordering = get_tool_loading_order()

    core_tools = ordering.get_tools_for_order(ToolLoadOrder.CORE_INFRASTRUCTURE)
    assert "core" in core_tools

    info = ordering.get_tool_info("core")
    assert info is not None
    assert info.name == "core"
    assert ordering.is_critical("core") is True


def test_validate_dependencies_and_get_dependency_chain():
    reset_tool_loading_order()
    ordering = get_tool_loading_order()

    # container requires core and deps
    valid, missing = ordering.validate_dependencies("container", {"core", "deps"})
    assert valid is True and missing == []

    valid, missing = ordering.validate_dependencies("container", {"core"})
    assert valid is False and "deps" in missing

    chain = ordering.get_dependency_chain("container")
    # container depends on core and deps (order-insensitive but should include both)
    assert "core" in chain and "deps" in chain


def test_get_load_sequence_and_circular_detection():
    reset_tool_loading_order()
    ordering = get_tool_loading_order()

    seq = ordering.get_load_sequence(["core", "deps", "container"])
    # container must come after its dependencies
    assert seq.index("core") < seq.index("container")
    assert seq.index("deps") < seq.index("container")

    # introduce a circular dependency between two test tools
    t1 = ToolLoadInfo(name="t1", load_order=ToolLoadOrder.SYSTEM_UTILITIES, required_dependencies=["t2"], optional_dependencies=[])
    t2 = ToolLoadInfo(name="t2", load_order=ToolLoadOrder.SYSTEM_UTILITIES, required_dependencies=["t1"], optional_dependencies=[])

    ordering.register_tool(t1)
    ordering.register_tool(t2)

    with pytest.raises(ValueError):
        ordering.get_load_sequence(["t1", "t2"])


def test_validate_load_sequence_and_safe_sequence_exclusion():
    reset_tool_loading_order()
    ordering = get_tool_loading_order()

    # validate_load_sequence should report missing deps when called only with container
    valid, missing, circular = ordering.validate_load_sequence(["container"])  # missing core/deps
    assert not valid
    assert any("requires" in m for m in missing)

    # safe sequence for container+core should include container (dependencies are added recursively)
    safe_sequence, excluded = ordering.get_safe_load_sequence(["container", "core"])
    assert "container" in safe_sequence
    assert excluded == []

    # registering a tool with an unknown dependency causes it to be excluded
    bad = ToolLoadInfo(name="bad_tool", load_order=ToolLoadOrder.SYSTEM_UTILITIES, required_dependencies=["no_such_dep"], optional_dependencies=[])
    ordering.register_tool(bad)
    safe_sequence2, excluded2 = ordering.get_safe_load_sequence(["bad_tool", "core"])
    assert any("bad_tool" in e for e in excluded2)


def test_fallback_sequence_and_priorities():
    reset_tool_loading_order()
    ordering = get_tool_loading_order()

    # fallback used when unknown tool triggers ValueError in get_load_sequence
    fallback = ordering._fallback_load_sequence(["unknown_a", "core"])
    assert "core" in fallback

    priorities = ordering.get_load_priorities(["core", "deps", "container"])
    # priorities should be sorted and include tuples
    assert all(isinstance(p, tuple) and len(p) == 2 for p in priorities)
    names = [p[0] for p in priorities]
    assert "core" in names


def test_register_and_notify_callbacks(capfd):
    reset_tool_loading_order()
    ordering = get_tool_loading_order()

    called = []

    def cb(name):
        called.append(name)

    ordering.register_load_callback("core", cb)
    ordering.notify_tool_loaded("core")

    assert called == ["core"]


def test_failure_impact_and_should_continue():
    reset_tool_loading_order()
    ordering = get_tool_loading_order()

    # If database fails, tools depending on it should be reported
    fails = ordering.get_failure_impact_analysis("database", ordering.get_tools_for_order(ToolLoadOrder.SPECIALIZED_TOOLS))
    # impact keys should include the failed tool when dependencies exist
    assert isinstance(fails, dict)

    # critical tool stops loading
    cont, reason = ordering.should_continue_loading("core", ["core"])
    assert cont is False
    assert "stopping" in reason

    # non-critical tool does not stop loading
    cont, reason = ordering.should_continue_loading("limits", ["limits"])
    assert cont is True


def test_get_tool_description_and_stats_consistency():
    reset_tool_loading_order()
    ordering = get_tool_loading_order()

    desc = ordering.get_tool_description("core")
    assert "Core" in desc or "core" in desc.lower()

    stats = ordering.get_tool_statistics()
    # the total_tools should equal sum of counts across orders
    total_by_order = sum(stats["tools_by_order"].values())
    assert total_by_order == stats["total_tools"]
