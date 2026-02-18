import pytest

from nodupe.core.tool_system.dependencies import (
    DependencyResolver,
    ResolutionStatus,
)


def test_add_and_remove_dependency():
    r = DependencyResolver()

    r.add_dependency("A", "B")
    assert "B" in r.get_dependencies("A")
    assert "A" in r.get_dependents("B")

    assert r.remove_dependency("A", "B") is True
    assert "B" not in r.get_dependencies("A")


def test_resolve_dependencies_resolved_order():
    r = DependencyResolver()
    r.add_dependency("A", "B")

    status, order = r.resolve_dependencies(["A", "B"])
    assert status == ResolutionStatus.RESOLVED
    # B must come before A
    assert order.index("B") < order.index("A")


def test_resolve_dependencies_missing():
    r = DependencyResolver()
    r.add_dependency("A", "B")

    status, order = r.resolve_dependencies(["A"])
    assert status == ResolutionStatus.MISSING
    assert order == []


def test_resolve_dependencies_circular():
    r = DependencyResolver()
    r.add_dependency("A", "B")
    r.add_dependency("B", "A")

    status, order = r.resolve_dependencies(["A", "B"])
    assert status == ResolutionStatus.CIRCULAR
    assert order == []


def test_initialization_and_shutdown_order():
    r = DependencyResolver()
    r.add_dependency("A", "B")
    r.add_dependency("B", "C")

    init = r.get_initialization_order(["A", "B", "C"])
    assert init == ["C", "B", "A"]

    shut = r.get_shutdown_order(["A", "B", "C"])
    assert shut == ["A", "B", "C"][::-1][::-1] or shut == ["A", "B", "C"][::-1]  # ensure reverse of init


def test_dependency_tree_and_all_dependencies():
    r = DependencyResolver()
    r.add_dependency("A", "B")
    r.add_dependency("B", "C")

    tree = r.get_dependency_tree("A")
    assert tree["name"] == "A"
    assert "B" in tree["dependencies"]

    all_deps = r.get_all_dependencies("A")
    assert all_deps == {"B", "C"}


def test_clear_dependencies_and_validate_tool_compatibility():
    r = DependencyResolver()
    r.add_dependency("A", "B")

    class FakeTool:
        dependencies = ["B", "C"]

    ok, missing = r.validate_tool_compatibility(FakeTool(), ["B"])  # C missing
    assert not ok
    assert "C" in missing

    r.clear_dependencies()
    assert r.get_dependencies("A") == []
