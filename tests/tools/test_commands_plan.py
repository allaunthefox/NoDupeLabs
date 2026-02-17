import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from nodupe.core.database.files import FileRepository
from nodupe.tools.commands.plan import PlanTool
from nodupe.tools.databases.connection import DatabaseConnection
from nodupe.tools.databases.schema import DatabaseSchema


@pytest.fixture(autouse=True)
def clear_db_instances():
    DatabaseConnection._instances.clear()
    yield
    DatabaseConnection._instances.clear()


def _make_db_and_repo(tmp_path: Path):
    db_path = str(tmp_path / "plan_test.db")
    db_conn = DatabaseConnection.get_instance(db_path)
    DatabaseSchema(db_conn.get_connection()).create_schema()
    repo = FileRepository(db_conn)
    return db_conn, repo


def test_execute_plan_no_files_returns_zero(tmp_path: Path, capsys):
    db_conn, repo = _make_db_and_repo(tmp_path)

    class C:
        def get_service(self, name):
            if name == "database":
                return db_conn
            return None

    tool = PlanTool()
    args = SimpleNamespace(
        strategy="newest", output=str(tmp_path / "out.json"), container=C()
    )

    rc = tool.execute_plan(args)
    captured = capsys.readouterr()
    assert rc == 0
    assert "No files in database to plan" in captured.out


def test_execute_plan_groups_and_output_and_db_updates(tmp_path: Path):
    db_conn, repo = _make_db_and_repo(tmp_path)

    # create three files with same hash -> one keeper + two duplicates
    content = [
        {"path": "/tmp/a.txt", "size": 10, "modified_time": 100, "hash": "h"},
        {"path": "/tmp/b.txt", "size": 11, "modified_time": 50, "hash": "h"},
        {"path": "/tmp/c.txt", "size": 12, "modified_time": 75, "hash": "h"},
    ]

    ids = [
        repo.add_file(f["path"], f["size"], f["modified_time"], f["hash"])
        for f in content
    ]

    class C:
        def get_service(self, name):
            if name == "database":
                return db_conn
            return None

    out_file = tmp_path / "plan.json"
    tool = PlanTool()
    args = SimpleNamespace(
        strategy="newest", output=str(out_file), container=C()
    )

    rc = tool.execute_plan(args)
    assert rc == 0

    # output file created and contains actions
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert "actions" in data and isinstance(data["actions"], list)

    # newest keeper should be modified_time 100 -> /tmp/a.txt
    keep_actions = [a for a in data["actions"] if a["type"] == "KEEP"]
    delete_actions = [a for a in data["actions"] if a["type"] == "DELETE"]
    assert any("/tmp/a.txt" in k["path"] for k in keep_actions)
    assert len(delete_actions) == 2

    # DB should mark duplicates as duplicate_of keeper id
    keeper = repo.get_file_by_path("/tmp/a.txt")
    assert keeper is not None
    for d in ["/tmp/b.txt", "/tmp/c.txt"]:
        rec = repo.get_file_by_path(d)
        assert rec is not None
        assert rec["is_duplicate"] is True
        assert rec["duplicate_of"] == keeper["id"]


def test_execute_plan_oldest_strategy_and_reassign_keeper_when_marked_duplicate(
    tmp_path: Path, monkeypatch
):
    db_conn, repo = _make_db_and_repo(tmp_path)

    # create two files that will form a duplicate group
    id1 = repo.add_file("/tmp/old.txt", 10, 10, "hh")
    id2 = repo.add_file("/tmp/new.txt", 10, 20, "hh")

    # mark the oldest (keeper under 'oldest' strategy) as duplicate initially
    repo.update_file(id1, is_duplicate=True, duplicate_of=id2)

    # ensure FileRepository has a mark_as_original method so PlanTool can call it
    def _mark_as_original(self, file_id):
        return self.update_file(file_id, is_duplicate=False)

    monkeypatch.setattr(
        FileRepository, "mark_as_original", _mark_as_original, raising=False
    )

    class C:
        def get_service(self, name):
            if name == "database":
                return db_conn
            return None

    out_file = tmp_path / "plan2.json"
    tool = PlanTool()
    args = SimpleNamespace(
        strategy="oldest", output=str(out_file), container=C()
    )

    rc = tool.execute_plan(args)
    assert rc == 0

    # after plan, the oldest (/tmp/old.txt) should be the keeper and should have been unmarked
    keeper = repo.get_file_by_path("/tmp/old.txt")
    assert keeper is not None
    assert keeper["is_duplicate"] is False

    # the newer file should be marked duplicate_of keeper
    newer = repo.get_file_by_path("/tmp/new.txt")
    assert newer is not None
    assert newer["is_duplicate"] is True
    assert newer["duplicate_of"] == keeper["id"]


def test_execute_plan_ignores_files_without_hash(tmp_path: Path):
    db_conn, repo = _make_db_and_repo(tmp_path)

    # file without hash should be ignored
    repo.add_file("/tmp/nohash.txt", 1, 1, None)

    class C:
        def get_service(self, name):
            if name == "database":
                return db_conn
            return None

    tool = PlanTool()
    args = SimpleNamespace(
        strategy="newest", output=str(tmp_path / "out3.json"), container=C()
    )

    rc = tool.execute_plan(args)
    assert rc == 0
