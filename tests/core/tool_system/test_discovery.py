import ast
from pathlib import Path

import pytest

from nodupe.core.tool_system.discovery import (
    create_tool_discovery,
    ToolDiscovery,
)


def test_discover_valid_tool_file(tmp_path):
    tdir = tmp_path
    tool_file = tdir / "mytool.py"
    tool_file.write_text(
        'name = "mytool"\n__version__ = "0.1.2"\ndependencies = ["core", "database"]\nimport os\ndef foo():\n    return True\n'
    )

    disc = create_tool_discovery()
    found = disc.discover_tools_in_directory(tdir)

    assert len(found) == 1
    ti = found[0]
    assert ti.name == "mytool"
    assert ti.version == "0.1.2"
    assert "core" in ti.dependencies


def test_discover_ignores_init_py(tmp_path):
    tdir = tmp_path
    (tdir / "__init__.py").write_text("# package init")
    (tdir / "tool_a.py").write_text("name = 'tool_a'\nimport sys")

    disc = ToolDiscovery()
    found = disc.discover_tools_in_directory(tdir)

    # should discover only tool_a.py and ignore __init__.py
    assert any(t.name == "tool_a" for t in found)
    assert not any(t.name == "__init__" for t in found)


def test_find_tool_by_name_search_directories(tmp_path):
    tdir = tmp_path
    (tdir / "searchme.py").write_text("name = 'searchme'\nimport os")

    disc = ToolDiscovery()
    ti = disc.find_tool_by_name("searchme", [tdir])

    assert ti is not None
    assert ti.name == "searchme"


def test_validate_tool_file_checks(tmp_path):
    tdir = tmp_path

    zero = tdir / "zero.py"
    zero.write_text("")

    bad = tdir / "bad.py"
    bad.write_text("def broken(:\n")

    good = tdir / "good.py"
    good.write_text("name = 'good'\nimport os\n")

    disc = ToolDiscovery()

    assert not disc.validate_tool_file(zero)
    assert not disc.validate_tool_file(bad)
    assert disc.validate_tool_file(good)


def test_parse_metadata_dependencies_and_capabilities(tmp_path):
    tdir = tmp_path
    f = tdir / "meta.py"
    f.write_text(
        'name = "meta"\n__version__ = "2.0"\ndependencies = ["a", "b"]\ncapabilities = {"commands": ["c"]}\nimport os'
    )

    disc = ToolDiscovery()
    ti = disc._extract_tool_info(f)

    assert ti is not None
    assert ti.name == "meta"
    assert ti.version == "2.0"
    assert "a" in ti.dependencies
    assert ti.capabilities.get("commands") == ["c"]
