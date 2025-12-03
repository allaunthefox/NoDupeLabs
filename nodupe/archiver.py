# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

import zipfile
import tarfile
import os
from pathlib import Path
from typing import List, Dict, Any

try:
    import py7zr
    HAS_7Z = True
except ImportError:
    HAS_7Z = False

try:
    import zstandard  # type: ignore # noqa: F401,E501
    HAS_ZSTD = True
except ImportError:
    HAS_ZSTD = False

try:
    import rarfile
    HAS_RAR = True
except ImportError:
    HAS_RAR = False


class ArchiveHandler:
    def __init__(self, path: Path):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"Archive not found: {path}")
        self.type = self._detect_type()

    def _detect_type(self) -> str:
        s = str(self.path).lower()
        if s.endswith(".zip"):
            return "zip"
        if s.endswith(".7z"):
            return "7z"
        if s.endswith(".rar"):
            return "rar"
        if s.endswith(".tar"):
            return "tar"
        if s.endswith((".tar.gz", ".tgz")):
            return "tar"
        if s.endswith((".tar.bz2", ".tbz2")):
            return "tar"
        if s.endswith((".tar.xz", ".txz")):
            return "tar"
        return "unknown"

    def list_contents(self) -> List[Dict[str, Any]]:
        if self.type == "zip":
            return self._list_zip()
        if self.type == "7z":
            return self._list_7z()
        if self.type == "rar":
            return self._list_rar()
        if self.type == "tar":
            return self._list_tar()
        raise ValueError(f"Unsupported archive type: {self.type}")

    def extract(self, dest: Path) -> None:
        dest = Path(dest)
        dest.mkdir(parents=True, exist_ok=True)
        dest.mkdir(parents=True, exist_ok=True)
        if self.type == "zip":
            self._extract_zip(dest)
        elif self.type == "7z":
            self._extract_7z(dest)
        elif self.type == "rar":
            self._extract_rar(dest)
        elif self.type == "tar":
            self._extract_tar(dest)
        else:
            raise ValueError(f"Unsupported archive type: {self.type}")

    def _list_zip(self):
        results = []
        try:
            with zipfile.ZipFile(self.path, 'r') as zf:
                for info in zf.infolist():
                    results.append({
                        "path": info.filename,
                        "size": info.file_size,
                        "is_dir": info.is_dir()
                    })
        except (RuntimeError, zipfile.BadZipFile) as e:
            if "password" in str(e).lower() or "encrypted" in str(e).lower():
                raise PermissionError(
                    f"Password required for {self.path}"
                ) from e
            raise
        return results

    def _extract_zip(self, dest):
        try:
            with zipfile.ZipFile(self.path, 'r') as zf:
                zf.extractall(path=dest)
        except (RuntimeError, zipfile.BadZipFile) as e:
            if "password" in str(e).lower() or "encrypted" in str(e).lower():
                raise PermissionError(
                    f"Password required for {self.path}"
                ) from e
            raise

    def _list_7z(self):
        if not HAS_7Z:
            raise ImportError("py7zr not installed")
        results = []
        try:
            with py7zr.SevenZipFile(self.path, 'r') as archive:
                for f in archive.list():
                    results.append({
                        "path": f.filename,
                        "size": f.uncompressed,
                        "is_dir": f.is_directory
                    })
        except py7zr.exceptions.PasswordRequired as e:
            raise PermissionError(f"Password required for {self.path}") from e
        return results

    def _extract_7z(self, dest):
        if not HAS_7Z:
            raise ImportError("py7zr not installed")
        try:
            with py7zr.SevenZipFile(self.path, 'r') as archive:
                archive.extractall(path=dest)
        except py7zr.exceptions.PasswordRequired as e:
            raise PermissionError(f"Password required for {self.path}") from e

    def _list_rar(self):
        if not HAS_RAR:
            raise ImportError("rarfile not installed")
        try:
            results = []
            with rarfile.RarFile(self.path) as rf:
                for info in rf.infolist():
                    results.append({
                        "path": info.filename,
                        "size": info.file_size,
                        "is_dir": info.isdir()
                    })
            return results
        except rarfile.PasswordRequired as e:
            raise PermissionError(f"Password required for {self.path}") from e
        except rarfile.RarExecError as e:
            raise OSError("External tool 'unrar' not found") from e

    def _extract_rar(self, dest):
        if not HAS_RAR:
            raise ImportError("rarfile not installed")
        try:
            with rarfile.RarFile(self.path) as rf:
                rf.extractall(path=dest)
        except rarfile.PasswordRequired as e:
            raise PermissionError(f"Password required for {self.path}") from e
        except rarfile.RarExecError as e:
            raise OSError("External tool 'unrar' not found") from e

    def _list_tar(self):
        results = []
        with tarfile.open(self.path, 'r:*') as tf:
            for member in tf.getmembers():
                results.append({
                    "path": member.name,
                    "size": member.size,
                    "is_dir": member.isdir()
                })
        return results

    def _extract_tar(self, dest):
        with tarfile.open(self.path, 'r:*') as tf:
            def is_within_directory(directory, target):
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
                prefix = os.path.commonprefix([abs_directory, abs_target])
                return prefix == abs_directory

            for member in tf.getmembers():
                member_path = os.path.join(dest, member.name)
                if not is_within_directory(dest, member_path):
                    raise RuntimeError("Attempted Path Traversal in Tar File")
            tf.extractall(path=dest)
