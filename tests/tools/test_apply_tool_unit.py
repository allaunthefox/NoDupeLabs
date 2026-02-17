import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.commands.apply import ApplyTool


def make_args(action, container=None, **kw):
    ns = argparse.Namespace()
    ns.action = action
    ns.destination = kw.get("destination")
    ns.dry_run = kw.get("dry_run", False)
    ns.verbose = kw.get("verbose", False)
    # Only set 'input' attribute when explicitly provided in tests. The
    # production CLI may or may not include this attribute and the tool
    # treats a present-but-None value as a missing required input.
    if "input" in kw:
        ns.input = kw.get("input")
    ns.container = container
    return ns


def test_execute_apply_requires_container():
    t = ApplyTool()
    args = make_args("list", container=None)
    assert t.execute_apply(args) == 1


def test_execute_apply_no_duplicates_returns_zero():
    mock_container = MagicMock()
    mock_db = MagicMock()
    mock_container.get_service.return_value = mock_db

    # FileRepository.get_duplicate_files -> empty
    with patch("nodupe.tools.commands.apply.FileRepository") as mock_repo_cls:
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_duplicate_files.return_value = []

        t = ApplyTool()
        args = make_args("list", container=mock_container)

        rc = t.execute_apply(args)
        assert rc == 0
        mock_repo.get_duplicate_files.assert_called_once()


def test_execute_apply_list_outputs_duplicates(monkeypatch, tmp_path):
    mock_container = MagicMock()
    mock_db = MagicMock()
    mock_container.get_service.return_value = mock_db

    # Build fake duplicate entries
    dup = {"id": 9, "path": str(tmp_path / "dup.txt"), "duplicate_of": 1}
    orig = {"id": 1, "path": str(tmp_path / "orig.txt")}

    with patch("nodupe.tools.commands.apply.FileRepository") as mock_repo_cls:
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_duplicate_files.return_value = [dup]
        mock_repo.get_file.return_value = orig

        t = ApplyTool()
        args = make_args("list", container=mock_container)

        rc = t.execute_apply(args)
        assert rc == 0
        mock_repo.get_duplicate_files.assert_called_once()
        mock_repo.get_file.assert_called_with(1)


def test_execute_apply_delete_dry_run_and_real(tmp_path):
    # Prepare a real temporary file to exercise path.exists branch
    file_path = tmp_path / "to_delete.txt"
    file_path.write_text("x")

    mock_container = MagicMock()
    mock_db = MagicMock()
    mock_container.get_service.return_value = mock_db

    dup = {"id": 5, "path": str(file_path), "duplicate_of": 2}

    with patch("nodupe.tools.commands.apply.FileRepository") as mock_repo_cls:
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_duplicate_files.return_value = [dup]

        # Dry-run: Filesystem.remove_file should NOT be called
        with patch("nodupe.tools.commands.apply.Filesystem") as mock_fs:
            t = ApplyTool()
            args = make_args("delete", container=mock_container, dry_run=True)

            rc = t.execute_apply(args)
            assert rc == 0
            mock_fs.remove_file.assert_not_called()

        # Real delete: Filesystem.remove_file should be called
        with patch("nodupe.tools.commands.apply.Filesystem") as mock_fs:
            mock_fs.remove_file.return_value = None
            mock_repo.delete_file.return_value = None

            t2 = ApplyTool()
            args2 = make_args("delete", container=mock_container, dry_run=False)

            rc2 = t2.execute_apply(args2)
            assert rc2 == 0
            mock_fs.remove_file.assert_called()
            mock_repo.delete_file.assert_called_with(5)
