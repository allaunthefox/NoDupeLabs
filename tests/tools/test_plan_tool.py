import argparse
import json
from unittest.mock import Mock, patch

from nodupe.tools.commands.plan import PlanTool


def test_execute_plan_no_files(tmp_path):
    tool = PlanTool()
    args = argparse.Namespace(strategy="newest", output=str(tmp_path / "plan.json"), container=Mock())

    with patch("nodupe.core.database.files.FileRepository") as mock_repo_cls:
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_all_files.return_value = []

        rc = tool.execute_plan(args)

        assert rc == 0
        assert not (tmp_path / "plan.json").exists()


def test_execute_plan_groups_and_writes_plan(tmp_path):
    tool = PlanTool()
    out_file = tmp_path / "plan.json"
    args = argparse.Namespace(strategy="newest", output=str(out_file), container=Mock())

    files = [
        {"id": 1, "path": "/f/keep.txt", "hash": "h1", "modified_time": 100, "is_duplicate": False},
        {"id": 2, "path": "/f/dup1.txt", "hash": "h1", "modified_time": 50, "is_duplicate": True},
        {"id": 3, "path": "/f/dup2.txt", "hash": "h1", "modified_time": 10, "is_duplicate": True},
    ]

    with patch("nodupe.core.database.files.FileRepository") as mock_repo_cls:
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_all_files.return_value = files
        mock_repo.mark_as_duplicate = Mock()
        mock_repo.mark_as_original = Mock()

        rc = tool.execute_plan(args)

        assert rc == 0
        assert out_file.exists()

        data = json.loads(out_file.read_text())
        # 1 KEEP + 2 DELETE actions expected
        assert len(data["actions"]) == 3
        # mark_as_duplicate should have been called for the two duplicate ids
        assert mock_repo.mark_as_duplicate.call_count == 2


def test_register_commands_sets_defaults():
    tool = PlanTool()
    import argparse as _argparse

    parser = _argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    tool.register_commands(subparsers)
    p = parser.parse_args(["plan"])
    # Should attach a `func` attribute pointing to tool.execute_plan
    assert hasattr(p, "func")
    assert p.func == tool.execute_plan
