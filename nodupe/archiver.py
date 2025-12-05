# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Archive file handling with unified interface.

This module provides a consistent API for working with various archive
formats (zip, tar, 7z, rar, etc.) including listing contents and
extraction.

Supported Formats:
    - ZIP (.zip) - Standard Python zipfile, always available
    - TAR (.tar, .tar.gz, .tgz, .tar.bz2, .tbz2, .tar.xz, .txz)
      - Standard Python tarfile, always available
    - 7Z (.7z) - Requires py7zr package (optional)
    - RAR (.rar) - Requires rarfile package and unrar tool (optional)

Key Features:
    - Automatic format detection from file extension
    - Graceful degradation when optional dependencies unavailable
    - Password-protected archive detection
    - Path traversal attack prevention (tar extraction)
    - Consistent dict-based return format for all archive types

Security:
    - TAR extraction validates all paths to prevent directory traversal
    - Password-protected archives raise PermissionError with clear message
    - External tool requirements (unrar) detected and reported

Dependencies:
    - zipfile, tarfile (standard library, always available)
    - py7zr (optional, for .7z support)
    - rarfile (optional, for .rar support, requires unrar binary)
    - zstandard (optional, for .tar.zst support)

Example:
    >>> from pathlib import Path
    >>> handler = ArchiveHandler(Path('archive.zip'))
    >>> contents = handler.list_contents()
    >>> for item in contents:
    ...     print(f"{item['path']}: {item['size']} bytes")
    >>> handler.extract(Path('/tmp/extracted'))
"""

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
    """Unified handler for various archive formats.

    Provides consistent interface for listing and extracting archive
    contents across multiple formats (zip, tar, 7z, rar).

    Attributes:
        path: Path to the archive file
        type: Detected archive type (zip, tar, 7z, rar, unknown)

    Raises:
        FileNotFoundError: If archive file doesn't exist
        ImportError: If optional dependency unavailable for format
        PermissionError: If archive requires password
        OSError: If external tool (unrar) not found

    Example:
        >>> handler = ArchiveHandler(Path('data.zip'))
        >>> print(handler.type)
        'zip'
        >>> files = handler.list_contents()
        >>> handler.extract(Path('/tmp/out'))
    """

    def __init__(self, path: Path):
        """Initialize archive handler with path.

        Args:
            path: Path to archive file

        Raises:
            FileNotFoundError: If path doesn't exist
        """
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"Archive not found: {path}")
        self.type = self._detect_type()

    def _detect_type(self) -> str:
        """Detect archive format from file extension.

        Returns:
            Archive type string: zip, tar, 7z, rar, or unknown
        """
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
        """List archive contents without extraction.

        Returns:
            List of dicts with keys:
                - path: Relative path within archive
                - size: Uncompressed size in bytes
                - is_dir: True if directory, False if file

        Raises:
            ImportError: If required library unavailable for format
            PermissionError: If archive requires password
            ValueError: If archive type unsupported
        """
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
        """Extract archive contents to destination directory.

        Creates destination directory if it doesn't exist. For tar archives,
        validates paths to prevent directory traversal attacks.

        Args:
            dest: Destination directory path

        Raises:
            ImportError: If required library unavailable for format
            PermissionError: If archive requires password
            OSError: If external tool unavailable (unrar)
            RuntimeError: If path traversal attempted in tar file
            ValueError: If archive type unsupported
        """
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
        """List contents of zip archive.

        Returns a list of dicts describing each entry in the zip file.
        """
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
        """Extract zip archive into destination directory.

        Args:
            dest: destination path where the archive will be extracted.
        """
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
        """List contents of a 7z archive using py7zr.

        Raises ImportError if py7zr is not available.
        """
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
        """Extract a 7z archive to the given destination.

        Args:
            dest: destination directory path
        """
        if not HAS_7Z:
            raise ImportError("py7zr not installed")
        try:
            with py7zr.SevenZipFile(self.path, 'r') as archive:
                archive.extractall(path=dest)
        except py7zr.exceptions.PasswordRequired as e:
            raise PermissionError(f"Password required for {self.path}") from e

    def _list_rar(self):
        """List contents of a rar archive using rarfile.

        Raises ImportError if rarfile is not available.
        """
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
        """Extract rar archive to destination directory.

        Args:
            dest: destination directory
        """
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
        """List contents of a tar archive.

        Uses the standard library tarfile module and returns a list of dicts
        describing entries (path, size, is_dir).
        """
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
        """Safely extract tar archive to destination, preventing path traversal.

        Args:
            dest: destination directory
        Raises:
            RuntimeError: if a path traversal attempt is detected
        """
        with tarfile.open(self.path, 'r:*') as tf:
            def is_within_directory(directory, target):
                """Return True if `target` path is inside `directory`.

                Used to protect against path traversal attacks when
                extracting tar archives.
                """
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
                prefix = os.path.commonprefix([abs_directory, abs_target])
                return prefix == abs_directory

            for member in tf.getmembers():
                member_path = os.path.join(dest, member.name)
                if not is_within_directory(dest, member_path):
                    raise RuntimeError("Attempted Path Traversal in Tar File")
            tf.extractall(path=dest)
