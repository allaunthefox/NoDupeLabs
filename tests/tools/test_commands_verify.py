import argparse
import hashlib
import json
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

import pytest

from nodupe.tools.commands.verify import VerifyTool
from nodupe.tools.databases.connection import DatabaseConnection
from nodupe.tools.databases.schema import DatabaseSchema
from nodupe.tools.databases.files import FileRepository


@pytest.fixture(autouse=True)
def clear_db_instances():
    # ensure DatabaseConnection singleton does not leak between tests
    DatabaseConnection._instances.clear()
    yield
    DatabaseConnection._instances.clear()


def _make_db_and_repo(tmp_path: Path):
    db_path = str(tmp_path / "verify_test.db")
    db_conn = DatabaseConnection.get_instance(db_path)
    # create full schema expected by FileRepository
    DatabaseSchema(db_conn.get_connection()).create_schema()
    repo = FileRepository(db_conn)
    return db_conn, repo


def test_verify_integrity_missing_file_counts_error(tmp_path: Path):
    _, repo = _make_db_and_repo(tmp_path)
    # add a file record pointing to a non-existent path
    fid = repo.add_file(str(tmp_path / "missing.txt"), 123, 1, "h")
    assert fid is not None

    tool = VerifyTool()
    args = SimpleNamespace(fast=False, verbose=True)

    results = tool._verify_integrity(repo, args)
    assert results["checks"] == 1
    assert results["errors"] == 1
    assert results["warnings"] == 0


def test_verify_integrity_size_mismatch_and_read_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _, repo = _make_db_and_repo(tmp_path)

    # create a real file but store an incorrect size in DB
    p = tmp_path / "f.txt"
    p.write_bytes(b"hello-world")

    fid = repo.add_file(str(p), 9999, 1, "h")
    assert fid is not None

    tool = VerifyTool()
    args = SimpleNamespace(fast=False, verbose=True)

    # simulate a read error for this file only
    real_open = open

    def fake_open(path, *a, **kw):
        if Path(path) == p:
            raise OSError("cannot read")
        return real_open(path, *a, **kw)

    monkeypatch.setattr("builtins.open", fake_open)

    results = tool._verify_integrity(repo, args)
    # one check, size mismatch -> error, read error -> another error
    assert results["checks"] == 1
    assert results["errors"] >= 1


def test_verify_integrity_success(tmp_path: Path):
    _, repo = _make_db_and_repo(tmp_path)

    p = tmp_path / "ok.txt"
    content = b"good-content"
    p.write_bytes(content)

    fid = repo.add_file(str(p), len(content), 1, hashlib.sha256(content).hexdigest())
    assert fid is not None

    tool = VerifyTool()
    args = SimpleNamespace(fast=False, verbose=False)

    results = tool._verify_integrity(repo, args)
    assert results["checks"] == 1
    assert results["errors"] == 0


def test_verify_consistency_orphan_and_self_reference(tmp_path: Path):
    _, repo = _make_db_and_repo(tmp_path)

    # add original file
    a = tmp_path / "a.txt"
    a.write_text("x")
    id_a = repo.add_file(str(a), a.stat().st_size, 1, "h1")

    # add duplicate that references an original (we'll simulate the original being missing
    # at verification time by patching repo.get_file)
    b = tmp_path / "b.txt"
    b.write_text("y")
    id_b = repo.add_file(str(b), b.stat().st_size, 1, "h2")
    # mark as duplicate pointing to the original (valid in DB)
    repo.update_file(id_b, is_duplicate=True, duplicate_of=id_a)

    # add self-referencing file
    c = tmp_path / "c.txt"
    c.write_text("z")
    id_c = repo.add_file(str(c), c.stat().st_size, 1, "h3")
    repo.update_file(id_c, is_duplicate=True, duplicate_of=id_c)

    tool = VerifyTool()
    args = SimpleNamespace(fast=False, verbose=True)

    # simulate the original being missing during verification by patching get_file
    original_get_file = repo.get_file

    def fake_get_file(fid):
        if fid == id_a:
            return None
        return original_get_file(fid)

    repo.get_file = fake_get_file

    results = tool._verify_consistency(repo, args)
    # checks should be at least 3 and errors should reflect orphan + self-reference
    assert results["checks"] >= 3
    assert results["errors"] >= 2


def test_verify_checksums_fast_and_missing_and_mismatch_and_match(tmp_path: Path):
    _, repo = _make_db_and_repo(tmp_path)

    # fast mode should skip and return zeros
    tool = VerifyTool()
    args_fast = SimpleNamespace(fast=True, verbose=False)
    results = tool._verify_checksums(repo, args_fast)
    assert results == {"checks": 0, "errors": 0, "warnings": 0}

    # create file with no hash stored -> should warn
    f1 = tmp_path / "nohash.txt"
    f1.write_text("data")
    id1 = repo.add_file(str(f1), f1.stat().st_size, 1, None)

    args = SimpleNamespace(fast=False, verbose=True)
    results = tool._verify_checksums(repo, args)
    # no hash stored -> warning, checks should be 0 because it skips on missing hash
    assert results["warnings"] >= 1

    # create file with mismatched hash
    f2 = tmp_path / "mismatch.txt"
    f2.write_text("abcd")
    id2 = repo.add_file(str(f2), f2.stat().st_size, 1, "deadbeef")

    results = tool._verify_checksums(repo, args)
    # should detect the mismatch
    assert results["checks"] >= 1
    assert results["errors"] >= 1

    # create file with correct hash
    content = b"ok-content"
    f3 = tmp_path / "good.txt"
    f3.write_bytes(content)
    h = hashlib.sha256(content).hexdigest()
    id3 = repo.add_file(str(f3), f3.stat().st_size, 1, h)

    results = tool._verify_checksums(repo, args)
    # at least one successful check and no errors for the good file
    assert results["checks"] >= 1


def test_execute_verify_returns_nonzero_on_error_and_writes_output(tmp_path: Path, capsys):
    db_conn, repo = _make_db_and_repo(tmp_path)

    # add file with bad hash
    f = tmp_path / "bad.txt"
    f.write_text("bad")
    repo.add_file(str(f), f.stat().st_size, 1, "0000")

    # simple container that provides the database service
    class C:
        def get_service(self, name):
            if name == "database":
                return db_conn
            return None

    tool = VerifyTool()
    out_file = tmp_path / "out.json"
    args = SimpleNamespace(mode="checksums", fast=False, verbose=False, repair=False, output=str(out_file), container=C())

    rc = tool.execute_verify(args)
    assert rc == 1

    # output file should be created and contain JSON summary
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["summary"]["total_errors"] >= 1
    captured = capsys.readouterr()
    assert "Verification Summary" in captured.out
