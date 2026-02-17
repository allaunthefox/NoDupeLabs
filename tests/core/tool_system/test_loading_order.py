import pytest

from nodupe.core.tool_system.loading_order import (
    ToolLoadingOrder,
    reset_tool_loading_order,
    ToolLoadOrder,
)


def test_get_load_sequence_includes_required_deps():
    order = ToolLoadingOrder()

    seq = order.get_load_sequence(["container"])

    # container depends on core and deps; ensure container comes after them
    assert "container" in seq
    assert "core" in seq
    assert "deps" in seq
    assert seq.index("container") > seq.index("core")
    assert seq.index("container") > seq.index("deps")


def test_validate_dependencies_reports_missing():
    order = ToolLoadingOrder()

    # database requires 'security' among others; omit it from available set
    valid, missing = order.validate_dependencies(
        "database", {"core", "config", "limits"}
    )
    assert not valid
    assert "security" in missing


def test_get_dependency_chain_excludes_self():
    order = ToolLoadingOrder()

    chain = order.get_dependency_chain("loader")
    # loader should not appear in its own dependency chain
    assert "loader" not in chain
    # core and discovery are part of loader's dependencies (transitively or directly)
    assert any(x in chain for x in ("core", "discovery", "registry"))


def test_validate_load_sequence_detects_missing_deps():
    order = ToolLoadingOrder()

    ok, missing, circular = order.validate_load_sequence(["database"])
    assert not ok
    assert any("requires" in m for m in missing)


def test_get_safe_load_sequence_excludes_unresolvable():
    order = ToolLoadingOrder()

    # Register a synthetic tool that requires a dependency not present in
    # the registry; the safe load sequence should exclude that tool.
    from nodupe.core.tool_system.loading_order import ToolLoadInfo, ToolLoadOrder

    fake = ToolLoadInfo(
        name="fake_tool",
        load_order=ToolLoadOrder.SPECIALIZED_TOOLS,
        required_dependencies=["missing_dep"],
        optional_dependencies=[],
    )
    order.register_tool(fake)

    safe_seq, excluded = order.get_safe_load_sequence(["fake_tool"])

    assert "fake_tool" not in safe_seq
    assert any("missing_dep" in e for e in excluded)


def test_get_load_priorities_sorted():
    order = ToolLoadingOrder()

    priorities = order.get_load_priorities(["core", "container", "database"])
    # Ensure we received priorities for the requested tools
    names = [p[0] for p in priorities]
    assert set(names) <= {"core", "container", "database"}

    # Check list is sorted descending by priority value
    values = [p[1] for p in priorities]
    assert values == sorted(values, reverse=True)


def test_register_and_notify_callbacks_and_exception_handling(monkeypatch):
    order = ToolLoadingOrder()

    called = []

    def cb(name):
        called.append(name)

    order.register_load_callback("core", cb)
    order.notify_tool_loaded("core")
    assert called == ["core"]

    # callback that raises should be swallowed but logged
    def bad_cb(name):
        raise RuntimeError("boom")

    order.register_load_callback("core", bad_cb)

    logged = {"called": False}

    def fake_exc(msg):
        logged["called"] = True

    monkeypatch.setattr("nodupe.core.tool_system.loading_order.logger.exception", lambda msg: fake_exc(msg))

    order.notify_tool_loaded("core")
    assert logged["called"] is True


def test_get_tool_statistics_contains_expected_keys():
    order = ToolLoadingOrder()
    stats = order.get_tool_statistics()

    assert "total_tools" in stats
    assert "tools_by_order" in stats
    assert "critical_tools" in stats
    assert "dependency_counts" in stats
    assert "core" in stats["critical_tools"]
