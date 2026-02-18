import os
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from nodupe.tools.commands.apply import ApplyTool


class DummyRepo:
    def __init__(self, db):
        self._deleted = []

    def get_duplicate_files(self):
        return []

    def get_file(self, fid):
        return None

    def delete_file(self, fid):
        self._deleted.append(fid)
        return True


def test_execute_apply_input_required():
    tool = ApplyTool()
    args = SimpleNamespace(input=None, action="list", container=object())
    assert tool.execute_apply(args) == 1


def test_execute_apply_invalid_action():
    tool = ApplyTool()
    args = SimpleNamespace(action="unknown", container=object())
    assert tool.execute_apply(args) == 1


def test_execute_apply_move_requires_destination():
    tool = ApplyTool()
    args = SimpleNamespace(action="move", destination=None, container=object())
    assert tool.execute_apply(args) == 1


def test_execute_apply_no_container_returns_error(tmp_path):
    tool = ApplyTool()
    d = tmp_path / "d"
    d.mkdir()
    args = SimpleNamespace(paths=[str(d)], action="list", container=None)
    assert tool.execute_apply(args) == 1


def test_execute_apply_no_duplicates_reports_and_returns_zero(capsys):
    tool = ApplyTool()

    class C:
        def get_service(self, name):
            return object()

    # Patch FileRepository to return no duplicates
    with patch("nodupe.tools.commands.apply.FileRepository") as FR:
        fr = Mock()
        fr.get_duplicate_files.return_value = []
        FR.return_value = fr

        args = SimpleNamespace(action="list", container=C())
        rv = tool.execute_apply(args)

    assert rv == 0
    captured = capsys.readouterr()
    assert "No items marked as duplicates" in captured.out


def test_execute_apply_list_prints_duplicates(capsys):
    tool = ApplyTool()

    class DummyRepo2:
        def __init__(self, db=None):
            pass

        def get_duplicate_files(self):
            return [
                {"id": 2, "path": "/tmp/dup.txt", "duplicate_of": 1}
            ]

        def get_file(self, fid):
            if fid == 1:
                return {"id": 1, "path": "/tmp/orig.txt"}
            return None

    class C:
        def get_service(self, name):
            return object()

    with patch("nodupe.tools.commands.apply.FileRepository", DummyRepo2):
        args = SimpleNamespace(action="list", container=C(), verbose=False)
        rv = tool.execute_apply(args)

    assert rv == 0
    out = capsys.readouterr().out
    assert "Identified Duplicates" in out
    assert "Duplicate of: /tmp/orig.txt" in out


def test_execute_apply_delete_dry_run_and_actual(tmp_path, capsys):
    # create a real file to be deleted
    fpath = tmp_path / "to_delete.txt"
    fpath.write_text("x")

    class RepoForDelete:
        def __init__(self, db):
            pass

        def get_duplicate_files(self):
            return [{"id": 10, "path": str(fpath), "duplicate_of": 1}]

        def delete_file(self, fid):
            self.deleted = fid
            return True

    class C:
        def get_service(self, name):
            return object()

    tool = ApplyTool()

    # Dry-run: file should remain and no delete_file called
    with patch("nodupe.tools.commands.apply.FileRepository", RepoForDelete):
        args = SimpleNamespace(action="delete", dry_run=True, container=C(), destination=None, verbose=True)
        rv = tool.execute_apply(args)
    assert rv == 0
    assert fpath.exists()

    # Actual delete: Filesystem.remove_file will remove the file
    with patch("nodupe.tools.commands.apply.FileRepository", RepoForDelete):
        args = SimpleNamespace(action="delete", dry_run=False, container=C(), destination=None, verbose=True)
        rv = tool.execute_apply(args)

    assert rv == 0
    assert not fpath.exists()
