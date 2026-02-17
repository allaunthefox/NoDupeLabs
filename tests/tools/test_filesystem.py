import os
from pathlib import Path
from unittest.mock import patch

import pytest

from nodupe.tools.os_filesystem.filesystem import Filesystem, FilesystemError


def test_safe_write_and_safe_read_and_get_size(tmp_path):
    target = tmp_path / "data.bin"

    # Write bytes atomically (default)
    Filesystem.safe_write(target, b"hello world")
    assert target.exists()

    data = Filesystem.safe_read(target)
    assert data == b"hello world"

    # get_size should match
    assert Filesystem.get_size(target) == len(data)

    # Non-atomic write also works
    target2 = tmp_path / "data2.bin"
    Filesystem.safe_write(target2, b"abc", atomic=False)
    assert target2.read_bytes() == b"abc"


def test_safe_read_errors(tmp_path):
    missing = tmp_path / "missing.bin"
    with pytest.raises(FilesystemError):
        Filesystem.safe_read(missing)

    # Create a file larger than allowed max_size
    p = tmp_path / "big.bin"
    p.write_bytes(b"x" * 100)

    with pytest.raises(FilesystemError):
        Filesystem.safe_read(p, max_size=10)


def test_validate_path_and_list_directory_and_ensure_directory(tmp_path):
    d = tmp_path / "subdir"
    Filesystem.ensure_directory(d)
    assert d.exists() and d.is_dir()

    f1 = d / "a.txt"
    f1.write_text("x")
    f2 = d / "b.log"
    f2.write_text("y")

    # validate_path must_exist True works
    assert Filesystem.validate_path(f1, must_exist=True) is True

    # list_directory with pattern
    found = Filesystem.list_directory(d, pattern="*.txt")
    assert any(p.name == "a.txt" for p in found)

    # validate_path with non-existent and must_exist should raise
    with pytest.raises(FilesystemError):
        Filesystem.validate_path(tmp_path / "nope", must_exist=True)


def test_remove_copy_move_behaviors(tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("content")

    dst = tmp_path / "dst" / "src.txt"

    # copy_file succeeds
    Filesystem.copy_file(src, dst)
    assert dst.exists()

    # copy_file when destination exists and overwrite=False raises
    with pytest.raises(FilesystemError):
        Filesystem.copy_file(src, dst, overwrite=False)

    # move_file to a new location
    dest_move = tmp_path / "moved" / "src.txt"
    Filesystem.move_file(src, dest_move)
    assert dest_move.exists()

    # remove_file missing_ok True should not raise
    Filesystem.remove_file(tmp_path / "nope.txt", missing_ok=True)

    # remove_file missing_ok False should raise
    with pytest.raises(FilesystemError):
        Filesystem.remove_file(tmp_path / "nope2.txt", missing_ok=False)


def test_operations_raise_filesystem_error_on_oserror(tmp_path):
    # Simulate mkdir failing for ensure_directory
    with patch("pathlib.Path.mkdir", side_effect=OSError("perm")):
        with pytest.raises(FilesystemError):
            Filesystem.ensure_directory(tmp_path / "will/fail")

    # Simulate stat failing for get_size
    with patch("pathlib.Path.stat", side_effect=OSError("statfail")):
        with pytest.raises(FilesystemError):
            Filesystem.get_size(tmp_path / "nope")
