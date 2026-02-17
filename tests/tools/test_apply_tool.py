from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from nodupe.tools.commands.apply import ApplyTool


def test_execute_apply_invalid_action_returns_error():
    tool = ApplyTool()
    args = SimpleNamespace(action="invalid", container=Mock())

    rc = tool.execute_apply(args)
    assert rc == 1


def test_execute_apply_no_container_returns_error():
    tool = ApplyTool()
    args = SimpleNamespace(action="list", container=None)

    rc = tool.execute_apply(args)
    assert rc == 1


def test_execute_apply_list_no_duplicates(capfd):
    tool = ApplyTool()
    fake_container = Mock()

    with patch("nodupe.tools.commands.apply.FileRepository") as mock_repo_cls:
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_duplicate_files.return_value = []

        args = SimpleNamespace(action="list", container=fake_container)
        rc = tool.execute_apply(args)

        assert rc == 0
        captured = capfd.readouterr()
        assert "No items marked as duplicates" in captured.out


def test_execute_apply_delete_dry_run(tmp_path, capfd):
    tool = ApplyTool()

    # create a temporary file to represent a duplicate
    f = tmp_path / "dup.txt"
    f.write_text("hello")

    duplicate_entry = {"id": 7, "path": str(f), "duplicate_of": 1}

    fake_container = Mock()

    with patch("nodupe.tools.commands.apply.FileRepository") as mock_repo_cls, patch(
        "nodupe.tools.commands.apply.Filesystem"
    ) as mock_fs:
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_duplicate_files.return_value = [duplicate_entry]
        mock_repo.get_file.return_value = {"id": 1, "path": "/orig.txt"}
        mock_repo.delete_file = Mock()

        args = SimpleNamespace(
            action="delete",
            dry_run=True,
            container=fake_container,
            destination=None,
            verbose=False,
        )

        rc = tool.execute_apply(args)

        assert rc == 0
        out = capfd.readouterr().out
        assert "DRY-RUN" in out
        # In dry-run, delete_file should NOT be called
        assert mock_repo.delete_file.call_count == 0
